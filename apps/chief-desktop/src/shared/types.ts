// Shapes of what cos prints (cos ask/history/status/brief --json) plus the few envelopes the
// main process adds. The renderer displays these; it never invents their values.
import type { Block } from "./blocks.js";

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
  // Rich answer (docs/response-blocks.md). Empty for old turns. Never holds a URL: sources carry
  // link ids, and the URLs stay in the main process's resource table.
  blocks: Block[];
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
      blocks: Block[];
    }
  | Failure;

// openLink: the main process looked the link id up in its resource table and opened it (or not).
export type OpenLinkResult = { ok: true } | Failure;

export type HistoryResult = { ok: true; turns: Turn[] } | Failure;

// The home card (cos brief --json "card"): deterministic, built by cos from the same tool results.
// Each part has a status and display text; "unavailable" text never carries the underlying error.
export type CardStatus = "ok" | "empty" | "unavailable";
export type HomeCard = {
  greeting: string;
  date: string;
  date_iso: string;
  calendar: { status: CardStatus; text: string; count: number; next: { title: string; start: string | null } | null };
  reminders: { status: CardStatus; text: string; due: number; overdue: number };
  weather: { status: CardStatus; text: string };
};

// card is null when cos sent none or it failed validation; the brief lines still show.
export type BriefResult = { ok: true; lines: string[]; card: HomeCard | null } | Failure;

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
      auto_search: boolean;
    }
  | Failure;

// cos auto-search on|off --json. Main process only (the tray toggle); no bridge.
export type AutoSearchResult = { ok: true; auto_search: boolean } | Failure;

// cos warm --json. Main process only (app launch, window shown after a long hide); no bridge.
export type WarmResult = { ok: true; model: string; loaded: boolean; keep_alive: string } | Failure;

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
  openLink(linkId: string): Promise<OpenLinkResult>;
  brief(): Promise<BriefResult>;
  status(): Promise<StatusResult>;
  stop(): Promise<ControlResult>;
  resume(): Promise<ControlResult>;
  setPin(pinned: boolean): Promise<WindowState>;
  setProtection(enabled: boolean): Promise<WindowState>;
  hide(): Promise<void>;
  onEvent(listener: (event: ShellEvent) => void): () => void;
}
