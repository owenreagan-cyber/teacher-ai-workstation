import type { IpcMainInvokeEvent } from "electron";

const TASK_ID_RE = /^[a-f0-9]{32}$/;
const MAX_ASK = 16_000;
const MAX_TITLE = 200;
const MAX_KIND = 80;
const MAX_IDEM = 120;

export function requireString(value: unknown, max: number, label: string): string {
  if (typeof value !== "string") throw new Error(`${label} must be a string`);
  const s = value.trim();
  if (!s || s.length > max) throw new Error(`${label} invalid`);
  return s;
}

export function validateAskInput(question: unknown, sessionId: unknown): { question: string; sessionId: string } {
  const q = requireString(question, MAX_ASK, "question");
  const sid = requireString(sessionId, 40, "sessionId");
  if (!/^[a-z0-9-]{1,40}$/.test(sid)) throw new Error("sessionId invalid");
  return { question: q, sessionId: sid };
}

export function validateTaskId(taskId: unknown): string {
  const id = requireString(taskId, 32, "taskId");
  if (!TASK_ID_RE.test(id)) throw new Error("taskId invalid");
  return id;
}

export function validateCreateTask(title: unknown, kind: unknown, idempotencyKey: unknown) {
  return {
    title: requireString(title, MAX_TITLE, "title"),
    kind: requireString(kind, MAX_KIND, "kind"),
    idempotencyKey: requireString(idempotencyKey, MAX_IDEM, "idempotencyKey"),
  };
}

export function validateOptionalState(state: unknown): string | undefined {
  if (state === undefined || state === null || state === "") return undefined;
  return requireString(state, 40, "state");
}

export function assertTrusted(trusted: (event: IpcMainInvokeEvent) => boolean, event: IpcMainInvokeEvent): void {
  if (!trusted(event)) throw new Error("untrusted sender");
}
