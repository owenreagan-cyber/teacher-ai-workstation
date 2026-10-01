// buildArgs: exact argv per action, validation, and no shell strings. Runs against tsc output.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const { buildArgs, ArgsError, MAX_QUESTION_CHARS, SESSION_ID_RE } = require("../out/main/args.js");

test("every action produces the exact expected argv", () => {
  assert.deepEqual(buildArgs("ask", { question: "what time is it", sessionId: "default" }), [
    "ask", "--session", "default", "--json", "--", "what time is it",
  ]);
  assert.deepEqual(buildArgs("history", { sessionId: "default" }), ["history", "--session", "default", "--json"]);
  assert.deepEqual(buildArgs("brief"), ["brief", "--json"]);
  assert.deepEqual(buildArgs("status"), ["status", "--json"]);
  assert.deepEqual(buildArgs("stop"), ["stop", "chief-desktop"]);
  assert.deepEqual(buildArgs("resume"), ["resume"]);
});

test("question is trimmed and kept as one argv element after --", () => {
  const argv = buildArgs("ask", { question: "  --version  ", sessionId: "s-1" });
  assert.deepEqual(argv, ["ask", "--session", "s-1", "--json", "--", "--version"]);
});

test("invalid session ids are rejected", () => {
  for (const sessionId of ["../x", "A", "", "a".repeat(41), "a/b", "a b", "default\n", undefined, null, 7, ["default"]]) {
    assert.throws(() => buildArgs("ask", { question: "hi", sessionId }), ArgsError, String(sessionId));
    assert.throws(() => buildArgs("history", { sessionId }), ArgsError, String(sessionId));
  }
  assert.ok(SESSION_ID_RE.test("a".repeat(40)));
});

test("oversize, empty, non-text, and NUL questions are rejected", () => {
  assert.equal(MAX_QUESTION_CHARS, 4000);
  assert.doesNotThrow(() => buildArgs("ask", { question: "x".repeat(4000), sessionId: "default" }));
  for (const question of ["x".repeat(4001), "", "   ", undefined, 42, { toString: () => "hi" }, "a\0b"]) {
    assert.throws(() => buildArgs("ask", { question, sessionId: "default" }), ArgsError);
  }
});

test("unknown actions are rejected", () => {
  assert.throws(() => buildArgs("exec", {}), ArgsError);
  assert.throws(() => buildArgs("ask --json", {}), ArgsError);
});

test("no argument is ever a shell string", () => {
  const nasty = "what time is it; rm -rf ~ && $(touch /tmp/pwned) `id` | cat > out";
  const argv = buildArgs("ask", { question: nasty, sessionId: "default" });
  assert.ok(argv.every((a) => typeof a === "string"));
  assert.equal(argv.length, 6);
  assert.equal(argv[5], nasty, "the question is passed verbatim as a single argv element");
  for (const action of ["brief", "status", "stop", "resume"]) {
    for (const a of buildArgs(action)) assert.match(a, /^[a-z-]+$/);
  }
});
