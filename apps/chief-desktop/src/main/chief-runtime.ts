import { stripUrls, toBlocks, type Resource, toResources } from "../shared/blocks.js";
import type {
  AskResult,
  Failure,
  StatusResult,
} from "../shared/types.js";
import type { CosdConnectionSnapshot, CosdTask, QueueSnapshot, TaskHistoryEvent } from "../shared/cosd.js";
import { CosRunner, toStatus } from "./cos.js";
import { CosdClient } from "./cosd/client.js";
import { CosdConnectionManager, daemonModeFromEnv } from "./cosd/connection.js";
import { CosdHttpError } from "./cosd/http.js";

const isStr = (v: unknown): v is string => typeof v === "string";
const isStrList = (v: unknown): v is string[] => Array.isArray(v) && v.every(isStr);

function fail(error_kind: Failure["error_kind"], error: string): Failure {
  return { ok: false, error, error_kind };
}

function answerFromDaemon(body: Record<string, unknown>, onResources: (r: Resource[]) => void): AskResult {
  if (body.ok !== true) {
    const kinds = ["usage", "stopped", "model_unavailable", "internal", "timeout"] as const;
    const kind = kinds.find((k) => k === body.error_kind) ?? "internal";
    return fail(kind, typeof body.error === "string" ? body.error : "ask failed");
  }
  const answer = typeof body.text === "string" ? body.text : typeof body.answer === "string" ? body.answer : "";
  const tools_used = isStrList(body.tools_used) ? [...body.tools_used] : [];
  const notices = isStrList(body.notices) ? body.notices.map(stripUrls) : [];
  const resources = toResources(body.resources);
  onResources(resources);
  return {
    ok: true,
    answer: stripUrls(answer),
    tools_used,
    model: body.model === null || isStr(body.model) ? (body.model as string | null) : null,
    notices,
    fast_path: body.fast_path === true,
    session_id: body.session_id === null || isStr(body.session_id) ? (body.session_id as string | null) : null,
    ts: isStr(body.ts) ? body.ts : new Date().toISOString(),
    total_ms: typeof body.total_ms === "number" ? body.total_ms : 0,
    blocks: toBlocks(body.blocks),
  };
}

export class ChiefRuntime {
  private askAbort: AbortController | null = null;
  private readonly cosd = new CosdClient();

  constructor(
    readonly cos: CosRunner,
    readonly connection: CosdConnectionManager,
    private readonly onResources: (resources: Resource[]) => void,
  ) {}

  connectionSnapshot(): CosdConnectionSnapshot {
    return this.connection.snapshot();
  }

  private async daemonRequiredFailure(): Promise<Failure> {
    await this.connection.refresh();
    const snap = this.connection.snapshot();
    return fail("setup", snap.detail ?? "cosd is required but unavailable");
  }

  async ask(question: unknown, sessionId: unknown): Promise<AskResult> {
    const q = String(question ?? "").trim();
    const sid = sessionId ? String(sessionId) : null;
    if (!q) return fail("usage", "ask needs a question");

    const mode = daemonModeFromEnv();
    const ep = this.connection.getEndpoint();
    if (mode !== "disabled" && ep) {
      this.askAbort?.abort();
      this.askAbort = new AbortController();
      try {
        const body = await this.cosd.ask(ep, q, sid, this.askAbort.signal);
        return answerFromDaemon(body, this.onResources);
      } catch (e) {
        if (e instanceof CosdHttpError && e.kind === "usage" && e.message === "cancelled") {
          return fail("usage", "Request cancelled");
        }
        if (mode === "required") return this.daemonRequiredFailure();
        // fall through to standalone
      }
    } else if (mode === "required") {
      return this.daemonRequiredFailure();
    }

    return this.cos.ask(question, sessionId);
  }

  cancelAsk(): void {
    this.askAbort?.abort();
    this.askAbort = null;
  }

  async status(): Promise<StatusResult> {
    const mode = daemonModeFromEnv();
    const ep = this.connection.getEndpoint();
    const snap = this.connection.snapshot();

    if (mode !== "disabled" && ep) {
      try {
        const body = await this.cosd.status(ep);
        const base = toStatus(body);
        if (!base) return fail("internal", "Chief returned an unexpected response.");
        return {
          ...base,
          via_daemon: true,
          cosd_connection: snap.state,
          execution_mode: "daemon",
        };
      } catch {
        if (mode === "required") return this.daemonRequiredFailure();
      }
    } else if (mode === "required") {
      return this.daemonRequiredFailure();
    }

    const local = await this.cos.status();
    if (!local.ok) return local;
    return { ...local, via_daemon: false, cosd_connection: snap.state, execution_mode: "standalone" };
  }

  async listTasks(state?: string): Promise<{ ok: true; tasks: CosdTask[]; total: number; limit: number; offset: number } | Failure> {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Tasks require a running cosd");
    try {
      const { tasks, total, limit, offset } = await this.cosd.listTasks(ep, { state, limit: 100 });
      return { ok: true, tasks, total, limit, offset };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "task list failed");
    }
  }

  async getTask(taskId: string) {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Tasks require a running cosd");
    try {
      return { ok: true as const, task: await this.cosd.getTask(ep, taskId) };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "task fetch failed");
    }
  }

  async createTask(title: string, kind: string, idempotencyKey: string) {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Tasks require a running cosd");
    try {
      const { task, reused } = await this.cosd.createTask(ep, {
        kind,
        title,
        description: "",
        payload: {},
        priority: 0,
        idempotency_key: idempotencyKey,
        requested_by: "chief-desktop",
        source: "chief-app",
        data_class: "internal",
      });
      return { ok: true as const, task, reused };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "task create failed");
    }
  }

  async cancelTask(taskId: string) {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Tasks require a running cosd");
    try {
      return { ok: true as const, task: await this.cosd.cancelTask(ep, taskId) };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "cancel failed");
    }
  }

  async retryTask(taskId: string) {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Tasks require a running cosd");
    try {
      return { ok: true as const, task: await this.cosd.retryTask(ep, taskId) };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "retry failed");
    }
  }

  async taskHistory(taskId: string): Promise<{ ok: true; task_id: string; events: TaskHistoryEvent[] } | Failure> {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Tasks require a running cosd");
    try {
      const events = await this.cosd.taskHistory(ep, taskId);
      return { ok: true, task_id: taskId, events };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "history failed");
    }
  }

  async queueSnapshot(): Promise<{ ok: true; queue: QueueSnapshot } | Failure> {
    const ep = this.connection.getEndpoint();
    if (!ep) return fail("setup", "Queue requires a running cosd");
    try {
      return { ok: true, queue: await this.cosd.queue(ep) };
    } catch (e) {
      return fail("internal", e instanceof CosdHttpError ? e.message : "queue failed");
    }
  }

  // Non-daemon paths stay on cos CLI.
  history(sessionId: unknown) {
    return this.cos.history(sessionId);
  }
  brief() {
    return this.cos.brief();
  }
  home(cached: boolean) {
    return this.cos.home(cached);
  }
  configGet() {
    return this.cos.configGet();
  }
  configSet(key: unknown, value: unknown) {
    return this.cos.configSet(key, value);
  }
  warm() {
    return this.cos.warm();
  }
  stop() {
    return this.cos.stop();
  }
  resume() {
    return this.cos.resume();
  }
  setAutoSearch(enabled: boolean) {
    return this.cos.setAutoSearch(enabled);
  }
}
