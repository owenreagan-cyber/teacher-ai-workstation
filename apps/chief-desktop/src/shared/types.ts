// Shapes of what cos prints (cos ask/history/status/brief --json) plus the few envelopes the
// main process adds. The renderer displays these; it never invents their values.
import type { Block } from "./blocks.js";
import type { CosdConnectionState, ExecutionMode } from "./cosd.js";
import type { OpsPrefs } from "./ops-prefs.js";
import type { HomeSnapshot } from "./home.js";
import type { ConfigReport } from "./settings.js";

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
      via_daemon?: boolean;
      cosd_connection?: CosdConnectionState;
      execution_mode?: ExecutionMode;
    }
  | Failure;

// cos home --json (src/shared/home.ts), plus the main process's in-memory Mac samples.
export type HomeResult = ({ ok: true } & HomeSnapshot) | Failure;

// cos config get|set --json (src/shared/settings.ts): what the Settings screen reads and writes.
export type ConfigResult = ({ ok: true } & ConfigReport) | Failure;

// cos auto-search on|off --json. Main process only (the tray toggle); no bridge.
export type AutoSearchResult = { ok: true; auto_search: boolean } | Failure;

// cos warm --json. Main process only (app launch, window shown after a long hide); no bridge.
export type WarmResult = { ok: true; model: string; loaded: boolean; keep_alive: string } | Failure;

// cos stop / resume print text, not JSON: success is exit code 0. The UI then re-reads status.
export type ControlResult = { ok: true } | Failure;

// Window state owned by the Electron main process (not cos state).
// startAtLogin and hotkey are shown in Settings for reading only: start at login changes from the menu
// bar icon (main process only), the hotkey in desktop.json.
export type WindowState = { pinned: boolean; protected: boolean; startAtLogin: boolean | null; hotkey: string };

// One-way notices from the main process (tray menu actions). Fixed set; no payload from cos.
export type ShellEvent =
  | { kind: "brief-requested" }
  | { kind: "status-changed" }
  | { kind: "cosd-connection"; snapshot: import("./cosd.js").CosdConnectionSnapshot }
  | { kind: "cosd-task-event"; event: { id: number; type: string; title?: string; task_id?: string } }
  | { kind: "ask-chunk"; text: string }
  | { kind: "window-state"; state: WindowState };

export interface ChiefBridge {
  ask(question: string, sessionId: string): Promise<AskResult>;
  history(sessionId: string): Promise<HistoryResult>;
  openLink(linkId: string): Promise<OpenLinkResult>;
  brief(): Promise<BriefResult>;
  home(cached: boolean): Promise<HomeResult>;
  configGet(): Promise<ConfigResult>;
  configSet(key: string, value: unknown): Promise<ConfigResult>;
  status(): Promise<StatusResult>;
  stop(): Promise<ControlResult>;
  resume(): Promise<ControlResult>;
  setPin(pinned: boolean): Promise<WindowState>;
  setProtection(enabled: boolean): Promise<WindowState>;
  hide(): Promise<void>;
  cosdConnection(): Promise<import("./cosd.js").CosdConnectionResult>;
  cosdReconnect(): Promise<import("./cosd.js").CosdConnectionResult>;
  cancelAsk(): Promise<void>;
  listTasks(state?: string): Promise<import("./cosd.js").TaskListResult>;
  getTask(taskId: string): Promise<import("./cosd.js").TaskDetailResult>;
  createTask(title: string, kind: string, idempotencyKey: string): Promise<import("./cosd.js").TaskDetailResult & { reused?: boolean }>;
  cancelTask(taskId: string): Promise<import("./cosd.js").TaskDetailResult>;
  retryTask(taskId: string): Promise<import("./cosd.js").TaskDetailResult>;
  taskHistory(taskId: string): Promise<import("./cosd.js").TaskHistoryResult>;
  queueSnapshot(): Promise<import("./cosd.js").QueueResult>;
  devScanRoots(): Promise<import("./devscan.js").DevScanRootsResult>;
  devScanAddRoot(): Promise<import("./devscan.js").DevScanRootsResult>;
  devScanRemoveRoot(rootPath: string): Promise<import("./devscan.js").DevScanRootsResult>;
  devScanRun(includeProcesses: boolean): Promise<import("./devscan.js").DevScanRunResult>;
  devScanExecute(taskId: string): Promise<import("./devscan.js").DevScanRunResult>;
  devScanReport(taskId: string): Promise<import("./devscan.js").DevScanRunResult>;
  listDevices(filter?: { status?: string; profile?: string }): Promise<import("./devices.js").DeviceListResult>;
  getDevice(deviceId: string): Promise<import("./devices.js").DeviceDetailResult>;
  createDevice(input: import("./devices.js").DeviceCreateInput): Promise<import("./devices.js").DeviceDetailResult>;
  updateDevice(deviceId: string, patch: import("./devices.js").DevicePatchInput): Promise<import("./devices.js").DeviceDetailResult>;
  disableDevice(deviceId: string, confirm: boolean): Promise<import("./devices.js").DeviceDetailResult>;
  enableDevice(deviceId: string, confirm: boolean): Promise<import("./devices.js").DeviceDetailResult>;
  revokeDevice(deviceId: string, confirm: boolean): Promise<import("./devices.js").DeviceDetailResult>;
  removeDevice(deviceId: string, confirm: boolean): Promise<{ ok: true } | Failure>;
  bootstrapDevice(displayName: string, confirm: boolean): Promise<import("./devices.js").DeviceDetailResult & { created?: boolean }>;
  deviceCredentials(deviceId: string): Promise<import("./devices.js").DeviceCredentialsResult>;
  rotateDeviceCredential(deviceId: string, confirm: boolean): Promise<{ ok: true; credential: import("./devices.js").CredentialMetadata } | Failure>;
  revokeDeviceCredential(deviceId: string, confirm: boolean): Promise<{ ok: true } | Failure>;
  createEnrollmentInvitation(input: import("./devices.js").EnrollmentCreateInput): Promise<import("./devices.js").EnrollmentInvitationResult>;
  listPendingEnrollments(): Promise<import("./devices.js").EnrollmentListResult>;
  getEnrollment(enrollmentId: string): Promise<import("./devices.js").EnrollmentDetailResult>;
  approveEnrollment(enrollmentId: string, input: import("./devices.js").EnrollmentApproveInput, confirm: boolean): Promise<import("./devices.js").EnrollmentActionResult>;
  rejectEnrollment(enrollmentId: string, confirm: boolean): Promise<import("./devices.js").EnrollmentActionResult>;
  cancelEnrollment(enrollmentId: string, confirm: boolean): Promise<import("./devices.js").EnrollmentActionResult>;
  cosdStart(): Promise<{ ok: boolean; error?: string }>;
  cosdStop(confirm: boolean): Promise<{ ok: boolean; error?: string }>;
  cosdRestart(confirm: boolean): Promise<{ ok: boolean; error?: string }>;
  runtimeSnapshot(): Promise<{ ok: true; body: Record<string, unknown> } | { ok: false; error: string }>;
  opsPrefsGet(): Promise<{ ok: true; prefs: OpsPrefs }>;
  opsPrefsSet(prefs: OpsPrefs): Promise<{ ok: true }>;
  onEvent(listener: (event: ShellEvent) => void): () => void;
}
