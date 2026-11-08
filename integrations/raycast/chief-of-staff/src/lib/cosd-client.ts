import { requestJson, CosdHttpError } from "./http";
import { processAlive, readDaemonToken, readPidRecord } from "./paths";
import type { AskSuccess, ApiError, ConnectionSnapshot, CosdTask, CosdConnectionState } from "./types";

const MIN_VERSION = [0, 1, 0];
const ASK_TIMEOUT_MS = 310_000;
const TASK_ID_RE = /^[a-f0-9]{32}$/;

function parseVersion(text: string): number[] {
  const parts = (text || "0.0.0").split(".");
  return [0, 1, 2].map((i) => parseInt(parts[i] ?? "0", 10) || 0);
}

function versionOk(v: string): boolean {
  const a = parseVersion(v);
  for (let i = 0; i < 3; i++) {
    if (a[i] > MIN_VERSION[i]) return true;
    if (a[i] < MIN_VERSION[i]) return false;
  }
  return true;
}

function toTask(raw: unknown): CosdTask | null {
  if (typeof raw !== "object" || raw === null) return null;
  const t = raw as Record<string, unknown>;
  const id = t.id;
  if (typeof id !== "string" || !TASK_ID_RE.test(id)) return null;
  const state = t.state;
  const title = t.title;
  if (typeof title !== "string" || typeof state !== "string") return null;
  return {
    id,
    kind: typeof t.kind === "string" ? t.kind : "",
    title,
    state: state as CosdTask["state"],
    priority: typeof t.priority === "number" ? t.priority : 0,
    created_at: typeof t.created_at === "string" ? t.created_at : "",
    updated_at: typeof t.updated_at === "string" ? t.updated_at : "",
    attempt_count: typeof t.attempt_count === "number" ? t.attempt_count : 0,
    blocked_reason: t.blocked_reason === null || typeof t.blocked_reason === "string" ? (t.blocked_reason as string | null) : null,
    last_error: t.last_error === null || typeof t.last_error === "string" ? (t.last_error as string | null) : null,
    next_retry_at: t.next_retry_at === null || typeof t.next_retry_at === "string" ? (t.next_retry_at as string | null) : null,
  };
}

export class CosdClient {
  constructor(readonly stateRoot: string) {}

  private token(): string | null {
    return readDaemonToken(this.stateRoot);
  }

  private endpoint(): { host: string; port: number } | null {
    const rec = readPidRecord(this.stateRoot);
    if (!rec || !processAlive(rec.pid)) return null;
    return { host: rec.host, port: rec.port };
  }

  async connectionSnapshot(): Promise<ConnectionSnapshot> {
    const ep = this.endpoint();
    if (!ep) {
      return {
        state: "DISCONNECTED",
        detail: "cosd is not running (start with bin/cosd start)",
        daemon_version: null,
        host: null,
        port: null,
      };
    }
    const tok = this.token();
    if (!tok) {
      return {
        state: "AUTH_ERROR",
        detail: "cosd API token missing in private state",
        daemon_version: null,
        host: ep.host,
        port: ep.port,
      };
    }
    try {
      const health = await requestJson(ep.host, ep.port, "/health");
      if (health.body.ok !== true) {
        return { state: "DEGRADED", detail: "health check failed", daemon_version: null, host: ep.host, port: ep.port };
      }
      const ver = typeof health.body.version === "string" ? health.body.version : "0.0.0";
      if (!versionOk(ver)) {
        return {
          state: "VERSION_MISMATCH",
          detail: `cosd ${ver} is below required 0.1.0`,
          daemon_version: ver,
          host: ep.host,
          port: ep.port,
        };
      }
      const status = await requestJson(ep.host, ep.port, "/v1/status", { token: tok });
      if (status.status === 401) {
        return { state: "AUTH_ERROR", detail: "invalid or rotated token", daemon_version: ver, host: ep.host, port: ep.port };
      }
      if (status.body.ok !== true) {
        return { state: "DEGRADED", detail: "status probe failed", daemon_version: ver, host: ep.host, port: ep.port };
      }
      return { state: "CONNECTED", detail: null, daemon_version: ver, host: ep.host, port: ep.port };
    } catch (e) {
      const msg = e instanceof CosdHttpError ? e.message : "connection failed";
      return { state: "RECOVERING", detail: msg, daemon_version: null, host: ep.host, port: ep.port };
    }
  }

  private async authed(path: string, init: { method?: string; body?: unknown; timeoutMs?: number } = {}) {
    const snap = await this.connectionSnapshot();
    if (snap.state !== "CONNECTED" || snap.host === null || snap.port === null) {
      throw new CosdHttpError(snap.detail ?? "cosd unavailable", "setup");
    }
    const tok = this.token();
    if (!tok) throw new CosdHttpError("token unavailable", "auth");
    return requestJson(snap.host, snap.port, path, { ...init, token: tok });
  }

  async ask(question: string, sessionId: string | null, signal?: AbortSignal): Promise<AskSuccess | ApiError> {
    try {
      if (signal?.aborted) return { ok: false, error: "cancelled", error_kind: "usage" };
      const { status, body } = await this.authed("/v1/ask", {
        method: "POST",
        body: { question, ...(sessionId ? { session_id: sessionId } : {}) },
        timeoutMs: ASK_TIMEOUT_MS,
      });
      if (body.ok === true) return body as AskSuccess;
      return { ok: false, error: String(body.error ?? "ask failed"), error_kind: String(body.error_kind ?? "internal") };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("ask failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async createTask(fields: Record<string, unknown>): Promise<{ ok: true; task: CosdTask; reused: boolean } | ApiError> {
    try {
      const { status, body } = await this.authed("/v1/tasks", { method: "POST", body: fields });
      const task = toTask(body.task);
      if (!task) return { ok: false, error: "invalid task response", error_kind: "internal" };
      return { ok: true, task, reused: body.reused === true };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("create failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async listTasks(query: { state?: string; limit?: number } = {}): Promise<{ ok: true; tasks: CosdTask[]; total: number } | ApiError> {
    try {
      const qs = new URLSearchParams();
      if (query.state) qs.set("state", query.state);
      if (query.limit) qs.set("limit", String(query.limit));
      const suffix = qs.size ? `?${qs.toString()}` : "";
      const { body } = await this.authed(`/v1/tasks${suffix}`);
      const raw = Array.isArray(body.tasks) ? body.tasks : [];
      const tasks = raw.map(toTask).filter((t): t is CosdTask => t !== null);
      return { ok: true, tasks, total: typeof body.total === "number" ? body.total : tasks.length };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("list failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async getTask(taskId: string): Promise<{ ok: true; task: CosdTask } | ApiError> {
    if (!TASK_ID_RE.test(taskId)) return { ok: false, error: "invalid task id", error_kind: "usage" };
    try {
      const { body } = await this.authed(`/v1/tasks/${taskId}`);
      const task = toTask(body.task);
      if (!task) return { ok: false, error: "invalid task", error_kind: "internal" };
      return { ok: true, task };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("get failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async cancelTask(taskId: string, reason?: string): Promise<{ ok: true; task: CosdTask } | ApiError> {
    if (!TASK_ID_RE.test(taskId)) return { ok: false, error: "invalid task id", error_kind: "usage" };
    try {
      const { body } = await this.authed(`/v1/tasks/${taskId}/cancel`, {
        method: "POST",
        body: reason ? { reason } : {},
      });
      const task = toTask(body.task);
      if (!task) return { ok: false, error: "invalid task", error_kind: "internal" };
      return { ok: true, task };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("cancel failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async retryTask(taskId: string): Promise<{ ok: true; task: CosdTask } | ApiError> {
    if (!TASK_ID_RE.test(taskId)) return { ok: false, error: "invalid task id", error_kind: "usage" };
    try {
      const { body } = await this.authed(`/v1/tasks/${taskId}/retry`, { method: "POST", body: {} });
      const task = toTask(body.task);
      if (!task) return { ok: false, error: "invalid task", error_kind: "internal" };
      return { ok: true, task };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("retry failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async taskHistory(taskId: string): Promise<{ ok: true; events: { ts: string; event: string }[] } | ApiError> {
    if (!TASK_ID_RE.test(taskId)) return { ok: false, error: "invalid task id", error_kind: "usage" };
    try {
      const { body } = await this.authed(`/v1/tasks/${taskId}/history`);
      const events = Array.isArray(body.events)
        ? body.events
            .map((ev) => {
              if (typeof ev !== "object" || ev === null) return null;
              const e = ev as Record<string, unknown>;
              if (typeof e.ts !== "string" || typeof e.event !== "string") return null;
              return { ts: e.ts, event: e.event };
            })
            .filter((x): x is { ts: string; event: string } => x !== null)
        : [];
      return { ok: true, events };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("history failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async queueSnapshot(): Promise<{ ok: true; paused: boolean; task_counts: Record<string, number>; active_leases: unknown[] } | ApiError> {
    try {
      const { body } = await this.authed("/v1/queue");
      return {
        ok: true,
        paused: body.paused === true,
        task_counts: typeof body.task_counts === "object" && body.task_counts !== null ? (body.task_counts as Record<string, number>) : {},
        active_leases: Array.isArray(body.active_leases) ? body.active_leases : [],
      };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("queue failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async workers(): Promise<{ ok: true; workers: unknown[] } | ApiError> {
    try {
      const { body } = await this.authed("/v1/workers");
      return { ok: true, workers: Array.isArray(body.workers) ? body.workers : [] };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("workers failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }

  async status(): Promise<Record<string, unknown> | null> {
    try {
      const { body } = await this.authed("/v1/status");
      return body.ok === true ? body : null;
    } catch {
      return null;
    }
  }

  async runtimeSnapshot(): Promise<{ ok: true; body: Record<string, unknown> } | ApiError> {
    try {
      const { body } = await this.authed("/v1/runtime");
      if (body.ok !== true) return { ok: false, error: String(body.error ?? "runtime failed"), error_kind: "internal" };
      return { ok: true, body };
    } catch (e) {
      const err = e instanceof CosdHttpError ? e : new CosdHttpError("runtime failed");
      return { ok: false, error: err.message, error_kind: err.kind };
    }
  }
}

export function clientFromPreferences(stateDir: string): CosdClient {
  return new CosdClient(stateDir);
}

export function connectionLabel(state: CosdConnectionState): string {
  switch (state) {
    case "CONNECTED":
      return "Connected";
    case "DISCONNECTED":
      return "Disconnected";
    case "AUTH_ERROR":
      return "Auth error";
    case "VERSION_MISMATCH":
      return "Version mismatch";
    case "DEGRADED":
      return "Degraded";
    case "RECOVERING":
      return "Recovering";
    default:
      return state;
  }
}
