// "Search by Brave" shows on answers built from search results, and only on those.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const { searchAttribution } = require("../out/shared/attribution.js");

test("search answers with result links are attributed to Brave", () => {
  const summary = "Radar shows rain.\n\nSources:\n1. Test Result A — https://example.com/a";
  assert.equal(searchAttribution({ answer: summary, tools_used: ["web.search"] }), "Search by Brave");
  const raw = 'Web results for "x":\n1. Test Result A — snippet\n   https://example.com/a';
  assert.equal(searchAttribution({ answer: raw, tools_used: ["web.search"] }), "Search by Brave");
});

test("no attribution without results or without a search", () => {
  for (const answer of ["Search limit reached for today: 30/30. Resets tomorrow.",
    "Web search is unavailable: web search not set up: store a Brave Search API key in the macOS Keychain (see \"Web search\" in CHIEF-OF-STAFF.md)."]) {
    assert.equal(searchAttribution({ answer, tools_used: ["web.search"] }), null);
  }
  assert.equal(searchAttribution({ answer: "See https://example.com", tools_used: ["time.now"] }), null);
});
