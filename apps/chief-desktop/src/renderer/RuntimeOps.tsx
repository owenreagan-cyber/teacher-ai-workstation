import { useCallback, useEffect, useState } from "react";

import type { OpsPrefs } from "../shared/ops-prefs";
import { type RuntimeBody, runtimeSummary } from "../shared/runtime";

export function RuntimeOpsSection() {
  const [runtime, setRuntime] = useState<RuntimeBody | null>(null);
  const [prefs, setPrefs] = useState<OpsPrefs | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const summary = runtimeSummary(runtime);

  const refresh = useCallback(async () => {
    const snap = await window.chief.runtimeSnapshot();
    if (snap.ok) setRuntime(snap.body as RuntimeBody);
    const p = await window.chief.opsPrefsGet();
    if (p.ok) setPrefs(p.prefs);
  }, []);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 30_000);
    return () => clearInterval(id);
  }, [refresh]);

  const run = async (action: "start" | "stop" | "restart", confirm: boolean) => {
    if (!confirm && (action === "stop" || action === "restart")) return;
    setBusy(action);
    setError(null);
    const res =
      action === "start"
        ? await window.chief.cosdStart()
        : action === "stop"
          ? await window.chief.cosdStop(true)
          : await window.chief.cosdRestart(true);
    setBusy(null);
    if (!res.ok) setError(res.error ?? "failed");
    await window.chief.cosdReconnect();
    await refresh();
  };

  const togglePref = async (key: keyof OpsPrefs, value: boolean) => {
    if (!prefs) return;
    const next = { ...prefs, [key]: value };
    setPrefs(next);
    await window.chief.opsPrefsSet(next);
  };

  return (
    <section className="rounded-xl border border-line bg-surface p-4">
      <h2 className="mb-3 text-[13px] font-semibold">Runtime & notifications</h2>
      <p className="mb-3 text-[12px] text-muted">
        {summary.state} · cosd {summary.version} · {summary.commit} · python {summary.python} · uptime{" "}
        {runtime?.uptime_s ?? "—"}s · queue {runtime?.queue_paused ? "paused" : "active"}
      </p>
      {summary.warning && (
        <p className="mb-3 text-[12px] text-bad" data-testid="runtime-warning">
          {summary.warning}
        </p>
      )}
      <div className="mb-3 flex flex-wrap gap-2">
        <button type="button" className="rounded-md border border-line px-2 py-1 text-[12px]" disabled={!!busy} onClick={() => void run("start", true)}>
          Start cosd
        </button>
        <button type="button" className="rounded-md border border-line px-2 py-1 text-[12px]" disabled={!!busy} onClick={() => void run("stop", window.confirm("Stop cosd?"))}>
          Stop cosd
        </button>
        <button
          type="button"
          className="rounded-md border border-line px-2 py-1 text-[12px]"
          disabled={!!busy}
          onClick={() => void run("restart", window.confirm("Restart cosd?"))}
        >
          Restart cosd
        </button>
      </div>
      {error && <p className="mb-2 text-[12px] text-bad">{error}</p>}
      {prefs && (
        <ul className="space-y-1 text-[12px]">
          {(
            [
              ["notifyTaskCompleted", "Task completed"],
              ["notifyTaskFailed", "Task failed"],
              ["notifyDaemonConnection", "Daemon connection"],
              ["streamingAsk", "Streaming ask (chunked)"],
              ["progressViaEvents", "Live task events (SSE)"],
            ] as const
          ).map(([key, label]) => (
            <li key={key}>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={prefs[key]} onChange={(e) => void togglePref(key, e.target.checked)} />
                {label}
              </label>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
