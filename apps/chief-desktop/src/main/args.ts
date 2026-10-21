// The only place cos argv is built. Pure: no I/O, no Electron, so it is unit-tested directly.
// Every value becomes one argv element for execFile (never a shell string).

export const SESSION_ID_RE = /^[a-z0-9-]{1,40}$/; // must match cos/sessions.py
export const MAX_QUESTION_CHARS = 4000;
export const STOP_REASON = "chief-desktop";

import { SETTABLE_KEYS } from "../shared/settings.js";

export type Action =
  | "ask" | "history" | "brief" | "status" | "stop" | "resume" | "warm" | "auto-search" | "home"
  | "config-get" | "config-set";

export type Params = { question?: unknown; sessionId?: unknown; enabled?: unknown; cached?: unknown; key?: unknown; value?: unknown };
export const MAX_CONFIG_VALUE_CHARS = 4000;

export class ArgsError extends Error {}

export function checkSessionId(sessionId: unknown): string {
  if (typeof sessionId !== "string" || !SESSION_ID_RE.test(sessionId)) {
    throw new ArgsError("session id must be 1-40 characters of a-z, 0-9, or '-'");
  }
  return sessionId;
}

export function checkQuestion(question: unknown): string {
  if (typeof question !== "string") throw new ArgsError("question must be text");
  const trimmed = question.trim();
  if (!trimmed) throw new ArgsError("question is empty");
  if (trimmed.length > MAX_QUESTION_CHARS) {
    throw new ArgsError(`question is longer than ${MAX_QUESTION_CHARS} characters`);
  }
  if (trimmed.includes("\0")) throw new ArgsError("question contains a NUL character");
  return trimmed;
}

export function checkConfigKey(key: unknown): string {
  if (typeof key !== "string" || !(SETTABLE_KEYS as readonly string[]).includes(key)) {
    throw new ArgsError(`setting ${String(key)} can't be changed from the window`);
  }
  return key;
}

function configValue(value: unknown): string {
  let text: string | undefined;
  try {
    text = JSON.stringify(value);
  } catch {
    text = undefined;
  }
  if (text === undefined) throw new ArgsError("setting value must be JSON");
  if (text.length > MAX_CONFIG_VALUE_CHARS) throw new ArgsError("setting value is too long");
  return text;
}

export function buildArgs(action: Action, params: Params = {}): string[] {
  switch (action) {
    case "ask":
      // "--" ends option parsing, so a question such as "--version" stays a question.
      return ["ask", "--session", checkSessionId(params.sessionId), "--json", "--", checkQuestion(params.question)];
    case "history":
      return ["history", "--session", checkSessionId(params.sessionId), "--json"];
    case "brief":
      return ["brief", "--json"];
    case "home":
      // --cached reads cos's cache only (the window paints at once); otherwise due sections refresh.
      return params.cached === true ? ["home", "--json", "--cached"] : ["home", "--json"];
    case "status":
      return ["status", "--json"];
    case "stop":
      return ["stop", STOP_REASON];
    case "resume":
      return ["resume"];
    case "warm":
      return ["warm", "--json"];
    case "auto-search":
      // Main process only (the tray toggle). Only a real boolean turns it on.
      return ["auto-search", params.enabled === true ? "on" : "off", "--json"];
    case "config-get":
      return ["config", "get", "--json"];
    case "config-set":
      // Only the keys the Settings screen may change; the value travels as one JSON argv element.
      return ["config", "set", "--json", "--", checkConfigKey(params.key), configValue(params.value)];
    default:
      throw new ArgsError(`unknown action: ${String(action)}`);
  }
}
