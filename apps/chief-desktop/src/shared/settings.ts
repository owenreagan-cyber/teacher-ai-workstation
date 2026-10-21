// Settings: what `cos config get|set --json` returns, validated field by field, plus the helpers the
// Settings screen uses to build a new places object. Pure (no Electron, no DOM, no I/O). cos validates
// every write against the config schema; nothing here decides what is allowed.

export const SETTABLE_KEYS = ["places", "auto_search", "model", "model_keep_alive"] as const;
export type SettableKey = (typeof SETTABLE_KEYS)[number];
export const KEEP_ALIVE_CHOICES = ["0", "30m", "1h", "2h", "4h", "8h"] as const;

export type PlaceValue = { name: string; latitude: number; longitude: number };
export type ConfigValues = {
  places: Record<string, PlaceValue>;
  auto_search: boolean;
  model: string;
  fallback_model: string | null;
  model_keep_alive: string;
  search_daily_limit: number;
  search_monthly_limit: number;
};
export type ConfigReport = { path: string; values: ConfigValues };

const PLACE_KEY_RE = /^[a-z][a-z0-9_]{0,19}$/; // must match cos/config.py PLACE_KEY_RE
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const isCount = (v: unknown): v is number => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const shortStr = (v: unknown, max: number): v is string => typeof v === "string" && v.length <= max;

function place(v: unknown): PlaceValue | null {
  if (!isObj(v) || !shortStr(v.name, 60) || !isNum(v.latitude) || !isNum(v.longitude)) return null;
  if (Math.abs(v.latitude) > 90 || Math.abs(v.longitude) > 180) return null;
  return { name: v.name, latitude: v.latitude, longitude: v.longitude };
}

/** The report with exactly the known fields, or null. */
export function toConfigReport(v: unknown): ConfigReport | null {
  if (!isObj(v) || !shortStr(v.path, 500) || !isObj(v.values)) return null;
  const o = v.values;
  if (!isObj(o.places) || Object.keys(o.places).length > 10) return null;
  const places: Record<string, PlaceValue> = {};
  for (const [key, value] of Object.entries(o.places)) {
    const p = place(value);
    if (!PLACE_KEY_RE.test(key) || p === null) return null;
    places[key] = p;
  }
  if (typeof o.auto_search !== "boolean" || !shortStr(o.model, 100) || !shortStr(o.model_keep_alive, 20)) return null;
  if (!(o.fallback_model === null || shortStr(o.fallback_model, 100))) return null;
  if (!isCount(o.search_daily_limit) || !isCount(o.search_monthly_limit)) return null;
  return {
    path: v.path,
    values: {
      places, auto_search: o.auto_search, model: o.model, fallback_model: o.fallback_model,
      model_keep_alive: o.model_keep_alive, search_daily_limit: o.search_daily_limit, search_monthly_limit: o.search_monthly_limit,
    },
  };
}

/** A key for a new place from its name: "Raleigh, NC" -> "raleigh_nc" (unique among existing keys). */
export function placeKey(name: string, existing: string[]): string {
  let base = name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").replace(/^[^a-z]+/, "");
  base = (base || "place").slice(0, 17);
  let key = base;
  for (let i = 2; existing.includes(key); i++) key = `${base}_${i}`.slice(0, 20);
  return key;
}

export type PlaceDraft = { name: string; latitude: string; longitude: string };

/** A place from typed text, or an error to show. cos checks it again before anything is written. */
export function parsePlace(draft: PlaceDraft): PlaceValue | string {
  const name = draft.name.trim();
  if (!name) return "Type a name for the place.";
  if (name.length > 60) return "The name can be at most 60 characters.";
  const latitude = Number(draft.latitude.trim());
  const longitude = Number(draft.longitude.trim());
  if (!draft.latitude.trim() || !Number.isFinite(latitude) || Math.abs(latitude) > 90) return "Latitude must be a number from -90 to 90.";
  if (!draft.longitude.trim() || !Number.isFinite(longitude) || Math.abs(longitude) > 180) return "Longitude must be a number from -180 to 180.";
  return { name, latitude, longitude };
}
