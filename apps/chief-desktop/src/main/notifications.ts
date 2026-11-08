import { Notification } from "electron";

import type { OpsPrefs } from "./ops-prefs.js";

const seen = new Map<string, number>();
const DEDUP_MS = 60_000;

function dedupKey(kind: string, taskId?: string) {
  return `${kind}:${taskId ?? ""}`;
}

export function shouldNotify(kind: string, taskId?: string): boolean {
  const key = dedupKey(kind, taskId);
  const now = Date.now();
  const prev = seen.get(key);
  if (prev !== undefined && now - prev < DEDUP_MS) return false;
  seen.set(key, now);
  return true;
}

export function notifyTaskEvent(
  prefs: OpsPrefs,
  eventType: string,
  opts: { title?: string; taskId?: string } = {},
): void {
  const { title, taskId } = opts;
  if (!Notification.isSupported()) return;
  const t = eventType.toLowerCase();
  if (t.includes("completed") && !prefs.notifyTaskCompleted) return;
  if (t.includes("failed") && !prefs.notifyTaskFailed) return;
  if (t.includes("blocked") && !prefs.notifyTaskBlocked) return;
  if (t.includes("recover") && !prefs.notifyRecovery) return;
  if (t.includes("daemon.") && !prefs.notifyDaemonConnection) return;
  if (!shouldNotify(eventType, taskId)) return;
  const body = title ? String(title).slice(0, 120) : "Chief of Staff";
  const n = new Notification({ title: "Chief", body: `${eventType}: ${body}` });
  n.show();
}

export function notifyDaemonConnection(prefs: OpsPrefs, message: string): void {
  if (!prefs.notifyDaemonConnection) return;
  if (!shouldNotify(`daemon:${message}`)) return;
  if (!Notification.isSupported()) return;
  const n = new Notification({ title: "Chief runtime", body: message });
  n.show();
}
