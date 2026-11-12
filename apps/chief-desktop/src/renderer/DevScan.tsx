import { useCallback, useEffect, useState } from "react";

import {
  DEV_SCAN_LIMITS_TEXT,
  type DevScanReport,
  type DevScanRunResult,
  MEASUREMENT_LABELS,
  describeLimits,
  formatBytes,
} from "../shared/devscan";
import type { ChiefBridge } from "../shared/types";

const BUTTON = "rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-accent hover:bg-accent-soft disabled:opacity-50";
const PRIMARY = "rounded-md bg-accent px-2.5 py-1 text-[12px] font-medium text-on-accent disabled:opacity-50";

type ScanBridge = Pick<ChiefBridge, "devScanRoots" | "devScanAddRoot" | "devScanRemoveRoot" | "devScanRun">;

export function formatScanTime(iso: string): string {
  return iso ? `${iso.replace("T", " ").slice(0, 16)} UTC` : "unknown";
}

function Stat(props: { label: string; value: number; tone?: string }) {
  return (
    <div className="min-w-[110px]">
      <div className={`text-[18px] font-semibold ${props.tone ?? ""}`}>{props.value}</div>
      <div className="text-[12px] text-muted">{props.label}</div>
    </div>
  );
}

function Heading(props: { children: React.ReactNode }) {
  return <h3 className="mt-4 mb-1 text-[13px] font-semibold">{props.children}</h3>;
}

/** The scan report. Pure display of a validated report; it never sees raw daemon JSON. */
export function DevScanReportView(props: { report: DevScanReport }) {
  const r = props.report;
  const limits = describeLimits(r);
  const dirty = r.repositories.filter((repo) => repo.dirty === true);
  const notInspected = r.repositories.filter((repo) => repo.errors.length > 0);
  const noUpstream = r.repositories.filter((repo) => repo.has_upstream === false).length;
  const builds = r.storage_findings.filter((s) => s.bytes !== null).slice(0, 5);
  const memory = r.process_findings.filter((p) => p.finding === "process_memory").slice(0, 5);
  const stale = r.process_findings.filter((p) => p.finding === "possible_stale_process");
  const omitted = Object.entries(r.omitted).filter(([, n]) => n > 0);

  return (
    <div className="space-y-1 text-[13px]" data-testid="dev-scan-report">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`font-semibold ${r.status === "complete" ? "text-good" : "text-warn"}`}>
          {r.status === "complete" ? "Scan complete" : "Scan partial: results are incomplete"}
        </span>
        <span className="text-[12px] text-muted">
          Started {formatScanTime(r.started_at)} · finished {formatScanTime(r.finished_at)} · {r.roots_scanned} approved folder
          {r.roots_scanned === 1 ? "" : "s"}
        </span>
      </div>
      {r.status === "partial" && (
        <p className="text-[12px] text-warn">
          {limits.length ? `Why: ${limits.join("; ")}.` : "Some locations could not be fully checked."} Numbers below may be too low.
        </p>
      )}

      <div className="flex flex-wrap gap-4 py-2">
        <Stat label="Repositories" value={r.summary.repositories} />
        <Stat label="With uncommitted changes" value={r.summary.dirty_repositories} tone={r.summary.dirty_repositories ? "text-warn" : ""} />
        <Stat label="Possible duplicate groups" value={r.summary.possible_duplicate_families} />
        <Stat label="Large build folders (100 MB+)" value={r.summary.large_build_directories} />
        <Stat label="Warnings" value={r.summary.warnings} />
      </div>

      <Heading>Suggested next steps</Heading>
      <ul className="list-disc space-y-1 pl-5">
        {r.recommendations.map((rec) => (
          <li key={rec.code} className={rec.severity === "attention" ? "text-warn" : ""}>
            {rec.message}
          </li>
        ))}
      </ul>

      {dirty.length > 0 && (
        <>
          <Heading>Repositories with uncommitted changes</Heading>
          <ul className="space-y-1">
            {dirty.slice(0, 15).map((repo) => (
              <li key={repo.path}>
                <span className="font-medium">{repo.name}</span>{" "}
                <span className="text-muted">
                  {repo.detached ? "detached HEAD" : repo.branch ?? "no branch"} · {repo.modified_count ?? "?"} modified ·{" "}
                  {repo.untracked_count ?? "?"} untracked
                  {repo.has_upstream === false ? " · no upstream" : ""}
                </span>
              </li>
            ))}
          </ul>
          {dirty.length > 15 && <p className="text-[12px] text-muted">{dirty.length - 15} more not listed here.</p>}
        </>
      )}
      {noUpstream > 0 && (
        <p className="text-[12px] text-muted">
          {noUpstream} repositories have no upstream branch configured. That is normal for local-only work, not an error.
        </p>
      )}

      {notInspected.length > 0 && (
        <>
          <Heading>Not inspected: needs your review</Heading>
          <p className="text-[12px] text-muted">
            Chief did not read these repositories, so their status is unknown. Nothing was changed.
          </p>
          <ul className="space-y-1">
            {notInspected.slice(0, 15).map((repo) => (
              <li key={repo.path}>
                <span className="font-medium">{repo.name}</span>{" "}
                <span className="text-muted">{repo.errors[0]}</span>
              </li>
            ))}
          </ul>
          {notInspected.length > 15 && <p className="text-[12px] text-muted">{notInspected.length - 15} more not listed here.</p>}
        </>
      )}

      {builds.length > 0 && (
        <>
          <Heading>Largest build and dependency folders</Heading>
          <ul className="space-y-1">
            {builds.map((s) => (
              <li key={s.path}>
                <span className="font-mono text-[12px]">{formatBytes(s.bytes)}</span>{" "}
                <span className="text-muted">({MEASUREMENT_LABELS[s.measurement]})</span> {s.kind.replace("_", " ")}
                <div className="selectable break-all text-[12px] text-muted">{s.path}</div>
              </li>
            ))}
          </ul>
        </>
      )}

      {r.duplicate_families.length > 0 && (
        <>
          <Heading>Possible duplicate project groups: needs your review</Heading>
          <ul className="space-y-2">
            {r.duplicate_families.map((f) => (
              <li key={f.normalized_name}>
                <div className="font-medium">{f.members.map((m) => m.name).join(" · ")}</div>
                <div className="text-[12px] text-muted">Evidence: {f.evidence.map((e) => e.replace(/_/g, " ")).join(", ")}</div>
              </li>
            ))}
          </ul>
        </>
      )}

      {r.include_processes && (
        <>
          <Heading>Memory use by development tools</Heading>
          {memory.length === 0 ? (
            <p className="text-muted">No development processes found, or the snapshot was unavailable.</p>
          ) : (
            <ul className="space-y-1">
              {memory.map((p) => (
                <li key={p.pid}>
                  <span className="font-mono text-[12px]">{formatBytes(p.rss_bytes)}</span> {p.name}{" "}
                  <span className="text-muted">({p.category.replace("_", " ")}, pid {p.pid})</span>
                </li>
              ))}
            </ul>
          )}
          {stale.length > 0 && (
            <>
              <Heading>Possible stale processes (not confirmed)</Heading>
              <ul className="space-y-1">
                {stale.map((p) => (
                  <li key={p.pid}>
                    {p.name} <span className="text-muted">pid {p.pid} · {p.evidence.map((e) => e.replace(/_/g, " ")).join(", ")}. Check it yourself; Chief will not stop it.</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {r.warnings.length > 0 && (
        <>
          <Heading>Warnings</Heading>
          <ul className="list-disc space-y-1 pl-5 text-muted">
            {r.warnings.map((w, i) => (
              <li key={`${w.code}-${i}`}>{w.message}</li>
            ))}
          </ul>
        </>
      )}
      {omitted.length > 0 && (
        <p className="pt-2 text-[12px] text-warn">
          Not shown because of the report size limit: {omitted.map(([k, n]) => `${n} ${k.replace(/_/g, " ")}`).join(", ")}.
        </p>
      )}
      <p className="pt-2 text-[12px] text-muted">
        Read-only: Chief did not change any project, process, or file. Checked {r.coverage.entries_visited} items; skipped{" "}
        {r.coverage.excluded_directories_skipped} private folders and {r.coverage.symlinks_skipped} links.
      </p>
    </div>
  );
}

export function DevScanPanel(props: {
  bridge: ScanBridge;
  onRan?: (result: Extract<DevScanRunResult, { ok: true }>) => void;
  initialRoots?: string[];
  initialIncludeProcesses?: boolean;
  initialRunning?: boolean;
  initialResult?: DevScanRunResult | null;
}) {
  const { bridge, onRan } = props;
  const [roots, setRoots] = useState<string[]>(props.initialRoots ?? []);
  const [includeProcesses, setIncludeProcesses] = useState(props.initialIncludeProcesses ?? true);
  const [running, setRunning] = useState(props.initialRunning ?? false);
  const [result, setResult] = useState<DevScanRunResult | null>(props.initialResult ?? null);
  const [error, setError] = useState<string | null>(null);

  const loadRoots = useCallback(async () => {
    const res = await bridge.devScanRoots();
    if (res.ok) setRoots(res.roots);
    else setError(res.error);
  }, [bridge]);

  useEffect(() => {
    if (props.initialRoots === undefined) void loadRoots();
  }, [loadRoots, props.initialRoots]);

  const addRoot = async () => {
    setError(null);
    const res = await bridge.devScanAddRoot();
    if (res.ok) setRoots(res.roots);
    else setError(res.error);
  };

  const removeRoot = async (root: string) => {
    setError(null);
    const res = await bridge.devScanRemoveRoot(root);
    if (res.ok) setRoots(res.roots);
    else setError(res.error);
  };

  const run = async () => {
    setError(null);
    setRunning(true);
    try {
      const res = await bridge.devScanRun(includeProcesses);
      setResult(res);
      if (res.ok) onRan?.(res);
      else setError(res.error);
    } catch {
      setError("The scan could not be started.");
    } finally {
      setRunning(false);
    }
  };

  const noRoots = roots.length === 0;
  return (
    <section className="rounded-xl border border-line bg-surface p-4" aria-label="Development scan">
      <h2 className="text-[14px] font-semibold">Development scan</h2>
      <p className="mt-1 text-[12px] text-muted">
        A read-only check of the development folders you approve. Chief reads folder names, sizes, and Git status. It never opens file
        contents, follows links out of a folder, or changes anything. It runs only when you press the button.
      </p>

      <h3 className="mt-3 text-[13px] font-semibold">Approved folders</h3>
      {noRoots ? (
        <p className="text-[13px] text-muted">No folders approved yet. Approve a folder such as your Projects folder to begin.</p>
      ) : (
        <ul className="mt-1 space-y-1">
          {roots.map((root) => (
            <li key={root} className="flex items-center gap-2 text-[13px]">
              <span className="selectable min-w-0 flex-1 break-all font-mono text-[12px]">{root}</span>
              <button type="button" className={BUTTON} onClick={() => void removeRoot(root)} disabled={running}>
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-2">
        <button type="button" className={BUTTON} onClick={() => void addRoot()} disabled={running}>
          Approve a folder…
        </button>
      </div>

      <label className="mt-3 flex items-center gap-2 text-[13px]">
        <input type="checkbox" checked={includeProcesses} onChange={(e) => setIncludeProcesses(e.target.checked)} disabled={running} />
        Include a process and memory snapshot (names and memory only, never command lines)
      </label>

      <p className="mt-2 text-[12px] text-muted">
        Scope: {noRoots ? "nothing yet" : `${roots.length} approved folder${roots.length === 1 ? "" : "s"}`}, {DEV_SCAN_LIMITS_TEXT}.
        Private folders (keys, credentials, Library) are always skipped.
      </p>

      <div className="mt-3 flex items-center gap-3">
        <button type="button" className={PRIMARY} onClick={() => void run()} disabled={running || noRoots}>
          {running ? "Scanning…" : "Run Development Scan"}
        </button>
        {running && <span className="text-[12px] text-muted">This can take up to a minute.</span>}
      </div>
      {error && <p className="mt-2 text-[13px] text-bad">{error}</p>}

      {result?.ok && result.report && (
        <div className="mt-4 border-t border-line pt-3">
          <DevScanReportView report={result.report} />
        </div>
      )}
      {result?.ok && !result.report && (
        <p className="mt-3 text-[13px] text-bad">
          The scan {result.state === "FAILED" ? "failed" : `ended as ${result.state.toLowerCase()}`}
          {result.error ? `: ${result.error}` : "."} You can retry it from the task list.
        </p>
      )}
    </section>
  );
}
