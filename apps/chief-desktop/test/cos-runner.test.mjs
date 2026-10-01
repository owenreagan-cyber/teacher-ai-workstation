// CosRunner against a fake cos executable (never the real one): argv passes verbatim with no
// shell, the environment is minimal, and bad output becomes data instead of a crash.
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { CosRunner, minimalEnv } = require("../out/main/cos.js");

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-desktop-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function fakeCos(name, body) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, `#!${process.execPath}\n${body}\n`, { mode: 0o700 });
  return file;
}

// Echoes its argv and environment keys back as an ask-shaped answer.
const echo = fakeCos(
  "echo-cos",
  `const a = process.argv.slice(2);
   if (a[0] === "history") { console.log(JSON.stringify([{ ts: "t", question: "q", answer: "a", tools_used: [], fast_path: true, model: null, notices: [], total_ms: 1 }])); process.exit(0); }
   console.log(JSON.stringify({ ok: true, answer: JSON.stringify(a), tools_used: [], model: null, notices: [], fast_path: false,
     session_id: "default", ts: "t", total_ms: 1, env: Object.keys(process.env).sort() }));`,
);

test("argv reaches cos verbatim, with no shell interpretation", async () => {
  const marker = path.join(dir, "pwned");
  const question = `hi; touch ${marker} && $(touch ${marker}) \`touch ${marker}\``;
  const res = await new CosRunner(echo).ask(question, "default");
  assert.equal(res.ok, true);
  assert.deepEqual(JSON.parse(res.answer), ["ask", "--session", "default", "--json", "--", question]);
  assert.equal(fs.existsSync(marker), false);
});

test("the environment is minimal", async () => {
  const res = await new CosRunner(echo).ask("hi", "default");
  assert.deepEqual(res.env.filter((k) => k !== "__CF_USER_TEXT_ENCODING"), ["HOME", "LANG", "PATH"]);
  assert.deepEqual(Object.keys(minimalEnv()).sort(), ["HOME", "LANG", "PATH"]);
});

test("history arrays become a turns envelope", async () => {
  const res = await new CosRunner(echo).history("default");
  assert.equal(res.ok, true);
  assert.equal(res.turns.length, 1);
});

test("invalid input never runs cos", async () => {
  const res = await new CosRunner(path.join(dir, "does-not-run")).ask("hi", "../x");
  assert.equal(res.ok, false);
  assert.equal(res.error_kind, "setup"); // missing path is checked first
  const res2 = await new CosRunner(echo).ask("x".repeat(4001), "default");
  assert.deepEqual([res2.ok, res2.error_kind], [false, "usage"]);
});

test("missing cos and desktop.json errors are setup errors", async () => {
  const res = await new CosRunner(path.join(dir, "missing")).status();
  assert.deepEqual([res.ok, res.error_kind], [false, "setup"]);
  assert.match(res.error, /not found/);
  const res2 = await new CosRunner(echo, "desktop.json is not valid JSON").status();
  assert.deepEqual([res2.ok, res2.error_kind], [false, "setup"]);
});

test("unparseable output becomes an internal error", async () => {
  const garbage = fakeCos("garbage-cos", `console.log("Traceback (most recent call last): boom"); process.exit(1);`);
  const res = await new CosRunner(garbage).ask("hi", "default");
  assert.deepEqual(res, { ok: false, error_kind: "internal", error: "Chief returned an unexpected response." });
});

test("cos error kinds pass through", async () => {
  const down = fakeCos("down-cos", `console.log(JSON.stringify({ ok: false, error: "local model unavailable: refused", error_kind: "model_unavailable" })); process.exit(4);`);
  const res = await new CosRunner(down).ask("hi", "default");
  assert.deepEqual([res.ok, res.error_kind], [false, "model_unavailable"]);
  const odd = fakeCos("odd-cos", `console.log(JSON.stringify({ ok: false, error: "x", error_kind: "made-up" }));`);
  assert.equal((await new CosRunner(odd).ask("hi", "default")).error_kind, "internal");
});

test("stop and resume succeed on exit 0 and fail otherwise", async () => {
  const ok = fakeCos("ok-cos", `process.exit(0);`);
  assert.deepEqual(await new CosRunner(ok).stop(), { ok: true });
  const bad = fakeCos("bad-cos", `process.exit(2);`);
  const res = await new CosRunner(bad).resume();
  assert.deepEqual([res.ok, res.error_kind], [false, "internal"]);
});
