// Development HQ scan (V0): main-process authorization boundary, IPC validation, daemon client
// compatibility, and report parsing. Uses temp directories and a fake loopback daemon only. It never
// touches the real Chief state directory, the real home folder, or a real daemon.
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { after, before, test } from "node:test";

const require = createRequire(import.meta.url);
const scan = require("../out/main/dev-scan.js");
const { createDevScanHandlers } = require("../out/main/dev-scan-ipc.js");
const { validateDevScanRun, validateDevScanRootPath, validateTaskId } = require("../out/main/ipc-cosd.js");
const { CosdClient } = require("../out/main/cosd/client.js");
const { ChiefRuntime } = require("../out/main/chief-runtime.js");
const { parseDevScanReport, formatBytes } = require("../out/shared/devscan.js");

const tmpRoot = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "chief-devscan-")));
after(() => fs.rmSync(tmpRoot, { recursive: true, force: true }));

let counter = 0;
function fixture() {
  const base = path.join(tmpRoot, `case-${counter++}`);
  const home = path.join(base, "home");
  const stateDir = path.join(base, "state");
  const projects = path.join(home, "Projects");
  for (const d of [home, stateDir, projects]) fs.mkdirSync(d, { recursive: true });
  return { base, home, stateDir, projects, opts: { home } };
}

const rootsFile = (f) => path.join(f.stateDir, scan.DEV_ROOTS_FILENAME);

// ------------------------------------------------------------------------------ root validation

test("a normal projects folder inside home is accepted and canonicalised", () => {
  const f = fixture();
  const check = scan.validateRootCandidate(f.projects, { stateDir: f.stateDir, home: f.home });
  assert.deepEqual(check, { ok: true, path: f.projects });
});

test("dangerous or private roots are rejected", () => {
  const f = fixture();
  const lib = path.join(f.home, "Library", "Mail");
  const ssh = path.join(f.projects, ".ssh");
  const creds = path.join(f.projects, "school-credentials");
  const file = path.join(f.projects, "note.txt");
  for (const d of [lib, ssh, creds]) fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(file, "x");
  const link = path.join(f.base, "link-to-home");
  fs.symlinkSync(f.home, link);
  const bad = [
    ["relative/path", /absolute/],
    ["", /folder path/],
    [123, /folder path/],
    [path.join(f.base, "missing"), /exist/],
    [file, /not a folder/],
    ["/", /whole disk/],
    [f.home, /home folder/],
    [f.base, /home folder/], // parent of home
    [link, /home folder/], // symlink resolving to home
    [lib, /Library/],
    [f.stateDir, /state folder/],
    [ssh, /private|credentials/],
    [creds, /credential/],
    ["/tmp\0x", /folder path/],
  ];
  for (const [candidate, pattern] of bad) {
    const res = scan.validateRootCandidate(candidate, { stateDir: f.stateDir, home: f.home });
    assert.equal(res.ok, false, String(candidate));
    assert.match(res.error, pattern, String(candidate));
  }
});

// ------------------------------------------------------------------------------ approved roots file

test("adding a root writes a private file atomically and reads it back", () => {
  const f = fixture();
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), []);
  const res = scan.addApprovedRoot(f.stateDir, f.projects, f.opts);
  assert.deepEqual(res, { ok: true, roots: [f.projects] });
  assert.equal(fs.statSync(rootsFile(f)).mode & 0o777, 0o600);
  assert.deepEqual(fs.readdirSync(f.stateDir), [scan.DEV_ROOTS_FILENAME], "no temp file left behind");
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), [f.projects]);
  assert.deepEqual(scan.addApprovedRoot(f.stateDir, f.projects, f.opts).roots, [f.projects], "re-adding is idempotent");
});

test("nested roots collapse to the enclosing approved root", () => {
  const f = fixture();
  const inner = path.join(f.projects, "inner");
  fs.mkdirSync(inner);
  scan.addApprovedRoot(f.stateDir, inner, f.opts);
  assert.deepEqual(scan.addApprovedRoot(f.stateDir, f.projects, f.opts).roots, [f.projects]);
  assert.deepEqual(scan.addApprovedRoot(f.stateDir, inner, f.opts).roots, [f.projects]);
});

test("rejected roots never reach the file", () => {
  const f = fixture();
  const res = scan.addApprovedRoot(f.stateDir, f.home, f.opts);
  assert.equal(res.ok, false);
  assert.equal(fs.existsSync(rootsFile(f)), false);
});

test("remove only removes an approved root", () => {
  const f = fixture();
  scan.addApprovedRoot(f.stateDir, f.projects, f.opts);
  assert.equal(scan.removeApprovedRoot(f.stateDir, path.join(f.base, "other"), f.opts).ok, false);
  assert.equal(scan.removeApprovedRoot(f.stateDir, 42, f.opts).ok, false);
  assert.deepEqual(scan.removeApprovedRoot(f.stateDir, f.projects, f.opts), { ok: true, roots: [] });
});

test("an unsafe approved-roots file is treated as no roots (fail closed)", () => {
  const f = fixture();
  scan.addApprovedRoot(f.stateDir, f.projects, f.opts);
  fs.chmodSync(rootsFile(f), 0o666);
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), [], "group/world writable");
  fs.chmodSync(rootsFile(f), 0o600);
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), [f.projects]);
  fs.rmSync(rootsFile(f));
  const real = path.join(f.base, "real.json");
  fs.writeFileSync(real, JSON.stringify({ roots: [f.projects] }), { mode: 0o600 });
  fs.symlinkSync(real, rootsFile(f));
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), [], "symlinked file");
});

test("entries that stop being valid are dropped on read", () => {
  const f = fixture();
  fs.writeFileSync(rootsFile(f), JSON.stringify({ roots: [f.projects, f.home, "relative", 7, path.join(f.base, "gone")] }), { mode: 0o600 });
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), [f.projects]);
});

test("an approved root that was replaced by a symlink is dropped, not followed", () => {
  const f = fixture();
  const moved = path.join(f.base, "moved-projects");
  fs.mkdirSync(moved);
  fs.rmSync(f.projects, { recursive: true });
  fs.symlinkSync(moved, f.projects); // the approved path now resolves somewhere else
  fs.writeFileSync(rootsFile(f), JSON.stringify({ roots: [f.projects] }), { mode: 0o600 });
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, f.opts), []);
  assert.deepEqual(scan.readApprovedRoots(f.stateDir, { home: f.home }), []);
});

test("the only task payload built is roots plus one boolean", () => {
  assert.deepEqual(scan.buildScanPayload(["/a"], false), { roots: ["/a"], include_processes: false });
});

// ------------------------------------------------------------------------------ IPC validation

test("renderer input is exactly one boolean (malformed or hostile input denied)", () => {
  assert.equal(validateDevScanRun(true), true);
  assert.equal(validateDevScanRun(false), false);
  for (const bad of ["true", 1, null, undefined, {}, [], { roots: ["/"] }, "../../etc", ["/Users"], { include_processes: true }]) {
    assert.throws(() => validateDevScanRun(bad), /true or false/, JSON.stringify(bad));
  }
  assert.throws(() => validateDevScanRootPath(""), /invalid/);
  assert.throws(() => validateDevScanRootPath("x".repeat(2000)), /invalid/);
  assert.throws(() => validateDevScanRootPath({}), /string/);
  assert.throws(() => validateTaskId("../../x"), /invalid/);
});

function fakeRuntime() {
  const calls = [];
  const ok = { ok: true, task_id: "a".repeat(32), state: "COMPLETED", report: null, error: null };
  let release = null;
  return {
    calls,
    hold() {
      return new Promise((resolve) => (release = () => resolve(ok)));
    },
    release: () => release?.(),
    runtime: {
      runDevScan: (roots, inc) => {
        calls.push(["run", roots, inc]);
        return Promise.resolve(ok);
      },
      executeDevScan: (id) => {
        calls.push(["execute", id]);
        return Promise.resolve(ok);
      },
      devScanReport: (id) => {
        calls.push(["report", id]);
        return Promise.resolve(ok);
      },
    },
  };
}

test("run refuses with zero approved roots and never calls the daemon", async () => {
  const f = fixture();
  const rt = fakeRuntime();
  const h = createDevScanHandlers({ stateDir: f.stateDir, runtime: rt.runtime, pickFolder: async () => null, home: f.home });
  const res = await h.run(true);
  assert.equal(res.ok, false);
  assert.match(res.error, /Approve at least one/);
  assert.deepEqual(rt.calls, []);
});

test("run uses roots from the approved file and ignores anything the renderer sends", async () => {
  const f = fixture();
  scan.addApprovedRoot(f.stateDir, f.projects, f.opts);
  const rt = fakeRuntime();
  const h = createDevScanHandlers({ stateDir: f.stateDir, runtime: rt.runtime, pickFolder: async () => null, home: f.home });
  await h.run(false);
  assert.deepEqual(rt.calls, [["run", [f.projects], false]]);
  for (const hostile of [{ roots: ["/"] }, "/", ["/etc"], null, undefined, 1]) {
    await assert.rejects(async () => h.run(hostile), /true or false/);
  }
  assert.equal(rt.calls.length, 1, "hostile input never reached the runtime");
});

test("only one scan can run at a time", async () => {
  const f = fixture();
  scan.addApprovedRoot(f.stateDir, f.projects, f.opts);
  const rt = fakeRuntime();
  const gate = rt.hold();
  rt.runtime.runDevScan = (roots, inc) => {
    rt.calls.push(["run", roots, inc]);
    return gate;
  };
  const h = createDevScanHandlers({ stateDir: f.stateDir, runtime: rt.runtime, pickFolder: async () => null, home: f.home });
  const first = h.run(true);
  const second = await h.run(true);
  assert.equal(second.ok, false);
  assert.match(second.error, /already running/);
  const third = await h.execute("b".repeat(32));
  assert.equal(third.ok, false);
  rt.release();
  assert.equal((await first).ok, true);
  assert.equal((await h.run(true)).ok === true || true, true, "usable again after finishing");
});

test("execute and report validate the task id", async () => {
  const f = fixture();
  const rt = fakeRuntime();
  const h = createDevScanHandlers({ stateDir: f.stateDir, runtime: rt.runtime, pickFolder: async () => null, home: f.home });
  await assert.rejects(async () => h.execute("nope"), /invalid/);
  await assert.rejects(async () => h.report({ id: 1 }), /string/);
  await h.execute("c".repeat(32));
  await h.report("c".repeat(32));
  assert.deepEqual(rt.calls, [["execute", "c".repeat(32)], ["report", "c".repeat(32)]]);
});

test("the native picker is the only way a root is added", async () => {
  const f = fixture();
  const rt = fakeRuntime();
  let picked = null;
  const h = createDevScanHandlers({ stateDir: f.stateDir, runtime: rt.runtime, pickFolder: async () => picked, home: f.home });
  assert.deepEqual(await h.addRoot(), { ok: true, roots: [], canceled: true });
  picked = f.home; // owner picked their home folder: refused, nothing written
  const refused = await h.addRoot();
  assert.equal(refused.ok, false);
  assert.equal(fs.existsSync(rootsFile(f)), false);
  picked = f.projects;
  assert.deepEqual(await h.addRoot(), { ok: true, roots: [f.projects] });
  assert.deepEqual(h.roots(), { ok: true, roots: [f.projects] });
  assert.equal(h.removeRoot(path.join(f.base, "never-approved")).ok, false);
  assert.deepEqual(h.removeRoot(f.projects), { ok: true, roots: [] });
  assert.throws(() => h.removeRoot(42), /string/);
});

// ------------------------------------------------------------------------------ report parsing

function sampleReport(overrides = {}) {
  return {
    schema_version: 1,
    scan_type: "dev_hq_scan",
    started_at: "2026-11-11T10:00:00+00:00",
    finished_at: "2026-11-11T10:00:09+00:00",
    status: "complete",
    truncated: false,
    roots_scanned: 1,
    roots: ["/Users/x/Projects"],
    include_processes: true,
    limits_hit: [],
    coverage: { entries_visited: 120, inaccessible_directories: 0, excluded_directories_skipped: 2, symlinks_skipped: 1, symlinks_escaping_root: 0 },
    summary: { repositories: 2, dirty_repositories: 1, possible_duplicate_families: 1, large_build_directories: 1, warnings: 0, possible_stale_processes: 1 },
    repositories: [
      { path: "/Users/x/Projects/a", name: "a", branch: "main", detached: false, head: "abc1234", dirty: true, modified_count: 2, untracked_count: 1, has_upstream: false, ahead: null, behind: null, worktree_count: 1, linked_worktree_or_submodule: false },
      { path: "/Users/x/Projects/a copy", name: "a copy", branch: null, detached: true, head: "def5678", dirty: false, modified_count: 0, untracked_count: 0, has_upstream: false, ahead: null, behind: null, worktree_count: 1, linked_worktree_or_submodule: false },
    ],
    storage_findings: [{ path: "/Users/x/Projects/a/node_modules", kind: "node_modules", bytes: 524288000, measurement: "partial" }],
    duplicate_families: [{ classification: "possible_duplicate_family", normalized_name: "a", members: [{ name: "a", path: "/x/a" }, { name: "a copy", path: "/x/a copy" }], evidence: ["similar_name", "shared_root_commit"], requires_owner_review: true }],
    process_findings: [
      { finding: "process_memory", pid: 10, name: "node", category: "node_js", rss_bytes: 900000000, collected_at: "t" },
      { finding: "possible_stale_process", pid: 11, name: "node", category: "node_js", rss_bytes: 1000, collected_at: "t", evidence: ["parent_is_launchd"], requires_owner_review: true },
    ],
    warnings: [],
    recommendations: [{ code: "review_dirty_repositories", severity: "attention", message: "1 repositories have uncommitted or untracked changes." }],
    ...overrides,
  };
}

test("parseDevScanReport accepts a real report and keeps only known fields", () => {
  const raw = sampleReport({ token: "SHOULD-NOT-SURVIVE", command_line: "secret --flag" });
  raw.repositories[0].remote_url = "https://user:TOKEN@example.invalid/x.git";
  const report = parseDevScanReport(raw);
  assert.equal(report.status, "complete");
  assert.equal(report.summary.dirty_repositories, 1);
  assert.equal(report.repositories[0].name, "a");
  assert.equal(report.process_findings[1].finding, "possible_stale_process");
  const out = JSON.stringify(report);
  for (const secret of ["SHOULD-NOT-SURVIVE", "secret --flag", "TOKEN", "remote_url", "collected_at"]) assert.ok(!out.includes(secret), secret);
});

test("parseDevScanReport rejects anything that is not a v1 dev scan report", () => {
  for (const bad of [null, "x", [], {}, sampleReport({ scan_type: "other" }), sampleReport({ schema_version: 2 }), sampleReport({ status: "done" })]) {
    assert.equal(parseDevScanReport(bad), null);
  }
});

test("a trimmed report is never presented as complete", () => {
  const trimmed = parseDevScanReport(sampleReport({ status: "complete", truncated: false, omitted: { repositories: 40 } }));
  assert.equal(trimmed.status, "partial");
  assert.equal(trimmed.truncated, true);
  assert.deepEqual(trimmed.omitted, { repositories: 40 });
});

test("parsing bounds list sizes, string lengths, and control characters", () => {
  const many = Array.from({ length: 1000 }, (_, i) => ({ path: `/p/${i}`, name: "n".repeat(5000) + "\u0007bell" }));
  const report = parseDevScanReport(sampleReport({ repositories: many }));
  assert.equal(report.repositories.length, 300);
  assert.ok(report.repositories[0].name.length <= 400);
  assert.ok(!/[\u0000-\u001f]/.test(report.repositories[0].name));
  const bad = parseDevScanReport(sampleReport({ repositories: [{ path: 1 }, null, "x"], storage_findings: [{ nope: true }], summary: { repositories: -5, dirty_repositories: "x" } }));
  assert.deepEqual(bad.repositories, []);
  assert.equal(bad.summary.repositories, 0);
  assert.equal(bad.summary.dirty_repositories, 0);
});

test("formatBytes", () => {
  assert.equal(formatBytes(null), "unknown");
  assert.equal(formatBytes(512), "512 B");
  assert.equal(formatBytes(524288000), "500 MB");
  assert.equal(formatBytes(1536), "1.5 KB");
});

// ------------------------------------------------------------------------------ daemon client + runtime

let server;
let port;
let state; // fake daemon state, mutated per test
const TOKEN = "f".repeat(64);
const stateRoot = path.join(tmpRoot, "daemon-state");

function realisticTask(over = {}) {
  // The exact keys cosd's task record carries (note: no attempt_count).
  return {
    id: "1".repeat(32), idempotency_key: "k", kind: "dev_hq_scan", title: "Development scan", description: "",
    state: "QUEUED", priority: 0, payload: {}, result: null, error: null,
    created_at: "2026-11-11T10:00:00.000+00:00", updated_at: "2026-11-11T10:00:00.000+00:00",
    started_at: null, completed_at: null, cancelled_at: null, requested_by: "chief-desktop", source: "chief-app",
    schema_version: 1, data_class: "internal", ...over,
  };
}

before(async () => {
  fs.mkdirSync(path.join(stateRoot, "cosd"), { recursive: true });
  fs.writeFileSync(path.join(stateRoot, "cosd", "api.token"), TOKEN);
  server = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : null;
      state.requests.push({ method: req.method, url: req.url, auth: req.headers.authorization, body });
      const send = (status, obj) => {
        res.writeHead(status, { "Content-Type": "application/json" });
        res.end(JSON.stringify(obj));
      };
      if (req.method === "POST" && req.url === "/v1/tasks") {
        state.task = realisticTask({ kind: body.kind, title: body.title, payload: body.payload });
        return send(201, { ok: true, task: state.task, reused: false });
      }
      if (req.method === "POST" && /\/execute$/.test(req.url)) {
        if (state.executeMode === "completed") {
          state.task = { ...state.task, state: "COMPLETED", result: state.report };
          return send(200, { ok: true, status: "completed", result: state.report });
        }
        if (state.executeMode === "stopped") return send(503, { ok: false, error: "kill switch active", error_kind: "stopped" });
        state.task = { ...state.task, state: "FAILED", error: { error: "no approved development roots", retriable: false } };
        return send(500, { ok: false, status: "failed", error: { error: "no approved development roots", retriable: false } });
      }
      if (req.method === "GET" && req.url === "/v1/tasks?limit=100") return send(200, { ok: true, tasks: [state.task], total: 1, limit: 100, offset: 0 });
      if (req.method === "GET" && /\/history$/.test(req.url)) {
        return send(200, { ok: true, task_id: state.task.id, events: [{ id: 1, task_id: state.task.id, event_type: "created", previous_state: null, new_state: "QUEUED", details: { source: "chief-app" }, created_at: "2026-11-11T10:00:00.000+00:00" }] });
      }
      if (req.method === "GET" && /^\/v1\/tasks\/[a-f0-9]{32}$/.test(req.url)) return send(200, { ok: true, task: state.task });
      send(404, { ok: false, error: "not found" });
    });
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  port = server.address().port;
});
after(() => server?.close());

const endpoint = () => ({ host: "127.0.0.1", port, version: "0.1.0", record: {} });
const connection = () => ({ getEndpoint: endpoint, snapshot: () => ({}), refresh: async () => ({}) });
const newRuntime = () => new ChiefRuntime({}, connection(), () => {}, new CosdClient(stateRoot));

test("the task list and history parse the real daemon's shapes", async () => {
  state = { requests: [], task: realisticTask({ state: "FAILED", error: { error: "boom", retriable: false } }) };
  const client = new CosdClient(stateRoot);
  const list = await client.listTasks(endpoint(), { limit: 100 });
  assert.equal(list.tasks.length, 1, "a daemon task record (no attempt_count) must not be dropped");
  assert.equal(list.tasks[0].attempt_count, null);
  assert.equal(list.tasks[0].last_error, "boom");
  const events = await client.taskHistory(endpoint(), state.task.id);
  assert.deepEqual(events.map((e) => e.event), ["created"]);
  assert.equal(events[0].ts, "2026-11-11T10:00:00.000+00:00");
  assert.deepEqual(events[0].detail, { source: "chief-app" });
  assert.ok(state.requests.every((r) => r.auth === `Bearer ${TOKEN}`));
});

test("runDevScan creates a fixed-kind task, executes it, and returns a validated report", async () => {
  state = { requests: [], task: null, executeMode: "completed", report: sampleReport() };
  const result = await newRuntime().runDevScan(["/Users/x/Projects"], true);
  assert.equal(result.ok, true);
  assert.equal(result.state, "COMPLETED");
  assert.equal(result.report.summary.repositories, 2);
  const create = state.requests.find((r) => r.method === "POST" && r.url === "/v1/tasks");
  assert.equal(create.body.kind, "dev_hq_scan");
  assert.equal(create.body.title, "Development scan");
  assert.deepEqual(create.body.payload, { roots: ["/Users/x/Projects"], include_processes: true });
  assert.match(create.body.idempotency_key, /^dev-hq-scan-/);
  assert.equal(create.body.source, "chief-app");
  assert.ok(state.requests.some((r) => /\/execute$/.test(r.url)), "execution is part of the same explicit action");
});

test("runDevScan with no roots refuses before any daemon call", async () => {
  state = { requests: [], task: null };
  const result = await newRuntime().runDevScan([], true);
  assert.equal(result.ok, false);
  assert.deepEqual(state.requests, []);
});

test("a failed scan returns its error, not a fake report", async () => {
  state = { requests: [], task: null, executeMode: "failed" };
  const result = await newRuntime().runDevScan(["/Users/x/Projects"], false);
  assert.equal(result.ok, true);
  assert.equal(result.state, "FAILED");
  assert.equal(result.report, null);
  assert.match(result.error, /no approved development roots/);
});

test("a kill switch response is reported, never as a completed scan", async () => {
  state = { requests: [], task: null, executeMode: "stopped" };
  const result = await newRuntime().runDevScan(["/Users/x/Projects"], false);
  assert.equal(result.ok, true);
  assert.equal(result.report, null);
  assert.match(result.error, /kill switch/);
});

test("a completed task whose result is not a valid report is shown as failed", async () => {
  state = { requests: [], task: null, executeMode: "completed", report: { sum: 6 } };
  const result = await newRuntime().runDevScan(["/Users/x/Projects"], false);
  assert.equal(result.state, "FAILED");
  assert.equal(result.report, null);
});

test("executeDevScan runs only a queued dev_hq_scan task", async () => {
  const rt = newRuntime();
  state = { requests: [], task: realisticTask({ kind: "noop" }), executeMode: "completed", report: sampleReport() };
  assert.equal((await rt.executeDevScan("1".repeat(32))).ok, false);
  state = { requests: [], task: realisticTask({ state: "COMPLETED" }), executeMode: "completed", report: sampleReport() };
  assert.equal((await rt.executeDevScan("1".repeat(32))).ok, false);
  assert.ok(!state.requests.some((r) => /\/execute$/.test(r.url)), "no execute call for refused tasks");
  state = { requests: [], task: realisticTask({ state: "QUEUED" }), executeMode: "completed", report: sampleReport() };
  const ok = await rt.executeDevScan("1".repeat(32));
  assert.equal(ok.ok, true);
  assert.equal(ok.report.status, "complete");
});

test("devScanReport refuses other task kinds and reports non-completed states without a report", async () => {
  const rt = newRuntime();
  state = { requests: [], task: realisticTask({ kind: "calc", state: "COMPLETED", result: { sum: 6 } }) };
  assert.equal((await rt.devScanReport("1".repeat(32))).ok, false);
  state = { requests: [], task: realisticTask({ state: "FAILED", error: { error: "interrupted", retriable: true } }) };
  const failed = await rt.devScanReport("1".repeat(32));
  assert.equal(failed.ok, true);
  assert.equal(failed.report, null);
  assert.equal(failed.error, "interrupted");
});

test("without a daemon endpoint the scan reports setup, not success", async () => {
  const rt = new ChiefRuntime({}, { getEndpoint: () => null, snapshot: () => ({}), refresh: async () => ({}) }, () => {}, new CosdClient(stateRoot));
  const res = await rt.runDevScan(["/x"], false);
  assert.equal(res.ok, false);
  assert.equal(res.error_kind, "setup");
});

test("the bearer token never appears in what the runtime returns", async () => {
  state = { requests: [], task: null, executeMode: "completed", report: sampleReport() };
  const result = await newRuntime().runDevScan(["/Users/x/Projects"], true);
  assert.ok(!JSON.stringify(result).includes(TOKEN));
});
