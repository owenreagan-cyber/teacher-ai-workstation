import fs from "node:fs";
import path from "node:path";

import type { App } from "electron";

import { DEFAULT_OPS_PREFS, type OpsPrefs } from "../shared/ops-prefs.js";

export type { OpsPrefs };
export { DEFAULT_OPS_PREFS };

export function opsPrefsPath(getPath: App["getPath"]): string {
  return path.join(getPath("userData"), "ops-prefs.json");
}

export function loadOpsPrefs(getPath: App["getPath"]): OpsPrefs {
  try {
    const raw = JSON.parse(fs.readFileSync(opsPrefsPath(getPath), "utf-8")) as Partial<OpsPrefs>;
    return { ...DEFAULT_OPS_PREFS, ...raw };
  } catch {
    return { ...DEFAULT_OPS_PREFS };
  }
}

export function saveOpsPrefs(getPath: App["getPath"], prefs: OpsPrefs): void {
  const file = opsPrefsPath(getPath);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(prefs, null, 2), { mode: 0o600 });
}
