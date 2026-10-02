// App preferences (Start at login): remembered in prefs.json, private, and null until the first run.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { loadPrefs, savePrefs } = require("../out/main/config.js");

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-prefs-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

test("missing or unreadable prefs mean the first run has not happened", () => {
  assert.deepEqual(loadPrefs(path.join(dir, "missing.json")), { startAtLogin: null });
  const bad = path.join(dir, "bad.json");
  fs.writeFileSync(bad, "{not json");
  assert.deepEqual(loadPrefs(bad), { startAtLogin: null });
  fs.writeFileSync(bad, JSON.stringify({ startAtLogin: "yes" }));
  assert.deepEqual(loadPrefs(bad), { startAtLogin: null });
});

test("the Start at login choice is remembered in a private file", () => {
  const file = path.join(dir, "sub", "prefs.json");
  savePrefs(file, { startAtLogin: false });
  assert.deepEqual(loadPrefs(file), { startAtLogin: false });
  assert.equal(fs.statSync(file).mode & 0o777, 0o600);
  savePrefs(file, { startAtLogin: true });
  assert.deepEqual(loadPrefs(file), { startAtLogin: true });
});
