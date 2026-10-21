// Settings: argv for cos config get/set, a round trip through the real cos (temp state folder,
// synthetic places), the report validator, place helpers, and the rendered page.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { CosRunner } = require("../out/main/cos.js");
const { buildArgs, ArgsError } = require("../out/main/args.js");
const { parsePlace, placeKey, toConfigReport } = require("../out/shared/settings.js");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const { SettingsPage } = require("../out-test/renderer/Settings.js");

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-settings-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function realCos(state) {
  const file = path.join(dir, `cos-${path.basename(state)}`);
  fs.writeFileSync(file, `#!${process.execPath}
    const { execFileSync } = require("node:child_process");
    try {
      process.stdout.write(execFileSync(${JSON.stringify(path.join(REPO, "bin", "cos"))}, process.argv.slice(2), {
        env: { ...process.env, COS_STATE_DIR: ${JSON.stringify(state)} }, encoding: "utf8" }));
    } catch (e) { process.stdout.write(String(e.stdout ?? "")); process.exit(e.status ?? 1); }\n`, { mode: 0o700 });
  return file;
}

test("argv: config get and set, settable keys only, the value as one JSON element", () => {
  assert.deepEqual(buildArgs("config-get"), ["config", "get", "--json"]);
  assert.deepEqual(buildArgs("config-set", { key: "auto_search", value: false }), ["config", "set", "--json", "--", "auto_search", "false"]);
  assert.deepEqual(buildArgs("config-set", { key: "places", value: { home: { name: "A; rm -rf ~", latitude: 1, longitude: 2 } } }),
    ["config", "set", "--json", "--", "places", '{"home":{"name":"A; rm -rf ~","latitude":1,"longitude":2}}']);
  for (const key of ["ollama_url", "search_daily_limit", "places; rm", "", undefined, 5]) {
    assert.throws(() => buildArgs("config-set", { key, value: 1 }), ArgsError, String(key));
  }
  assert.throws(() => buildArgs("config-set", { key: "model", value: "x".repeat(5000) }), ArgsError);
  assert.throws(() => buildArgs("config-set", { key: "model", value: undefined }), ArgsError);
});

test("Settings round-trips through cos config", async () => {
  const state = path.join(dir, "state-a");
  const runner = new CosRunner(realCos(state));
  const got = await runner.configGet();
  assert.equal(got.ok, true);
  assert.equal(got.values.places.home.name, "Sims, NC");
  assert.ok(got.path.endsWith("config.json"));
  const places = { ...got.values.places, test_gym: { name: "Test Gym", latitude: 35.7, longitude: -78.1 } };
  const set = await runner.configSet("places", places);
  assert.equal(set.ok, true);
  assert.deepEqual(set.values.places.test_gym, { name: "Test Gym", latitude: 35.7, longitude: -78.1 });
  assert.equal((await runner.configSet("auto_search", false)).values.auto_search, false);
  assert.equal((await runner.configSet("model_keep_alive", "30m")).values.model_keep_alive, "30m");
  const again = await runner.configGet();
  assert.deepEqual(again.values.places.test_gym, places.test_gym);
  assert.equal(again.values.auto_search, false);
  assert.equal(fs.statSync(path.join(state, "config.json")).mode & 0o777, 0o600);
  const audit = fs.readFileSync(path.join(state, "audit.jsonl"), "utf-8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
  assert.deepEqual(audit.filter((r) => r.kind === "config_change").map((r) => r.key), ["places", "auto_search", "model_keep_alive"]);
});

test("a bad value comes back as cos's message, and nothing is written", async () => {
  const state = path.join(dir, "state-b");
  const runner = new CosRunner(realCos(state));
  const bad = await runner.configSet("places", { home: { name: "Nowhere", latitude: 95, longitude: 0 } });
  assert.equal(bad.ok, false);
  assert.equal(bad.error_kind, "usage");
  assert.match(bad.error, /latitude out of range/);
  assert.equal(fs.existsSync(path.join(state, "config.json")), false);
  const refused = await runner.configSet("ollama_url", "http://example.com");
  assert.deepEqual([refused.ok, refused.error_kind], [false, "usage"]);
});

test("only known report fields pass", () => {
  const report = toConfigReport({ ok: true, path: "~/x/config.json", settable: [], extra: 1, values: {
    places: { home: { name: "A", latitude: 1, longitude: 2, extra: true } }, auto_search: true, model: "m", fallback_model: null,
    model_keep_alive: "2h", search_daily_limit: 30, search_monthly_limit: 600, ollama_url: "http://x" } });
  assert.deepEqual(Object.keys(report.values).sort(), ["auto_search", "fallback_model", "model", "model_keep_alive", "places", "search_daily_limit", "search_monthly_limit"]);
  assert.deepEqual(report.values.places.home, { name: "A", latitude: 1, longitude: 2 });
  assert.equal(toConfigReport({ path: "p", values: { places: { "Bad Key": { name: "A", latitude: 1, longitude: 2 } } } }), null);
});

test("place helpers", () => {
  assert.equal(placeKey("Raleigh, NC", ["home", "work"]), "raleigh_nc");
  assert.equal(placeKey("Raleigh, NC", ["raleigh_nc"]), "raleigh_nc_2");
  assert.equal(placeKey("123", []), "place");
  assert.deepEqual(parsePlace({ name: " Test Gym ", latitude: "35.7", longitude: "-78.1" }), { name: "Test Gym", latitude: 35.7, longitude: -78.1 });
  assert.match(parsePlace({ name: "", latitude: "1", longitude: "1" }), /name/);
  assert.match(parsePlace({ name: "A", latitude: "north", longitude: "1" }), /Latitude/);
  assert.match(parsePlace({ name: "A", latitude: "1", longitude: "181" }), /Longitude/);
});

test("the Settings page renders its sections and footer", () => {
  const initial = { path: "~/Library/Application Support/ChiefOfStaff/config.json", values: {
    places: { home: { name: "Sims, NC", latitude: 35.76, longitude: -78.06 }, work: { name: "Clayton, NC", latitude: 35.65, longitude: -78.46 } },
    auto_search: true, model: "qwen3.6:35b", fallback_model: "gpt-oss:20b", model_keep_alive: "2h", search_daily_limit: 30, search_monthly_limit: 600 } };
  const html = renderToStaticMarkup(React.createElement(SettingsPage, {
    windowState: { pinned: false, protected: true, startAtLogin: true, hotkey: "Control+Alt+C" }, onWindowState() {},
    bridge: { configGet: async () => ({ ok: true, ...initial }), configSet: async () => ({ ok: true, ...initial }), setProtection: async () => ({}) },
    initial,
  })).replace(/&#x27;/g, "'");
  for (const want of ["General", "Start at login", "Screen protection", "Control+Option+C", "Follows macOS", "Weather places",
    "Sims, NC", "Clayton, NC", "35.76, -78.06", "Add a place", "Search and local model", "Auto web search", "30 a day · 600 a month",
    "qwen3.6:35b", "Fallback: gpt-oss:20b", "These settings are saved in config.json in Chief's data folder"]) {
    assert.ok(html.includes(want), want);
  }
  assert.match(html, /aria-label="Edit Sims, NC"/);
});
