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
  public_key_fingerprint?: string | null;
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

export const ENROLLMENT_STATUSES = [
  "PENDING",
  "AWAITING_OWNER_APPROVAL",
  "APPROVED",
  "REJECTED",
  "EXPIRED",
  "COMPLETED",
  "CANCELLED",
] as const;
export type EnrollmentStatus = (typeof ENROLLMENT_STATUSES)[number];

export const ENROLLMENT_STATUS_LABELS: Record<EnrollmentStatus, string> = {
  PENDING: "Waiting for device",
  AWAITING_OWNER_APPROVAL: "Awaiting approval",
  APPROVED: "Approved — delivery pending",
  REJECTED: "Rejected",
  EXPIRED: "Expired",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};

export type EnrollmentRecord = {
  enrollment_id: string;
  status: EnrollmentStatus;
  source: string;
  display_name: string;
  device_type: DeviceType;
  platform: string;
  app_version: string;
  owner_id: string;
  requested_profile: DeviceProfile;
  approved_profile: DeviceProfile | null;
  requested_permissions: string[];
  approved_permissions: string[];
  public_key_fingerprint: string | null;
  protocol_version: number;
  created_at: string;
  updated_at: string;
  expires_at: string;
  redeemed_at: string | null;
  approved_at: string | null;
  completed_at: string | null;
  rejected_at: string | null;
  cancelled_at: string | null;
  delivery_expires_at: string | null;
  device_id: string | null;
  credential_id: string | null;
  replaces_device_id: string | null;
  reason: string | null;
  failed_attempts: number;
};

export type EnrollmentInvitationResult =
  | { ok: true; enrollment: EnrollmentRecord; pairing_code: string; qr_payload: string; expires_at: string }
  | { ok: false; error: string; error_kind: string };

export type EnrollmentListResult =
  | { ok: true; enrollments: EnrollmentRecord[]; total: number; limit: number; offset: number }
  | { ok: false; error: string; error_kind: string };

export type EnrollmentDetailResult =
  | { ok: true; enrollment: EnrollmentRecord }
  | { ok: false; error: string; error_kind: string };

export type EnrollmentActionResult =
  | { ok: true; enrollment: EnrollmentRecord; device?: DeviceRecord; credential?: CredentialMetadata }
  | { ok: false; error: string; error_kind: string };

export type EnrollmentCreateInput = {
  display_name: string;
  device_type: DeviceType;
  platform: string;
  requested_profile: DeviceProfile;
  app_version?: string;
  owner_id?: string;
};

export type EnrollmentApproveInput = {
  device_profile: DeviceProfile;
  replaces_device_id?: string;
  allow_owner?: boolean;
};

export const PROFILE_RESTRICTIONS: Record<DeviceProfile, string> = {
  owner: "Full authorized control, including device and credential administration.",
  personal: "Personal ask, tasks, history, and sessions; no device administration.",
  partner: "Shared ask and task capture/read; no private personal history, execution, or administration.",
  school: "Restricted ask, task capture, and status only; no history, sessions, execution, or administration.",
  read_only: "Status, task list, and task history only; cannot change records.",
  capture_only: "Create tasks and read status only; cannot ask, list tasks, or execute.",
  revoked: "No access at all.",
};

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
    public_key_fingerprint: typeof o.public_key_fingerprint === "string" ? o.public_key_fingerprint : null,
  };
}

export function validateEnrollmentId(value: unknown): string {
  return validateDeviceId(value);
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export function parseEnrollment(raw: unknown): EnrollmentRecord | null {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return null;
  const o = raw as Record<string, unknown>;
  if (typeof o.enrollment_id !== "string" || !DEVICE_ID_RE.test(o.enrollment_id)) return null;
  if (typeof o.status !== "string" || !(ENROLLMENT_STATUSES as readonly string[]).includes(o.status)) return null;
  if (typeof o.display_name !== "string" || !o.display_name) return null;
  if (typeof o.device_type !== "string" || !(DEVICE_TYPES as readonly string[]).includes(o.device_type)) return null;
  if (typeof o.device_profile === "string") return null; // enrollments use requested/approved profiles
  if (typeof o.requested_profile !== "string" || !(DEVICE_PROFILES as readonly string[]).includes(o.requested_profile)) return null;
  if (o.approved_profile !== null && (typeof o.approved_profile !== "string" || !(DEVICE_PROFILES as readonly string[]).includes(o.approved_profile))) return null;
  if (typeof o.created_at !== "string" || typeof o.expires_at !== "string") return null;
  return {
    enrollment_id: o.enrollment_id,
    status: o.status as EnrollmentStatus,
    source: typeof o.source === "string" ? o.source : "",
    display_name: o.display_name,
    device_type: o.device_type as DeviceType,
    platform: typeof o.platform === "string" ? o.platform : "unknown",
    app_version: typeof o.app_version === "string" ? o.app_version : "",
    owner_id: typeof o.owner_id === "string" ? o.owner_id : "unassigned",
    requested_profile: o.requested_profile as DeviceProfile,
    approved_profile: typeof o.approved_profile === "string" ? (o.approved_profile as DeviceProfile) : null,
    requested_permissions: stringList(o.requested_permissions),
    approved_permissions: stringList(o.approved_permissions),
    public_key_fingerprint: typeof o.public_key_fingerprint === "string" ? o.public_key_fingerprint : null,
    protocol_version: typeof o.protocol_version === "number" ? o.protocol_version : 1,
    created_at: o.created_at,
    updated_at: typeof o.updated_at === "string" ? o.updated_at : o.created_at,
    expires_at: o.expires_at,
    redeemed_at: typeof o.redeemed_at === "string" ? o.redeemed_at : null,
    approved_at: typeof o.approved_at === "string" ? o.approved_at : null,
    completed_at: typeof o.completed_at === "string" ? o.completed_at : null,
    rejected_at: typeof o.rejected_at === "string" ? o.rejected_at : null,
    cancelled_at: typeof o.cancelled_at === "string" ? o.cancelled_at : null,
    delivery_expires_at: typeof o.delivery_expires_at === "string" ? o.delivery_expires_at : null,
    device_id: typeof o.device_id === "string" ? o.device_id : null,
    credential_id: typeof o.credential_id === "string" ? o.credential_id : null,
    replaces_device_id: typeof o.replaces_device_id === "string" ? o.replaces_device_id : null,
    reason: typeof o.reason === "string" ? o.reason : null,
    failed_attempts: typeof o.failed_attempts === "number" ? o.failed_attempts : 0,
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

export function enrollmentApprovalMessage(name: string, profile: DeviceProfile): string {
  return `Approve "${name}" as ${PROFILE_LABELS[profile]}?\n\n${PROFILE_RESTRICTIONS[profile]}\n\nThis grants access immediately.`;
}

export function enrollmentLifecycleMessage(action: "reject" | "cancel", name: string): string {
  if (action === "reject") return `Reject the enrollment request from "${name}"?`;
  return `Cancel the enrollment request from "${name}"?`;
}
