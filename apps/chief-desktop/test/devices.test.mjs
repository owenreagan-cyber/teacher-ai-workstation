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

const ENROLLMENT = {
  enrollment_id: "c".repeat(32),
  status: "AWAITING_OWNER_APPROVAL",
  source: "owner_invitation",
  display_name: "School iPad",
  device_type: "ipad",
  platform: "ipados",
  app_version: "0.1.0",
  owner_id: "school",
  requested_profile: "school",
  approved_profile: null,
  requested_permissions: ["ask", "status.read", "tasks.create"],
  approved_permissions: [],
  public_key_fingerprint: "d".repeat(64),
  protocol_version: 1,
  created_at: "2026-11-08T12:00:00.000+00:00",
  updated_at: "2026-11-08T12:00:00.000+00:00",
  expires_at: "2026-11-08T12:10:00.000+00:00",
  redeemed_at: null,
  approved_at: null,
  completed_at: null,
  rejected_at: null,
  cancelled_at: null,
  delivery_expires_at: null,
  device_id: null,
  credential_id: null,
  replaces_device_id: null,
  reason: null,
  failed_attempts: 0,
};

test("parseEnrollment accepts bounded enrollment records and drops secrets", () => {
  const parsed = devices.parseEnrollment({ ...ENROLLMENT, pairing_code: "SECRET", token: "SECRET" });
  assert.ok(parsed);
  assert.equal(parsed.requested_profile, "school");
  assert.equal(parsed.status, "AWAITING_OWNER_APPROVAL");
  assert.equal(parsed.pairing_code, undefined);
  assert.equal(parsed.token, undefined);
  assert.equal(devices.parseEnrollment({ ...ENROLLMENT, status: "NOPE" }), null);
  assert.equal(devices.parseEnrollment({ ...ENROLLMENT, requested_profile: "superuser" }), null);
});

test("enrollment approval text states the exact profile restrictions", () => {
  const message = devices.enrollmentApprovalMessage("School iPad", "school");
  assert.ok(message.includes("School iPad"));
  assert.ok(message.includes("Restricted ask"));
  assert.ok(message.includes("no history"));
  assert.ok(devices.enrollmentLifecycleMessage("reject", "iPad").includes("Reject"));
  assert.ok(devices.enrollmentLifecycleMessage("cancel", "iPad").includes("Cancel"));
});

test("IPC enrollment validators bound profiles and ids", () => {
  const create = ipc.validateEnrollmentCreateInput({
    display_name: "School iPad",
    device_type: "ipad",
    platform: "ipados",
    requested_profile: "school",
  });
  assert.equal(create.requested_profile, "school");
  assert.throws(() => ipc.validateEnrollmentCreateInput({ display_name: "x", requested_profile: "revoked" }));
  assert.throws(() => ipc.validateEnrollmentCreateInput({ display_name: "x", requested_profile: "owner", device_type: "toaster" }));
  const approve = ipc.validateEnrollmentApproveInput({ device_profile: "school" });
  assert.equal(approve.device_profile, "school");
  assert.throws(() => ipc.validateEnrollmentApproveInput({ device_profile: "revoked" }));
  assert.throws(() => ipc.validateEnrollmentApproveInput({ device_profile: "school", replaces_device_id: "short" }));
  assert.equal(ipc.validateEnrollmentId("a".repeat(32)), "a".repeat(32));
});
