// The Today page snapshot (`cos home --json`): validated field by field, plus the freshness labels
// and the greeting the window shows. Pure (no Electron, no DOM, no I/O) so the main process, the
// renderer, and tests share it. cos decides every value; this file only checks shapes and lays out
// text. Text bound for the renderer has every URL removed (calendar titles can carry meeting links).
import { stripUrls } from "./blocks.js";

export type SectionStatus = "current" | "updating" | "stale" | "unavailable";
export type Section<T> = {
  status: SectionStatus;
  generated_at: string | null;
  interval_s: number;
  reason: string | null;
  data: T | null;
};

export type WeatherDay = {
  date: string;
  label: string;
  high_f: number | null;
  low_f: number | null;
  rain_chance_pct: number | null;
  conditions: string;
};
export type WeatherData = {
  place: string | null;
  temp_f: number | null;
  feels_like_f: number | null;
  conditions: string;
  is_day: boolean | null;
  high_f: number | null;
  low_f: number | null;
  rain_chance_pct: number | null;
  wind_mph: number | null;
  days: WeatherDay[];
};
export type CalendarEvent = {
  title: string;
  course: string | null;
  all_day: boolean;
  start: string | null;
  end: string | null;
};
export type CalendarData = { count: number; events: CalendarEvent[] };
export type ReminderItem = { title: string; due: string | null; overdue: boolean };
export type RemindersData = { count: number; overdue: number; line: string; items: ReminderItem[] };
export type MacData = {
  memory_free_pct: number | null;
  cpu_load_pct: number | null;
  disk_free_gb: number | null;
  disk_total_gb: number | null;
  battery_pct: number | null;
  battery_state: string | null;
  power_source: string | null;
  uptime: string | null;
  loaded_models: string[] | null;
  health: "healthy" | "attention";
  attention: string[];
};
export type BuildItem = { title: string; ref: string; pr: number | null; merged_at: string | null };
export type BuildsData = { branch: string; items: BuildItem[] };
export type AgentsData = { available: false; items: never[] };

export type NeedKind = "decision" | "suggestion" | "info";
// open_link: a link id from the main process's resource table (never a URL); page: a page of this
// window; command: a cos command shown for Owen to copy (the window never runs it).
export type NeedAction =
  | { type: "open_link"; label: string; link_id: string }
  | { type: "page"; label: string; page: string }
  | { type: "command"; label: string; command: string };
export type NeedItem = {
  id: string;
  kind: NeedKind;
  title: string;
  reason: string;
  source: string;
  created_at: string;
  action: NeedAction | null;
};
export type NeedsData = { items: NeedItem[] };

// Memory and CPU samples kept by the main process for trend lines (memory only, never on disk).
export type MacSample = { t: number; memory_free_pct: number | null; cpu_load_pct: number | null };

export type HomeSnapshot = {
  generated_at: string;
  greeting: string;
  date: string;
  place: string | null;
  stopped: boolean;
  weather: Section<WeatherData>;
  calendar: Section<CalendarData>;
  reminders: Section<RemindersData>;
  mac: Section<MacData>;
  needs: Section<NeedsData>;
  builds: Section<BuildsData>;
  agents: Section<AgentsData>;
  mac_history: MacSample[];
};

const MAX_TEXT = 300;
const STATUSES: SectionStatus[] = ["current", "updating", "stale", "unavailable"];
export const PAGES = ["today", "chat", "agents", "mac", "settings"] as const;
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown, max = MAX_TEXT): string | null => (typeof v === "string" && v.length <= max ? stripUrls(v) : null);
const optStr = (v: unknown, max = MAX_TEXT): string | null | undefined => (v === null || v === undefined ? null : (str(v, max) ?? undefined));
const int = (v: unknown, lo = -1e9, hi = 1e9): number | null =>
  typeof v === "number" && Number.isSafeInteger(v) && v >= lo && v <= hi ? v : null;
const optInt = (v: unknown, lo?: number, hi?: number): number | null | undefined =>
  v === null || v === undefined ? null : (int(v, lo, hi) ?? undefined);
const optBool = (v: unknown): boolean | null | undefined => (v === null || v === undefined ? null : typeof v === "boolean" ? v : undefined);

/** Every element valid, or null (the whole list is dropped). */
function list<T>(v: unknown, item: (x: unknown) => T | null, max: number): T[] | null {
  if (!Array.isArray(v) || v.length > max) return null;
  const out: T[] = [];
  for (const x of v) {
    const ok = item(x);
    if (ok === null) return null;
    out.push(ok);
  }
  return out;
}

const temp = (v: unknown) => optInt(v, -100, 150);
const pct = (v: unknown) => optInt(v, 0, 100);

function weatherDay(v: unknown): WeatherDay | null {
  if (!isObj(v)) return null;
  const date = typeof v.date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v.date) ? v.date : null;
  const label = str(v.label, 20), conditions = str(v.conditions, 60);
  const high = temp(v.high_f), low = temp(v.low_f), rain = pct(v.rain_chance_pct);
  if (date === null || label === null || conditions === null || high === undefined || low === undefined || rain === undefined) return null;
  return { date, label, high_f: high, low_f: low, rain_chance_pct: rain, conditions };
}

export function toWeather(v: unknown): WeatherData | null {
  if (!isObj(v)) return null;
  const place = optStr(v.place, 60), conditions = str(v.conditions, 60), isDay = optBool(v.is_day);
  const t = temp(v.temp_f), feels = temp(v.feels_like_f), high = temp(v.high_f), low = temp(v.low_f);
  const rain = pct(v.rain_chance_pct), wind = optInt(v.wind_mph, 0, 300), days = list(v.days, weatherDay, 7);
  if (place === undefined || conditions === null || isDay === undefined || days === null) return null;
  if ([t, feels, high, low, rain, wind].some((x) => x === undefined)) return null;
  return {
    place, temp_f: t!, feels_like_f: feels!, conditions, is_day: isDay, high_f: high!, low_f: low!,
    rain_chance_pct: rain!, wind_mph: wind!, days,
  };
}

function calendarEvent(v: unknown): CalendarEvent | null {
  if (!isObj(v) || typeof v.all_day !== "boolean") return null;
  const title = str(v.title, 120), course = optStr(v.course, 8), start = optStr(v.start, 20), end = optStr(v.end, 20);
  if (title === null || course === undefined || start === undefined || end === undefined) return null;
  return { title, course, all_day: v.all_day, start, end };
}

export function toCalendar(v: unknown): CalendarData | null {
  if (!isObj(v)) return null;
  const count = int(v.count, 0), events = list(v.events, calendarEvent, 50);
  return count === null || events === null ? null : { count, events };
}

function reminderItem(v: unknown): ReminderItem | null {
  if (!isObj(v) || typeof v.overdue !== "boolean") return null;
  const title = str(v.title, 120), due = optStr(v.due, 30);
  return title === null || due === undefined ? null : { title, due, overdue: v.overdue };
}

export function toReminders(v: unknown): RemindersData | null {
  if (!isObj(v)) return null;
  const count = int(v.count, 0), overdue = int(v.overdue, 0), line = str(v.line, 120), items = list(v.items, reminderItem, 20);
  return count === null || overdue === null || line === null || items === null ? null : { count, overdue, line, items };
}

export function toMac(v: unknown): MacData | null {
  if (!isObj(v)) return null;
  const nums = {
    memory_free_pct: pct(v.memory_free_pct),
    cpu_load_pct: optInt(v.cpu_load_pct, 0, 10_000),
    disk_free_gb: optInt(v.disk_free_gb, 0),
    disk_total_gb: optInt(v.disk_total_gb, 0),
    battery_pct: pct(v.battery_pct),
  };
  if (Object.values(nums).some((x) => x === undefined)) return null;
  const strs = { battery_state: optStr(v.battery_state, 40), power_source: optStr(v.power_source, 40), uptime: optStr(v.uptime, 20) };
  if (Object.values(strs).some((x) => x === undefined)) return null;
  const loaded = v.loaded_models === null || v.loaded_models === undefined ? null : list(v.loaded_models, (x) => str(x, 120), 10);
  if (loaded === null && v.loaded_models !== null && v.loaded_models !== undefined) return null;
  const attention = list(v.attention, (x) => str(x, 120), 10);
  if ((v.health !== "healthy" && v.health !== "attention") || attention === null) return null;
  return {
    memory_free_pct: nums.memory_free_pct!, cpu_load_pct: nums.cpu_load_pct!, disk_free_gb: nums.disk_free_gb!,
    disk_total_gb: nums.disk_total_gb!, battery_pct: nums.battery_pct!, battery_state: strs.battery_state!,
    power_source: strs.power_source!, uptime: strs.uptime!, loaded_models: loaded, health: v.health, attention,
  };
}

function buildItem(v: unknown): BuildItem | null {
  if (!isObj(v)) return null;
  const title = str(v.title, 120), ref = typeof v.ref === "string" && /^[0-9a-f]{4,12}$/.test(v.ref) ? v.ref : null;
  const pr = optInt(v.pr, 1), mergedAt = optStr(v.merged_at, 40);
  if (title === null || ref === null || pr === undefined || mergedAt === undefined) return null;
  return { title, ref, pr, merged_at: mergedAt };
}

export function toBuilds(v: unknown): BuildsData | null {
  if (!isObj(v)) return null;
  const branch = str(v.branch, 40), items = list(v.items, buildItem, 5);
  return branch === null || items === null ? null : { branch, items };
}

export function toAgents(v: unknown): AgentsData | null {
  // No agents exist in this build: only the empty, unavailable shape passes.
  return isObj(v) && v.available === false && Array.isArray(v.items) && v.items.length === 0 ? { available: false, items: [] } : null;
}

const NEED_KINDS: NeedKind[] = ["decision", "suggestion", "info"];

function needAction(v: unknown): NeedAction | null | undefined {
  if (v === null || v === undefined) return null;
  if (!isObj(v)) return undefined;
  const label = str(v.label, 40);
  if (label === null) return undefined;
  if (v.type === "open_link" && typeof v.link_id === "string" && /^lnk-[0-9a-f]{16}$/.test(v.link_id)) {
    return { type: "open_link", label, link_id: v.link_id };
  }
  if (v.type === "page" && PAGES.includes(v.page as (typeof PAGES)[number])) return { type: "page", label, page: v.page as string };
  if (v.type === "command") {
    const command = str(v.command, 200);
    return command === null ? undefined : { type: "command", label, command };
  }
  return undefined;
}

export function toNeedItem(v: unknown): NeedItem | null {
  if (!isObj(v)) return null;
  const id = typeof v.id === "string" && /^[a-z0-9_.:-]{1,80}$/.test(v.id) ? v.id : null;
  const kind = NEED_KINDS.find((k) => k === v.kind) ?? null;
  const title = str(v.title, 120), reason = str(v.reason, 300), source = str(v.source, 30), created = str(v.created_at, 40);
  const action = needAction(v.action);
  if (id === null || kind === null || title === null || reason === null || source === null || created === null) return null;
  return action === undefined ? null : { id, kind, title, reason, source, created_at: created, action };
}

export function toNeeds(v: unknown): NeedsData | null {
  if (!isObj(v) || !Array.isArray(v.items)) return null;
  // One bad item is dropped, never the whole list.
  return { items: v.items.slice(0, 50).map(toNeedItem).filter((x): x is NeedItem => x !== null) };
}

function section<T>(v: unknown, data: (x: unknown) => T | null): Section<T> | null {
  if (!isObj(v)) return null;
  const status = STATUSES.find((s) => s === v.status);
  const generated = optStr(v.generated_at, 40), interval = int(v.interval_s, 1, 86_400), reason = optStr(v.reason, MAX_TEXT);
  if (status === undefined || generated === undefined || interval === null || reason === undefined) return null;
  const d = v.data === null || v.data === undefined ? null : data(v.data);
  // Data that fails validation is not shown: the card says it is unavailable instead.
  if (d === null && v.data !== null && v.data !== undefined) {
    return { status: "unavailable", generated_at: generated, interval_s: interval, reason: "Chief returned data it couldn't show", data: null };
  }
  return { status, generated_at: generated, interval_s: interval, reason, data: d };
}

/** The snapshot with exactly the known fields and correct types, or null. mac_history is added by
 * the main process afterwards. */
export function toHomeSnapshot(v: unknown): Omit<HomeSnapshot, "mac_history"> | null {
  if (!isObj(v)) return null;
  const greeting = str(v.greeting, 60), date = str(v.date, 60), generated = str(v.generated_at, 40), place = optStr(v.place, 60);
  if (greeting === null || date === null || generated === null || place === undefined || typeof v.stopped !== "boolean") return null;
  const weather = section(v.weather, toWeather), calendar = section(v.calendar, toCalendar);
  const reminders = section(v.reminders, toReminders), mac = section(v.mac, toMac), needs = section(v.needs, toNeeds);
  const builds = section(v.builds, toBuilds), agents = section(v.agents, toAgents);
  if (!weather || !calendar || !reminders || !mac || !needs || !builds || !agents) return null;
  return { generated_at: generated, greeting, date, place, stopped: v.stopped, weather, calendar, reminders, mac, needs, builds, agents };
}

// ----------------------------------------------------------------------------- what the window shows

/** "Good morning, Owen" ... from the current time (never from the cache). Before 5 AM: "Working late". */
export function greetingFor(now: Date, name = "Owen"): string {
  const h = now.getHours();
  if (h < 5) return `Working late, ${name}`;
  return `Good ${h < 12 ? "morning" : h < 17 ? "afternoon" : "evening"}, ${name}`;
}

/** "Monday, October 19" */
export function dateLine(now: Date): string {
  return now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

export function clockTime(d: Date): string {
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
}

// A card may run a little past its interval while the next refresh is in flight.
export const STALE_GRACE_MS = 30_000;

export type Freshness = { label: string; stale: boolean; fade: boolean; tone: "ok" | "muted" | "warn" };

/** The label each card shows, computed against the current time: a card past its interval says
 * "Stale · last checked <time>" and fades its numbers, whatever cos last said. */
export function freshness(s: Section<unknown>, now: Date): Freshness {
  const generated = s.generated_at ? new Date(s.generated_at) : null;
  const valid = generated !== null && !Number.isNaN(generated.getTime());
  if (s.data === null) {
    return { label: s.status === "updating" ? "Checking…" : (s.reason ?? "Unavailable"), stale: false, fade: false, tone: "muted" };
  }
  const last = valid ? `last checked ${clockTime(generated)}` : "last check unknown";
  const age = valid ? now.getTime() - generated.getTime() : Infinity;
  if (age > s.interval_s * 1000 + STALE_GRACE_MS || s.status === "stale") {
    return { label: `Stale · ${last}`, stale: true, fade: true, tone: "warn" };
  }
  if (s.status === "updating") return { label: `Updating · ${last}`, stale: false, fade: false, tone: "muted" };
  return { label: valid ? `Updated ${clockTime(generated)}` : "Updated", stale: false, fade: false, tone: "ok" };
}

/** Decisions and suggestions for the two Today cards, split by kind only (cos never ranks them). */
export function splitNeeds(items: NeedItem[], maxDecisions = 5): {
  decisions: NeedItem[];
  decisionCount: number;
  suggestions: NeedItem[];
  info: NeedItem[];
} {
  const decisions = items.filter((i) => i.kind === "decision");
  return {
    decisions: decisions.slice(0, maxDecisions),
    decisionCount: decisions.length,
    suggestions: items.filter((i) => i.kind === "suggestion"),
    info: items.filter((i) => i.kind === "info"),
  };
}

export const MAC_HISTORY_MS = 30 * 60 * 1000;

/** Append a sample and drop those older than 30 minutes (the main process keeps them in memory). */
export function addMacSample(history: MacSample[], sample: MacSample): MacSample[] {
  const last = history[history.length - 1];
  const next = last && last.t === sample.t ? history : [...history, sample];
  return next.filter((s) => sample.t - s.t <= MAC_HISTORY_MS);
}
