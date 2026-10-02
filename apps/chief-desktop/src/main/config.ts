// Desktop settings (desktop.json, written by Owen) and remembered window state (written by the app).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const COS_STATE_DIR = path.join(os.homedir(), "Library", "Application Support", "ChiefOfStaff");
export const DESKTOP_CONFIG_PATH = path.join(COS_STATE_DIR, "desktop.json");
export const DEFAULT_COS_PATH = "~/Projects/taw-cos-m1/bin/cos";
export const DEFAULT_HOTKEY = "Control+Alt+C"; // Control+Option+C

export type DesktopConfig = { cosPath: string; hotkey: string; error: string | null };

function expandHome(p: string): string {
  return p === "~" ? os.homedir() : p.startsWith("~/") ? path.join(os.homedir(), p.slice(2)) : p;
}

export function loadDesktopConfig(file = DESKTOP_CONFIG_PATH): DesktopConfig {
  const config: DesktopConfig = { cosPath: expandHome(DEFAULT_COS_PATH), hotkey: DEFAULT_HOTKEY, error: null };
  let raw: string;
  try {
    raw = fs.readFileSync(file, "utf-8");
  } catch {
    return config; // no desktop.json: defaults
  }
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return { ...config, error: `${file} is not valid JSON` };
  }
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    return { ...config, error: `${file} must be a JSON object` };
  }
  const obj = data as Record<string, unknown>;
  if (obj.cosPath !== undefined) {
    if (typeof obj.cosPath !== "string" || !path.isAbsolute(expandHome(obj.cosPath))) {
      return { ...config, error: `cosPath in ${file} must be an absolute path (or start with ~/)` };
    }
    config.cosPath = expandHome(obj.cosPath);
  }
  if (obj.hotkey !== undefined) {
    if (typeof obj.hotkey !== "string" || !obj.hotkey.trim()) {
      return { ...config, error: `hotkey in ${file} must be a non-empty string` };
    }
    config.hotkey = obj.hotkey.trim();
  }
  return config;
}

export const MIN_SIZE = { width: 340, height: 420 };
export const MAX_SIZE = { width: 520, height: 900 };
export const DEFAULT_SIZE = { width: 380, height: 540 };

export type SavedWindow = {
  x?: number;
  y?: number;
  width: number;
  height: number;
  pinned: boolean;
  protected: boolean; // remembered, but every launch starts protected regardless
};

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

export function loadWindowState(file: string): SavedWindow {
  const fallback: SavedWindow = { ...DEFAULT_SIZE, pinned: false, protected: true };
  try {
    const d = JSON.parse(fs.readFileSync(file, "utf-8")) as Record<string, unknown>;
    return {
      x: isNum(d.x) ? Math.round(d.x) : undefined,
      y: isNum(d.y) ? Math.round(d.y) : undefined,
      width: isNum(d.width) ? clamp(Math.round(d.width), MIN_SIZE.width, MAX_SIZE.width) : DEFAULT_SIZE.width,
      height: isNum(d.height) ? clamp(Math.round(d.height), MIN_SIZE.height, MAX_SIZE.height) : DEFAULT_SIZE.height,
      pinned: d.pinned === true,
      protected: d.protected !== false,
    };
  } catch {
    return fallback;
  }
}

// App preferences (written by the app). startAtLogin is null until the first run has set it.
export type Prefs = { startAtLogin: boolean | null };

export function loadPrefs(file: string): Prefs {
  try {
    const d = JSON.parse(fs.readFileSync(file, "utf-8")) as Record<string, unknown>;
    return { startAtLogin: typeof d.startAtLogin === "boolean" ? d.startAtLogin : null };
  } catch {
    return { startAtLogin: null };
  }
}

export function savePrefs(file: string, prefs: Prefs): void {
  writePrivateJson(file, prefs);
}

function writePrivateJson(file: string, value: unknown): void {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
    const tmp = `${file}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(value), { mode: 0o600 });
    fs.renameSync(tmp, file);
  } catch {
    // Losing a preference or window geometry is harmless; never crash over it.
  }
}

export function saveWindowState(file: string, state: SavedWindow): void {
  writePrivateJson(file, state);
}
