// desktop.json: cosPath may start with ~/ (expanded to the home folder); a relative path or ~user is
// refused with a plain error, and the default points at the main checkout.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { DEFAULT_COS_PATH, expandHome, loadDesktopConfig, loadWindowState, DEFAULT_SIZE } = require("../out/main/config.js");

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-desktop-config-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function desktopJson(name, value) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, typeof value === "string" ? value : JSON.stringify(value));
  return file;
}

test("a leading ~ in cosPath is expanded to the home folder", () => {
  const cfg = loadDesktopConfig(desktopJson("tilde.json", { cosPath: "~/Projects/teacher-ai-workstation/bin/cos" }));
  assert.equal(cfg.error, null);
  assert.equal(cfg.cosPath, path.join(os.homedir(), "Projects", "teacher-ai-workstation", "bin", "cos"));
  assert.equal(expandHome("~"), os.homedir());
  assert.equal(expandHome("/Users/x/bin/cos"), "/Users/x/bin/cos");
  assert.equal(expandHome("~other/bin/cos"), "~other/bin/cos");
});

test("an absolute cosPath is kept; relative and ~user paths are refused", () => {
  assert.equal(loadDesktopConfig(desktopJson("abs.json", { cosPath: "/opt/cos/bin/cos" })).cosPath, "/opt/cos/bin/cos");
  for (const cosPath of ["bin/cos", "~other/bin/cos", 5]) {
    const cfg = loadDesktopConfig(desktopJson(`bad-${String(cosPath).replace(/\W/g, "")}.json`, { cosPath }));
    assert.match(cfg.error, /cosPath .* must be an absolute path \(or start with ~\/\)/, String(cosPath));
  }
});

test("the default cosPath is the main checkout, expanded", () => {
  assert.equal(DEFAULT_COS_PATH, "~/Projects/teacher-ai-workstation/bin/cos");
  const cfg = loadDesktopConfig(path.join(dir, "missing.json"));
  assert.equal(cfg.cosPath, path.join(os.homedir(), "Projects", "teacher-ai-workstation", "bin", "cos"));
  assert.equal(loadDesktopConfig(desktopJson("broken.json", "{nope")).error.endsWith("is not valid JSON"), true);
});

test("a size remembered from the compact window opens at the full default", () => {
  const file = desktopJson("window-state.json", { width: 380, height: 540, pinned: false });
  assert.deepEqual([loadWindowState(file).width, loadWindowState(file).height], [DEFAULT_SIZE.width, DEFAULT_SIZE.height]);
  const big = desktopJson("window-big.json", { width: 1500, height: 900 });
  assert.deepEqual([loadWindowState(big).width, loadWindowState(big).height], [1500, 900]);
});
