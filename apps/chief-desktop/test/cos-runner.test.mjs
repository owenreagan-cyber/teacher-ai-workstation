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

// Echoes its argv (as the answer) and environment keys (as notices) back as an ask-shaped answer.
const echo = fakeCos(
  "echo-cos",
  `const a = process.argv.slice(2);
   if (a[0] === "history") { console.log(JSON.stringify([{ ts: "t", question: "q", answer: "a", tools_used: [], fast_path: true, model: null, notices: [], total_ms: 1 }])); process.exit(0); }
   console.log(JSON.stringify({ ok: true, answer: JSON.stringify(a), tools_used: [], model: null, fast_path: false,
     session_id: "default", ts: "t", total_ms: 1, notices: Object.keys(process.env).sort() }));`,
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
  assert.deepEqual(res.notices.filter((k) => k !== "__CF_USER_TEXT_ENCODING"), ["HOME", "LANG", "PATH"]);
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

// M15A-002: the full Turn shape is validated before anything reaches the renderer.
const VALID = { ts: "t", question: "q", answer: "a", tools_used: ["time.now"], fast_path: false, model: "m", notices: [], total_ms: 5 };
const { notices: _dropped, ...MISSING_NOTICES } = VALID;
const MALFORMED = {
  "malformed tools_used": { ...VALID, tools_used: "time.now" },
  "tools_used item not a string": { ...VALID, tools_used: ["time.now", 3] },
  "missing notices": MISSING_NOTICES,
  "string fast_path": { ...VALID, fast_path: "false" },
  "negative total_ms": { ...VALID, total_ms: -1 },
  "string total_ms": { ...VALID, total_ms: "5" },
  "fractional total_ms": { ...VALID, total_ms: 1.5 },
  "numeric model": { ...VALID, model: 7 },
  "null answer": { ...VALID, answer: null },
  "non-object turn": "not a turn",
};
const KEYS = ["answer", "fast_path", "model", "notices", "question", "tools_used", "total_ms", "ts"];

test("history drops each malformed turn and keeps the valid ones", async () => {
  for (const [name, bad] of Object.entries(MALFORMED)) {
    const fake = fakeCos(`hist-${name.replace(/\W+/g, "-")}`,
      `console.log(JSON.stringify(${JSON.stringify([{ ...VALID, question: "q1" }, bad, { ...VALID, question: "q2", extra: "x" }])}));`);
    const res = await new CosRunner(fake).history("default");
    assert.equal(res.ok, true, name);
    assert.deepEqual(res.turns.map((t) => t.question), ["q1", "q2"], name);
    for (const t of res.turns) assert.deepEqual(Object.keys(t).sort(), KEYS, `${name}: only known fields pass`);
  }
});

test("history with a non-JSON line from cos is an internal error, not a partial array", async () => {
  const fake = fakeCos("hist-nonjson", `console.log("[" + JSON.stringify(${JSON.stringify(VALID)}) + ",\\nnot json]");`);
  const res = await new CosRunner(fake).history("default");
  assert.deepEqual([res.ok, res.error_kind], [false, "internal"]);
});

test("ask with any malformed turn field is rejected, never passed on", async () => {
  for (const [name, bad] of Object.entries(MALFORMED)) {
    if (typeof bad !== "object") continue;
    const { question: _q, ...fields } = bad;
    const fake = fakeCos(`ask-${name.replace(/\W+/g, "-")}`,
      `console.log(JSON.stringify(${JSON.stringify({ ok: true, ...fields, session_id: "default" })}));`);
    const res = await new CosRunner(fake).ask("hi", "default");
    assert.deepEqual([res.ok, res.error_kind], [false, "internal"], name);
  }
  const badSession = fakeCos("ask-bad-session",
    `console.log(JSON.stringify(${JSON.stringify({ ok: true, ...VALID, session_id: 5 })}));`);
  assert.equal((await new CosRunner(badSession).ask("hi", "default")).ok, false);
});

test("a valid ask passes only known fields", async () => {
  const { question: _q, ...fields } = VALID;
  const fake = fakeCos("ask-valid",
    `console.log(JSON.stringify(${JSON.stringify({ ok: true, ...fields, session_id: "default", injected: "<b>x</b>" })}));`);
  const res = await new CosRunner(fake).ask("hi", "default");
  assert.equal(res.ok, true);
  assert.deepEqual(Object.keys(res).sort(), ["answer", "fast_path", "model", "notices", "ok", "session_id", "tools_used", "total_ms", "ts"]);
});
