// cosd task and connection shapes (validated in the main process before reaching the renderer).

export type CosdConnectionState =
  | "DISCONNECTED"
  | "CONNECTING"
  | "CONNECTED"
  | "DEGRADED"
  | "AUTH_ERROR"
  | "VERSION_MISMATCH"
  | "RECOVERING";

export type ExecutionMode = "daemon" | "standalone";

export type TaskState =
  | "QUEUED"
  | "CLAIMED"
  | "RUNNING"
  | "BLOCKED"
  | "FAILED"
  | "COMPLETED"
  | "CANCELLED";

export type CosdTask = {
  id: string;
  kind: string;
  title: string;
  state: TaskState;
  priority: number;
  created_at: string;
  updated_at: string;
  attempt_count: number;
  blocked_reason: string | null;
  last_error: string | null;
  next_retry_at: string | null;
};

export type TaskListResult =
  | { ok: true; tasks: CosdTask[]; total: number; limit: number; offset: number }
  | { ok: false; error: string; error_kind: string };

export type TaskDetailResult = { ok: true; task: CosdTask } | { ok: false; error: string; error_kind: string };

export type TaskHistoryEvent = { ts: string; event: string; detail?: Record<string, unknown> };

export type TaskHistoryResult =
  | { ok: true; task_id: string; events: TaskHistoryEvent[] }
  | { ok: false; error: string; error_kind: string };

export type QueueSnapshot = {
  paused: boolean;
  task_counts: Record<string, number>;
  active_leases: unknown[];
};

export type QueueResult = { ok: true; queue: QueueSnapshot } | { ok: false; error: string; error_kind: string };

export type CosdHealth = {
  ok: boolean;
  service?: string;
  version?: string;
};

export type CosdConnectionSnapshot = {
  state: CosdConnectionState;
  execution_mode: ExecutionMode;
  detail: string | null;
  daemon_version: string | null;
};

export type CosdConnectionResult = { ok: true; snapshot: CosdConnectionSnapshot } | { ok: false; error: string; error_kind: string };
