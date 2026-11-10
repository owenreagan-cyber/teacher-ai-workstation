// Presentation rules for the runtime snapshot, kept pure so they can be tested
// without a DOM. The daemon is the source of truth; this only formats it.

export type RuntimeProvenance = {
  loaded_commit?: string | null;
  loaded_branch?: string | null;
  python?: string | null;
  environment?: string | null;
  source_available?: boolean;
};

export type RuntimeBody = {
  ok?: boolean;
  cosd_version?: string;
  uptime_s?: number | null;
  queue_paused?: boolean;
  state?: string | null;
  state_reasons?: string[] | null;
  provenance?: RuntimeProvenance | null;
  checkout?: { restart_required?: boolean | null; current_commit?: string | null; reason?: string | null } | null;
};

export type RuntimeSummary = {
  state: string;
  version: string;
  commit: string;
  python: string;
  warning: string | null;
};

const KNOWN_STATES = ["HEALTHY", "DEGRADED", "RECOVERING", "BLOCKED", "DISCONNECTED"];

export function runtimeSummary(body: RuntimeBody | null | undefined): RuntimeSummary {
  const state = body?.state && KNOWN_STATES.includes(body.state) ? body.state : "UNKNOWN";
  const commit = body?.provenance?.loaded_commit ?? "unknown";
  const python = body?.provenance?.python ?? "unknown";
  const reasons = (body?.state_reasons ?? []).filter(Boolean);

  let warning: string | null = null;
  if (body?.checkout?.restart_required === true) {
    const current = body.checkout.current_commit ?? "a newer checkout";
    warning = `Restart required: running ${commit}, checkout is ${current}.`;
  } else if (state === "BLOCKED" || state === "DEGRADED" || state === "RECOVERING") {
    warning = reasons.length ? reasons.join("; ") : null;
  }

  return {
    state,
    version: body?.cosd_version ?? "—",
    commit,
    python,
    warning,
  };
}
