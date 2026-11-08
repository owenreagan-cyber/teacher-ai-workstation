import { useCallback, useEffect, useState } from "react";

import {
  type CredentialMetadata,
  DEVICE_PROFILES,
  type DeviceProfile,
  type DeviceRecord,
  PROFILE_LABELS,
  STATUS_LABELS,
  confirmationMessage,
} from "../shared/devices";
import type { ChiefBridge } from "../shared/types";

const INPUT = "selectable rounded-md border border-line bg-bg px-2 py-1 text-[13px] outline-none focus:border-accent";
const BUTTON = "rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-accent hover:bg-accent-soft disabled:opacity-50";
const DANGER = "rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-bad hover:bg-bg disabled:opacity-50";

function statusTone(status: DeviceRecord["status"]): string {
  if (status === "active") return "text-good";
  if (status === "disabled") return "text-warn";
  if (status === "revoked") return "text-bad";
  return "text-muted";
}

function Row(props: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 text-[13px]">
      <span className="text-muted">{props.label}</span>
      <span className="min-w-0 text-right">{props.children}</span>
    </div>
  );
}

export function DevicesPage(props: {
  bridge: ChiefBridge;
  initial?: DeviceRecord[];
  initialCredentials?: CredentialMetadata[];
}) {
  const { bridge } = props;
  const [devices, setDevices] = useState<DeviceRecord[]>(props.initial ?? []);
  const [selected, setSelected] = useState<DeviceRecord | null>(props.initial?.[0] ?? null);
  const [credentials, setCredentials] = useState<CredentialMetadata[]>(props.initialCredentials ?? []);
  const [name, setName] = useState(props.initial?.[0]?.display_name ?? "");
  const [profile, setProfile] = useState<DeviceProfile>(props.initial?.[0]?.device_profile ?? "school");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const res = await bridge.listDevices();
    if (res.ok) {
      setDevices(res.devices);
      setError(null);
      return res.devices;
    }
    setError(res.error);
    return [];
  }, [bridge]);

  const open = useCallback(async (device: DeviceRecord) => {
    setSelected(device);
    setName(device.display_name);
    setProfile(device.device_profile);
    const res = await bridge.deviceCredentials(device.device_id);
    setCredentials(res.ok ? res.credentials : []);
  }, [bridge]);

  useEffect(() => {
    void load();
  }, [load]);

  const run = async (action: () => Promise<{ ok: boolean; error?: string } | { ok: true }>) => {
    setBusy(true);
    try {
      const res = await action();
      if (!res.ok) setError((res as { error?: string }).error ?? "Device action failed");
      const list = await load();
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

  const hasPrimary = devices.some((d) => d.is_primary_owner);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[16px] font-semibold">Devices</h1>
        <p className="text-[12px] text-muted">
          Local owner management only. Remote enrollment, pairing, and network access are disabled in this milestone.
        </p>
      </div>
      {error && <p role="alert" className="text-[13px] text-bad">{error}</p>}
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
