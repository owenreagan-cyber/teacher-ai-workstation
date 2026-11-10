"""Deterministic concurrency regression for device-pairing redemption.

Root cause this suite guards against
------------------------------------
`DeviceDatabase` uses one shared SQLite connection with an RLock. `execute()`
held the lock only for the statement call and returned a cursor; callers then
called `.fetchone()` outside the lock. When another thread committed on the
same connection in that window, SQLite reset the open statement and the fetch
returned a row whose columns were all NULL. `_row_to_record` then raised
`TypeError: int() argument must be ... not 'NoneType'` inside one of the two
concurrent redemptions instead of returning a clean conflict.

The fix materializes reads under the lock (`query_one` / `query_all`) and the
redemption path validates the state transition inside a transaction.

These tests use barriers and hooks rather than sleeps, so the interleavings are
reproducible.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import unittest
from pathlib import Path

from pairing_support import PairingStateTest

from cos.audit import verify as verify_audit
from cosd.devices import DeviceRegistry
from cosd.devices.models import DeviceError
from cosd.devices.pairing import PairingService
from cosd.devices.pairing.service import _row_to_record

from cosd.devices.pairing.client import test_identity


class ConcurrencyTests(PairingStateTest):
    def setUp(self):
        super().setUp()
        # Keep rate limits out of the way: these tests are about atomicity.
        self.pairing.invite_limit = 100000
        self.pairing.redeem_limit = 100000
        self.pairing.invite_window_s = 100000
        self.pairing.redeem_window_s = 100000

    # ---------------------------------------------------------------- helpers
    def _race(self, invitation, identities, *, after_read=None):
        """Start every thread, let all of them read, then release them together.

        `_find_code_row` is wrapped so each thread performs its lookup before
        any thread is allowed to write. That is the exact window the old code
        mishandled, made deterministic.
        """
        barrier = threading.Barrier(len(identities))
        original = self.pairing._find_code_row

        def hooked(enrollment_id, pairing_code):
            row = original(enrollment_id, pairing_code)
            barrier.wait(timeout=15)
            if after_read is not None:
                after_read()
            return row

        self.pairing._find_code_row = hooked
        results: list[tuple[str, object]] = [("pending", None)] * len(identities)
        redemptions: list[object] = [None] * len(identities)

        def worker(index: int) -> None:
            try:
                redemptions[index] = self.redeem(invitation, identities[index])
                results[index] = ("ok", None)
            except DeviceError as exc:
                results[index] = ("error", exc.http_status)
            except BaseException as exc:  # noqa: BLE001 - any leak is a failure
                results[index] = ("unexpected", type(exc).__name__)

        threads = [
            threading.Thread(target=worker, args=(index,), daemon=True)
            for index in range(len(identities))
        ]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=20)
        finally:
            self.pairing._find_code_row = original
        return results, redemptions

    def _assert_one_winner(self, results):
        self.assertEqual([r[0] for r in results].count("ok"), 1, results)
        for kind, detail in results:
            if kind == "ok":
                continue
            self.assertEqual(kind, "error", f"uncontrolled failure: {results}")
            self.assertIn(detail, (401, 409, 410), results)

    def _device_total(self) -> int:
        return int(self.registry.list_devices()["total"])

    # ------------------------------------------------- 1. two, then ten races
    def test_two_concurrent_redemptions_have_one_winner(self):
        invitation = self.invite()
        results, redemptions = self._race(invitation, [self.identity(b"a"), self.identity(b"b")])
        self._assert_one_winner(results)

        winner = redemptions[[r[0] for r in results].index("ok")]
        _, device, _ = self.approve(invitation)
        self.complete(invitation, winner, self.identity(b"a") if results[0][0] == "ok" else self.identity(b"b"))
        self.assertEqual(self._device_total(), 1)
        self.assertEqual(len(self.registry.list_credentials(device["device_id"])), 1)

    def test_ten_concurrent_redemptions_have_one_winner(self):
        invitation = self.invite()
        identities = [self.identity(bytes([i])) for i in range(10)]
        results, _ = self._race(invitation, identities)
        self._assert_one_winner(results)

    def test_same_code_with_different_identities_creates_one_device(self):
        invitation = self.invite()
        identities = [self.identity(b"id-%d" % i) for i in range(5)]
        results, redemptions = self._race(invitation, identities)
        self._assert_one_winner(results)

        idx = [r[0] for r in results].index("ok")
        _, device, _ = self.approve(invitation, profile="school")
        self.complete(invitation, redemptions[idx], identities[idx])
        self.assertEqual(self._device_total(), 1)
        credentials = self.registry.list_credentials(device["device_id"])
        self.assertEqual(len(credentials), 1)

    # ------------------------------------- 2. races with terminal transitions
    def test_redemption_racing_expiry_fails_closed(self):
        invitation = self.invite()
        results, _ = self._race(
            invitation,
            [self.identity(b"exp")],
            after_read=lambda: self.advance(10 ** 6),
        )
        self.assertEqual(results[0][0], "error", results)
        self.assertEqual(results[0][1], 410, results)
        self.assertEqual(self._device_total(), 0)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "EXPIRED",
        )

    def test_redemption_racing_cancellation_fails_closed(self):
        invitation = self.invite()
        results, _ = self._race(
            invitation,
            [self.identity(b"cancel")],
            after_read=lambda: self.pairing.cancel(
                invitation.enrollment.enrollment_id, confirm=True
            ),
        )
        self.assertEqual(results[0][0], "error", results)
        self.assertIn(results[0][1], (409, 410), results)
        self.assertEqual(self._device_total(), 0)

    def test_approval_racing_second_redemption_keeps_one_device(self):
        invitation = self.invite()
        identity = self.identity(b"approve")
        redemption = self.redeem(invitation, identity)

        barrier = threading.Barrier(2)
        outcome: dict[str, object] = {}

        def approve_worker():
            barrier.wait(timeout=10)
            try:
                outcome["approve"] = self.approve(invitation)
            except DeviceError as exc:
                outcome["approve_error"] = exc.http_status

        def redeem_worker():
            barrier.wait(timeout=10)
            try:
                self.redeem(invitation, self.identity(b"late"))
                outcome["redeem"] = "ok"
            except DeviceError as exc:
                outcome["redeem"] = f"error:{exc.http_status}"

        threads = [threading.Thread(target=approve_worker), threading.Thread(target=redeem_worker)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertNotIn("redeem", {k: v for k, v in outcome.items() if v == "ok"}, outcome)
        self.assertIn(str(outcome.get("redeem")), ("error:409", "error:410"), outcome)
        self.assertIn("approve", outcome, outcome)
        _, device, _ = outcome["approve"]
        self.complete(invitation, redemption, identity)
        self.assertEqual(len(self.registry.list_credentials(device["device_id"])), 1)

    def test_repeated_approval_issues_one_credential(self):
        invitation = self.invite()
        identity = self.identity(b"double-approve")
        redemption = self.redeem(invitation, identity)
        _, device, _ = self.approve(invitation)

        with self.assertRaises(DeviceError):
            self.approve(invitation)

        self.complete(invitation, redemption, identity)
        self.assertEqual(len(self.registry.list_credentials(device["device_id"])), 1)

    # ------------------------------------------- 3. malformed and legacy rows
    def test_missing_protocol_version_fails_closed(self):
        row = {"protocol_version": None}
        with self.assertRaises(DeviceError) as caught:
            _row_to_record(row)
        self.assertEqual(caught.exception.http_status, 409)

    def test_unsupported_protocol_version_is_rejected(self):
        invitation = self.invite()
        with self.assertRaises(DeviceError):
            self.redeem(invitation, self.identity(b"v99"), protocol_version=99)
        self.assertEqual(self._device_total(), 0)

    def test_partially_populated_record_does_not_raise_type_error(self):
        # A record with a protocol version but no identity material must not
        # explode: redeem treats it as unusable and fails closed.
        invitation = self.invite()
        record = self.registry.db.query_one(
            "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
            (invitation.enrollment.enrollment_id,),
        )
        parsed = _row_to_record(record)
        self.assertEqual(parsed.protocol_version, 1)

    # ------------------------------------- 4. interruption, restart and retry
    def test_interrupted_transaction_leaves_no_partial_state(self):
        invitation = self.invite()
        identity = self.identity(b"interrupt")
        original = self.pairing._update
        calls = {"n": 0}

        def failing_update(*args, **kwargs):
            calls["n"] += 1
            raise RuntimeError("simulated crash before commit")

        self.pairing._update = failing_update
        try:
            with self.assertRaises(RuntimeError):
                self.redeem(invitation, identity)
        finally:
            self.pairing._update = original

        self.assertGreaterEqual(calls["n"], 1)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "PENDING",
        )
        self.assertEqual(self._device_total(), 0)

    def test_restart_preserves_committed_redemption(self):
        invitation = self.invite()
        self.redeem(invitation, self.identity(b"restart"))
        enrollment_id = invitation.enrollment.enrollment_id

        self.registry.close()
        reopened = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        try:
            service = PairingService(reopened, cipher=self.cipher, clock=lambda: self.now)
            self.assertEqual(
                service.get_enrollment(enrollment_id).status, "AWAITING_OWNER_APPROVAL"
            )
        finally:
            reopened.close()
        # Leave a usable registry for tearDown.
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        self.pairing = PairingService(self.registry, cipher=self.cipher, clock=lambda: self.now)

    def test_retry_after_uncertain_response_is_conflict(self):
        invitation = self.invite()
        identity = self.identity(b"retry")
        self.redeem(invitation, identity)
        with self.assertRaises(DeviceError) as caught:
            self.redeem(invitation, identity)
        self.assertEqual(caught.exception.http_status, 409)
        self.assertEqual(self._device_total(), 0)

    # ------------------------------------------------ 5. contention and audit
    def test_write_transaction_blocks_reader_without_corruption(self):
        invitation = self.invite()
        barrier = threading.Barrier(2)
        errors: list[str] = []

        def reader():
            barrier.wait(timeout=10)
            try:
                self.redeem(invitation, self.identity(b"blocked"))
            except DeviceError:
                pass
            except BaseException as exc:  # noqa: BLE001
                errors.append(type(exc).__name__)

        thread = threading.Thread(target=reader)
        with self.registry.db.transaction() as conn:
            thread.start()
            barrier.wait(timeout=10)
            # Hold the write transaction while the reader blocks on the lock.
            conn.execute(
                "UPDATE enrollment_requests SET updated_at = updated_at WHERE enrollment_id = ?",
                (invitation.enrollment.enrollment_id,),
            )
        thread.join(timeout=20)
        self.assertEqual(errors, [])

    def test_independent_invitations_do_not_interfere(self):
        invitations = [self.invite(display_name=f"Device {i}") for i in range(5)]
        results: list[str] = []

        def worker(invitation, index):
            try:
                self.redeem(invitation, self.identity(b"ind-%d" % index))
                results.append("ok")
            except DeviceError as exc:
                results.append(f"error:{exc.http_status}")

        threads = [
            threading.Thread(target=worker, args=(inv, i)) for i, inv in enumerate(invitations)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertEqual(results.count("ok"), 5, results)

    def test_audit_records_one_success_and_one_replay(self):
        invitation = self.invite()
        results, _ = self._race(invitation, [self.identity(b"audit-a"), self.identity(b"audit-b")])
        self._assert_one_winner(results)

        lines = [
            json.loads(line)
            for line in Path(self.audit_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        kinds = [entry.get("kind") for entry in lines]
        self.assertEqual(kinds.count("pairing.redeemed"), 1, kinds)
        # The loser takes one of two legitimate paths: an audited replay
        # refusal (it observed the new state) or a transaction-level conflict
        # (it raced to the write). Neither may record a success.
        self.assertLessEqual(kinds.count("pairing.replay_denied"), 1, kinds)
        # Nothing may be recorded as a successful completion before approval.
        self.assertNotIn("pairing.completed", kinds)
        self.assertTrue(verify_audit(self.audit_path).ok)


class ReadCoherencyTests(PairingStateTest):
    """The direct regression for the all-NULL row."""

    def test_read_helpers_return_coherent_rows_under_concurrent_writes(self):
        invitation = self.invite()
        enrollment_id = invitation.enrollment.enrollment_id
        stop = threading.Event()
        failures: list[str] = []

        def writer():
            while not stop.is_set():
                with self.registry.db.transaction() as conn:
                    conn.execute(
                        "UPDATE enrollment_requests SET updated_at = ? WHERE enrollment_id = ?",
                        (f"stamp-{threading.get_ident()}", enrollment_id),
                    )

        thread = threading.Thread(target=writer, daemon=True)
        thread.start()
        try:
            for _ in range(300):
                row = self.registry.db.query_one(
                    "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
                    (enrollment_id,),
                )
                if row is None or row["enrollment_id"] is None or row["protocol_version"] is None:
                    failures.append(dict(row) if row is not None else "no row")
                    break
        finally:
            stop.set()
            thread.join(timeout=20)
        self.assertEqual(failures, [])


class StaticGuardTests(unittest.TestCase):
    """Prevent reintroduction of the cursor-fetch pattern that caused this bug.

    A read is only safe when it runs on a connection whose lock is already
    held: the connection yielded by ``transaction()`` (``conn`` / ``c`` /
    ``active_conn``) or the internal connection inside ``_migrate``. Every
    other receiver is flagged, so an alias such as ``db``, ``self.db``,
    ``self._db`` or a future helper cannot slip through.
    """

    SAFE_RECEIVER = re.compile(r"\b(?:conn|c|active_conn|self\._conn)\s*$")

    def test_cosd_modules_do_not_fetch_from_a_shared_cursor(self):
        repo_root = Path(__file__).resolve().parents[4]
        root = repo_root / "cosd"
        offenders: list[str] = []
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts or path.name.startswith("test_"):
                continue
            text = path.read_text(encoding="utf-8")
            index = 0
            while True:
                index = text.find(".execute(", index)
                if index == -1:
                    break
                tail = text[index: index + 400]
                chained = ".fetchone()" in tail or ".fetchall()" in tail
                receiver = text[max(0, index - 40): index]
                safe = bool(self.SAFE_RECEIVER.search(receiver))
                if chained and not safe:
                    line = text.count("\n", 0, index) + 1
                    offenders.append(f"{path.relative_to(repo_root)}:{line}")
                index += len(".execute(")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
