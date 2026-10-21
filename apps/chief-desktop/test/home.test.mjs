// The Today snapshot: what reaches the renderer from `cos home --json`, freshness labels (stale and
// fade), decisions vs suggestions by kind, and the in-memory Mac history. Fake cos executables, plus
// one run of the real cos in fixture mode so the Python shape and this validator cannot drift.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { after, test } from "node:test";

process.env.TZ = "America/New_York";
const require = createRequire(import.meta.url);
const { CosRunner } = require("../out/main/cos.js");
const { addMacSample, dateLine, freshness, greetingFor, MAC_HISTORY_MS, splitNeeds, toHomeSnapshot } = require("../out/shared/home.js");

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REPO = path.resolve(APP, "..", "..");
const SNAPSHOT = JSON.parse(fs.readFileSync(path.join(APP, "test", "fixtures", "home-snapshot.json"), "utf-8"));
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-home-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function fakeCos(name, body) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, `#!${process.execPath}\n${body}\n`, { mode: 0o700 });
  return file;
}
const printing = (name, payload) => fakeCos(name, `console.log(JSON.stringify(${JSON.stringify(payload)}));`);

test("a full snapshot reaches the renderer with exactly the known fields", async () => {
  const res = await new CosRunner(printing("home-cos", SNAPSHOT)).home(true);
  assert.equal(res.ok, true);
  assert.equal(res.greeting, "Good afternoon, Owen");
  assert.equal(res.weather.data.temp_f, 68);
  assert.equal(res.weather.data.days.length, 7);
  assert.deepEqual(res.calendar.data.events[0], { title: "Lesson 42", course: "SM5", all_day: false, start: "9:00 AM", end: "9:45 AM" });
  assert.deepEqual(res.mac_history, []);
  assert.deepEqual(Object.keys(res).sort(), ["agents", "builds", "calendar", "date", "generated_at", "greeting", "mac",
    "mac_history", "needs", "ok", "place", "reminders", "stopped", "weather"]);
});

test("argv: --cached only for the first paint", () => {
  const { buildArgs } = require("../out/main/args.js");
  assert.deepEqual(buildArgs("home", { cached: true }), ["home", "--json", "--cached"]);
  assert.deepEqual(buildArgs("home", { cached: "yes" }), ["home", "--json"]);
  assert.deepEqual(buildArgs("home"), ["home", "--json"]);
});

test("a section with bad data is shown as unavailable; the rest stay", () => {
  const bad = structuredClone(SNAPSHOT);
  bad.weather.data.temp_f = "hot";
  const snap = toHomeSnapshot(bad);
  assert.equal(snap.weather.status, "unavailable");
  assert.equal(snap.weather.data, null);
  assert.equal(snap.mac.status, "current");
  const noAgents = structuredClone(SNAPSHOT);
  noAgents.agents.data.items = [{ name: "x" }];
  assert.equal(toHomeSnapshot(noAgents).agents.data, null);
  const broken = structuredClone(SNAPSHOT);
  delete broken.mac;
  assert.equal(toHomeSnapshot(broken), null);
});

test("URLs never reach the renderer, and one bad need is dropped alone", () => {
  const s = structuredClone(SNAPSHOT);
  s.calendar.data.events[0].title = "Zoom https://example.com/j/123 call";
  s.needs.data.items.push({ id: "x", kind: "decision", title: 5 });
  const snap = toHomeSnapshot(s);
  assert.equal(snap.calendar.data.events[0].title.includes("https"), false);
  assert.equal(snap.needs.data.items.length, SNAPSHOT.needs.data.items.length);
});

test("need links reach the main process's resource table, never the renderer", async () => {
  const s = structuredClone(SNAPSHOT);
  const link = { type: "open_link", label: "Open doc", link_id: "lnk-0123456789abcdef" };
  s.needs.data.items[0].action = link;
  s.resources = [{ id: "lnk-0123456789abcdef", url: "https://example.com/doc" }];
  const sink = [];
  const res = await new CosRunner(printing("home-links", s), null, (r) => sink.push(...r)).home(false);
  assert.deepEqual(res.needs.data.items[0].action, link);
  assert.deepEqual(sink, [{ id: "lnk-0123456789abcdef", url: "https://example.com/doc" }]);
  assert.equal(JSON.stringify(res).includes("example.com"), false);
  // A command action is text to copy; an item with an unknown action type is dropped.
  s.needs.data.items[0].action = { type: "run", label: "Run", command: "rm -rf ~" };
  assert.equal(toHomeSnapshot(s).needs.data.items.length, SNAPSHOT.needs.data.items.length - 1);
});

test("decisions and suggestions are split by kind only", () => {
  const { decisions, decisionCount, suggestions, info } = splitNeeds(toHomeSnapshot(SNAPSHOT).needs.data.items);
  assert.ok(decisions.every((i) => i.kind === "decision"));
  assert.ok(suggestions.every((i) => i.kind === "suggestion"));
  assert.deepEqual(info.map((i) => i.id), ["canvas:not-connected"]);
  assert.equal(decisionCount, 6);
  assert.equal(decisions.length, 5); // five at most, then "View all"
  assert.deepEqual(suggestions.map((i) => i.id), ["config:search-key"]);
});

test("a card past its interval is stale with the last-checked time, and fades", () => {
  const s = toHomeSnapshot(SNAPSHOT);
  const at = new Date("2026-10-01T14:30:00-04:00");
  assert.deepEqual(freshness(s.weather, at), { label: "Updated 2:30 PM", stale: false, fade: false, tone: "ok" });
  const late = new Date(at.getTime() + (900 + 31) * 1000);
  assert.deepEqual(freshness(s.weather, late), { label: "Stale · last checked 2:30 PM", stale: true, fade: true, tone: "warn" });
  assert.equal(freshness(s.mac, new Date(at.getTime() + 61_000)).stale, true);
  assert.equal(freshness(s.mac, new Date(at.getTime() + 45_000)).stale, false);
  assert.equal(freshness({ ...s.weather, status: "stale", reason: "Couldn't refresh" }, at).fade, true);
  assert.equal(freshness({ ...s.weather, status: "updating" }, at).label, "Updating · last checked 2:30 PM");
  assert.equal(freshness({ ...s.weather, status: "unavailable", reason: "Weather unavailable", data: null }, at).label, "Weather unavailable");
});

test("the greeting comes from the current time, including after midnight", () => {
  const at = (h, m = 0) => new Date(2026, 9, 19, h, m);
  assert.equal(greetingFor(at(0, 30)), "Working late, Owen");
  assert.equal(greetingFor(at(4, 59)), "Working late, Owen");
  assert.equal(greetingFor(at(5)), "Good morning, Owen");
  assert.equal(greetingFor(at(12)), "Good afternoon, Owen");
  assert.equal(greetingFor(at(17)), "Good evening, Owen");
  assert.equal(greetingFor(at(23, 59)), "Good evening, Owen");
  assert.equal(dateLine(at(9)), "Monday, October 19");
});

test("Mac history keeps 30 minutes of samples, in order, without duplicates", () => {
  let h = [];
  const t0 = 1_000_000;
  for (let i = 0; i <= 70; i++) h = addMacSample(h, { t: t0 + i * 30_000, memory_free_pct: 50, cpu_load_pct: i });
  assert.equal(h[h.length - 1].t - h[0].t <= MAC_HISTORY_MS, true);
  assert.equal(h.length, 61);
  assert.equal(addMacSample(h, h[h.length - 1]).length, 61);
});

test("the main process keeps Mac history in memory only", () => {
  const main = fs.readFileSync(path.join(APP, "src", "main", "main.ts"), "utf-8");
  const fn = main.match(/async function home\([\s\S]*?\n}\n/)?.[0] ?? "";
  assert.match(fn, /macHistory = addMacSample\(/);
  assert.doesNotMatch(fn, /write|save|fs\./i);
});

test("the real cos in fixture mode produces a snapshot this validator accepts", async () => {
  const state = path.join(dir, "cos-state");
  const wrapper = fakeCos("fixture-cos", `
    const { execFileSync } = require("node:child_process");
    const out = execFileSync(${JSON.stringify(path.join(REPO, "bin", "cos"))}, process.argv.slice(2), {
      env: { ...process.env, COS_STATE_DIR: ${JSON.stringify(state)},
             COS_FIXTURE_DIR: ${JSON.stringify(path.join(REPO, "evals", "fixtures", "default"))}, TZ: "America/New_York" },
      encoding: "utf8" });
    process.stdout.write(out);`);
  const runner = new CosRunner(wrapper);
  const first = await runner.home(true);
  assert.equal(first.ok, true);
  assert.equal(first.weather.status, "updating");
  const res = await runner.home(false);
  assert.equal(res.ok, true);
  for (const name of ["weather", "calendar", "reminders", "mac", "builds", "agents"]) {
    assert.equal(res[name].status, "current", name);
    assert.notEqual(res[name].data, null, name);
  }
  assert.equal(res.place, "Sims, NC");
  assert.equal(res.reminders.data.line, "3 reminders due (1 overdue)");
});
