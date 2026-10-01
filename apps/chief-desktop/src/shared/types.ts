// Shapes of what cos prints (cos ask/history/status/brief --json) plus the few envelopes the
// main process adds. The renderer displays these; it never invents their values.

export type CosErrorKind = "usage" | "stopped" | "model_unavailable" | "internal";
// Kinds the desktop shell itself can report before or around a cos call.
export type ShellErrorKind = "setup" | "timeout";
export type ErrorKind = CosErrorKind | ShellErrorKind;

export type Failure = { ok: false; error: string; error_kind: ErrorKind };

export type Turn = {
  ts: string;
  question: string;
  answer: string;
  tools_used: string[];
  fast_path: boolean;
  model: string | null;
  notices: string[];
  total_ms: number;
};

export type AskResult =
  | {
      ok: true;
      answer: string;
      tools_used: string[];
      model: string | null;
      notices: string[];
      fast_path: boolean;
      session_id: string | null;
      ts: string;
      total_ms: number;
    }
  | Failure;

export type HistoryResult = { ok: true; turns: Turn[] } | Failure;

export type BriefResult = { ok: true; lines: string[] } | Failure;

export type StatusResult =
  | {
      ok: true;
      kill_switch: boolean;
      kill_switch_reason: string | null;
      model: string;
      fallback_model: string | null;
      ollama_reachable: boolean;
      loaded_models: string[];
      audit: "ok" | "empty" | "fail";
      version: string;
    }
  | Failure;

// cos stop / resume print text, not JSON: success is exit code 0. The UI then re-reads status.
export type ControlResult = { ok: true } | Failure;

// Window state owned by the Electron main process (not cos state).
export type WindowState = { pinned: boolean; protected: boolean };

// One-way notices from the main process (tray menu actions). Fixed set; no payload from cos.
export type ShellEvent =
  | { kind: "brief-requested" }
  | { kind: "status-changed" }
  | { kind: "window-state"; state: WindowState };

export interface ChiefBridge {
  ask(question: string, sessionId: string): Promise<AskResult>;
  history(sessionId: string): Promise<HistoryResult>;
  brief(): Promise<BriefResult>;
  status(): Promise<StatusResult>;
  stop(): Promise<ControlResult>;
  resume(): Promise<ControlResult>;
  setPin(pinned: boolean): Promise<WindowState>;
  setProtection(enabled: boolean): Promise<WindowState>;
  hide(): Promise<void>;
  onEvent(listener: (event: ShellEvent) => void): () => void;
}
