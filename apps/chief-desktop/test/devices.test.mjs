import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const devices = require("../out-test/shared/devices.js");
const ipc = require("../out/main/ipc-cosd.js");

const RAW = {
  device_id: "a".repeat(32),
  display_name: "Classroom iPad",
  device_type: "ipad",
  platform: "ipados",
  owner_id: "school",
  device_profile: "school",
  trust_level: "restricted",
  status: "active",
  app_version: "0.1.0",
  registered_at: "2026-11-08T00:00:00.000+00:00",
  last_seen_at: null,
  updated_at: "2026-11-08T00:00:00.000+00:00",
  revoked_at: null,
  metadata: { tag: "cart-1" },
  is_primary_owner: false,
  // These must never be carried into the renderer's model.
  keychain_ref: "device:secret",
  verifier: "hash",
  token: "secret",
};

test("parseDevice accepts a bounded record and drops secret fields", () => {
  const device = devices.parseDevice(RAW);
  assert.ok(device);
  assert.equal(device.display_name, "Classroom iPad");
  assert.equal(device.device_profile, "school");
  assert.equal(device.status, "active");
  assert.equal(device.keychain_ref, undefined);
  assert.equal(device.verifier, undefined);
  assert.equal(device.token, undefined);
});

test("parseDevice rejects malformed records", () => {
  assert.equal(devices.parseDevice({ ...RAW, device_id: "nope" }), null);
  assert.equal(devices.parseDevice({ ...RAW, device_profile: "superuser" }), null);
  assert.equal(devices.parseDevice({ ...RAW, status: "unknown" }), null);
  assert.equal(devices.parseDevice(null), null);
});

test("every access-changing action requires confirmation", () => {
  for (const action of ["profile", "disable", "enable", "revoke", "remove"]) {
    assert.equal(devices.requiresConfirmation(action), true, action);
    assert.ok(devices.confirmationMessage(action, "iPad").includes("iPad"), action);
  }
});

test("IPC validators bound device input", () => {
  const input = ipc.validateDeviceCreateInput({
    display_name: "School iPad",
    device_type: "ipad",
    platform: "ipados",
    owner_id: "school",
    device_profile: "school",
    metadata: { tag: "cart-1" },
  });
  assert.equal(input.device_profile, "school");
  assert.throws(() => ipc.validateDeviceCreateInput({ display_name: "x", metadata: { api_token: "x" } }));
  assert.throws(() => ipc.validateDeviceCreateInput({ display_name: "x", device_type: "toaster" }));
  assert.throws(() => ipc.validateDevicePatchInput({}));
  assert.equal(ipc.validateDevicePatchInput({ device_profile: "read_only" }).device_profile, "read_only");
  assert.throws(() => ipc.validateDeviceConfirm(false));
  assert.equal(ipc.validateDeviceConfirm(true), true);
  assert.throws(() => ipc.validateDeviceId("short"));
  assert.equal(ipc.validateDeviceId("a".repeat(32)), "a".repeat(32));
});
