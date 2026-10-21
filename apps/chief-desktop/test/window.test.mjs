// The full window, rendered to static markup from the tsc build of the renderer (out-test/): the
// Today page from a fixture snapshot, decisions vs suggestions by kind, the stale label and fade,
// chat mode persistence, the rail breakpoint, starters, and the keyboard map.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

process.env.TZ = "America/New_York";
const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const { TodayPage } = require("../out-test/renderer/Today.js");
const { Rail } = require("../out-test/renderer/Rail.js");
const { ChatPanel } = require("../out-test/renderer/Chat.js");
const { toHomeSnapshot } = require("../out-test/shared/home.js");
const layout = require("../out-test/shared/layout.js");

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RAW = JSON.parse(fs.readFileSync(path.join(APP, "test", "fixtures", "home-snapshot.json"), "utf-8"));
const AT = new Date("2026-10-01T14:30:00-04:00");
const h = React.createElement;

function today(raw = RAW, now = AT) {
  const snap = { ...toHomeSnapshot(raw), mac_history: [] };
  return renderToStaticMarkup(h(TodayPage, {
    home: { state: "ready", snap }, now, briefing: false, onBrief() {}, onAction() {}, onRetry() {},
  }));
}
const text = (html) => html.replace(/<[^>]+>/g, " ").replace(/&#x27;/g, "'").replace(/&amp;/g, "&").replace(/\s+/g, " ");

test("the Today page renders from a fixture snapshot", () => {
  const html = today();
  const t = text(html);
  for (const want of [
    "Good afternoon, Owen", "Thursday, October 1 · Sims, NC", "Today's brief", "Dev Mode", "coming with the Mac helper",
    "Needs your decision", "Suggested next steps", "Weather · Sims, NC", "68°", "partly cloudy",
    "SM5", "Lesson 42", "3 reminders due (1 overdue)", "Memory free", "61%", "CPU load", "18%", "214 GB",
    "test-model-a:latest", "Healthy", "No agents running.", "Working, Waiting or Done, and a Stop button",
    "Recent builds", "Test build five", "#105", "aaaa005", "Canvas planner status isn't connected yet.",
  ]) assert.ok(t.includes(want), want);
  assert.match(html, /<button[^>]*disabled[^>]*>Dev Mode<\/button>/);
  assert.equal((html.match(/aria-label="7-day forecast"/g) ?? []).length, 1);
  assert.equal((html.match(/<li class="flex flex-col items-center/g) ?? []).length, 7);
});

test("decisions and suggestions land in their own cards, five decisions at most", () => {
  const html = today();
  const decisionsAt = html.indexOf("Needs your decision");
  const suggestionsAt = html.indexOf("Suggested next steps");
  const card = (from, to) => text(html.slice(from, to));
  const decisions = card(decisionsAt, suggestionsAt);
  const suggestions = card(suggestionsAt, html.indexOf("Weather ·"));
  assert.ok(decisions.includes("Test decision one") && decisions.includes("Test decision five"));
  assert.ok(!decisions.includes("Latest real-model eval"), "the sixth decision waits for View all");
  assert.ok(decisions.includes("View all 6"));
  assert.ok(!decisions.includes("Store the web search key"));
  assert.ok(suggestions.includes("Store the web search key"));
  assert.ok(!suggestions.includes("Test decision"));
  assert.match(html, /aria-label="6 items"/);
});

test("empty needs: Nothing needs your decision.", () => {
  const raw = structuredClone(RAW);
  raw.needs.data.items = [];
  const t = text(today(raw));
  assert.ok(t.includes("Nothing needs your decision."));
  assert.ok(t.includes("No suggestions right now."));
});

test("a card past its interval shows Stale · last checked and fades its numbers", () => {
  assert.equal((today().match(/chief-faded/g) ?? []).length, 0);
  const html = today(RAW, new Date(AT.getTime() + 20 * 60_000)); // weather is 15 min, Mac 30 s
  assert.ok(text(html).includes("Stale · last checked 2:30 PM"));
  assert.ok((html.match(/chief-faded/g) ?? []).length >= 4);
  assert.match(html, /data-stale="true"/);
});

test("the greeting is computed from the clock, not the snapshot", () => {
  const t = text(today(RAW, new Date("2026-10-02T00:40:00-04:00")));
  assert.ok(t.includes("Working late, Owen"));
  assert.ok(t.includes("Friday, October 2"));
});

test("chat mode persists across restarts", () => {
  const store = new Map();
  const s = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, String(v)) };
  assert.equal(layout.loadChatMode(s), "split");
  layout.saveChatMode(s, "focus");
  assert.equal(layout.loadChatMode(s), "focus");
  layout.saveChatMode(s, "hide");
  assert.equal(layout.loadChatMode(s), "hide");
  assert.equal(layout.toggleHide(s, "hide"), "focus", "⌘\\ brings back the mode before Hide");
  assert.equal(layout.toggleHide(s, "split"), "hide");
  store.set(layout.CHAT_MODE_KEY, "sideways");
  assert.equal(layout.loadChatMode(s), "split");
  const broken = { getItem() { throw new Error("denied"); }, setItem() { throw new Error("denied"); } };
  assert.equal(layout.loadChatMode(broken), "split");
  assert.doesNotThrow(() => layout.saveChatMode(broken, "hide"));
});

test("the rail collapses to icons below the breakpoint and in Focus", () => {
  assert.equal(layout.RAIL_BREAKPOINT_PX, 1100);
  assert.equal(layout.railCollapsed(1099, "split"), true);
  assert.equal(layout.railCollapsed(1100, "split"), false);
  assert.equal(layout.railCollapsed(1600, "focus"), true);
  const rail = (collapsed) => renderToStaticMarkup(h(Rail, {
    collapsed, active: "today", dot: { color: "green", label: "Ready" }, stopped: false, onPage() {}, onKillSwitch() {},
  }));
  const wide = rail(false);
  const narrow = rail(true);
  assert.ok(text(wide).includes("Agents & builds") && text(wide).includes("Ready") && text(wide).includes("Stop Chief"));
  assert.ok(!text(narrow).includes("Agents & builds"), "labels hidden when collapsed");
  for (const name of ["Today", "Chat", "Agents &amp; builds", "Mac", "Files (later)", "Settings", "Stop Chief"]) {
    assert.ok(narrow.includes(`aria-label="${name}"`), name);
  }
  assert.match(narrow, /data-collapsed="true"/);
  assert.match(wide, /<button[^>]*disabled[^>]*>.*Files.*later/);
});

test("an empty chat shows the starter buttons", () => {
  const ref = { current: null };
  const html = renderToStaticMarkup(h(ChatPanel, {
    turns: [], cards: [], pending: null, input: "", asking: false, focus: true, inputRef: ref, feedRef: ref,
    onScroll() {}, onInput() {}, onKeyDown() {}, onSend() {},
  }));
  for (const s of ["Summarize today", "Diagnose my Mac", "What needs me?"]) assert.ok(text(html).includes(s), s);
  assert.match(html, /max-w-\[780px\]/);
  assert.match(html, /aria-label="Message Chief"/);
});

test("keyboard: ⌘1–⌘5 pages, ⌘\\ Hide, ⌘K input, Esc hides the window", () => {
  const k = (key, meta = true) => layout.shortcutFor({ key, metaKey: meta, ctrlKey: false, altKey: false, shiftKey: false });
  assert.deepEqual(k("1"), { kind: "page", page: "today" });
  assert.deepEqual(k("2"), { kind: "page", page: "chat" });
  assert.deepEqual(k("3"), { kind: "page", page: "agents" });
  assert.deepEqual(k("4"), { kind: "page", page: "mac" });
  assert.equal(k("5"), null, "Files comes later");
  assert.deepEqual(k("\\"), { kind: "toggle-hide" });
  assert.deepEqual(k("k"), { kind: "focus-input" });
  assert.deepEqual(k("Escape", false), { kind: "hide-window" });
  assert.equal(k("1", false), null);
});
