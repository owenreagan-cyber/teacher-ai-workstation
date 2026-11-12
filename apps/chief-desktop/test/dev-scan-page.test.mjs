// Development scan UI: rendered with static markup against injected state and a fake bridge.
// This checks what the owner would read; it is not a claim that the packaged app was visually checked.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const { DevScanPanel, DevScanReportView } = require("../out-test/renderer/DevScan.js");
const { TaskCenter } = require("../out-test/renderer/Tasks.js");
const { parseDevScanReport } = require("../out-test/shared/devscan.js");

const h = React.createElement;
const text = (html) => html.replace(/<[^>]+>/g, " ").replace(/&#x27;/g, "'").replace(/&amp;/g, "&").replace(/\s+/g, " ");
const bridge = {
  devScanRoots: async () => ({ ok: true, roots: [] }),
  devScanAddRoot: async () => ({ ok: true, roots: [] }),
  devScanRemoveRoot: async () => ({ ok: true, roots: [] }),
  devScanRun: async () => ({ ok: false, error: "x", error_kind: "usage" }),
};

function report(over = {}) {
  return parseDevScanReport({
    schema_version: 1, scan_type: "dev_hq_scan", started_at: "2026-11-11T10:00:00+00:00", finished_at: "2026-11-11T10:00:09+00:00",
    status: "complete", truncated: false, roots_scanned: 2, roots: ["/p"], include_processes: true, limits_hit: [],
    coverage: { entries_visited: 321, inaccessible_directories: 0, excluded_directories_skipped: 3, symlinks_skipped: 4 },
    summary: { repositories: 12, dirty_repositories: 2, possible_duplicate_families: 1, large_build_directories: 1, warnings: 1, possible_stale_processes: 1 },
    repositories: [
      { path: "/p/alpha", name: "alpha", branch: "main", detached: false, head: "abc1234", dirty: true, modified_count: 3, untracked_count: 1, has_upstream: false },
      { path: "/p/beta", name: "beta", branch: null, detached: true, head: "def5678", dirty: true, modified_count: 0, untracked_count: 2, has_upstream: true },
      { path: "/p/clean", name: "clean", branch: "main", detached: false, head: "0000000", dirty: false, modified_count: 0, untracked_count: 0, has_upstream: false },
    ],
    storage_findings: [{ path: "/p/alpha/node_modules", kind: "node_modules", bytes: 524288000, measurement: "partial" }],
    duplicate_families: [{ classification: "possible_duplicate_family", normalized_name: "grade-book", members: [{ name: "grade-book", path: "/p/g" }, { name: "grade-book copy", path: "/p/g2" }], evidence: ["similar_name", "shared_root_commit"] }],
    process_findings: [
      { finding: "process_memory", pid: 10, name: "ollama", category: "ollama", rss_bytes: 7340032000 },
      { finding: "possible_stale_process", pid: 11, name: "node", category: "node_js", rss_bytes: 1048576, evidence: ["parent_is_launchd", "running_over_12h"] },
    ],
    warnings: [{ code: "x", message: "2 repositories had incomplete Git metadata" }],
    recommendations: [
      { code: "review_dirty_repositories", severity: "attention", message: "2 repositories have uncommitted or untracked changes. Review each one." },
      { code: "review_possible_duplicates", severity: "attention", message: "1 groups of similarly named repositories may be duplicates." },
    ],
    ...over,
  });
}

test("the panel explains scope and approved roots before any scan runs", () => {
  const t = text(renderToStaticMarkup(h(DevScanPanel, { bridge, initialRoots: ["/Users/x/Projects", "/Users/x/Developer"] })));
  for (const want of [
    "Development scan", "read-only", "never opens file contents", "runs only when you press the button",
    "Approved folders", "/Users/x/Projects", "/Users/x/Developer", "Approve a folder", "Remove",
    "process and memory snapshot", "never command lines",
    "2 approved folders", "5 folder levels deep", "40,000 files and folders", "150 repositories", "about 40 seconds",
    "Private folders (keys, credentials, Library) are always skipped", "Run Development Scan",
  ]) {
    assert.ok(t.includes(want), want);
  }
});

test("with no approved folders the run button is disabled and says why", () => {
  const html = renderToStaticMarkup(h(DevScanPanel, { bridge, initialRoots: [] }));
  assert.match(text(html), /No folders approved yet/);
  assert.match(html, /<button[^>]*disabled=""[^>]*>Run Development Scan<\/button>/);
});

test("while scanning, the button is disabled and shows progress text", () => {
  const html = renderToStaticMarkup(h(DevScanPanel, { bridge, initialRoots: ["/p"], initialRunning: true }));
  assert.match(html, /<button[^>]*disabled=""[^>]*>Scanning…<\/button>/);
  assert.match(text(html), /up to a minute/);
});

test("nothing starts automatically: rendering the panel never calls the bridge", () => {
  const calls = [];
  const spy = Object.fromEntries(Object.keys(bridge).map((k) => [k, (...a) => (calls.push(k), bridge[k](...a))]));
  renderToStaticMarkup(h(DevScanPanel, { bridge: spy, initialRoots: ["/p"] }));
  assert.deepEqual(calls, []);
});

test("a failed scan shows the error and points to retry", () => {
  const t = text(renderToStaticMarkup(h(DevScanPanel, { bridge, initialRoots: ["/p"], initialResult: { ok: true, task_id: "a".repeat(32), state: "FAILED", report: null, error: "kill switch active" } })));
  assert.match(t, /The scan failed: kill switch active/);
  assert.match(t, /retry it from the task list/);
});

test("the report shows status, counts, next steps, dirty repos, big folders, duplicates, and processes", () => {
  const t = text(renderToStaticMarkup(h(DevScanReportView, { report: report() })));
  for (const want of [
    "Scan complete", "Started 2026-11-11 10:00 UTC", "finished 2026-11-11 10:00 UTC", "2 approved folders",
    "Repositories", "12", "With uncommitted changes", "Possible duplicate groups", "Large build folders (100 MB+)", "Warnings",
    "Suggested next steps", "Review each one.",
    "Repositories with uncommitted changes", "alpha", "main", "3 modified", "1 untracked", "no upstream", "detached HEAD", "beta",
    "Largest build and dependency folders", "500 MB", "at least (partial)", "node modules", "/p/alpha/node_modules",
    "Possible duplicate project groups: needs your review", "grade-book copy", "shared root commit",
    "Memory use by development tools", "ollama", "6.8 GB", "Possible stale processes (not confirmed)", "Chief will not stop it",
    "2 repositories had incomplete Git metadata",
    "Chief did not change any project, process, or file", "Checked 321 items", "skipped 3 private folders and 4 links",
  ]) {
    assert.ok(t.includes(want), want);
  }
  assert.ok(!t.includes("clean"), "clean repositories are not listed as problems");
  assert.ok(!/orphan/i.test(t), "never claims a confirmed orphan");
});

test("repositories Chief refused to inspect are listed by name with the reason", () => {
  const t = text(
    renderToStaticMarkup(
      h(DevScanReportView, {
        report: report({
          status: "partial",
          repositories: [
            {
              path: "/p/held",
              name: "held",
              branch: null,
              detached: false,
              head: null,
              dirty: null,
              modified_count: null,
              untracked_count: null,
              has_upstream: null,
              errors: ["not inspected: repository config defines filters or includes, which are not run during a scan"],
            },
            { path: "/p/zzz-inspected", name: "zzz-inspected", branch: "main", dirty: false, modified_count: 0, untracked_count: 0 },
          ],
        }),
      }),
    ),
  );
  assert.match(t, /Not inspected: needs your review/);
  assert.match(t, /held/);
  assert.match(t, /repository config defines filters or includes/);
  assert.match(t, /their status is unknown/);
  assert.ok(!t.includes("zzz-inspected"), "a repository that was inspected is not listed as refused");
});

test("a partial report says it is incomplete and why", () => {
  const t = text(renderToStaticMarkup(h(DevScanReportView, { report: report({ status: "partial", limits_hit: ["depth_limit", "deadline"], coverage: { entries_visited: 5, inaccessible_directories: 2, excluded_directories_skipped: 0, symlinks_skipped: 0 } }) })));
  assert.match(t, /Scan partial: results are incomplete/);
  assert.match(t, /folder depth limit; time limit; 2 folders could not be read/);
  assert.match(t, /Numbers below may be too low/);
  assert.ok(!t.includes("Scan complete"));
});

test("a trimmed report states what was left out and is never shown as complete", () => {
  const t = text(renderToStaticMarkup(h(DevScanReportView, { report: report({ status: "complete", omitted: { repositories: 40, storage_findings: 3 } }) })));
  assert.match(t, /Scan partial/);
  assert.match(t, /Not shown because of the report size limit: 40 repositories, 3 storage findings/);
  assert.ok(!t.includes("Scan complete"));
});

test("process sections are absent when processes were not requested", () => {
  const t = text(renderToStaticMarkup(h(DevScanReportView, { report: report({ include_processes: false, process_findings: [] }) })));
  assert.ok(!t.includes("Memory use by development tools"));
});

test("the existing Tasks page still renders its controls and now includes the scan panel", () => {
  globalThis.window = { chief: bridge };
  try {
    const t = text(renderToStaticMarkup(h(TaskCenter)));
    for (const want of ["Runtime:", "Retry connection", "All", "QUEUED", "RUNNING", "COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "New diagnostic task", "No tasks", "Run Development Scan", "Approved folders"]) {
      assert.ok(t.includes(want), want);
    }
  } finally {
    delete globalThis.window;
  }
});
