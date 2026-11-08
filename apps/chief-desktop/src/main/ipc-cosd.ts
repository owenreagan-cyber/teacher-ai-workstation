import type { IpcMainInvokeEvent } from "electron";

import {
  DEVICE_PROFILES,
  DEVICE_STATUSES,
  type DeviceCreateInput,
  type DevicePatchInput,
  type DeviceProfile,
  validateDeviceProfile,
  validateDeviceType,
  validateDisplayName,
  validateMetadata,
  validatePlatform,
} from "../shared/devices.js";

const TASK_ID_RE = /^[a-f0-9]{32}$/;
const MAX_ASK = 16_000;
const MAX_TITLE = 200;
const MAX_KIND = 80;
const MAX_IDEM = 120;
const MAX_OWNER = 64;
const MAX_APP_VERSION = 64;

export function requireString(value: unknown, max: number, label: string): string {
  if (typeof value !== "string") throw new Error(`${label} must be a string`);
  const s = value.trim();
  if (!s || s.length > max) throw new Error(`${label} invalid`);
  return s;
}

export function validateAskInput(question: unknown, sessionId: unknown): { question: string; sessionId: string } {
  const q = requireString(question, MAX_ASK, "question");
  const sid = requireString(sessionId, 40, "sessionId");
  if (!/^[a-z0-9-]{1,40}$/.test(sid)) throw new Error("sessionId invalid");
  return { question: q, sessionId: sid };
}

export function validateTaskId(taskId: unknown): string {
  const id = requireString(taskId, 32, "taskId");
  if (!TASK_ID_RE.test(id)) throw new Error("taskId invalid");
  return id;
}

export function validateCreateTask(title: unknown, kind: unknown, idempotencyKey: unknown) {
  return {
    title: requireString(title, MAX_TITLE, "title"),
    kind: requireString(kind, MAX_KIND, "kind"),
    idempotencyKey: requireString(idempotencyKey, MAX_IDEM, "idempotencyKey"),
  };
}

export function validateOptionalState(state: unknown): string | undefined {
  if (state === undefined || state === null || state === "") return undefined;
  return requireString(state, 40, "state");
}

export function assertTrusted(trusted: (event: IpcMainInvokeEvent) => boolean, event: IpcMainInvokeEvent): void {
  if (!trusted(event)) throw new Error("untrusted sender");
}

// ------------------------------------------------------------------ devices

export function validateDeviceId(value: unknown): string {
  const id = requireString(value, 32, "deviceId");
  if (!TASK_ID_RE.test(id)) throw new Error("deviceId invalid");
  return id;
}

export function validateCredentialId(value: unknown): string | undefined {
  if (value === undefined || value === null || value === "") return undefined;
  const id = requireString(value, 32, "credentialId");
  if (!TASK_ID_RE.test(id)) throw new Error("credentialId invalid");
  return id;
}

export function validateDeviceConfirm(value: unknown): true {
  if (value !== true) throw new Error("confirmation required");
  return true;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validateDeviceCreateInput(value: unknown): DeviceCreateInput {
  if (!isRecord(value)) throw new Error("device input must be an object");
  const owner = value.owner_id === undefined ? "unassigned" : requireString(value.owner_id, MAX_OWNER, "ownerId");
  return {
    display_name: validateDisplayName(value.display_name),
    device_type: validateDeviceType(value.device_type ?? "other"),
    platform: validatePlatform(value.platform ?? "unknown"),
    owner_id: owner,
    device_profile: validateDeviceProfile(value.device_profile ?? "capture_only"),
    metadata: validateMetadata(value.metadata),
  };
}

export function validateDevicePatchInput(value: unknown): DevicePatchInput {
  if (!isRecord(value)) throw new Error("device patch must be an object");
  const patch: DevicePatchInput = {};
  if ("display_name" in value) patch.display_name = validateDisplayName(value.display_name);
  if ("device_profile" in value) patch.device_profile = validateDeviceProfile(value.device_profile);
  if ("metadata" in value) patch.metadata = validateMetadata(value.metadata);
  if ("app_version" in value) {
    const version = value.app_version;
    if (typeof version !== "string" || version.length > MAX_APP_VERSION) throw new Error("appVersion invalid");
    patch.app_version = version.trim();
  }
  if (Object.keys(patch).length === 0) throw new Error("no device fields to update");
  return patch;
}

export function validateDeviceFilter(value: unknown): { status?: string; profile?: DeviceProfile } {
  if (value === undefined || value === null) return {};
  if (!isRecord(value)) throw new Error("device filter must be an object");
  const out: { status?: string; profile?: DeviceProfile } = {};
  if (value.status !== undefined && value.status !== "") {
    const status = requireString(value.status, 16, "status");
    if (!(DEVICE_STATUSES as readonly string[]).includes(status)) throw new Error("status invalid");
    out.status = status;
  }
  if (value.profile !== undefined && value.profile !== "") {
    const profile = validateDeviceProfile(value.profile);
    if (!(DEVICE_PROFILES as readonly string[]).includes(profile)) throw new Error("profile invalid");
    out.profile = profile;
  }
  return out;
}
