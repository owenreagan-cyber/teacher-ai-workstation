// Home card: what reaches the renderer from `cos brief --json`, and the text the card shows.
// Fake cos executables only, plus one run of the real cos in fixture mode (synthetic data, a temp
// state directory), so the Python card shape and this validator cannot drift apart.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { CosRunner } = require("../out/main/cos.js");
const { cardView, isStale, localDay, toHomeCard } = require("../out/shared/homeCard.js");

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-home-card-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function fakeCos(name, body) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, `#!${process.execPath}\n${body}\n`, { mode: 0o700 });
  return file;
}
const briefCos = (name, payload) => fakeCos(name, `console.log(JSON.stringify(${JSON.stringify(payload)}));`);

const CARD = {
  greeting: "Good afternoon, Owen",
  date: "Thursday, October 1",
  date_iso: "2026-10-01",
  calendar: { status: "ok", count: 3, next: { title: "Test Event B", start: "3:30 PM" }, text: "Next: 3:30 PM Test Event B · 3 events today" },
  reminders: { status: "ok", due: 3, overdue: 1, text: "3 reminders due (1 overdue)" },
  weather: { status: "ok", text: "68°F partly cloudy · H 74 / L 55 · rain 20%" },
};
const LINES = ["Daily Brief — Thursday, October 1, 2026", "Weather: 68°F partly cloudy"];

test("a full card reaches the renderer and renders greeting, date, next event, reminders, weather", async () => {
  const res = await new CosRunner(briefCos("full-cos", { ok: true, lines: LINES, card: CARD })).brief();
  assert.equal(res.ok, true);
  assert.deepEqual(res.lines, LINES);
  assert.deepEqual(res.card, CARD);
  const view = cardView(res.card);
  assert.equal(view.greeting, "Good afternoon, Owen");
  assert.equal(view.date, "Thursday, October 1");
  assert.deepEqual(view.rows.map((r) => r.text), [CARD.calendar.text, CARD.reminders.text, CARD.weather.text]);
  assert.deepEqual(view.rows.map((r) => r.muted), [false, false, false]);
  assert.equal(view.summary, "Good afternoon, Owen · Next: 3:30 PM Test Event B");
});

test("empty and unavailable states render their fixed text, muted", async () => {
  const card = {
    ...CARD,
    calendar: { status: "unavailable", count: 0, next: null, text: "Calendar unavailable" },
    reminders: { status: "empty", due: 0, overdue: 0, text: "No reminders due" },
    weather: { status: "unavailable", text: "Weather unavailable" },
  };
  const res = await new CosRunner(briefCos("unavail-cos", { ok: true, lines: LINES, card })).brief();
  const view = cardView(res.card);
  assert.deepEqual(view.rows.map((r) => [r.text, r.muted]), [
    ["Calendar unavailable", true], ["No reminders due", true], ["Weather unavailable", true]]);
  assert.equal(view.summary, "Good afternoon, Owen · Calendar unavailable");
  const empty = cardView({ ...CARD, calendar: { status: "empty", count: 0, next: null, text: "Nothing scheduled" } });
  assert.equal(empty.rows[0].text, "Nothing scheduled");
});

test("a malformed card is dropped (not shown) while the brief lines still pass", async () => {
  const bad = {
    "no card": undefined,
    "card is a string": "Good afternoon",
    "missing weather": { ...CARD, weather: undefined },
    "bad status": { ...CARD, calendar: { ...CARD.calendar, status: "fine" } },
    "negative count": { ...CARD, reminders: { ...CARD.reminders, overdue: -1 } },
    "next not an object": { ...CARD, calendar: { ...CARD.calendar, next: "Test Event B" } },
    "numeric title": { ...CARD, calendar: { ...CARD.calendar, next: { title: 5, start: null } } },
    "bad date_iso": { ...CARD, date_iso: "October 1" },
    "oversized text": { ...CARD, weather: { status: "ok", text: "x".repeat(301) } },
  };
  for (const [name, card] of Object.entries(bad)) {
    const res = await new CosRunner(briefCos(`bad-${name.replace(/\W+/g, "-")}`, { ok: true, lines: LINES, card })).brief();
    assert.equal(res.ok, true, name);
    assert.equal(res.card, null, name);
    assert.deepEqual(res.lines, LINES, name);
  }
});

test("only known card fields pass", () => {
  const card = toHomeCard({ ...CARD, html: "<img src=x>", calendar: { ...CARD.calendar, extra: 1, next: { ...CARD.calendar.next, url: "x" } } });
  assert.deepEqual(Object.keys(card).sort(), ["calendar", "date", "date_iso", "greeting", "reminders", "weather"]);
  assert.deepEqual(Object.keys(card.calendar).sort(), ["count", "next", "status", "text"]);
  assert.deepEqual(Object.keys(card.calendar.next).sort(), ["start", "title"]);
});

test("errors from cos come back as data (never a stack trace)", async () => {
  const stopped = fakeCos("brief-stopped", `console.log(JSON.stringify({ ok: false, error: "stopped by kill switch", error_kind: "stopped" })); process.exit(3);`);
  assert.deepEqual(await new CosRunner(stopped).brief(), { ok: false, error: "stopped by kill switch", error_kind: "stopped" });
  const crash = fakeCos("brief-crash", `console.log("Traceback (most recent call last):"); process.exit(1);`);
  assert.deepEqual(await new CosRunner(crash).brief(), { ok: false, error_kind: "internal", error: "Chief returned an unexpected response." });
});

test("the card goes stale when a new local day starts", () => {
  assert.equal(localDay(new Date(2026, 9, 1, 23, 59)), "2026-10-01");
  assert.equal(isStale(CARD, new Date(2026, 9, 1, 23, 59)), false);
  assert.equal(isStale(CARD, new Date(2026, 9, 2, 0, 0)), true);
});

test("the real cos in fixture mode produces a card this validator accepts", async () => {
  const state = path.join(dir, "cos-state");
  // CosRunner passes a minimal environment, so the wrapper sets fixture mode itself.
  const wrapper = fakeCos("fixture-cos", `
    const { execFileSync } = require("node:child_process");
    const out = execFileSync(${JSON.stringify(path.join(REPO, "bin", "cos"))}, process.argv.slice(2), {
      env: { ...process.env, COS_STATE_DIR: ${JSON.stringify(state)},
             COS_FIXTURE_DIR: ${JSON.stringify(path.join(REPO, "evals", "fixtures", "default"))}, TZ: "America/New_York" },
      encoding: "utf8" });
    process.stdout.write(out);`);
  const res = await new CosRunner(wrapper).brief();
  assert.equal(res.ok, true);
  assert.deepEqual(res.card, CARD);
  assert.match(res.lines[0], /^Daily Brief — Thursday, October 1, 2026/);
});
