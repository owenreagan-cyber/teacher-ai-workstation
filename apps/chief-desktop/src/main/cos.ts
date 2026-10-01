// Runs the local cos CLI with execFile (no shell) and turns its stdout into typed results.
// The app makes no network requests; only cos talks to Ollama / Open-Meteo, under its own allowlist.
import { execFile } from "node:child_process";
import fs from "node:fs";
import os from "node:os";

import type {
  AskResult,
  BriefResult,
  ControlResult,
  ErrorKind,
  Failure,
  HistoryResult,
  StatusResult,
  Turn,
} from "../shared/types.js";
import { type Action, ArgsError, buildArgs, type Params } from "./args.js";

const TIMEOUT_MS: Record<Action, number> = {
  ask: 300_000, // a cold 35B model load can take a while
  brief: 90_000,
  history: 10_000,
  status: 10_000,
  stop: 10_000,
  resume: 10_000,
};
const MAX_BUFFER = 2_000_000;

export function minimalEnv(): Record<string, string> {
  return {
    PATH: "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
    HOME: os.homedir(),
    LANG: "en_US.UTF-8",
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
  constructor(
    private readonly cosPath: string,
    private readonly setupError: string | null = null,
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

  private static envelope<T>(value: unknown, valid: (v: Record<string, unknown>) => boolean): T | Failure {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      return fail("internal", "Chief returned an unexpected response.");
    }
    const v = value as Record<string, unknown>;
    if (v.ok === false) {
      const kinds: ErrorKind[] = ["usage", "stopped", "model_unavailable", "internal", "setup", "timeout"];
      const kind = kinds.includes(v.error_kind as ErrorKind) ? (v.error_kind as ErrorKind) : "internal";
      return fail(kind, typeof v.error === "string" ? v.error : "error");
    }
    return v.ok === true && valid(v) ? (v as T) : fail("internal", "Chief returned an unexpected response.");
  }

  async ask(question: unknown, sessionId: unknown): Promise<AskResult> {
    const v = await this.json("ask", { question, sessionId });
    return CosRunner.envelope<AskResult>(v, (o) => typeof o.answer === "string" && Array.isArray(o.tools_used));
  }

  async history(sessionId: unknown): Promise<HistoryResult> {
    const v = await this.json("history", { sessionId });
    if (Array.isArray(v)) {
      const turns = v.filter((t): t is Turn => typeof t === "object" && t !== null && typeof t.answer === "string");
      return { ok: true, turns };
    }
    return CosRunner.envelope<HistoryResult>(v, () => false);
  }

  async brief(): Promise<BriefResult> {
    const v = await this.json("brief");
    return CosRunner.envelope<BriefResult>(v, (o) => Array.isArray(o.lines));
  }

  async status(): Promise<StatusResult> {
    const v = await this.json("status");
    return CosRunner.envelope<StatusResult>(v, (o) => typeof o.kill_switch === "boolean");
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
