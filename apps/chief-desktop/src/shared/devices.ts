// Device registry shapes and the client-side confirmation policy. The main
// process validates everything again before it reaches cosd; the renderer never
// sees a credential secret or a Keychain reference.

export const DEVICE_PROFILES = [
  "owner",
  "personal",
  "partner",
  "school",
  "read_only",
  "capture_only",
  "revoked",
] as const;
export type DeviceProfile = (typeof DEVICE_PROFILES)[number];

export const DEVICE_TYPES = ["mac", "iphone", "ipad", "other"] as const;
export type DeviceType = (typeof DEVICE_TYPES)[number];

export const DEVICE_STATUSES = ["active", "disabled", "revoked", "removed"] as const;
export type DeviceStatus = (typeof DEVICE_STATUSES)[number];

export const PLATFORMS = ["macos", "ios", "ipados", "unknown"] as const;
export type DevicePlatform = (typeof PLATFORMS)[number];

export type DeviceRecord = {
  device_id: string;
  display_name: string;
  device_type: DeviceType;
  platform: string;
  owner_id: string;
  device_profile: DeviceProfile;
  trust_level: string;
  status: DeviceStatus;
  app_version: string;
  registered_at: string;
  last_seen_at: string | null;
  updated_at: string;
  revoked_at: string | null;
  metadata: Record<string, unknown>;
  is_primary_owner: boolean;
};

export type CredentialMetadata = {
  credential_id: string;
  device_id: string;
  credential_type: string;
  status: string;
  created_at: string;
  expires_at: string | null;
  rotated_at: string | null;
  revoked_at: string | null;
};

export type DeviceListResult =
  | { ok: true; devices: DeviceRecord[]; total: number; limit: number; offset: number }
  | { ok: false; error: string; error_kind: string };

export type DeviceDetailResult =
  | { ok: true; device: DeviceRecord; credential?: CredentialMetadata }
  | { ok: false; error: string; error_kind: string };

export type DeviceCredentialsResult =
  | { ok: true; credentials: CredentialMetadata[]; device_id: string }
  | { ok: false; error: string; error_kind: string };

export type DeviceCreateInput = {
  display_name: string;
  device_type: DeviceType;
  platform: string;
  owner_id: string;
  device_profile: DeviceProfile;
  metadata: Record<string, unknown>;
};

export type DevicePatchInput = {
  display_name?: string;
  device_profile?: DeviceProfile;
  metadata?: Record<string, unknown>;
  app_version?: string;
};

export type DeviceAction = "profile" | "disable" | "enable" | "revoke" | "remove";

export const PROFILE_LABELS: Record<DeviceProfile, string> = {
  owner: "Owner",
  personal: "Personal",
  partner: "Partner",
  school: "School",
  read_only: "Read-only",
  capture_only: "Capture-only",
  revoked: "Revoked",
};

export const STATUS_LABELS: Record<DeviceStatus, string> = {
  active: "Active",
  disabled: "Disabled",
  revoked: "Revoked",
  removed: "Removed",
};

const DEVICE_ID_RE = /^[a-f0-9]{32}$/;
const MAX_NAME = 80;
const MAX_METADATA_BYTES = 8192;
const FORBIDDEN_METADATA_KEY = /(token|secret|passw|credential|private.?key|student|pupil|ssn|social.?security|dob|birth)/i;

export function validateDeviceId(value: unknown): string {
  if (typeof value !== "string" || !DEVICE_ID_RE.test(value.trim())) throw new Error("deviceId invalid");
  return value.trim();
}

export function validateDisplayName(value: unknown): string {
  if (typeof value !== "string") throw new Error("displayName must be text");
  const name = value.trim();
  if (!name || name.length > MAX_NAME) throw new Error("displayName invalid");
  return name;
}

export function validateDeviceProfile(value: unknown): DeviceProfile {
  if (typeof value !== "string" || !(DEVICE_PROFILES as readonly string[]).includes(value)) {
    throw new Error("deviceProfile invalid");
  }
  return value as DeviceProfile;
}

export function validateDeviceType(value: unknown): DeviceType {
  if (typeof value !== "string" || !(DEVICE_TYPES as readonly string[]).includes(value)) {
    throw new Error("deviceType invalid");
  }
  return value as DeviceType;
}

export function validatePlatform(value: unknown): DevicePlatform {
  if (typeof value !== "string" || !(PLATFORMS as readonly string[]).includes(value)) {
    throw new Error("platform invalid");
  }
  return value as DevicePlatform;
}

export function validateMetadata(value: unknown): Record<string, unknown> {
  if (value === undefined || value === null) return {};
  if (typeof value !== "object" || Array.isArray(value)) throw new Error("metadata must be an object");
  const out: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
    if (!key || key.length > 64) throw new Error("metadata key invalid");
    if (FORBIDDEN_METADATA_KEY.test(key)) throw new Error(`metadata key ${key} is not permitted`);
    if (item !== null && !["string", "number", "boolean", "object"].includes(typeof item)) {
      throw new Error(`metadata ${key} has an unsupported type`);
    }
    out[key] = item;
  }
  if (JSON.stringify(out).length > MAX_METADATA_BYTES) throw new Error("metadata too large");
  return out;
}

export function parseDevice(raw: unknown): DeviceRecord | null {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return null;
  const o = raw as Record<string, unknown>;
  if (typeof o.device_id !== "string" || !DEVICE_ID_RE.test(o.device_id)) return null;
  if (typeof o.display_name !== "string" || !o.display_name) return null;
  if (typeof o.device_type !== "string" || !(DEVICE_TYPES as readonly string[]).includes(o.device_type)) return null;
  if (typeof o.device_profile !== "string" || !(DEVICE_PROFILES as readonly string[]).includes(o.device_profile)) return null;
  if (typeof o.status !== "string" || !(DEVICE_STATUSES as readonly string[]).includes(o.status)) return null;
  if (typeof o.platform !== "string" || typeof o.owner_id !== "string") return null;
  if (typeof o.trust_level !== "string" || typeof o.app_version !== "string") return null;
  if (typeof o.registered_at !== "string" || typeof o.updated_at !== "string") return null;
  if (typeof o.is_primary_owner !== "boolean") return null;
  if (o.metadata !== undefined && (typeof o.metadata !== "object" || o.metadata === null || Array.isArray(o.metadata))) return null;
  return {
    device_id: o.device_id,
    display_name: o.display_name,
    device_type: o.device_type as DeviceType,
    platform: o.platform,
    owner_id: o.owner_id,
    device_profile: o.device_profile as DeviceProfile,
    trust_level: o.trust_level,
    status: o.status as DeviceStatus,
    app_version: o.app_version,
    registered_at: o.registered_at,
    last_seen_at: typeof o.last_seen_at === "string" ? o.last_seen_at : null,
    updated_at: o.updated_at,
    revoked_at: typeof o.revoked_at === "string" ? o.revoked_at : null,
    metadata: (o.metadata as Record<string, unknown>) ?? {},
    is_primary_owner: o.is_primary_owner,
  };
}

export function parseCredential(raw: unknown): CredentialMetadata | null {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return null;
  const o = raw as Record<string, unknown>;
  if (typeof o.credential_id !== "string" || !DEVICE_ID_RE.test(o.credential_id)) return null;
  if (typeof o.device_id !== "string" || typeof o.credential_type !== "string") return null;
  if (typeof o.status !== "string" || typeof o.created_at !== "string") return null;
  return {
    credential_id: o.credential_id,
    device_id: o.device_id,
    credential_type: o.credential_type,
    status: o.status,
    created_at: o.created_at,
    expires_at: typeof o.expires_at === "string" ? o.expires_at : null,
    rotated_at: typeof o.rotated_at === "string" ? o.rotated_at : null,
    revoked_at: typeof o.revoked_at === "string" ? o.revoked_at : null,
  };
}

/** Every lifecycle change that affects access requires an explicit confirmation. */
export function requiresConfirmation(action: DeviceAction): boolean {
  return action === "profile" || action === "disable" || action === "enable" || action === "revoke" || action === "remove";
}

export function confirmationMessage(action: DeviceAction, name: string): string {
  switch (action) {
    case "profile":
      return `Change the permission profile for "${name}"? Access changes immediately.`;
    case "disable":
      return `Disable "${name}"? It cannot authenticate until re-enabled.`;
    case "enable":
      return `Re-enable "${name}"? Its existing credential becomes usable again.`;
    case "revoke":
      return `Revoke "${name}" permanently? Its credentials stop working immediately.`;
    case "remove":
      return `Remove "${name}" from the registry? Audit provenance is retained.`;
  }
}
