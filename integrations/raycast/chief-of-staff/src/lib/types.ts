export type CosdConnectionState =
  | "DISCONNECTED"
  | "CONNECTING"
  | "CONNECTED"
  | "DEGRADED"
  | "AUTH_ERROR"
  | "VERSION_MISMATCH"
  | "RECOVERING";

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

export type ConnectionSnapshot = {
  state: CosdConnectionState;
  detail: string | null;
  daemon_version: string | null;
  host: string | null;
  port: number | null;
};

export type AskSuccess = {
  ok: true;
  text?: string;
  answer?: string;
  tools_used?: string[];
  model?: string | null;
  notices?: string[];
  session_id?: string | null;
  fast_path?: boolean;
};

export type ApiError = { ok: false; error: string; error_kind?: string };
