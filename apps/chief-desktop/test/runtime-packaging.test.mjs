// Packaged runtime discovery: a bundled runtime always wins over the checkout.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const { loadDesktopConfig, packagedRuntimePath } = require("../out/main/config.js");

function fakeResources() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-res-"));
  fs.mkdirSync(path.join(dir, "runtime"), { recursive: true });
  const launcher = path.join(dir, "runtime", "cos");
  fs.writeFileSync(launcher, "#!/bin/sh\n", { mode: 0o755 });
  return dir;
}

test("packaged runtime is discovered under Resources/runtime", () => {
  const resources = fakeResources();
  assert.equal(packagedRuntimePath(resources), path.join(resources, "runtime", "cos"));
  assert.equal(packagedRuntimePath(undefined), null);
  assert.equal(packagedRuntimePath("/nonexistent"), null);
});

test("a packaged build ignores a desktop.json checkout path", () => {
  const resources = fakeResources();
  const configFile = path.join(resources, "desktop.json");
  fs.writeFileSync(configFile, JSON.stringify({ cosPath: "~/Projects/teacher-ai-workstation/bin/cos" }));
  const config = loadDesktopConfig(configFile, resources);
  assert.equal(config.runtimeSource, "packaged");
  assert.equal(config.cosPath, path.join(resources, "runtime", "cos"));
});

test("an unpackaged build keeps the development path or explicit override", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-dev-"));
  const configFile = path.join(dir, "desktop.json");
  fs.writeFileSync(configFile, JSON.stringify({ cosPath: "/opt/example/bin/cos" }));
  const config = loadDesktopConfig(configFile, undefined);
  assert.equal(config.runtimeSource, "development");
  assert.equal(config.cosPath, "/opt/example/bin/cos");
});
