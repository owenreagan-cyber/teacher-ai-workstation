// The home card: validated from `cos brief --json` ("card") and turned into display text.
// Pure (no Electron, no DOM, no I/O) so the main process, the renderer, and tests share it.
// cos decides every value; this file only checks shapes and lays the text out.
import type { CardStatus, HomeCard } from "./types.js";

const MAX_TEXT = 300;
const STATUSES: CardStatus[] = ["ok", "empty", "unavailable"];

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const text = (v: unknown): string | null => (typeof v === "string" && v.length <= MAX_TEXT ? v : null);
const count = (v: unknown): number | null => (typeof v === "number" && Number.isSafeInteger(v) && v >= 0 ? v : null);
const status = (v: unknown): CardStatus | null => (STATUSES.includes(v as CardStatus) ? (v as CardStatus) : null);

/** A HomeCard with exactly the known fields and correct types, or null (the card is not shown). */
export function toHomeCard(value: unknown): HomeCard | null {
  if (!isObj(value) || !isObj(value.calendar) || !isObj(value.reminders) || !isObj(value.weather)) return null;
  const { calendar: c, reminders: r, weather: w } = value;
  const greeting = text(value.greeting);
  const date = text(value.date);
  const dateIso = typeof value.date_iso === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value.date_iso) ? value.date_iso : null;
  let next: HomeCard["calendar"]["next"] = null;
  if (c.next !== null) {
    if (!isObj(c.next)) return null;
    const title = text(c.next.title);
    const start = c.next.start === null ? null : text(c.next.start);
    if (title === null || (start === null && c.next.start !== null)) return null;
    next = { title, start };
  }
  const cs = status(c.status), ct = text(c.text), cc = count(c.count);
  const rs = status(r.status), rt = text(r.text), rd = count(r.due), ro = count(r.overdue);
  const ws = status(w.status), wt = text(w.text);
  if (greeting === null || date === null || dateIso === null) return null;
  if (cs === null || ct === null || cc === null || rs === null || rt === null || rd === null || ro === null) return null;
  if (ws === null || wt === null) return null;
  return {
    greeting,
    date,
    date_iso: dateIso,
    calendar: { status: cs, text: ct, count: cc, next },
    reminders: { status: rs, text: rt, due: rd, overdue: ro },
    weather: { status: ws, text: wt },
  };
}

export type CardRow = { key: "calendar" | "reminders" | "weather"; label: string; text: string; muted: boolean };
export type CardView = { greeting: string; date: string; rows: CardRow[]; summary: string };

/** What the card shows. summary is the one-line thin header used after the first question. */
export function cardView(card: HomeCard): CardView {
  const rows: CardRow[] = [
    { key: "calendar", label: "Calendar", text: card.calendar.text, muted: card.calendar.status !== "ok" },
    { key: "reminders", label: "Reminders", text: card.reminders.text, muted: card.reminders.status !== "ok" },
    { key: "weather", label: "Weather", text: card.weather.text, muted: card.weather.status !== "ok" },
  ];
  const next = card.calendar.next;
  const lead = next ? `Next: ${next.start ? `${next.start} ` : ""}${next.title}` : card.calendar.text;
  return { greeting: card.greeting, date: card.date, rows, summary: `${card.greeting} · ${lead}` };
}

/** The local calendar day of `now` as YYYY-MM-DD. */
export function localDay(now: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** True when the card was built on an earlier day than `now` (time to rebuild it). */
export function isStale(card: HomeCard, now: Date): boolean {
  return localDay(now) !== card.date_iso;
}
