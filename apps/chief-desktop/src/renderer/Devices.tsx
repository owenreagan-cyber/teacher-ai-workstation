import QRCode from "qrcode";
import { useCallback, useEffect, useState } from "react";

import {
  type CredentialMetadata,
  DEVICE_PROFILES,
  DEVICE_TYPES,
  type DeviceProfile,
  type DeviceRecord,
  type DeviceType,
  ENROLLMENT_STATUS_LABELS,
  type EnrollmentInvitationResult,
  type EnrollmentRecord,
  PLATFORMS,
  type DevicePlatform,
  PROFILE_LABELS,
  PROFILE_RESTRICTIONS,
  STATUS_LABELS,
  confirmationMessage,
  enrollmentApprovalMessage,
  enrollmentLifecycleMessage,
} from "../shared/devices";
import type { ChiefBridge } from "../shared/types";

const INPUT = "selectable rounded-md border border-line bg-bg px-2 py-1 text-[13px] outline-none focus:border-accent";
const BUTTON = "rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-accent hover:bg-accent-soft disabled:opacity-50";
const DANGER = "rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-bad hover:bg-bg disabled:opacity-50";

type Invitation = Extract<EnrollmentInvitationResult, { ok: true }>;

function statusTone(status: DeviceRecord["status"]): string {
  if (status === "active") return "text-good";
  if (status === "disabled") return "text-warn";
  if (status === "revoked") return "text-bad";
  return "text-muted";
}

function enrollmentTone(status: EnrollmentRecord["status"]): string {
  if (status === "APPROVED" || status === "COMPLETED") return "text-good";
  if (status === "EXPIRED" || status === "CANCELLED") return "text-muted";
  if (status === "REJECTED") return "text-bad";
  return "text-warn";
}

const APPROVABLE_PROFILES: readonly DeviceProfile[] = DEVICE_PROFILES.filter((p) => p !== "owner" && p !== "revoked");

function Row(props: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 text-[13px]">
      <span className="text-muted">{props.label}</span>
      <span className="min-w-0 text-right">{props.children}</span>
    </div>
  );
}

function countdownLabel(expiresAt: string | null, nowMs: number): string {
  if (!expiresAt) return "";
  const remaining = Date.parse(expiresAt) - nowMs;
  if (!Number.isFinite(remaining) || remaining <= 0) return "Expired";
  const minutes = Math.floor(remaining / 60_000);
  const seconds = Math.floor((remaining % 60_000) / 1000);
  return `${minutes}m ${seconds}s remaining`;
}

export function DevicesPage(props: {
  bridge: ChiefBridge;
  initial?: DeviceRecord[];
  initialCredentials?: CredentialMetadata[];
  initialEnrollments?: EnrollmentRecord[];
  initialInvitation?: Invitation | null;
  initialQrDataUrl?: string | null;
}) {
  const { bridge } = props;
  const [devices, setDevices] = useState<DeviceRecord[]>(props.initial ?? []);
  const [selected, setSelected] = useState<DeviceRecord | null>(props.initial?.[0] ?? null);
  const [credentials, setCredentials] = useState<CredentialMetadata[]>(props.initialCredentials ?? []);
  const [enrollments, setEnrollments] = useState<EnrollmentRecord[]>(props.initialEnrollments ?? []);
  const [invitation, setInvitation] = useState<Invitation | null>(props.initialInvitation ?? null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(props.initialQrDataUrl ?? null);
  const [approvalProfiles, setApprovalProfiles] = useState<Record<string, DeviceProfile>>({});
  const [name, setName] = useState(props.initial?.[0]?.display_name ?? "");
  const [profile, setProfile] = useState<DeviceProfile>(props.initial?.[0]?.device_profile ?? "school");
  const [enrollName, setEnrollName] = useState("");
  const [enrollType, setEnrollType] = useState<DeviceType>("ipad");
  const [enrollPlatform, setEnrollPlatform] = useState<DevicePlatform>("ipados");
  const [enrollProfile, setEnrollProfile] = useState<DeviceProfile>("capture_only");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [nowMs, setNowMs] = useState(() => Date.now());

  const loadDevices = useCallback(async () => {
    const res = await bridge.listDevices();
    if (res.ok) {
      setDevices(res.devices);
      return res.devices;
    }
    setError(res.error);
    return [];
  }, [bridge]);

  const loadEnrollments = useCallback(async () => {
    const res = await bridge.listPendingEnrollments();
    if (res.ok) setEnrollments(res.enrollments);
    else setError(res.error);
  }, [bridge]);

  const open = useCallback(async (device: DeviceRecord) => {
    setSelected(device);
    setName(device.display_name);
    setProfile(device.device_profile);
    const res = await bridge.deviceCredentials(device.device_id);
    setCredentials(res.ok ? res.credentials : []);
  }, [bridge]);

  useEffect(() => {
    void loadDevices();
    void loadEnrollments();
  }, [loadDevices, loadEnrollments]);

  useEffect(() => {
    if (!invitation) {
      setQrDataUrl(null);
      return;
    }
    let alive = true;
    void QRCode.toDataURL(invitation.qr_payload, { margin: 2, width: 220 })
      .then((url) => {
        if (alive) setQrDataUrl(url);
      })
      .catch(() => {
        if (alive) setError("Could not render the pairing QR code");
      });
    const timer = setInterval(() => setNowMs(Date.now()), 1000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [invitation]);

  const run = async (action: () => Promise<{ ok: boolean; error?: string } | { ok: true }>) => {
    setBusy(true);
    try {
      const res = await action();
      if (!res.ok) setError((res as { error?: string }).error ?? "Device action failed");
      const list = await loadDevices();
      await loadEnrollments();
      if (selected) {
        const fresh = list.find((d) => d.device_id === selected.device_id) ?? null;
        setSelected(fresh);
        if (fresh) {
          setName(fresh.display_name);
          setProfile(fresh.device_profile);
          const creds = await bridge.deviceCredentials(fresh.device_id);
          setCredentials(creds.ok ? creds.credentials : []);
        } else {
          setCredentials([]);
        }
      }
    } finally {
      setBusy(false);
    }
  };

  const saveName = () => {
    if (!selected) return;
    void run(() => bridge.updateDevice(selected.device_id, { display_name: name }));
  };

  const saveProfile = () => {
    if (!selected) return;
    if (!window.confirm(confirmationMessage("profile", selected.display_name))) return;
    void run(() => bridge.updateDevice(selected.device_id, { device_profile: profile }));
  };

  const lifecycle = (action: "disable" | "enable" | "revoke" | "remove") => {
    if (!selected) return;
    if (!window.confirm(confirmationMessage(action, selected.display_name))) return;
    void run(() => {
      if (action === "disable") return bridge.disableDevice(selected.device_id, true);
      if (action === "enable") return bridge.enableDevice(selected.device_id, true);
      if (action === "revoke") return bridge.revokeDevice(selected.device_id, true);
      return bridge.removeDevice(selected.device_id, true);
    });
  };

  const rotate = () => {
    if (!selected) return;
    if (!window.confirm(`Rotate the credential for "${selected.display_name}"? The old credential stops working immediately.`)) return;
    void run(() => bridge.rotateDeviceCredential(selected.device_id, true));
  };

  const revokeCredential = () => {
    if (!selected) return;
    if (!window.confirm(`Revoke every active credential for "${selected.display_name}"?`)) return;
    void run(() => bridge.revokeDeviceCredential(selected.device_id, true));
  };

  const bootstrap = () => {
    if (!window.confirm("Register this Mac as the primary owner device? This is a local bootstrap, not remote enrollment.")) return;
    void run(() => bridge.bootstrapDevice("Primary Mac", true));
  };

  const createInvitation = () => {
    const clean = enrollName.trim();
    if (!clean) {
      setError("Enter a name for the new device");
      return;
    }
    void run(async () => {
      const res = await bridge.createEnrollmentInvitation({
        display_name: clean,
        device_type: enrollType,
        platform: enrollPlatform,
        requested_profile: enrollProfile,
      });
      if (res.ok) {
        setInvitation(res);
        setNowMs(Date.now());
      } else {
        setError(res.error);
      }
      return res;
    });
  };

  const cancelInvitation = () => {
    if (!invitation) return;
    if (!window.confirm(`Cancel the invitation for "${invitation.enrollment.display_name}"?`)) return;
    void run(async () => {
      const res = await bridge.cancelEnrollment(invitation.enrollment.enrollment_id, true);
      if (res.ok) setInvitation(null);
      else setError(res.error);
      return res;
    });
  };

  const approveEnrollment = (enrollment: EnrollmentRecord) => {
    const requestedApprovable = APPROVABLE_PROFILES.includes(enrollment.requested_profile);
    const chosen =
      approvalProfiles[enrollment.enrollment_id] ??
      (requestedApprovable ? enrollment.requested_profile : "capture_only");
    if (!window.confirm(enrollmentApprovalMessage(enrollment.display_name, chosen))) return;
    void run(async () => {
      const res = await bridge.approveEnrollment(enrollment.enrollment_id, { device_profile: chosen }, true);
      if (res.ok && invitation?.enrollment.enrollment_id === enrollment.enrollment_id) setInvitation(null);
      if (!res.ok) setError(res.error);
      return res;
    });
  };

  const rejectEnrollment = (enrollment: EnrollmentRecord) => {
    if (!window.confirm(enrollmentLifecycleMessage("reject", enrollment.display_name))) return;
    void run(async () => {
      const res = await bridge.rejectEnrollment(enrollment.enrollment_id, true);
      if (res.ok && invitation?.enrollment.enrollment_id === enrollment.enrollment_id) setInvitation(null);
      if (!res.ok) setError(res.error);
      return res;
    });
  };

  const cancelEnrollment = (enrollment: EnrollmentRecord) => {
    if (!window.confirm(enrollmentLifecycleMessage("cancel", enrollment.display_name))) return;
    void run(async () => {
      const res = await bridge.cancelEnrollment(enrollment.enrollment_id, true);
      if (res.ok && invitation?.enrollment.enrollment_id === enrollment.enrollment_id) setInvitation(null);
      if (!res.ok) setError(res.error);
      return res;
    });
  };

  const hasPrimary = devices.some((d) => d.is_primary_owner);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[16px] font-semibold">Devices</h1>
        <p className="text-[12px] text-muted">
          Local owner management only. Pairing is local; remote enrollment, network access, and the TLS gateway are disabled in this milestone.
        </p>
      </div>
      {error && <p role="alert" className="text-[13px] text-bad">{error}</p>}

      <section aria-labelledby="pending-enrollments" className="space-y-3 rounded-xl border border-line bg-surface p-4">
        <h2 id="pending-enrollments" className="text-[14px] font-semibold">Pending Enrollments</h2>
        {enrollments.length === 0 ? (
          <p className="text-[12px] text-muted">No pending enrollment requests.</p>
        ) : (
          <ul className="divide-y divide-line">
            {enrollments.map((enrollment) => {
              const requestedApprovable = APPROVABLE_PROFILES.includes(enrollment.requested_profile);
              const chosen =
                approvalProfiles[enrollment.enrollment_id] ??
                (requestedApprovable ? enrollment.requested_profile : "capture_only");
              const canApprove = enrollment.status === "AWAITING_OWNER_APPROVAL";
              return (
                <li key={enrollment.enrollment_id} className="space-y-2 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`font-mono text-[12px] ${enrollmentTone(enrollment.status)}`}>
                      {ENROLLMENT_STATUS_LABELS[enrollment.status]}
                    </span>
                    <span className="text-[13px] font-medium">{enrollment.display_name}</span>
                    <span className="font-mono text-[12px] text-muted">{enrollment.enrollment_id.slice(0, 8)}…</span>
                  </div>
                  <div className="grid gap-1 text-[12px] text-muted sm:grid-cols-2">
                    <span>{enrollment.device_type} · {enrollment.platform} · app {enrollment.app_version || "—"}</span>
                    <span>Requested {PROFILE_LABELS[enrollment.requested_profile]}</span>
                    <span>Created {enrollment.created_at}</span>
                    <span>Expires {enrollment.expires_at}</span>
                    {enrollment.public_key_fingerprint && (
                      <span className="font-mono">Key {enrollment.public_key_fingerprint.slice(0, 16)}…</span>
                    )}
                  </div>
                  <p className="text-[12px] text-muted">{PROFILE_RESTRICTIONS[chosen]}</p>
                  {canApprove && (
                    <div className="flex flex-wrap items-end gap-2">
                      <label className="flex flex-col gap-0.5 text-[12px] text-muted">
                        Approve as
                        <select
                          className={INPUT}
                          value={chosen}
                          onChange={(e) =>
                            setApprovalProfiles((prev) => ({
                              ...prev,
                              [enrollment.enrollment_id]: e.target.value as DeviceProfile,
                            }))
                          }
                        >
                          {APPROVABLE_PROFILES.map((p) => (
                            <option key={p} value={p}>{PROFILE_LABELS[p]}</option>
                          ))}
                        </select>
                      </label>
                      <button type="button" className={BUTTON} disabled={busy} onClick={() => approveEnrollment(enrollment)}>
                        Approve
                      </button>
                      <button type="button" className={DANGER} disabled={busy} onClick={() => rejectEnrollment(enrollment)}>
                        Reject
                      </button>
                    </div>
                  )}
                  {(enrollment.status === "PENDING" || enrollment.status === "APPROVED") && (
                    <button type="button" className={DANGER} disabled={busy} onClick={() => cancelEnrollment(enrollment)}>
                      Cancel request
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section aria-labelledby="add-device" className="space-y-3 rounded-xl border border-line bg-surface p-4">
        <h2 id="add-device" className="text-[14px] font-semibold">Add Device</h2>
        <p className="text-[12px] text-muted">
          Generate a one-time pairing request. The code expires in ten minutes and never contains the master daemon token.
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-0.5 text-[12px] text-muted">
            Device name
            <input className={INPUT} value={enrollName} maxLength={80} onChange={(e) => setEnrollName(e.target.value)} />
          </label>
          <label className="flex flex-col gap-0.5 text-[12px] text-muted">
            Category
            <select className={INPUT} value={enrollType} onChange={(e) => setEnrollType(e.target.value as DeviceType)}>
              {DEVICE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-0.5 text-[12px] text-muted">
            Platform
            <select className={INPUT} value={enrollPlatform} onChange={(e) => setEnrollPlatform(e.target.value as DevicePlatform)}>
              {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-0.5 text-[12px] text-muted">
            Requested profile
            <select className={INPUT} value={enrollProfile} onChange={(e) => setEnrollProfile(e.target.value as DeviceProfile)}>
              {APPROVABLE_PROFILES.map((p) => <option key={p} value={p}>{PROFILE_LABELS[p]}</option>)}
            </select>
          </label>
          <button type="button" className={BUTTON} disabled={busy} onClick={createInvitation}>
            Generate pairing request
          </button>
        </div>
        {invitation && (
          <div className="flex flex-wrap items-start gap-4 rounded-lg border border-line bg-bg p-3">
            {qrDataUrl ? (
              <img src={qrDataUrl} alt="Pairing QR code" width={180} height={180} className="rounded bg-white p-1" />
            ) : (
              <div className="flex h-[180px] w-[180px] items-center justify-center rounded border border-line text-[12px] text-muted">
                Rendering QR…
              </div>
            )}
            <div className="min-w-0 space-y-1 text-[12px]">
              <p className="text-[13px] font-medium">{invitation.enrollment.display_name}</p>
              <p className="text-muted">Scan the QR or enter this one-time code on the new device:</p>
              <p className="selectable font-mono text-[14px] tracking-wider">{invitation.pairing_code}</p>
              <p className="text-muted">{countdownLabel(invitation.expires_at, nowMs)}</p>
              <p className="text-muted">The device must still be approved here before it receives a credential.</p>
              <button type="button" className={DANGER} disabled={busy} onClick={cancelInvitation}>
                Cancel request
              </button>
            </div>
          </div>
        )}
      </section>

      {!hasPrimary && (
        <button type="button" className={BUTTON} disabled={busy} onClick={bootstrap}>
          Register this Mac as primary
        </button>
      )}
      <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
        {devices.length === 0 ? (
          <li className="p-4 text-[13px] text-muted">No devices registered yet.</li>
        ) : (
          devices.map((device) => (
            <li key={device.device_id}>
              <button
                type="button"
                onClick={() => void open(device)}
                aria-current={selected?.device_id === device.device_id ? "true" : undefined}
                className={`flex w-full items-start gap-3 p-3 text-left hover:bg-bg ${
                  selected?.device_id === device.device_id ? "bg-accent-soft" : ""
                }`}
              >
                <span className={`shrink-0 font-mono text-[12px] ${statusTone(device.status)}`}>
                  {STATUS_LABELS[device.status]}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] font-medium">
                    {device.display_name}
                    {device.is_primary_owner ? " · primary owner" : ""}
                  </span>
                  <span className="block text-[12px] text-muted">
                    {device.device_type} · {device.platform} · {PROFILE_LABELS[device.device_profile]}
                  </span>
                </span>
              </button>
            </li>
          ))
        )}
      </ul>
      {selected && (
        <section aria-label="Device details" className="space-y-3 rounded-xl border border-line bg-surface p-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-[14px] font-semibold">{selected.display_name}</h2>
            <span className="font-mono text-[12px] text-muted">{selected.device_id.slice(0, 8)}…</span>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <Row label="Type">{selected.device_type}</Row>
            <Row label="Platform">{selected.platform}</Row>
            <Row label="Profile">{PROFILE_LABELS[selected.device_profile]}</Row>
            <Row label="Status">{STATUS_LABELS[selected.status]}</Row>
            <Row label="Registered">{selected.registered_at}</Row>
            <Row label="Last seen">{selected.last_seen_at ?? "Never"}</Row>
            <Row label="App version">{selected.app_version || "—"}</Row>
            <Row label="Owner">{selected.owner_id}</Row>
            {selected.public_key_fingerprint && (
              <Row label="Device key fingerprint">
                <span className="font-mono text-[12px]">{selected.public_key_fingerprint.slice(0, 16)}…</span>
              </Row>
            )}
          </div>

          <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-0.5 text-[12px] text-muted">
              Name
              <input className={INPUT} value={name} maxLength={80} onChange={(e) => setName(e.target.value)} />
            </label>
            <button type="button" className={BUTTON} disabled={busy} onClick={saveName}>
              Save name
            </button>
          </div>

          <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-0.5 text-[12px] text-muted">
              Permission profile
              <select className={INPUT} value={profile} onChange={(e) => setProfile(e.target.value as DeviceProfile)}>
                {DEVICE_PROFILES.filter((p) => p !== "revoked").map((p) => (
                  <option key={p} value={p}>
                    {PROFILE_LABELS[p]}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className={BUTTON} disabled={busy} onClick={saveProfile}>
              Change profile
            </button>
          </div>

          <div className="flex flex-wrap gap-2 border-t border-line pt-3">
            {selected.status === "active" && (
              <button type="button" className={BUTTON} disabled={busy} onClick={() => lifecycle("disable")}>
                Disable
              </button>
            )}
            {selected.status === "disabled" && (
              <button type="button" className={BUTTON} disabled={busy} onClick={() => lifecycle("enable")}>
                Re-enable
              </button>
            )}
            {(selected.status === "active" || selected.status === "disabled") && (
              <button type="button" className={DANGER} disabled={busy} onClick={() => lifecycle("revoke")}>
                Revoke
              </button>
            )}
            {(selected.status === "disabled" || selected.status === "revoked") && (
              <button type="button" className={DANGER} disabled={busy} onClick={() => lifecycle("remove")}>
                Remove
              </button>
            )}
            <button type="button" className={BUTTON} disabled={busy} onClick={rotate}>
              Rotate credential
            </button>
            <button type="button" className={DANGER} disabled={busy} onClick={revokeCredential}>
              Revoke credential
            </button>
          </div>

          <div>
            <h3 className="mb-1 text-[12px] font-semibold text-muted">Credentials</h3>
            {credentials.length === 0 ? (
              <p className="text-[12px] text-muted">No credentials.</p>
            ) : (
              <ul className="space-y-1 text-[12px] text-muted">
                {credentials.map((credential) => (
                  <li key={credential.credential_id} className="font-mono">
                    {credential.credential_id.slice(0, 8)}… · {credential.status} · created {credential.created_at}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
