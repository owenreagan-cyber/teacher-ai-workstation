"""Credential-provider lock scope: correctness under slow or failing providers.

P0.3a's review found that `approve()` performs credential-provider I/O while
holding the shared database lock. This suite pins the correctness invariants
around that design and measures its practical impact; it does not claim the
lock scope is optimal.
"""
from __future__ import annotations

import threading
import time
import unittest

from pairing_support import PairingStateTest

from cosd.devices import CredentialProviderError, DeviceRegistry, MemoryCredentialProvider
from cosd.devices.models import DeviceError
from cosd.devices.pairing import PairingService


class SlowProvider(MemoryCredentialProvider):
    """Counts and delays writes; can fail on the Nth write (1=credential, 2=envelope)."""

    def __init__(self, delay_s: float = 0.4, fail_on_call: int | None = None):
        super().__init__()
        self.delay_s = delay_s
        self.fail_on_call = fail_on_call
        self.set_calls = 0

    def set_secret(self, reference: str, secret: str) -> None:
        self.set_calls += 1
        time.sleep(self.delay_s)
        if self.fail_on_call == self.set_calls:
            raise CredentialProviderError("provider unavailable")
        super().set_secret(reference, secret)


class LockScopeTests(PairingStateTest):
    delay_s = 0.4

    def setUp(self):
        super().setUp()
        self.registry.close()
        self.provider = SlowProvider(delay_s=self.delay_s)
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        self.pairing = PairingService(self.registry, cipher=self.cipher, clock=lambda: self.now)

    def test_slow_provider_still_issues_exactly_one_credential(self):
        invitation = self.invite()
        identity = self.identity(b"slow")
        redemption = self.redeem(invitation, identity)

        started = time.monotonic()
        _, device, _ = self.approve(invitation)
        elapsed = time.monotonic() - started

        self.assertGreaterEqual(elapsed, self.delay_s)
        self.assertLess(elapsed, 10.0)
        self.assertEqual(self.provider.set_calls, 2)
        self.assertEqual(len(self.registry.list_credentials(device["device_id"])), 1)
        # The credential only becomes usable after the committed approval.
        self.complete(invitation, redemption, identity)

    def test_reads_during_slow_provider_remain_bounded(self):
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"scope"))
        latencies: list[float] = []
        stop = threading.Event()

        def reader():
            while not stop.is_set():
                started = time.monotonic()
                self.registry.list_devices()
                latencies.append(time.monotonic() - started)
                time.sleep(0.01)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        try:
            self.approve(invitation)
        finally:
            stop.set()
            thread.join(timeout=10)

        self.assertTrue(latencies)
        # Current design serializes reads behind provider I/O. Bound it: a
        # stalled provider must not block reads indefinitely.
        self.assertLess(max(latencies), 5.0)

    def test_concurrent_approvals_issue_one_credential(self):
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"race"))
        results: list[str] = []
        barrier = threading.Barrier(2)

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
        self.assertEqual(self.provider.set_calls, 2)
        devices = self.registry.list_devices()["devices"]
        self.assertEqual(len(devices), 1)
        self.assertEqual(len(self.registry.list_credentials(devices[0]["device_id"])), 1)


class ProviderFailureTests(PairingStateTest):
    def test_provider_failure_after_reservation_leaves_no_approved_device(self):
        self.registry.close()
        self.provider = SlowProvider(delay_s=0.01, fail_on_call=2)
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        self.pairing = PairingService(self.registry, cipher=self.cipher, clock=lambda: self.now)

        invitation = self.invite()
        self.redeem(invitation, self.identity(b"fail"))

        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 503)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "AWAITING_OWNER_APPROVAL",
        )


if __name__ == "__main__":
    unittest.main()
