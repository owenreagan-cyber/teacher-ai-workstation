"""Crash-consistent credential reservation (P0.3c.1).

The provider runs outside the database lock; the authoritative database decides
whether a credential is active. These tests use barriers and fault injection,
not sleeps, except where a deliberate provider delay is the thing being measured.
"""
from __future__ import annotations

import statistics
import threading
import time
import unittest
from unittest import mock

from pairing_support import PairingStateTest

from cosd.devices import CredentialProviderError, MemoryCredentialProvider
from cosd.devices.models import DeviceError


class HookProvider(MemoryCredentialProvider):
    """Counts writes and can run a hook or fail on a chosen write."""

    def __init__(self, *, delay_s: float = 0.0, fail_on: int | None = None, hook=None):
        super().__init__()
        self.delay_s = delay_s
        self.fail_on = fail_on
        self.hook = hook
        self.writes = 0

    def set_secret(self, reference: str, secret: str) -> None:
        self.writes += 1
        if self.delay_s:
            time.sleep(self.delay_s)
        if self.hook is not None:
            self.hook(self.writes)
        if self.fail_on == self.writes:
            raise CredentialProviderError("provider unavailable")
        super().set_secret(reference, secret)


class ReservationTests(PairingStateTest):
    def _install(self, provider):
        self.registry.close()
        from cosd.devices import DeviceRegistry
        from cosd.devices.pairing import PairingService

        self.registry = DeviceRegistry.open(
            self.state, credential_provider=provider, audit=self.audit
        )
        self.pairing = PairingService(self.registry, cipher=self.cipher, clock=lambda: self.now)
        return provider

    def _reservation(self, enrollment_id):
        return self.registry.db.query_one(
            "SELECT * FROM credential_reservations WHERE enrollment_id = ?", (enrollment_id,)
        )

    def test_two_concurrent_approvals_issue_one_credential(self):
        self._install(HookProvider(delay_s=0.15))
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"two"))
        barrier = threading.Barrier(2)
        results: list[str] = []

        def worker():
            barrier.wait(timeout=10)
            try:
                self.approve(invitation)
                results.append("ok")
            except DeviceError as exc:
                results.append(f"error:{exc.http_status}")

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertEqual(results.count("ok"), 1, results)
        self.assertEqual(len(results), 2, results)
        self.assertIn("error:409", results)
        devices = self.registry.list_devices()["devices"]
        self.assertEqual(len(devices), 1)
        self.assertEqual(len(self.registry.list_credentials(devices[0]["device_id"])), 1)
        self.assertIsNone(self._reservation(invitation.enrollment.enrollment_id))

    def test_ten_concurrent_approvals_issue_one_credential(self):
        self._install(HookProvider())
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"ten"))
        barrier = threading.Barrier(10)
        results: list[str] = []

        def worker():
            barrier.wait(timeout=15)
            try:
                self.approve(invitation)
                results.append("ok")
            except DeviceError as exc:
                results.append(f"error:{exc.http_status}")

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertEqual(results.count("ok"), 1, results)
        devices = self.registry.list_devices()["devices"]
        self.assertEqual(len(devices), 1)
        self.assertEqual(len(self.registry.list_credentials(devices[0]["device_id"])), 1)

    def test_independent_enrollments_proceed_independently(self):
        self._install(HookProvider(delay_s=0.2))
        invitations = [self.invite(display_name=f"D{i}") for i in range(3)]
        for i, invitation in enumerate(invitations):
            self.redeem(invitation, self.identity(bytes([i])))
        barrier = threading.Barrier(3)
        outcomes: list[str] = []

        def worker(invitation):
            barrier.wait(timeout=15)
            try:
                self.approve(invitation)
                outcomes.append("ok")
            except DeviceError as exc:
                outcomes.append(f"error:{exc.http_status}")

        threads = [threading.Thread(target=worker, args=(inv,)) for inv in invitations]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertEqual(outcomes.count("ok"), 3, outcomes)

    def test_provider_failure_before_credential_write_leaves_nothing(self):
        provider = self._install(HookProvider(fail_on=1))
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"fail1"))
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 503)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertIsNone(self._reservation(invitation.enrollment.enrollment_id))
        self.assertEqual(provider.count(), 0)

    def test_provider_failure_after_credential_write_cleans_up(self):
        provider = self._install(HookProvider(fail_on=2))
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"fail2"))
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 503)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertIsNone(self._reservation(invitation.enrollment.enrollment_id))
        self.assertEqual(provider.count(), 0)

    def test_activation_failure_cleans_provider_and_leaves_enrollment_pending(self):
        provider = self._install(HookProvider())
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"actfail"))
        with mock.patch.object(self.registry, "register_device", side_effect=RuntimeError("db gone")):
            with self.assertRaises(RuntimeError):
                self.approve(invitation)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertIsNone(self._reservation(invitation.enrollment.enrollment_id))
        self.assertEqual(provider.count(), 0)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "AWAITING_OWNER_APPROVAL",
        )

    def test_retry_after_success_is_conflict(self):
        self._install(HookProvider())
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"retry"))
        self.approve(invitation)
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)
        devices = self.registry.list_devices()["devices"]
        self.assertEqual(len(self.registry.list_credentials(devices[0]["device_id"])), 1)

    def test_reservation_expiry_during_provider_blocks_activation(self):
        def expire(call):
            if call == 1:
                self.advance(int(self.pairing.approval_ttl_s) + 5)

        self._install(HookProvider(hook=expire))
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"expire"))
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertIsNone(self._reservation(invitation.enrollment.enrollment_id))

    def test_cancellation_during_provider_blocks_activation(self):
        def cancel(call):
            if call == 1:
                self.pairing.cancel(invitation.enrollment.enrollment_id, confirm=True)

        invitation = self.invite()
        self._install(HookProvider(hook=cancel))
        self.redeem(invitation, self.identity(b"cancel"))
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)
        self.assertEqual(self.registry.list_devices()["total"], 0)

    def test_reconciliation_is_idempotent_and_never_approves(self):
        self._install(HookProvider())
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"reconcile"))
        enrollment_id = invitation.enrollment.enrollment_id
        # Simulate a crash right after the reservation commit.
        with self.registry.db.transaction() as conn:
            conn.execute(
                """INSERT INTO credential_reservations(
                    enrollment_id, reservation_id, credential_id, delivery_ref,
                    device_profile, public_key_fingerprint, expected_state, generation,
                    created_at, expires_at, attempts, state, reason
                ) VALUES (?, 'res1', 'cred1', 'enrollment:' || ?, 'school', ?, 'AWAITING_OWNER_APPROVAL', 1, ?, ?, 0, 'pending', NULL)""",
                (enrollment_id, enrollment_id, "fingerprint", "2020-01-01T00:00:00+00:00",
                 "2020-01-01T00:00:05+00:00"),
            )
        first = self.pairing.reconcile_reservations()
        second = self.pairing.reconcile_reservations()
        self.assertIn(enrollment_id, first["cleaned"])
        self.assertEqual(second["cleaned"], [])
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertEqual(
            self.pairing.get_enrollment(enrollment_id).status, "AWAITING_OWNER_APPROVAL"
        )

    def test_unrelated_reads_are_not_blocked_by_a_slow_provider(self):
        self._install(HookProvider(delay_s=1.0))
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"perf"))
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
            self.approve(invitation)
            elapsed = time.monotonic() - started
        finally:
            stop.set()
            thread.join(timeout=20)

        self.assertGreaterEqual(elapsed, 2.0)
        self.assertGreater(len(latencies), 100)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        self.assertLess(p95, 0.25, f"p95={p95:.3f}s over {len(latencies)} samples")
        self.assertLess(max(latencies), 1.0)


if __name__ == "__main__":
    unittest.main()
