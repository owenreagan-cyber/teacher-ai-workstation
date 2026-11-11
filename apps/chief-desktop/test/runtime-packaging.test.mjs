// Packaged runtime resolution: fail closed, never fall back to the checkout.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const { loadDesktopConfig, resolvePackagedRuntime } = require("../out/main/config.js");

const MANIFEST = {
  format: 1,
  runtime: { version: "0.1.0+abc123" },
  source: { commit: "abc123" },
  artifacts: { cos: { sha256: "aa" }, cosd: { sha256: "bb" } },
};

function packagedResources({ manifest = MANIFEST } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "chief-pkg-"));
  const resources = path.join(root, "Chief.app", "Contents", "Resources");
  const runtime = path.join(resources, "runtime");
  fs.mkdirSync(path.join(runtime, "py", "cos"), { recursive: true });
  fs.mkdirSync(path.join(runtime, "py", "cosd"), { recursive: true });
  fs.writeFileSync(path.join(runtime, "py", "cos", "__init__.py"), "");
  fs.writeFileSync(path.join(runtime, "py", "cosd", "__init__.py"), "");
  fs.writeFileSync(path.join(runtime, "cos"), "#!/bin/sh\n", { mode: 0o755 });
  fs.writeFileSync(path.join(runtime, "cosd"), "#!/bin/sh\n", { mode: 0o755 });
  fs.writeFileSync(path.join(runtime, "manifest.json"), JSON.stringify(manifest));
  return resources;
}

test("a complete bundled runtime resolves to the bundle", () => {
  const resources = packagedResources();
  assert.equal(resolvePackagedRuntime(resources).error, null);
  const config = loadDesktopConfig(path.join(resources, "desktop.json"), resources);
  assert.equal(config.runtimeSource, "packaged");
  assert.equal(config.cosPath, path.join(resources, "runtime", "cos"));
  assert.equal(config.error, null);
});

test("missing runtime directory fails closed instead of using the checkout", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "chief-pkg-"));
  const resources = path.join(root, "Chief.app", "Contents", "Resources");
  fs.mkdirSync(resources, { recursive: true });
  const config = loadDesktopConfig(path.join(resources, "desktop.json"), resources);
  assert.equal(config.runtimeSource, "packaged");
  assert.match(config.error, /cannot start/i);
  assert.ok(!config.cosPath.includes("teacher-ai-workstation"), config.cosPath);
});

test("missing launchers and sources are rejected", () => {
  for (const rel of [
    ["runtime", "cos"],
    ["runtime", "cosd"],
    ["runtime", "py", "cos", "__init__.py"],
    ["runtime", "py", "cosd", "__init__.py"],
  ]) {
    const resources = packagedResources();
    fs.rmSync(path.join(resources, ...rel));
    const result = resolvePackagedRuntime(resources);
    assert.notEqual(result.error, null, `expected error for missing ${rel.join("/")}`);
    assert.equal(result.path, null);
  }
});

test("invalid manifest is rejected", () => {
  for (const manifest of [{ format: 2 }, { format: 1, runtime: {} }, "not-an-object"]) {
    const resources = packagedResources({ manifest });
    assert.notEqual(resolvePackagedRuntime(resources).error, null);
  }
});

test("a stale desktop.json checkout path cannot redirect a packaged build", () => {
  const resources = packagedResources();
  const configFile = path.join(resources, "desktop.json");
  fs.writeFileSync(configFile, JSON.stringify({ cosPath: "~/Projects/teacher-ai-workstation/bin/cos" }));
  const config = loadDesktopConfig(configFile, resources);
  assert.equal(config.runtimeSource, "packaged");
  assert.equal(config.cosPath, path.join(resources, "runtime", "cos"));
});

test("development builds still accept the checkout path", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-dev-"));
  const configFile = path.join(dir, "desktop.json");
  fs.writeFileSync(configFile, JSON.stringify({ cosPath: "/opt/example/bin/cos" }));
  const config = loadDesktopConfig(configFile, path.join(dir, "electron-dist"));
  assert.equal(config.runtimeSource, "development");
  assert.equal(config.cosPath, "/opt/example/bin/cos");
  assert.equal(config.error, null);
});
