// Response blocks in the desktop shell: validation (unknown types rejected), no URL ever reaching
// the renderer, links opened only by id through the main process's table, and suggestion buttons
// that send text only. Fake cos executables, plus the real cos in fixture mode (synthetic data).
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { CosRunner } = require("../out/main/cos.js");
const { ResourceTable, openLink } = require("../out/main/resources.js");
const { toBlock, toBlocks, toResources, stripUrls, suggestionMessage, BLOCK_TYPES } = require("../out/shared/blocks.js");
const { searchAttribution } = require("../out/shared/attribution.js");

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-blocks-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function fakeCos(name, body) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, `#!${process.execPath}\n${body}\n`, { mode: 0o700 });
  return file;
}

const ID_A = "lnk-0123456789abcdef";
const ID_B = "lnk-fedcba9876543210";
const BLOCKS = [
  { type: "text", text: "The Rangers play Friday." },
  { type: "searched", query: "when do the ny rangers play" },
  { type: "sources", items: [{ title: "Result A", site: "example.com", link_id: ID_A }, { title: "Result B", site: "example.org", link_id: null }] },
  { type: "suggestions", items: [{ label: "Tomorrow", message: "weather tomorrow" }, { label: "Hourly", message: "hourly forecast" }] },
  { type: "notice", level: "warning", text: "The local model is unavailable." },
];

test("valid blocks pass with exactly their fields", () => {
  assert.deepEqual(toBlocks(BLOCKS), BLOCKS);
  const extra = toBlock({ type: "text", text: "x", html: "<b>x</b>" });
  assert.deepEqual(extra, { type: "text", text: "x" });
  assert.deepEqual([...BLOCK_TYPES].sort(), ["forecast_daily", "forecast_hourly", "notice", "searched", "sources", "suggestions", "text", "weather_now"]);
});

test("unknown types and bad fields are rejected; one bad block never blanks the rest", () => {
  const bad = [
    { type: "html", html: "<script>x</script>" },
    { type: "link", url: "https://example.com" },
    { type: "text", text: "see https://example.com" },
    { type: "text", text: "visit www.example.com" },
    { type: "sources", items: [{ title: "A", site: "s", link_id: "https://example.com" }] },
    { type: "suggestions", items: [{ label: "One", message: "x" }] },
    { type: "suggestions", items: [{ label: "L", message: "javascript:alert(1)" }, { label: "M", message: "ok" }] },
    { type: "notice", level: "error", text: "x" },
    { type: "weather_now", place: "Sims, NC" },
    "text",
    null,
  ];
  for (const b of bad) assert.equal(toBlock(b), null, JSON.stringify(b));
  assert.deepEqual(toBlocks([...bad, BLOCKS[0]]), [BLOCKS[0]]);
  assert.deepEqual(toBlocks("not a list"), []);
});

test("resources: only well-formed ids with https URLs", () => {
  assert.deepEqual(toResources([{ id: ID_A, url: "https://example.com/a" }, { id: "x", url: "https://example.com" },
    { id: ID_B, url: "http://example.org/b" }, { id: ID_B, url: "javascript:alert(1)" }, { id: ID_B, url: "https://user:pw@example.org/" }]),
  [{ id: ID_A, url: "https://example.com/a" }]);
});

test("the renderer receives no URLs; the main process receives the resources", async () => {
  const payload = {
    ok: true, ts: "t", session_id: "default", total_ms: 5, model: "m", fast_path: false, tools_used: ["web.search"],
    answer: "The Rangers play Friday.\n\nSearched: x\n\nSources:\n1. Result A — https://example.com/a\n2. Result B — http://example.org/b",
    notices: ["See https://example.net/n for details."], blocks: BLOCKS,
    resources: [{ id: ID_A, url: "https://example.com/a" }],
  };
  const got = [];
  const fake = fakeCos("ask-urls", `console.log(JSON.stringify(${JSON.stringify(payload)}));`);
  const res = await new CosRunner(fake, null, (r) => got.push(...r)).ask("when do the ny rangers play?", "default");
  assert.equal(res.ok, true);
  assert.doesNotMatch(JSON.stringify(res), /https?:|example\.(com|org|net)\/|resources/);
  assert.deepEqual(res.blocks, BLOCKS);
  assert.match(res.answer, /^The Rangers play Friday\.\n\nSearched: x\n\nSources:\n1\. Result A\n2\. Result B$/);
  assert.deepEqual(got, [{ id: ID_A, url: "https://example.com/a" }]);
  assert.equal(searchAttribution(res), "Search by Brave");

  const turn = { ...payload, question: "search https://example.com/q" };
  const hist = fakeCos("hist-urls", `console.log(JSON.stringify([${JSON.stringify(turn)}]));`);
  const got2 = [];
  const h = await new CosRunner(hist, null, (r) => got2.push(...r)).history("default");
  assert.doesNotMatch(JSON.stringify(h), /https?:/);
  assert.deepEqual(got2, [{ id: ID_A, url: "https://example.com/a" }]);
});

test("openLink opens only a known id, only https, through the table", async () => {
  const table = new ResourceTable();
  table.add([{ id: ID_A, url: "https://example.com/a" }, { id: ID_B, url: "http://example.org/b" }]);
  const opened = [];
  const open = async (url) => { opened.push(url); };
  assert.deepEqual(await openLink(table, ID_A, open), { ok: true });
  for (const id of [ID_B, "lnk-0000000000000000", "https://example.com/a", 42, null, `${ID_A} `]) {
    const res = await openLink(table, id, open);
    assert.equal(res.ok, false, String(id));
  }
  assert.deepEqual(opened, ["https://example.com/a"]);
  const failing = await openLink(table, ID_A, async () => { throw new Error("no browser"); });
  assert.deepEqual([failing.ok, failing.error_kind], [false, "internal"]);
});

test("a suggestion button sends exactly its message text", () => {
  assert.equal(suggestionMessage(BLOCKS[3], 0), "weather tomorrow");
  assert.equal(suggestionMessage(BLOCKS[3], 1), "hourly forecast");
  assert.equal(suggestionMessage(BLOCKS[3], 5), null);
  assert.equal(suggestionMessage(BLOCKS[0], 0), null);
});

test("stripUrls removes every URL form", () => {
  assert.equal(stripUrls("a https://x.example/p b"), "a b");
  assert.equal(stripUrls("1. Title — https://x.example/p"), "1. Title");
  assert.equal(stripUrls("see www.example.com/a."), "see");
});

test("the real cos in fixture mode produces blocks this validator accepts unchanged", async () => {
  const state = path.join(dir, "cos-state");
  const wrapper = fakeCos("fixture-cos", `
    const { execFileSync } = require("node:child_process");
    const out = execFileSync(${JSON.stringify(path.join(REPO, "bin", "cos"))}, process.argv.slice(2), {
      env: { ...process.env, COS_STATE_DIR: ${JSON.stringify(state)},
             COS_FIXTURE_DIR: ${JSON.stringify(path.join(REPO, "evals", "fixtures", "default"))}, TZ: "America/New_York" },
      encoding: "utf8" });
    process.stdout.write(out);`);
  for (const q of ["weather", "5 day forecast", "hourly forecast", "what can you do?", "weather in raleigh"]) {
    const res = await new CosRunner(wrapper).ask(q, "fixture");
    assert.equal(res.ok, true, q);
    const raw = JSON.parse(require("node:child_process").execFileSync(wrapper, ["ask", "--json", "--", q], { encoding: "utf8" }));
    assert.deepEqual(res.blocks, raw.blocks, q); // nothing dropped: both validators agree
    assert.ok(res.blocks.length >= 2, q);
  }
});
