// Response blocks (docs/response-blocks.md): validated from `cos ask --json` / `cos history --json`
// and rebuilt field by field. Pure (no Electron, no DOM, no I/O) so the main process, the renderer,
// and tests share it. cos decides every value; this file only checks shapes.
//
// URLs never reach the renderer: a source carries a link_id, and the URL it stands for stays in the
// main process's resource table. A block with any string that looks like a URL is dropped.

export type WeatherNowBlock = {
  type: "weather_now";
  place: string;
  temp_f: number | null;
  feels_like_f: number | null;
  conditions: string;
  is_day: boolean | null;
  high_f: number | null;
  low_f: number | null;
  rain_chance_pct: number | null;
  wind_mph: number | null;
  as_of: string | null;
};
export type HourlyPoint = { time: string; temp_f: number | null; rain_chance_pct: number | null; conditions: string; is_day: boolean | null };
export type DailyPoint = { date: string; label: string; high_f: number | null; low_f: number | null; rain_chance_pct: number | null; conditions: string };
export type SourceItem = { title: string; site: string; link_id: string | null };
export type Suggestion = { label: string; message: string };

export type Block =
  | { type: "text"; text: string }
  | WeatherNowBlock
  | { type: "forecast_hourly"; place: string; points: HourlyPoint[] }
  | { type: "forecast_daily"; place: string; days: DailyPoint[] }
  | { type: "sources"; items: SourceItem[] }
  | { type: "searched"; query: string }
  | { type: "suggestions"; items: Suggestion[] }
  | { type: "notice"; level: "info" | "warning"; text: string };

export type BlockType = Block["type"];
export const BLOCK_TYPES: readonly BlockType[] = [
  "text", "weather_now", "forecast_hourly", "forecast_daily", "sources", "searched", "suggestions", "notice",
];

// One resource: a URL from a tool result, known to the main process by its link id.
export type Resource = { id: string; url: string };

export const LINK_ID_RE = /^lnk-[0-9a-f]{16}$/;
export const MAX_BLOCKS = 12;
export const MAX_RESOURCES = 20;
const MAX_TEXT = 4000;
const MAX_SHORT = 200;
const URL_LIKE = /\b(?:https?|file|javascript):|\bwww\.[a-z0-9-]+\./i;

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);

function str(v: unknown, max = MAX_SHORT, allowEmpty = false): string | null {
  if (typeof v !== "string" || v.length > max || (!allowEmpty && !v.trim()) || URL_LIKE.test(v)) return null;
  return v;
}

const BAD = Symbol("bad");
type Maybe<T> = T | typeof BAD;

function optStr(v: unknown): Maybe<string | null> {
  return v === null ? null : (str(v) ?? BAD);
}

function int(v: unknown, lo: number, hi: number): Maybe<number | null> {
  if (v === null) return null;
  return typeof v === "number" && Number.isSafeInteger(v) && v >= lo && v <= hi ? v : BAD;
}

const temp = (v: unknown) => int(v, -100, 150);
const pct = (v: unknown) => int(v, 0, 100);

function optBool(v: unknown): Maybe<boolean | null> {
  return v === null || typeof v === "boolean" ? v : BAD;
}

function list<T>(v: unknown, min: number, max: number, item: (x: unknown) => T | null): T[] | null {
  if (!Array.isArray(v) || v.length < min || v.length > max) return null;
  const out: T[] = [];
  for (const x of v) {
    const ok = item(x);
    if (ok === null) return null;
    out.push(ok);
  }
  return out;
}

function anyBad(values: unknown[]): boolean {
  return values.some((v) => v === BAD);
}

function hourly(x: unknown): HourlyPoint | null {
  if (!isObj(x)) return null;
  const time = str(x.time, 20);
  const t = temp(x.temp_f), r = pct(x.rain_chance_pct), d = optBool(x.is_day);
  const conditions = str(x.conditions, 60);
  if (time === null || conditions === null || anyBad([t, r, d])) return null;
  return { time, temp_f: t as number | null, rain_chance_pct: r as number | null, conditions, is_day: d as boolean | null };
}

function daily(x: unknown): DailyPoint | null {
  if (!isObj(x)) return null;
  const date = typeof x.date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(x.date) ? x.date : null;
  const label = str(x.label, 20), conditions = str(x.conditions, 60);
  const hi = temp(x.high_f), lo = temp(x.low_f), r = pct(x.rain_chance_pct);
  if (date === null || label === null || conditions === null || anyBad([hi, lo, r])) return null;
  return { date, label, high_f: hi as number | null, low_f: lo as number | null, rain_chance_pct: r as number | null, conditions };
}

function source(x: unknown): SourceItem | null {
  if (!isObj(x)) return null;
  const title = str(x.title), site = str(x.site, 100);
  const linkId = x.link_id === null ? null : typeof x.link_id === "string" && LINK_ID_RE.test(x.link_id) ? x.link_id : undefined;
  if (title === null || site === null || linkId === undefined) return null;
  return { title, site, link_id: linkId };
}

function suggestion(x: unknown): Suggestion | null {
  if (!isObj(x)) return null;
  const label = str(x.label, 60), message = str(x.message, 300);
  return label === null || message === null ? null : { label, message };
}

/** One block with exactly its known fields, or null (unknown type or any bad field). */
export function toBlock(value: unknown): Block | null {
  if (!isObj(value)) return null;
  switch (value.type) {
    case "text": {
      const text = str(value.text, MAX_TEXT);
      return text === null ? null : { type: "text", text };
    }
    case "weather_now": {
      const place = str(value.place, 100), conditions = str(value.conditions, 60);
      const fields = {
        temp_f: temp(value.temp_f), feels_like_f: temp(value.feels_like_f), is_day: optBool(value.is_day),
        high_f: temp(value.high_f), low_f: temp(value.low_f), rain_chance_pct: pct(value.rain_chance_pct),
        wind_mph: int(value.wind_mph, 0, 300), as_of: optStr(value.as_of),
      };
      if (place === null || conditions === null || anyBad(Object.values(fields))) return null;
      return { type: "weather_now", place, conditions, ...(fields as Omit<WeatherNowBlock, "type" | "place" | "conditions">) };
    }
    case "forecast_hourly": {
      const place = str(value.place, 100), points = list(value.points, 1, 24, hourly);
      return place === null || points === null ? null : { type: "forecast_hourly", place, points };
    }
    case "forecast_daily": {
      const place = str(value.place, 100), days = list(value.days, 1, 7, daily);
      return place === null || days === null ? null : { type: "forecast_daily", place, days };
    }
    case "sources": {
      const items = list(value.items, 1, 5, source);
      return items === null ? null : { type: "sources", items };
    }
    case "searched": {
      const query = str(value.query, 200);
      return query === null ? null : { type: "searched", query };
    }
    case "suggestions": {
      const items = list(value.items, 2, 4, suggestion);
      return items === null ? null : { type: "suggestions", items };
    }
    case "notice": {
      const text = str(value.text, 500);
      const level = value.level === "info" || value.level === "warning" ? value.level : null;
      return text === null || level === null ? null : { type: "notice", level, text };
    }
    default:
      return null; // unknown type
  }
}

/** Valid blocks in order; a bad or unknown block is dropped, never blanking the rest. */
export function toBlocks(value: unknown): Block[] {
  if (!Array.isArray(value)) return [];
  return value.slice(0, MAX_BLOCKS).map(toBlock).filter((b): b is Block => b !== null);
}

/** Resources with a well-formed link id and an https URL; anything else is dropped. */
export function toResources(value: unknown): Resource[] {
  if (!Array.isArray(value)) return [];
  const out: Resource[] = [];
  for (const r of value.slice(0, MAX_RESOURCES)) {
    if (!isObj(r) || typeof r.id !== "string" || !LINK_ID_RE.test(r.id) || typeof r.url !== "string") continue;
    const url = httpsUrl(r.url);
    if (url !== null) out.push({ id: r.id, url });
  }
  return out;
}

/** The URL if it is a plain https URL (no credentials, no control characters), else null. */
export function httpsUrl(raw: string): string | null {
  if (raw.length > 2000 || /[\s\u0000-\u001f\u007f]/.test(raw)) return null;
  let u: URL;
  try {
    u = new URL(raw);
  } catch {
    return null;
  }
  if (u.protocol !== "https:" || !u.hostname || u.username || u.password) return null;
  return u.toString();
}

const ANY_URL = /\b(?:https?|file|javascript):\/*[^\s)\]>"']*|\bwww\.[a-z0-9-]+\.[^\s)\]>"']*/gi;

/** Text with every URL removed (the renderer never receives one). Tidies a dangling " — ". */
export function stripUrls(text: string): string {
  return text
    .replace(ANY_URL, "")
    .replace(/[ \t]+[—–-][ \t]*$/gm, "")
    .replace(/([^\s])[ \t]{2,}/g, "$1 ")
    .replace(/[ \t]+$/gm, "");
}

/** The message a suggestion button sends: its text only, exactly as cos wrote it. */
export function suggestionMessage(block: Block, index: number): string | null {
  if (block.type !== "suggestions") return null;
  return block.items[index]?.message ?? null;
}
