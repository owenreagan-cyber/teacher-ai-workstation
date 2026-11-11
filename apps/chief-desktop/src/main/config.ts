// Desktop settings (desktop.json, written by Owen) and remembered window state (written by the app).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const COS_STATE_DIR = path.join(os.homedir(), "Library", "Application Support", "ChiefOfStaff");
export const DESKTOP_CONFIG_PATH = path.join(COS_STATE_DIR, "desktop.json");
export const DEFAULT_COS_PATH = "~/Projects/teacher-ai-workstation/bin/cos"; // the main checkout since MERGE-1
export const DEFAULT_HOTKEY = "Control+Alt+C"; // Control+Option+C

export type DesktopConfig = {
  cosPath: string;
  hotkey: string;
  error: string | null;
  /** "packaged" when the immutable runtime ships inside the app bundle. */
  runtimeSource?: "packaged" | "development";
  /** Set when a packaged build cannot use its bundled runtime. Calls fail closed. */
  runtimeError?: string | null;
};

/** True when Electron is running from an installed bundle, not a source checkout. */
export function isPackagedResources(resourcesPath?: string): boolean {
  return typeof resourcesPath === "string" && /\.app\/Contents\/Resources\/?$/.test(resourcesPath);
}

export type PackagedRuntime = { path: string | null; error: string | null };

/**
 * Validate the bundled runtime. A packaged build must never silently degrade to
 * the development checkout, so a missing or malformed runtime is an error.
 */
export function resolvePackagedRuntime(resourcesPath?: string): PackagedRuntime {
  if (!resourcesPath) return { path: null, error: "no application resources directory" };
  const root = path.join(resourcesPath, "runtime");
  const cos = path.join(root, "cos");
  const cosd = path.join(root, "cosd");
  const manifest = path.join(root, "manifest.json");
  for (const [label, target] of [["cos launcher", cos], ["cosd launcher", cosd]] as const) {
    if (!fs.existsSync(target)) return { path: null, error: `packaged runtime is incomplete: ${label} is missing` };
  }
  for (const module of ["cos", "cosd"]) {
    const init = path.join(root, "py", module, "__init__.py");
    if (!fs.existsSync(init)) {
      return { path: null, error: `packaged runtime is incomplete: ${module} sources are missing` };
    }
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(fs.readFileSync(manifest, "utf-8"));
  } catch {
    return { path: null, error: "packaged runtime manifest is missing or unreadable" };
  }
  const m = parsed as { format?: unknown; runtime?: { version?: unknown }; source?: { commit?: unknown }; artifacts?: { cos?: { sha256?: unknown }; cosd?: { sha256?: unknown } } };
  const valid =
    m?.format === 1 &&
    typeof m.runtime?.version === "string" &&
    typeof m.source?.commit === "string" &&
    typeof m.artifacts?.cos?.sha256 === "string" &&
    typeof m.artifacts?.cosd?.sha256 === "string";
  if (!valid) return { path: null, error: "packaged runtime manifest is invalid" };
  return { path: cos, error: null };
}

/** The runtime staged into Resources/runtime by scripts/stage-runtime.mjs. */
export function packagedRuntimePath(resourcesPath?: string): string | null {
  if (!resourcesPath) return null;
  const candidate = path.join(resourcesPath, "runtime", "cos");
  try {
    return fs.existsSync(candidate) ? candidate : null;
  } catch {
    return null;
  }
}

export function runtimeResourcesPath(): string | undefined {
  return (process as unknown as { resourcesPath?: string }).resourcesPath;
}

/** A leading "~" or "~/" becomes the home folder; "~user/..." is not expanded (and is then refused). */
export function expandHome(p: string): string {
  return p === "~" ? os.homedir() : p.startsWith("~/") ? path.join(os.homedir(), p.slice(2)) : p;
}

export function loadDesktopConfig(file = DESKTOP_CONFIG_PATH, resourcesPath = runtimeResourcesPath()): DesktopConfig {
  // Inside an installed bundle the bundled runtime is authoritative. If it is
  // missing or malformed the build fails closed: it never falls back to the
  // development checkout.
  const packagedBuild = isPackagedResources(resourcesPath);
  const bundled = packagedBuild ? resolvePackagedRuntime(resourcesPath) : { path: null, error: null };
  const config: DesktopConfig = {
    cosPath:
      bundled.path ?? (packagedBuild ? path.join(resourcesPath as string, "runtime", "cos") : expandHome(DEFAULT_COS_PATH)),
    hotkey: DEFAULT_HOTKEY,
    error: bundled.error && packagedBuild ? `Chief cannot start: ${bundled.error}. Reinstall Chief.app.` : null,
    runtimeSource: packagedBuild ? "packaged" : "development",
    runtimeError: bundled.error,
  };
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
    // In a packaged build the runtime is authoritative; only allow an
    // override when there is no bundled runtime.
    if (config.runtimeSource !== "packaged") config.cosPath = expandHome(obj.cosPath);
  }
  if (obj.hotkey !== undefined) {
    if (typeof obj.hotkey !== "string" || !obj.hotkey.trim()) {
      return { ...config, error: `hotkey in ${file} must be a non-empty string` };
    }
    config.hotkey = obj.hotkey.trim();
  }
  return config;
}

// The full window (UI-1): rail, page, and chat. A size remembered from the old compact window
// (narrower than MIN_SIZE) starts at DEFAULT_SIZE instead of being stretched to the minimum.
export const MIN_SIZE = { width: 760, height: 560 };
export const MAX_SIZE = { width: 3840, height: 2400 };
export const DEFAULT_SIZE = { width: 1320, height: 860 };

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
      width: isNum(d.width) && d.width >= MIN_SIZE.width ? clamp(Math.round(d.width), MIN_SIZE.width, MAX_SIZE.width) : DEFAULT_SIZE.width,
      height: isNum(d.height) && d.height >= MIN_SIZE.height ? clamp(Math.round(d.height), MIN_SIZE.height, MAX_SIZE.height) : DEFAULT_SIZE.height,
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
