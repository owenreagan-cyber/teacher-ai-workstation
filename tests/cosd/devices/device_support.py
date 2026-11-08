"""Shared helpers for the device registry suites (hermetic)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# When discovery starts at tests/cosd/devices, the parent cosd test helpers are
# not on sys.path yet.
_COSD_TESTS = Path(__file__).resolve().parents[1]
if str(_COSD_TESTS) not in sys.path:
    sys.path.insert(0, str(_COSD_TESTS))

from support import CosdStateTest, RunningServer, free_port, http_json, wait_until  # noqa: E402

from cos.audit import AuditLog  # noqa: E402
from cos.policy import KillSwitch  # noqa: E402

from cosd.devices import (  # noqa: E402
    DeviceAuthorizationService,
    DeviceRegistry,
    MemoryCredentialProvider,
)


class DeviceStateTest(CosdStateTest):
    """Temp state, fake credential provider, isolated hash-chained audit log."""

    def setUp(self):
        super().setUp()
        os.environ["COSD_CREDENTIAL_PROVIDER"] = "memory"
        self.provider = MemoryCredentialProvider()
        self.audit_path = self.state / "audit.jsonl"
        self.audit = AuditLog(self.audit_path)
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        self.auth = DeviceAuthorizationService(
            self.registry, kill_switch=KillSwitch(self.state)
        )

    def tearDown(self):
        try:
            self.registry.close()
        finally:
            super().tearDown()

    def make_device(self, **overrides):
        fields = {
            "display_name": "Test iPad",
            "device_type": "ipad",
            "platform": "ipados",
            "owner_id": "school",
            "device_profile": "school",
            "metadata": {"tag": "classroom"},
        }
        fields.update(overrides)
        return self.registry.register_device(**fields)

    def start_server(self, **kwargs):
        kwargs.setdefault("use_subprocess", False)
        kwargs.setdefault("credential_provider", self.provider)
        return RunningServer(self.state, **kwargs)


def http_json_auth(
    port: int,
    path: str,
    *,
    authorization: str | None = None,
    method: str = "GET",
    body: dict | None = None,
) -> tuple[int, dict]:
    data = None
    headers: dict[str, str] = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"http://127.0.0.1:{port}{path}", data=data, method=method, headers=headers)
    if authorization is not None:
        req.add_header("Authorization", authorization)
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"ok": False, "error": payload}
