import { execFile } from "node:child_process";
import { promisify } from "node:util";

import type { CosdConnectionState, CosdHealth, CosdTask, QueueSnapshot, TaskHistoryEvent, TaskState } from "../../shared/cosd.js";
import { COS_STATE_DIR } from "../config.js";
import { CosdHttpError, requestAskNdjsonStream, requestJson } from "./http.js";
import { processAlive, readDaemonToken, readPidRecord, type PidRecord } from "./paths.js";

const execFileAsync = promisify(execFile);
const MIN_VERSION = [0, 1, 0];
const ASK_TIMEOUT_MS = 310_000;

const TASK_STATES = new Set<TaskState>([
  "QUEUED",
  "CLAIMED",
  "RUNNING",
  "BLOCKED",
  "FAILED",
  "COMPLETED",
  "CANCELLED",
]);

function parseVersion(text: string): number[] {
  return (text || "0.0.0").split(".").slice(0, 3).map((p) => Number.parseInt(p, 10) || 0);
}

function versionOk(text: string): boolean {
  const v = parseVersion(text);
  for (let i = 0; i < 3; i += 1) {
    if (v[i] > MIN_VERSION[i]) return true;
    if (v[i] < MIN_VERSION[i]) return false;
  }
  return true;
}

async function processIsCosd(pid: number): Promise<boolean> {
  if (process.platform !== "darwin") return processAlive(pid);
  try {
    const { stdout } = await execFileAsync("ps", ["-p", String(pid), "-o", "command="], {
      timeout: 2000,
      maxBuffer: 4096,
    });
    const cmd = String(stdout || "").trim();
    return cmd.includes("cosd");
  } catch {
    return false;
  }
}

export type DaemonEndpoint = { host: string; port: number; version: string; record: PidRecord };

function toTask(raw: unknown): CosdTask | null {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return null;
  const o = raw as Record<string, unknown>;
  const state = o.state;
  if (typeof o.id !== "string" || typeof o.kind !== "string" || typeof o.title !== "string") return null;
  if (typeof state !== "string" || !TASK_STATES.has(state as TaskState)) return null;
  if (typeof o.priority !== "number" || typeof o.created_at !== "string" || typeof o.updated_at !== "string") return null;
  if (typeof o.attempt_count !== "number") return null;
  return {
    id: o.id,
    kind: o.kind,
    title: o.title,
    state: state as TaskState,
    priority: o.priority,
    created_at: o.created_at,
    updated_at: o.updated_at,
    attempt_count: o.attempt_count,
    blocked_reason: typeof o.blocked_reason === "string" ? o.blocked_reason : null,
    last_error: typeof o.last_error === "string" ? o.last_error : null,
    next_retry_at: typeof o.next_retry_at === "string" ? o.next_retry_at : null,
  };
}

export class CosdClient {
  constructor(private readonly stateRoot = COS_STATE_DIR) {}

  private token(): string | null {
    return readDaemonToken(this.stateRoot);
  }

  async discover(): Promise<DaemonEndpoint | null> {
    const record = readPidRecord(this.stateRoot);
    if (!record || !processAlive(record.pid)) return null;
    if (!(await processIsCosd(record.pid))) return null;
    if (record.host !== "127.0.0.1" && record.host !== "localhost") return null;
    const health = await this.health(record.host, record.port);
    if (!health?.ok) return null;
    const version = String(health.version ?? "0.0.0");
    if (!versionOk(version)) return null;
    return { host: record.host, port: record.port, version, record };
  }

  async health(host: string, port: number): Promise<CosdHealth | null> {
    try {
      const { status, body } = await requestJson(host, port, "/health", { timeoutMs: 3000 });
      if (status !== 200 || body.ok !== true) return null;
      return { ok: true, service: String(body.service ?? ""), version: String(body.version ?? "") };
    } catch {
      return null;
    }
  }

  async probeAuth(ep: DaemonEndpoint): Promise<boolean> {
    const token = this.token();
    if (!token) return false;
    try {
      const { status, body } = await this.authed(ep, "GET", "/v1/status");
      return status === 200 && body.ok === true;
    } catch {
      return false;
    }
  }

  private async authed(
    ep: DaemonEndpoint,
    method: string,
    path: string,
    body?: unknown,
    timeoutMs?: number,
  ): Promise<{ status: number; body: Record<string, unknown> }> {
    const token = this.token();
    if (!token) throw new CosdHttpError("cosd token unavailable", "auth");
    return requestJson(ep.host, ep.port, path, { method, body, token, timeoutMs });
  }

  async status(ep: DaemonEndpoint): Promise<Record<string, unknown>> {
    const { status, body } = await this.authed(ep, "GET", "/v1/status");
    if (status !== 200 || body.ok !== true) throw new CosdHttpError("status failed", "internal");
    return body;
  }

  async askStream(
    ep: DaemonEndpoint,
    question: string,
    sessionId: string | null,
    signal: AbortSignal | undefined,
    onChunk: (text: string) => void,
  ): Promise<Record<string, unknown>> {
    if (signal?.aborted) throw new CosdHttpError("cancelled", "usage");
    const token = this.token();
    if (!token) throw new CosdHttpError("cosd token unavailable", "auth");
    return requestAskNdjsonStream(ep.host, ep.port, token, question, sessionId, onChunk, signal, ASK_TIMEOUT_MS);
  }

  async ask(ep: DaemonEndpoint, question: string, sessionId: string | null, signal?: AbortSignal): Promise<Record<string, unknown>> {
    if (signal?.aborted) throw new CosdHttpError("cancelled", "usage");
    const payload: Record<string, unknown> = { question };
    if (sessionId) payload.session_id = sessionId;
    const p = this.authed(ep, "POST", "/v1/ask", payload, ASK_TIMEOUT_MS);
    if (!signal) return (await p).body;
    return new Promise((resolve, reject) => {
      const onAbort = () => reject(new CosdHttpError("cancelled", "usage"));
      signal.addEventListener("abort", onAbort, { once: true });
      p.then((r) => {
        signal.removeEventListener("abort", onAbort);
        resolve(r.body);
      }).catch((e) => {
        signal.removeEventListener("abort", onAbort);
        reject(e);
      });
    });
  }

  async listTasks(ep: DaemonEndpoint, query: { state?: string; limit?: number; offset?: number } = {}) {
    const qs = new URLSearchParams();
    if (query.state) qs.set("state", query.state);
    if (query.limit !== undefined) qs.set("limit", String(query.limit));
    if (query.offset !== undefined) qs.set("offset", String(query.offset));
    const suffix = qs.size ? `?${qs.toString()}` : "";
    const { body } = await this.authed(ep, "GET", `/v1/tasks${suffix}`);
    const tasks = Array.isArray(body.tasks) ? body.tasks.map(toTask).filter((t): t is CosdTask => t !== null) : [];
    return {
      tasks,
      total: typeof body.total === "number" ? body.total : tasks.length,
      limit: typeof body.limit === "number" ? body.limit : tasks.length,
      offset: typeof body.offset === "number" ? body.offset : 0,
    };
  }

  async getTask(ep: DaemonEndpoint, taskId: string): Promise<CosdTask> {
    const { body } = await this.authed(ep, "GET", `/v1/tasks/${taskId}`);
    const task = toTask(body.task);
    if (!task) throw new CosdHttpError("invalid task", "internal");
    return task;
  }

  async createTask(ep: DaemonEndpoint, fields: Record<string, unknown>): Promise<{ task: CosdTask; reused: boolean }> {
    const { status, body } = await this.authed(ep, "POST", "/v1/tasks", fields);
    if (status !== 200 && status !== 201) throw new CosdHttpError(String(body.error ?? "create failed"), String(body.error_kind ?? "internal"));
    const task = toTask(body.task);
    if (!task) throw new CosdHttpError("invalid task", "internal");
    return { task, reused: body.reused === true };
  }

  async cancelTask(ep: DaemonEndpoint, taskId: string, reason?: string): Promise<CosdTask> {
    const { body } = await this.authed(ep, "POST", `/v1/tasks/${taskId}/cancel`, reason ? { reason } : {});
    const task = toTask(body.task);
    if (!task) throw new CosdHttpError("invalid task", "internal");
    return task;
  }

  async retryTask(ep: DaemonEndpoint, taskId: string): Promise<CosdTask> {
    const { body } = await this.authed(ep, "POST", `/v1/tasks/${taskId}/retry`, {});
    const task = toTask(body.task);
    if (!task) throw new CosdHttpError("invalid task", "internal");
    return task;
  }

  async taskHistory(ep: DaemonEndpoint, taskId: string): Promise<TaskHistoryEvent[]> {
    const { body } = await this.authed(ep, "GET", `/v1/tasks/${taskId}/history`);
    if (!Array.isArray(body.events)) return [];
    const out: TaskHistoryEvent[] = [];
    for (const ev of body.events) {
      if (typeof ev !== "object" || ev === null) continue;
      const o = ev as Record<string, unknown>;
      if (typeof o.ts !== "string" || typeof o.event !== "string") continue;
      const row: TaskHistoryEvent = { ts: o.ts, event: o.event };
      if (typeof o.detail === "object" && o.detail !== null) row.detail = o.detail as Record<string, unknown>;
      out.push(row);
    }
    return out;
  }

  async queue(ep: DaemonEndpoint): Promise<QueueSnapshot> {
    const { body } = await this.authed(ep, "GET", "/v1/queue");
    return {
      paused: body.paused === true,
      task_counts: typeof body.task_counts === "object" && body.task_counts !== null ? (body.task_counts as Record<string, number>) : {},
      active_leases: Array.isArray(body.active_leases) ? body.active_leases : [],
    };
  }

  async workers(ep: DaemonEndpoint): Promise<unknown[]> {
    const { body } = await this.authed(ep, "GET", "/v1/workers");
    return Array.isArray(body.workers) ? body.workers : [];
  }

  connectionStateFromDiscover(ep: DaemonEndpoint | null, authed: boolean): CosdConnectionState {
    if (!ep) return "DISCONNECTED";
    if (!versionOk(ep.version)) return "VERSION_MISMATCH";
    if (!authed) return "AUTH_ERROR";
    return "CONNECTED";
  }
}
