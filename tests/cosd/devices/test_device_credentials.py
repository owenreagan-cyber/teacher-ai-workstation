"""Credential lifecycle, verifier, Keychain provider, and leakage tests."""
from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from device_support import DeviceStateTest

from cosd.devices import (
    CredentialProviderError,
    CredentialService,
    DeviceError,
    DeviceRegistry,
    KeychainCredentialProvider,
    MemoryCredentialProvider,
)
from cosd.devices.credentials import CredentialInvalid


class FakeSecurityRunner:
    def __init__(self):
        self.items: dict[tuple[str, str], str] = {}
        self.commands: list[list[str]] = []

    def __call__(self, args):
        self.commands.append(list(args))
        assert args[0] == "security"
        op = args[1]
        service = args[args.index("-s") + 1]
        account = args[args.index("-a") + 1]
        key = (service, account)
        if op == "add-generic-password":
            secret = args[args.index("-w") + 1]
            self.items[key] = secret
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if op == "find-generic-password":
            if key not in self.items:
                return SimpleNamespace(returncode=44, stdout="", stderr="could not be found")
            return SimpleNamespace(returncode=0, stdout=self.items[key] + "\n", stderr="")
        if op == "delete-generic-password":
            if key not in self.items:
                return SimpleNamespace(returncode=44, stdout="", stderr="could not be found")
            del self.items[key]
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(op)


class FailingProvider:
    def get_secret(self, reference):
        raise CredentialProviderError("unavailable")

    def set_secret(self, reference, secret):
        raise CredentialProviderError("unavailable")

    def delete_secret(self, reference):
        raise CredentialProviderError("unavailable")


class CredentialTests(DeviceStateTest):
    def test_issue_verify_and_no_secret_in_sqlite(self):
        device, issued = self.make_device()
        self.assertIsNotNone(issued)
        self.assertRegex(issued.token, r"^[a-f0-9]{32}\.[A-Za-z0-9_-]+$")
        secret = issued.token.split(".", 1)[1]
        verification = self.registry.credentials.verify_token(issued.token)
        self.assertEqual(verification.device_id, device.device_id)
        self.assertEqual(verification.credential_id, issued.credential_id)
        rows = self.registry.db.execute("SELECT * FROM device_credentials").fetchall()
        dumped = " ".join(str(value) for row in rows for value in tuple(row))
        self.assertNotIn(secret, dumped)
        self.assertNotIn(issued.token, dumped)
        verifier = rows[0]["verifier"]
        self.assertNotEqual(verifier, secret)
        self.assertEqual(len(verifier), 64)

    def test_credentials_table_has_only_references(self):
        _, issued = self.make_device()
        row = self.registry.db.execute("SELECT * FROM device_credentials").fetchone()
        self.assertEqual(row["keychain_ref"], issued.keychain_ref)
        self.assertNotIn("token", row.keys())
        self.assertNotIn("secret", row.keys())

    def test_rotation_invalidates_old_token(self):
        device, issued = self.make_device()
        rotated = self.registry.rotate_credential(device.device_id)
        self.assertNotEqual(rotated["credential_id"], issued.credential_id)
        with self.assertRaises(CredentialInvalid):
            self.registry.credentials.verify_token(issued.token)
        statuses = {
            row["credential_id"]: row["status"]
            for row in self.registry.db.execute(
                "SELECT credential_id, status FROM device_credentials WHERE device_id = ?",
                (device.device_id,),
            ).fetchall()
        }
        self.assertEqual(statuses[issued.credential_id], "rotated")
        self.assertEqual(statuses[rotated["credential_id"]], "active")

    def test_expiration_fails_closed(self):
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        device, issued = self.make_device(credential_expires_at=past)
        with self.assertRaises(CredentialInvalid) as caught:
            self.registry.credentials.verify_token(issued.token)
        self.assertEqual(caught.exception.reason, "expired")
        self.assertFalse(self.registry.credentials.active_for_device(issued.credential_id, device.device_id))

    def test_future_expiration_works(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        _, issued = self.make_device(credential_expires_at=future)
        self.assertEqual(
            self.registry.credentials.verify_token(issued.token).credential_id,
            issued.credential_id,
        )

    def test_revocation_invalidates(self):
        device, issued = self.make_device()
        meta = self.registry.revoke_credential(device.device_id)
        self.assertEqual(meta["revoked"], 1)
        with self.assertRaises(CredentialInvalid) as caught:
            self.registry.credentials.verify_token(issued.token)
        self.assertEqual(caught.exception.reason, "status_revoked")

    def test_invalid_and_unknown_tokens(self):
        for token in ("", "nope", "a" * 32 + ".wrong", "b" * 32 + ".x"):
            with self.assertRaises(CredentialInvalid):
                self.registry.credentials.verify_token(token)

    def test_keychain_unavailable_blocks_issue_and_verify(self):
        failing = FailingProvider()
        registry = DeviceRegistry.open(
            self.state, credential_provider=failing, audit=self.audit
        )
        try:
            with self.assertRaises(DeviceError) as caught:
                registry.register_device(display_name="No store", device_type="ipad", platform="ipados")
            self.assertEqual(caught.exception.kind, "unavailable")
            self.assertEqual(registry.list_devices()["total"], 0)
        finally:
            registry.close()

        device, issued = self.make_device()
        original = self.registry.credentials._provider
        self.registry.credentials._provider = failing
        try:
            with self.assertRaises(CredentialProviderError):
                self.registry.credentials.verify_token(issued.token)
        finally:
            self.registry.credentials._provider = original

    def test_second_active_credential_is_refused(self):
        device, _ = self.make_device()
        with self.assertRaises(DeviceError) as caught:
            self.registry.credentials.issue(device.device_id)
        self.assertEqual(caught.exception.kind, "conflict")


class KeychainProviderTests(unittest.TestCase):
    def test_round_trip_uses_security_argv_only(self):
        runner = FakeSecurityRunner()
        provider = KeychainCredentialProvider(service="test.service", runner=runner)
        self.assertIsNone(provider.get_secret("ref-1"))
        provider.set_secret("ref-1", "top-secret")
        self.assertEqual(provider.get_secret("ref-1"), "top-secret")
        provider.delete_secret("ref-1")
        self.assertIsNone(provider.get_secret("ref-1"))
        for command in runner.commands:
            self.assertEqual(command[0], "security")
            self.assertNotIn("sh", command)
            self.assertNotIn("-c", command)

    def test_write_failure_raises_without_secret_in_message(self):
        class FailRunner:
            def __call__(self, args):
                return SimpleNamespace(returncode=1, stdout="", stderr="denied")

        provider = KeychainCredentialProvider(runner=FailRunner())
        with self.assertRaises(CredentialProviderError) as caught:
            provider.set_secret("ref", "super-secret-value")
        self.assertNotIn("super-secret-value", str(caught.exception))


class ServiceDirectTests(DeviceStateTest):
    def test_service_can_issue_to_existing_device(self):
        device, _ = self.make_device(issue_credential=False)
        service = CredentialService(self.registry.db, MemoryCredentialProvider())
        issued = service.issue(device.device_id)
        self.assertEqual(service.verify_token(issued.token).device_id, device.device_id)


if __name__ == "__main__":
    unittest.main()
