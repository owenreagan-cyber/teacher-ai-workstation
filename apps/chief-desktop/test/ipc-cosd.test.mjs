import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const { validateAskInput, validateTaskId, validateCreateTask } = require("../out/main/ipc-cosd.js");

test("validateAskInput accepts default session", () => {
  const v = validateAskInput("hello", "default");
  assert.equal(v.sessionId, "default");
});

test("validateAskInput rejects oversized question", () => {
  assert.throws(() => validateAskInput("x".repeat(20_000), "default"));
});

test("validateTaskId requires hex id", () => {
  assert.throws(() => validateTaskId("not-a-task"));
  const id = "a".repeat(32);
  assert.equal(validateTaskId(id), id);
});

test("validateCreateTask bounds strings", () => {
  const v = validateCreateTask("t", "diagnostic", "key-1");
  assert.equal(v.kind, "diagnostic");
});
