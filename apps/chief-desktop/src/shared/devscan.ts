// Development HQ scan (V0): the report shape the renderer sees, plus a bounded parser.
// The main process parses the daemon's task result with parseDevScanReport and sends only this
// validated, size-capped structure to the renderer. Raw task JSON never reaches the window.

import type { Failure } from "./types.js";

export const DEV_SCAN_KIND = "dev_hq_scan";
export const DEV_SCAN_TITLE = "Development scan";

// Shown to the owner before a scan starts. Keep in sync with ScanLimits in
// cosd/execution/dev_hq_scan.py (the daemon enforces the real values).
export const DEV_SCAN_LIMITS_TEXT = "up to 5 folder levels deep, 40,000 files and folders, 150 repositories, and about 40 seconds";

export type DevScanStatus = "complete" | "partial";

export type DevScanRepo = {
  path: string;
  name: string;
  branch: string | null;
  detached: boolean;
  head: string | null;
  dirty: boolean | null;
  modified_count: number | null;
  untracked_count: number | null;
  has_upstream: boolean | null;
  ahead: number | null;
  behind: number | null;
  worktree_count: number | null;
  linked_worktree_or_submodule: boolean;
  errors: string[];
};

export type DevScanStorage = {
  path: string;
  kind: string;
  bytes: number | null;
  measurement: "exact" | "partial" | "bounded_estimate" | "unavailable";
};

export type DevScanFamily = {
  normalized_name: string;
  members: { name: string; path: string }[];
  evidence: string[];
};

export type DevScanProcess = {
  finding: "process_memory" | "possible_stale_process";
  pid: number;
  name: string;
  category: string;
  rss_bytes: number;
  evidence: string[];
};

export type DevScanRecommendation = { code: string; severity: "info" | "attention"; message: string };

export type DevScanReport = {
  status: DevScanStatus;
  truncated: boolean;
  started_at: string;
  finished_at: string;
  roots: string[];
  roots_scanned: number;
  include_processes: boolean;
  limits_hit: string[];
  summary: {
    repositories: number;
    dirty_repositories: number;
    possible_duplicate_families: number;
    large_build_directories: number;
    warnings: number;
    possible_stale_processes: number;
  };
  coverage: { entries_visited: number; inaccessible_directories: number; excluded_directories_skipped: number; symlinks_skipped: number };
  repositories: DevScanRepo[];
  storage_findings: DevScanStorage[];
  duplicate_families: DevScanFamily[];
  process_findings: DevScanProcess[];
  warnings: { code: string; message: string }[];
  recommendations: DevScanRecommendation[];
  omitted: Record<string, number>;
};

export type DevScanRootsResult = { ok: true; roots: string[]; canceled?: boolean } | Failure;
export type DevScanRunResult =
  | { ok: true; task_id: string; state: string; report: DevScanReport | null; error: string | null }
  | Failure;

// ------------------------------------------------------------------------------ parsing

const MAX_STR = 400;
const CAPS = { repositories: 300, storage: 25, families: 10, members: 6, processes: 20, warnings: 20, recs: 10, list: 12 };
// eslint-disable-next-line no-control-regex
const CONTROL = /[\u0000-\u001f\u007f]/g;

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function str(v: unknown, fallback = ""): string {
  return typeof v === "string" ? v.replace(CONTROL, " ").slice(0, MAX_STR) : fallback;
}
function strOrNull(v: unknown): string | null {
  return typeof v === "string" ? str(v) : null;
}
function int(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= Number.MAX_SAFE_INTEGER ? Math.floor(v) : null;
}
function intOr0(v: unknown): number {
  return int(v) ?? 0;
}
function boolOrNull(v: unknown): boolean | null {
  return typeof v === "boolean" ? v : null;
}
function strList(v: unknown, cap = CAPS.list): string[] {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string").slice(0, cap).map((s) => str(s)) : [];
}
function list<T>(v: unknown, cap: number, map: (x: unknown) => T | null): T[] {
  if (!Array.isArray(v)) return [];
  const out: T[] = [];
  for (const item of v.slice(0, cap)) {
    const parsed = map(item);
    if (parsed !== null) out.push(parsed);
  }
  return out;
}

function parseRepo(raw: unknown): DevScanRepo | null {
  if (!isRecord(raw) || typeof raw.path !== "string" || typeof raw.name !== "string") return null;
  return {
    path: str(raw.path),
    name: str(raw.name),
    branch: strOrNull(raw.branch),
    detached: raw.detached === true,
    head: strOrNull(raw.head),
    dirty: boolOrNull(raw.dirty),
    modified_count: int(raw.modified_count),
    untracked_count: int(raw.untracked_count),
    has_upstream: boolOrNull(raw.has_upstream),
    ahead: int(raw.ahead),
    behind: int(raw.behind),
    worktree_count: int(raw.worktree_count),
    linked_worktree_or_submodule: raw.linked_worktree_or_submodule === true,
    errors: strList(raw.errors, 4),
  };
}

const MEASUREMENTS = new Set(["exact", "partial", "bounded_estimate", "unavailable"]);

function parseStorage(raw: unknown): DevScanStorage | null {
  if (!isRecord(raw) || typeof raw.path !== "string") return null;
  const measurement = typeof raw.measurement === "string" && MEASUREMENTS.has(raw.measurement) ? raw.measurement : "unavailable";
  return { path: str(raw.path), kind: str(raw.kind), bytes: int(raw.bytes), measurement: measurement as DevScanStorage["measurement"] };
}

function parseFamily(raw: unknown): DevScanFamily | null {
  if (!isRecord(raw) || raw.classification !== "possible_duplicate_family") return null;
  const members = list(raw.members, CAPS.members, (m) =>
    isRecord(m) && typeof m.path === "string" ? { name: str(m.name), path: str(m.path) } : null,
  );
  return members.length >= 2 ? { normalized_name: str(raw.normalized_name), members, evidence: strList(raw.evidence) } : null;
}

function parseProcess(raw: unknown): DevScanProcess | null {
  if (!isRecord(raw)) return null;
  const finding = raw.finding === "possible_stale_process" ? "possible_stale_process" : raw.finding === "process_memory" ? "process_memory" : null;
  const pid = int(raw.pid);
  const rss = int(raw.rss_bytes);
  if (finding === null || pid === null || rss === null) return null;
  return { finding, pid, name: str(raw.name), category: str(raw.category), rss_bytes: rss, evidence: strList(raw.evidence, 4) };
}

export function parseDevScanReport(raw: unknown): DevScanReport | null {
  if (!isRecord(raw) || raw.scan_type !== DEV_SCAN_KIND || raw.schema_version !== 1) return null;
  if (raw.status !== "complete" && raw.status !== "partial") return null;
  const s = isRecord(raw.summary) ? raw.summary : {};
  const c = isRecord(raw.coverage) ? raw.coverage : {};
  const omitted: Record<string, number> = {};
  if (isRecord(raw.omitted)) {
    for (const [k, v] of Object.entries(raw.omitted).slice(0, 8)) {
      const n = int(v);
      if (n !== null) omitted[str(k).slice(0, 40)] = n;
    }
  }
  const truncated = raw.truncated === true || Object.keys(omitted).length > 0;
  return {
    // A report is never shown as complete if anything was trimmed.
    status: raw.status === "complete" && !truncated ? "complete" : "partial",
    truncated,
    started_at: str(raw.started_at),
    finished_at: str(raw.finished_at),
    roots: strList(raw.roots, 16),
    roots_scanned: intOr0(raw.roots_scanned),
    include_processes: raw.include_processes === true,
    limits_hit: strList(raw.limits_hit),
    summary: {
      repositories: intOr0(s.repositories),
      dirty_repositories: intOr0(s.dirty_repositories),
      possible_duplicate_families: intOr0(s.possible_duplicate_families),
      large_build_directories: intOr0(s.large_build_directories),
      warnings: intOr0(s.warnings),
      possible_stale_processes: intOr0(s.possible_stale_processes),
    },
    coverage: {
      entries_visited: intOr0(c.entries_visited),
      inaccessible_directories: intOr0(c.inaccessible_directories),
      excluded_directories_skipped: intOr0(c.excluded_directories_skipped),
      symlinks_skipped: intOr0(c.symlinks_skipped),
    },
    repositories: list(raw.repositories, CAPS.repositories, parseRepo),
    storage_findings: list(raw.storage_findings, CAPS.storage, parseStorage),
    duplicate_families: list(raw.duplicate_families, CAPS.families, parseFamily),
    process_findings: list(raw.process_findings, CAPS.processes, parseProcess),
    warnings: list(raw.warnings, CAPS.warnings, (w) => (isRecord(w) ? { code: str(w.code), message: str(w.message) } : null)),
    recommendations: list(raw.recommendations, CAPS.recs, (r) =>
      isRecord(r) && typeof r.message === "string"
        ? { code: str(r.code), severity: r.severity === "attention" ? "attention" : "info", message: str(r.message) }
        : null,
    ),
    omitted,
  };
}

// ------------------------------------------------------------------------------ display helpers

export function formatBytes(bytes: number | null): string {
  if (bytes === null) return "unknown";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${i === 0 ? value : value.toFixed(value >= 10 ? 0 : 1)} ${units[i]}`;
}

export const MEASUREMENT_LABELS: Record<DevScanStorage["measurement"], string> = {
  exact: "exact",
  partial: "at least (partial)",
  bounded_estimate: "estimate",
  unavailable: "unavailable",
};

export const LIMIT_LABELS: Record<string, string> = {
  depth_limit: "folder depth limit",
  entry_limit: "file/folder count limit",
  repo_limit: "repository count limit",
  deadline: "time limit",
  git_timeout: "a Git check timed out",
  git_output_cap: "Git output was capped",
  measure_budget: "size-measurement budget",
  output_truncated: "report size limit",
  duplicate_family_limit: "duplicate-group limit",
};

export function describeLimits(report: DevScanReport): string[] {
  const out = report.limits_hit.map((l) => LIMIT_LABELS[l] ?? l);
  if (report.coverage.inaccessible_directories > 0) out.push(`${report.coverage.inaccessible_directories} folders could not be read`);
  return out;
}
