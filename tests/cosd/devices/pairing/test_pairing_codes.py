"""Pairing code entropy, expiry, single-use, replay, and rate limiting."""
from __future__ import annotations

import threading
import unittest
from datetime import datetime

from pairing_support import PairingStateTest

from cosd.devices import DeviceError
from cosd.devices.pairing.codes import (
    ALPHABET,
    CODE_LENGTH,
    generate_pairing_code,
    normalize_pairing_code,
    parse_qr_payload,
)


class CodeTests(PairingStateTest):
    def test_code_format_and_entropy(self):
        codes = {generate_pairing_code() for _ in range(300)}
        self.assertEqual(len(codes), 300)
        for display in list(codes)[:20]:
            normalized = normalize_pairing_code(display)
            self.assertEqual(len(normalized), CODE_LENGTH)
            self.assertTrue(all(ch in ALPHABET for ch in normalized))
            self.assertRegex(display, r"^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$")

    def test_normalization_accepts_common_input(self):
        self.assertEqual(normalize_pairing_code("abcd-efgh-jkmn"), "ABCDEFGHJKMN")
        self.assertEqual(normalize_pairing_code("ABCD EFGH JKMN"), "ABCDEFGHJKMN")
        with self.assertRaises(DeviceError):
            normalize_pairing_code("too-short")
        with self.assertRaises(DeviceError):
            normalize_pairing_code("ABCD-EFGH-JKM0")

    def test_invitation_has_ten_minute_code_and_qr_minimum(self):
        invitation = self.invite()
        created = datetime.fromisoformat(invitation.enrollment.created_at)
        expires = datetime.fromisoformat(invitation.enrollment.expires_at)
        self.assertLessEqual((expires - created).total_seconds(), 600)
        payload = parse_qr_payload(invitation.qr_payload)
        self.assertEqual(payload["enrollment_id"], invitation.enrollment.enrollment_id)
        self.assertEqual(payload["code"], invitation.pairing_code)
        self.assertNotIn("token", invitation.qr_payload.lower())
        self.assertNotIn("secret", invitation.qr_payload.lower())
        self.assertNotIn("credential", invitation.qr_payload.lower())

    def test_code_expires_and_cannot_be_used(self):
        invitation = self.invite()
        self.advance(601)
        with self.assertRaises(DeviceError) as caught:
            self.redeem(invitation)
        self.assertEqual(caught.exception.http_status, 410)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "EXPIRED",
        )

    def test_code_is_single_use_and_replay_is_denied(self):
        invitation = self.invite()
        identity = self.identity()
        first = self.redeem(invitation, identity)
        self.assertTrue(first.request_token)
        with self.assertRaises(DeviceError) as caught:
            self.redeem(invitation, identity)
        self.assertEqual(caught.exception.http_status, 409)
        events = self.registry.events_for(
            f"pairing:{invitation.enrollment.enrollment_id}"
        )
        self.assertIn("pairing.replay_denied", {event["event_type"] for event in events})

    def test_concurrent_redemption_has_one_winner(self):
        invitation = self.invite()
        identity = self.identity(b"concurrent")
        barrier = threading.Barrier(2)
        results: list[str] = []

        def worker():
            barrier.wait()
            try:
                self.redeem(invitation, identity)
                results.append("ok")
            except DeviceError as exc:
                results.append(f"error:{exc.http_status}")

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(results.count("ok"), 1, results)
        self.assertEqual(len(results), 2, results)

    def test_incorrect_code_is_bounded(self):
        self.pairing.max_code_attempts = 2
        invitation = self.invite()
        bad = "AAAA-AAAA-AAAA"
        with self.assertRaises(DeviceError) as first:
            self.redeem(invitation, pairing_code=bad)
        self.assertEqual(first.exception.http_status, 401)
        with self.assertRaises(DeviceError) as second:
            self.redeem(invitation, pairing_code=bad)
        self.assertEqual(second.exception.http_status, 429)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "EXPIRED",
        )

    def test_invitation_rate_limit(self):
        self.pairing.invite_limit = 2
        self.pairing.invite_window_s = 60
        self.invite(display_name="One")
        self.invite(display_name="Two")
        with self.assertRaises(DeviceError) as caught:
            self.invite(display_name="Three")
        self.assertEqual(caught.exception.http_status, 429)

    def test_redeem_rate_limit(self):
        self.pairing.redeem_limit = 2
        self.pairing.redeem_window_s = 60
        invitation = self.invite()
        for _ in range(2):
            with self.assertRaises(DeviceError):
                self.redeem(invitation, pairing_code="AAAA-AAAA-AAAA", source="test-ip")
        with self.assertRaises(DeviceError) as caught:
            self.redeem(invitation, pairing_code="AAAA-AAAA-AAAA", source="test-ip")
        self.assertEqual(caught.exception.http_status, 429)


if __name__ == "__main__":
    unittest.main()
