// Runs the local cos CLI with execFile (no shell) and turns its stdout into typed results.
// The app makes no network requests; only cos talks to Ollama / Open-Meteo, under its own allowlist.
import { execFile } from "node:child_process";
import fs from "node:fs";
import os from "node:os";

import type {
  AskResult,
  AutoSearchResult,
  BriefResult,
  ControlResult,
  ErrorKind,
  Failure,
  HistoryResult,
  HomeResult,
  StatusResult,
  Turn,
  WarmResult,
} from "../shared/types.js";
import { type Resource, stripUrls, toBlocks, toResources } from "../shared/blocks.js";
import { toHomeSnapshot } from "../shared/home.js";
import { toHomeCard } from "../shared/homeCard.js";
import { type Action, ArgsError, buildArgs, type Params } from "./args.js";

const TIMEOUT_MS: Record<Action, number> = {
  ask: 300_000, // a cold 35B model load can take a while
  brief: 90_000,
  history: 10_000,
  status: 10_000,
  stop: 10_000,
  resume: 10_000,
  warm: 300_000, // loading the model from disk
  "auto-search": 10_000,
  home: 40_000, // due sources refresh in parallel inside cos, each with its own timeout
};
const MAX_BUFFER = 2_000_000;

export function minimalEnv(): Record<string, string> {
  return {
    PATH: "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
    HOME: os.homedir(),
    LANG: "en_US.UTF-8",
  };
}

const isStr = (v: unknown): v is string => typeof v === "string";
const isStrList = (v: unknown): v is string[] => Array.isArray(v) && v.every(isStr);

/** The answer half of a turn, rebuilt field by field (same rules as cos/sessions.py check_turn), or null.
 * Text bound for the renderer has every URL removed; links reach it only as block link ids. */
function answerFields(o: Record<string, unknown>): Omit<Turn, "question"> | null {
  const { ts, answer, tools_used, fast_path, model, notices, total_ms } = o;
  if (!isStr(ts) || !isStr(answer) || !isStrList(tools_used) || typeof fast_path !== "boolean") return null;
  if (!(model === null || isStr(model)) || !isStrList(notices)) return null;
  if (typeof total_ms !== "number" || !Number.isSafeInteger(total_ms) || total_ms < 0) return null;
  return {
    ts,
    answer: stripUrls(answer),
    tools_used: [...tools_used],
    fast_path,
    model,
    notices: notices.map(stripUrls),
    total_ms,
    blocks: toBlocks(o.blocks),
  };
}

/** A full Turn with exactly the known fields and correct types, or null (dropped). */
export function toTurn(value: unknown): Turn | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  const o = value as Record<string, unknown>;
  const rest = answerFields(o);
  return rest && isStr(o.question) ? { ...rest, question: stripUrls(o.question) } : null;
}

/** The resources ({id, url}) a cos answer or history turn carries; they go to the main process only. */
function resourcesOf(value: unknown): Resource[] {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? toResources((value as Record<string, unknown>).resources)
    : [];
}

const AUDIT_STATES = ["ok", "empty", "fail"] as const;

/** `cos status --json`, rebuilt field by field with exactly the known fields, or null (invalid). */
export function toStatus(o: Record<string, unknown>): Extract<StatusResult, { ok: true }> | null {
  const { kill_switch, kill_switch_reason, model, fallback_model, ollama_reachable, loaded_models, audit, version } = o;
  const { auto_search } = o;
  if (typeof kill_switch !== "boolean" || typeof ollama_reachable !== "boolean") return null;
  if (typeof auto_search !== "boolean") return null;
  if (!(kill_switch_reason === null || isStr(kill_switch_reason)) || !isStr(model)) return null;
  if (!(fallback_model === null || isStr(fallback_model)) || !isStrList(loaded_models) || !isStr(version)) return null;
  const auditState = AUDIT_STATES.find((s) => s === audit);
  if (auditState === undefined) return null;
  return {
    ok: true,
    kill_switch,
    kill_switch_reason,
    model,
    fallback_model,
    ollama_reachable,
    loaded_models: [...loaded_models],
    audit: auditState,
    version,
    auto_search,
  };
}

function fail(error_kind: ErrorKind, error: string): Failure {
  return { ok: false, error, error_kind };
}

type Raw = { code: number | null; timedOut: boolean; stdout: string };

function run(cosPath: string, args: string[], timeout: number): Promise<Raw> {
  return new Promise((resolve) => {
    execFile(
      cosPath,
      args,
      { env: minimalEnv(), timeout, maxBuffer: MAX_BUFFER, windowsHide: true, encoding: "utf8" },
      (err, stdout) => {
        const e = err as (NodeJS.ErrnoException & { code?: number | string; killed?: boolean }) | null;
        const code = e ? (typeof e.code === "number" ? e.code : null) : 0;
        resolve({ code, timedOut: Boolean(e?.killed), stdout: String(stdout ?? "") });
      },
    );
  });
}

export class CosRunner {
  /** onResources receives the link table entries of every answer and history turn (main process). */
  constructor(
    private readonly cosPath: string,
    private readonly setupError: string | null = null,
    private readonly onResources: (resources: Resource[]) => void = () => {},
  ) {}

  private preflight(action: Action, params: Params): string[] | Failure {
    if (this.setupError) return fail("setup", this.setupError);
    if (!fs.existsSync(this.cosPath)) {
      return fail("setup", `cos was not found at ${this.cosPath}. Set cosPath in desktop.json.`);
    }
    try {
      return buildArgs(action, params);
    } catch (e) {
      return fail("usage", e instanceof ArgsError ? e.message : "invalid request");
    }
  }

  private async json(action: Action, params: Params = {}): Promise<unknown | Failure> {
    const args = this.preflight(action, params);
    if (!Array.isArray(args)) return args;
    const raw = await run(this.cosPath, args, TIMEOUT_MS[action]);
    if (raw.timedOut) return fail("timeout", "Chief took too long to answer.");
    try {
      return JSON.parse(raw.stdout.trim());
    } catch {
      return fail("internal", "Chief returned an unexpected response.");
    }
  }

  // pick rebuilds the success value from known, correctly typed fields only (null = invalid).
  private static envelope<T>(value: unknown, pick: (v: Record<string, unknown>) => T | null): T | Failure {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      return fail("internal", "Chief returned an unexpected response.");
    }
    const v = value as Record<string, unknown>;
    if (v.ok === false) {
      const kinds: ErrorKind[] = ["usage", "stopped", "model_unavailable", "internal", "setup", "timeout"];
      const kind = kinds.includes(v.error_kind as ErrorKind) ? (v.error_kind as ErrorKind) : "internal";
      return fail(kind, typeof v.error === "string" ? v.error : "error");
    }
    const picked = v.ok === true ? pick(v) : null;
    return picked ?? fail("internal", "Chief returned an unexpected response.");
  }

  async ask(question: unknown, sessionId: unknown): Promise<AskResult> {
    const v = await this.json("ask", { question, sessionId });
    const result = CosRunner.envelope<AskResult>(v, (o) => {
      const fields = answerFields(o);
      if (!fields || !(o.session_id === null || isStr(o.session_id))) return null;
      return { ok: true, ...fields, session_id: o.session_id };
    });
    if (result.ok) this.onResources(resourcesOf(v));
    return result;
  }

  async history(sessionId: unknown): Promise<HistoryResult> {
    const v = await this.json("history", { sessionId });
    if (Array.isArray(v)) {
      const turns = v.map(toTurn).filter((t): t is Turn => t !== null); // invalid turns are dropped
      this.onResources(v.flatMap(resourcesOf));
      return { ok: true, turns };
    }
    return CosRunner.envelope<HistoryResult>(v, () => null);
  }

  async brief(): Promise<BriefResult> {
    const v = await this.json("brief");
    return CosRunner.envelope<BriefResult>(v, (o) =>
      isStrList(o.lines) ? { ok: true, lines: [...o.lines], card: toHomeCard(o.card) } : null);
  }

  /** `cos home --json [--cached]`. mac_history starts empty; the main process fills it in. */
  async home(cached: boolean): Promise<HomeResult> {
    const v = await this.json("home", { cached: cached === true });
    const result = CosRunner.envelope<HomeResult>(v, (o) => {
      const snap = toHomeSnapshot(o);
      return snap ? { ok: true, ...snap, mac_history: [] } : null;
    });
    if (result.ok) this.onResources(resourcesOf(v));
    return result;
  }

  async status(): Promise<StatusResult> {
    const v = await this.json("status");
    return CosRunner.envelope<StatusResult>(v, toStatus);
  }

  async warm(): Promise<WarmResult> {
    const v = await this.json("warm");
    return CosRunner.envelope<WarmResult>(v, (o) =>
      isStr(o.model) && typeof o.loaded === "boolean" && isStr(o.keep_alive)
        ? { ok: true, model: o.model, loaded: o.loaded, keep_alive: o.keep_alive }
        : null);
  }

  /** Main process only (the tray toggle): `cos auto-search on|off --json`. */
  async setAutoSearch(enabled: boolean): Promise<AutoSearchResult> {
    const v = await this.json("auto-search", { enabled: enabled === true });
    return CosRunner.envelope<AutoSearchResult>(v, (o) =>
      typeof o.auto_search === "boolean" ? { ok: true, auto_search: o.auto_search } : null);
  }

  // stop/resume print text; success is exit code 0. The UI re-reads status for the truth.
  private async control(action: "stop" | "resume"): Promise<ControlResult> {
    const args = this.preflight(action, {});
    if (!Array.isArray(args)) return args;
    const raw = await run(this.cosPath, args, TIMEOUT_MS[action]);
    if (raw.timedOut) return fail("timeout", "Chief took too long to answer.");
    return raw.code === 0 ? { ok: true } : fail("internal", `cos ${action} failed.`);
  }

  stop(): Promise<ControlResult> {
    return this.control("stop");
  }

  resume(): Promise<ControlResult> {
    return this.control("resume");
  }
}
