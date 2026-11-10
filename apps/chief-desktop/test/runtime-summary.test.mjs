// Runtime presentation rules: state, provenance, and the restart warning.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const { runtimeSummary } = require("../out-test/shared/runtime.js");

test("healthy runtime reports state, version, commit and python", () => {
  const out = runtimeSummary({
    cosd_version: "0.1.0",
    state: "HEALTHY",
    state_reasons: [],
    provenance: { loaded_commit: "abc123", python: "3.12.13", environment: "venv" },
    checkout: { restart_required: false, current_commit: "abc123" },
  });
  assert.equal(out.state, "HEALTHY");
  assert.equal(out.version, "0.1.0");
  assert.equal(out.commit, "abc123");
  assert.equal(out.python, "3.12.13");
  assert.equal(out.warning, null);
});

test("a newer checkout produces an explicit restart warning", () => {
  const out = runtimeSummary({
    state: "DEGRADED",
    provenance: { loaded_commit: "aaa111", python: "3.12.13" },
    checkout: { restart_required: true, current_commit: "bbb222" },
  });
  assert.equal(out.state, "DEGRADED");
  assert.match(out.warning, /Restart required/);
  assert.match(out.warning, /aaa111/);
  assert.match(out.warning, /bbb222/);
});

test("degraded reasons are surfaced when there is no restart warning", () => {
  const out = runtimeSummary({
    state: "DEGRADED",
    state_reasons: ["execution queue is paused"],
    provenance: { loaded_commit: "abc123" },
    checkout: { restart_required: false },
  });
  assert.equal(out.warning, "execution queue is paused");
});

test("blocked state is reported without inventing provenance", () => {
  const out = runtimeSummary({
    state: "BLOCKED",
    state_reasons: ["kill switch engaged"],
  });
  assert.equal(out.state, "BLOCKED");
  assert.equal(out.commit, "unknown");
  assert.equal(out.python, "unknown");
  assert.equal(out.warning, "kill switch engaged");
});

test("unknown or missing state never reads as healthy", () => {
  for (const body of [null, {}, { state: "SOMETHING" }]) {
    assert.equal(runtimeSummary(body).state, "UNKNOWN");
  }
});

test("restart_required null (provenance unavailable) shows no false warning", () => {
  const out = runtimeSummary({
    state: "HEALTHY",
    provenance: { loaded_commit: null },
    checkout: { restart_required: null, current_commit: null },
  });
  assert.equal(out.warning, null);
});
