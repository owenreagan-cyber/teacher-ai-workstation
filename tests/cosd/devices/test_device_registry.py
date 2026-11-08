"""Device registry persistence, identity, and schema tests."""
from __future__ import annotations

import sqlite3
import unittest

from device_support import DeviceStateTest

from cosd.devices import DeviceError, DeviceRegistry, MemoryCredentialProvider
from cosd.devices.storage import _SCHEMA_V1, DEVICE_SCHEMA_KEY, DEVICE_SCHEMA_VERSION
from cosd.storage import SCHEMA_VERSION, TaskDatabase, database_path
from cosd.tasks import TaskRegistry


class RegistryTests(DeviceStateTest):
    def test_registration_fields(self):
        device, issued = self.make_device(display_name="Classroom iPad", app_version="0.1.0")
        self.assertEqual(device.display_name, "Classroom iPad")
        self.assertEqual(device.device_type, "ipad")
        self.assertEqual(device.platform, "ipados")
        self.assertEqual(device.owner_id, "school")
        self.assertEqual(device.device_profile, "school")
        self.assertEqual(device.trust_level, "restricted")
        self.assertEqual(device.status, "active")
        self.assertEqual(device.app_version, "0.1.0")
        self.assertTrue(device.registered_at.endswith("+00:00"))
        self.assertIsNotNone(issued)
        self.assertEqual(issued.credential_id, self.registry.list_credentials(device.device_id)[0]["credential_id"])

    def test_stable_identity_across_restart(self):
        device, _ = self.make_device()
        device_id = device.device_id
        self.registry.close()
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=MemoryCredentialProvider(), audit=self.audit
        )
        same = self.registry.get_device(device_id)
        self.assertEqual(same.device_id, device_id)
        self.assertEqual(same.display_name, device.display_name)

    def test_duplicate_device_id_is_rejected(self):
        device_id = "a" * 32
        self.make_device(device_id=device_id)
        with self.assertRaises(DeviceError) as caught:
            self.make_device(device_id=device_id)
        self.assertEqual(caught.exception.kind, "conflict")

    def test_rename_and_metadata(self):
        device, _ = self.make_device()
        renamed = self.registry.rename_device(device.device_id, "Front iPad")
        self.assertEqual(renamed.display_name, "Front iPad")
        updated = self.registry.update_metadata(
            device.device_id, {"tag": "cart-2", "note": "shared"}, app_version="0.2.0"
        )
        self.assertEqual(updated.metadata["tag"], "cart-2")
        self.assertEqual(updated.app_version, "0.2.0")

    def test_profile_change_updates_trust_without_inheritance(self):
        device, _ = self.make_device()
        changed = self.registry.change_profile(device.device_id, "read_only")
        self.assertEqual(changed.device_profile, "read_only")
        self.assertEqual(changed.trust_level, "restricted")

    def test_list_is_bounded_and_filterable(self):
        for i in range(3):
            self.make_device(display_name=f"iPad {i}", device_profile="school")
        self.make_device(display_name="Partner Mac", device_type="mac", platform="macos", device_profile="partner")
        page = self.registry.list_devices(limit=2)
        self.assertEqual(page["total"], 4)
        self.assertEqual(len(page["devices"]), 2)
        self.assertEqual(page["limit"], 2)
        school = self.registry.list_devices(profile="school")
        self.assertEqual(school["total"], 3)
        # The service clamps the requested limit to its maximum.
        self.assertEqual(self.registry.list_devices(limit=1000)["limit"], 100)

    def test_metadata_refuses_secrets_and_student_data(self):
        for key in ("api_token", "private_key", "student_name", "password"):
            with self.assertRaises(DeviceError):
                self.make_device(metadata={key: "x"})

    def test_invalid_fields(self):
        with self.assertRaises(DeviceError):
            self.make_device(device_type="toaster")
        with self.assertRaises(DeviceError):
            self.make_device(platform="windows")
        with self.assertRaises(DeviceError):
            self.make_device(device_profile="superuser")
        with self.assertRaises(DeviceError):
            self.make_device(display_name="")
        with self.assertRaises(DeviceError):
            self.make_device(display_name="x" * 81)


class BootstrapTests(DeviceStateTest):
    def test_primary_bootstrap_is_idempotent(self):
        first, issued, created = self.registry.bootstrap_primary_mac(confirm=True)
        self.assertTrue(created)
        self.assertTrue(first.is_primary_owner)
        self.assertEqual(first.device_profile, "owner")
        self.assertIsNotNone(issued)
        second, again, created_again = self.registry.bootstrap_primary_mac(confirm=True)
        self.assertFalse(created_again)
        self.assertIsNone(again)
        self.assertEqual(first.device_id, second.device_id)

    def test_bootstrap_requires_confirmation(self):
        with self.assertRaises(DeviceError):
            self.registry.bootstrap_primary_mac(confirm=False)

    def test_only_one_primary_owner(self):
        self.registry.bootstrap_primary_mac(confirm=True)
        with self.assertRaises(DeviceError) as caught:
            self.registry.register_device(
                display_name="Second Mac", device_type="mac", platform="macos",
                device_profile="owner", is_primary_owner=True,
            )
        self.assertEqual(caught.exception.kind, "conflict")


class StorageTests(DeviceStateTest):
    def test_device_tables_share_the_task_database(self):
        tasks = TaskRegistry.open(self.state)
        task, _ = tasks.create_task(kind="diagnostic", title="keep me")
        device, _ = self.make_device()
        reopened = TaskRegistry.open(self.state)
        self.assertEqual(reopened.get_task(task["id"])["title"], "keep me")
        self.assertEqual(self.registry.get_device(device.device_id).device_id, device.device_id)
        row = self.registry.db.execute(
            "SELECT value FROM schema_meta WHERE key = ?", (DEVICE_SCHEMA_KEY,)
        ).fetchone()
        self.assertEqual(int(row["value"]), DEVICE_SCHEMA_VERSION)
        task_row = self.registry.db.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        self.assertEqual(int(task_row["value"]), SCHEMA_VERSION)
        self.assertEqual(TaskDatabase(self.state).integrity_check(), "ok")

    def test_foreign_key_integrity(self):
        device, _ = self.make_device()
        with self.registry.db.transaction() as conn:
            with self.assertRaises(Exception):
                conn.execute(
                    "INSERT INTO device_credentials(credential_id, device_id, credential_type, "
                    "keychain_ref, verifier, verifier_salt, status, created_at) "
                    "VALUES (?, ?, 'device_access', 'r', 'v', 's', 'active', 'now')",
                    ("b" * 32, "f" * 32),
                )
        self.assertEqual(self.registry.db.integrity_check(), "ok")

    def test_v1_to_v2_migration_preserves_devices(self):
        path = database_path(self.state)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        try:
            conn.executescript(_SCHEMA_V1)
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, '1')",
                (DEVICE_SCHEMA_KEY,),
            )
            conn.execute(
                """INSERT INTO devices(
                    device_id, display_name, device_type, platform, owner_id,
                    device_profile, trust_level, status, app_version,
                    registered_at, last_seen_at, updated_at, revoked_at,
                    metadata_json, is_primary_owner
                ) VALUES (?, 'Legacy iPad', 'ipad', 'ipados', 'school', 'school',
                    'restricted', 'active', '0.1.0', 'a', NULL, 'a', NULL, '{}', 0)""",
                ("a" * 32,),
            )
            conn.commit()
        finally:
            conn.close()

        self.registry.close()
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=MemoryCredentialProvider(), audit=self.audit
        )
        device = self.registry.get_device("a" * 32)
        self.assertEqual(device.display_name, "Legacy iPad")
        self.assertIsNone(device.public_key_fingerprint)
        columns = {
            row[1] for row in self.registry.db.execute("PRAGMA table_info(devices)").fetchall()
        }
        self.assertIn("public_key_fingerprint", columns)
        indexes = {
            row[1] for row in self.registry.db.execute("PRAGMA index_list(devices)").fetchall()
        }
        self.assertIn("idx_devices_active_fingerprint", indexes)
        self.assertEqual(
            int(
                self.registry.db.execute(
                    "SELECT value FROM schema_meta WHERE key = ?", (DEVICE_SCHEMA_KEY,)
                ).fetchone()["value"]
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
