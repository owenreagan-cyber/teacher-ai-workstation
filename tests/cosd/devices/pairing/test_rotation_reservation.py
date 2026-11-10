"""Crash-consistent credential rotation (P0.3c.2).

Rotation reserves durably, writes the new secret with no database lock held,
then activates in one short transaction. The old credential stays usable until
that commit.
"""
from __future__ import annotations

import threading
import time
import unittest
from unittest import mock

from pairing_support import PairingStateTest

from cosd.devices import CredentialProviderError, DeviceRegistry, MemoryCredentialProvider
from cosd.devices.models import DeviceError


class HookProvider(MemoryCredentialProvider):
    def __init__(self, *, delay_s: float = 0.0, fail_set: int | None = None, fail_delete: int = 0):
        super().__init__()
        self.delay_s = delay_s
        self.fail_set = fail_set
        self.fail_delete = fail_delete
        self.sets = 0
        self.deletes = 0

    def set_secret(self, reference: str, secret: str) -> None:
        self.sets += 1
        if self.delay_s:
            time.sleep(self.delay_s)
        if self.fail_set == self.sets:
            raise CredentialProviderError("provider unavailable")
        super().set_secret(reference, secret)

    def delete_secret(self, reference: str) -> None:
        self.deletes += 1
        if self.fail_delete and self.deletes <= self.fail_delete:
            raise CredentialProviderError("delete unavailable")
        super().delete_secret(reference)


class RotationTests(PairingStateTest):
    def setUp(self):
        super().setUp()
        self.registry.close()
        self.provider = HookProvider()
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        self.device, self.issued = self.registry.register_device(
            display_name="Rotate", device_type="mac", platform="macos",
            owner_id="school", device_profile="school",
        )

    def _active_ids(self) -> list[str]:
        return [c["credential_id"] for c in self.registry.list_credentials(self.device.device_id)
                if c["status"] == "active"]

    def _reservation(self):
        return self.registry.db.query_one(
            "SELECT * FROM credential_rotation_reservations WHERE credential_id = ?",
            (self.issued.credential_id,),
        )

    def test_successful_rotation_swaps_authority(self):
        rotated = self.registry.credentials.rotate(self.issued.credential_id)
        self.assertNotEqual(rotated.credential_id, self.issued.credential_id)
        with self.assertRaises(Exception):
            self.registry.credentials.verify_token(self.issued.token)
        self.assertEqual(
            self.registry.credentials.verify_token(rotated.token).credential_id,
            rotated.credential_id,
        )
        self.assertEqual(self._active_ids(), [rotated.credential_id])
        self.assertIsNone(self._reservation())

    def test_two_concurrent_rotations_have_one_winner(self):
        results: list[str] = []
        barrier = threading.Barrier(2)

        def worker():
            barrier.wait(timeout=10)
            try:
                self.registry.credentials.rotate(self.issued.credential_id)
                results.append("ok")
            except DeviceError as exc:
                results.append(f"error:{exc.http_status}")

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertEqual(results.count("ok"), 1, results)
        self.assertEqual(len([r for r in results if r.startswith("error")]), 1, results)
        self.assertEqual(len(self._active_ids()), 1)

    def test_ten_concurrent_rotations_have_one_winner(self):
        results: list[str] = []
        barrier = threading.Barrier(10)

        def worker():
            barrier.wait(timeout=15)
            try:
                self.registry.credentials.rotate(self.issued.credential_id)
                results.append("ok")
            except DeviceError as exc:
                results.append(f"error:{exc.http_status}")

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertEqual(results.count("ok"), 1, results)
        self.assertEqual(len(self._active_ids()), 1)

    def test_provider_failure_keeps_old_credential_usable(self):
        # Registration already used write #1 on this provider; the next fails.
        self.provider.fail_set = 2
        with self.assertRaises(DeviceError) as caught:
            self.registry.credentials.rotate(self.issued.credential_id)
        self.assertEqual(caught.exception.http_status, 503)
        self.assertEqual(self._active_ids(), [self.issued.credential_id])
        self.assertEqual(
            self.registry.credentials.verify_token(self.issued.token).credential_id,
            self.issued.credential_id,
        )
        self.assertIsNone(self._reservation())

    def test_activation_failure_keeps_old_credential_usable(self):
        with mock.patch.object(self.registry.credentials, "_insert", side_effect=RuntimeError("db")):
            with self.assertRaises(RuntimeError):
                self.registry.credentials.rotate(self.issued.credential_id)
        self.assertEqual(self._active_ids(), [self.issued.credential_id])
        self.assertIsNone(self._reservation())
        self.assertEqual(
            self.registry.credentials.verify_token(self.issued.token).credential_id,
            self.issued.credential_id,
        )

    def test_startup_reconciliation_clears_pending_rotation_and_retry_succeeds(self):
        # Simulate a crash after the reservation commit: reservation + orphan secret.
        orphan = "device:orphan-rotation"
        self.provider.set_secret(orphan, "orphan-secret")
        with self.registry.db.transaction() as conn:
            conn.execute(
                """INSERT INTO credential_rotation_reservations(
                    credential_id, reservation_id, new_credential_id, new_keychain_ref,
                    device_id, created_at, expires_at, attempts, state, reason
                ) VALUES (?, 'res-rotate', 'new-cred', ?, ?, ?, ?, 0, 'pending', NULL)""",
                (self.issued.credential_id, orphan, self.device.device_id,
                 "2026-01-01T00:00:00+00:00", "2099-01-01T00:00:00+00:00"),
            )
        report = self.registry.reconcile_credential_rotations()
        self.assertIn(self.issued.credential_id, report["cleaned"])
        self.assertIsNone(self._reservation())
        self.assertEqual(self.provider.get_secret(orphan), None)
        # The old credential is still authoritative and rotation can be retried.
        self.assertEqual(self._active_ids(), [self.issued.credential_id])
        rotated = self.registry.credentials.rotate(self.issued.credential_id)
        self.assertEqual(self.registry.credentials.verify_token(rotated.token).credential_id,
                         rotated.credential_id)

    def test_old_secret_cleanup_failure_is_recorded_and_reconciled(self):
        provider = HookProvider(fail_delete=1)
        self.registry.close()
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=provider, audit=self.audit
        )
        rotated = self.registry.credentials.rotate(self.issued.credential_id)
        self.assertIsNotNone(
            self.registry.db.query_one(
                "SELECT * FROM credential_rotation_reservations WHERE state = 'cleanup_failed'"
            )
        )
        provider.fail_delete = 0
        self.registry.reconcile_credential_rotations()
        self.assertIsNone(
            self.registry.db.query_one(
                "SELECT * FROM credential_rotation_reservations WHERE state = 'cleanup_failed'"
            )
        )
        self.assertEqual(self.registry.credentials.verify_token(rotated.token).credential_id,
                         rotated.credential_id)

    def test_unrelated_reads_are_not_blocked_by_rotation(self):
        provider = HookProvider(delay_s=1.0)
        self.registry.close()
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=provider, audit=self.audit
        )
        latencies: list[float] = []
        stop = threading.Event()

        def reader():
            while not stop.is_set():
                started = time.monotonic()
                self.registry.list_devices()
                latencies.append(time.monotonic() - started)
                time.sleep(0.003)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        try:
            started = time.monotonic()
            self.registry.credentials.rotate(self.issued.credential_id)
            elapsed = time.monotonic() - started
        finally:
            stop.set()
            thread.join(timeout=20)
        self.assertGreaterEqual(elapsed, 1.0)
        self.assertGreater(len(latencies), 100)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        self.assertLess(p95, 0.25, f"p95={p95:.3f}s over {len(latencies)} samples")


if __name__ == "__main__":
    unittest.main()
