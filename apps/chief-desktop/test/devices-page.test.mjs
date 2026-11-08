import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const { DevicesPage } = require("../out-test/renderer/Devices.js");

const h = React.createElement;
const device = (overrides = {}) => ({
  device_id: "a".repeat(32),
  display_name: "Classroom iPad",
  device_type: "ipad",
  platform: "ipados",
  owner_id: "school",
  device_profile: "school",
  trust_level: "restricted",
  status: "active",
  app_version: "0.1.0",
  registered_at: "2026-11-08T12:00:00.000+00:00",
  last_seen_at: "2026-11-08T13:00:00.000+00:00",
  updated_at: "2026-11-08T13:00:00.000+00:00",
  revoked_at: null,
  metadata: { tag: "cart-1" },
  is_primary_owner: false,
  ...overrides,
});

const bridge = {
  listDevices: async () => ({ ok: true, devices: [], total: 0, limit: 50, offset: 0 }),
  deviceCredentials: async () => ({ ok: true, device_id: device().device_id, credentials: [] }),
};

const text = (html) => html.replace(/<[^>]+>/g, " ").replace(/&#x27;/g, "'").replace(/&amp;/g, "&").replace(/\s+/g, " ");

test("the device page lists devices and shows the selected record", () => {
  const second = device({ device_id: "b".repeat(32), display_name: "Partner Mac", device_type: "mac", platform: "macos", device_profile: "partner" });
  const html = renderToStaticMarkup(
    h(DevicesPage, { bridge, initial: [device({ is_primary_owner: true }), second], initialCredentials: [] }),
  );
  const t = text(html);
  for (const want of [
    "Devices", "Local owner management only", "Pairing is local; remote enrollment, network access, and the TLS gateway are disabled",
    "Classroom iPad", "Partner Mac", "ipad", "ipados", "School", "Active",
    "Registered", "Last seen", "App version", "0.1.0", "Permission profile",
    "Rotate credential", "Revoke credential",
  ]) {
    assert.ok(t.includes(want), want);
  }
  assert.ok(!t.includes("Register this Mac as primary"), "the primary device suppresses the bootstrap button");
});

test("the device page never renders credential secrets or Keychain references", () => {
  const raw = { ...device(), token: "super-secret-token", keychain_ref: "device:abc", verifier: "hash" };
  const credential = {
    credential_id: "c".repeat(32),
    device_id: raw.device_id,
    credential_type: "device_access",
    status: "active",
    created_at: "2026-11-08T12:00:00.000+00:00",
    expires_at: null,
    rotated_at: null,
    revoked_at: null,
    token: "super-secret-token",
    keychain_ref: "device:abc",
  };
  const html = renderToStaticMarkup(
    h(DevicesPage, { bridge, initial: [raw], initialCredentials: [credential] }),
  );
  assert.ok(text(html).includes("Credentials"));
  assert.ok(!html.includes("super-secret-token"));
  assert.ok(!html.includes("device:abc"));
  assert.ok(!html.includes("keychain_ref"));
});

test("the device page offers primary bootstrap when no primary exists", () => {
  const html = renderToStaticMarkup(h(DevicesPage, { bridge, initial: [] }));
  assert.ok(text(html).includes("Register this Mac as primary"));
});

test("the device page renders pending enrollments, approval controls, and the QR", () => {
  const enrollment = {
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
  const invitation = {
    ok: true,
    enrollment: { ...enrollment, status: "PENDING", pairing_code: "ABCD-EFGH-JKMN" },
    pairing_code: "ABCD-EFGH-JKMN",
    qr_payload: '{"v":1,"enrollment_id":"c","code":"ABCD-EFGH-JKMN"}',
    expires_at: "2026-11-08T12:10:00.000+00:00",
  };
  const html = renderToStaticMarkup(
    h(DevicesPage, {
      bridge,
      initial: [],
      initialEnrollments: [enrollment],
      initialInvitation: invitation,
      initialQrDataUrl: "data:image/png;base64,AAAA",
    }),
  );
  const t = text(html);
  for (const want of [
    "Pending Enrollments", "School iPad", "Awaiting approval", "Approve", "Reject",
    "Requested School", "Add Device", "Generate pairing request", "ABCD-EFGH-JKMN",
    "one-time code", "The device must still be approved",
  ]) {
    assert.ok(t.includes(want), want);
  }
  assert.match(html, /alt="Pairing QR code"/);
  assert.ok(!html.includes("keychain"));
  assert.ok(!html.includes("super-secret-token"));
});
