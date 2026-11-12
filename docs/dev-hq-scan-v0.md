# Development HQ scan (V0)

`dev_hq_scan` is Chief's first real `cosd` task handler. It is a bounded, read-only inventory of
development folders the owner has approved. It is not the full Development HQ product: there is no
scheduler, no second execution engine, and no new database. It reuses `cos`, `cosd`, the task
registry, and the Chief.app Tasks page.

**Chief coordinates. cosd tracks and executes. The owner controls.**

## What it reports

For each Git repository under an approved root: path, name, branch or detached HEAD, short revision,
dirty state with modified and untracked counts, worktree count (the primary worktree counts as one),
whether an upstream is configured, and ahead/behind when Git can tell without the network. A
repository with no upstream is normal, not an error; its ahead/behind is reported as unknown.

Also: build and dependency folders (`node_modules`, Python virtualenvs, `dist`/`build`/`out`/`target`
and similar) measured with caps, `possible_duplicate_family` groups, and an optional process and
memory snapshot. Findings are advisory text. Nothing is executed, moved, deleted, or stopped.

## Authority and scope

| Question | Answer |
|---|---|
| Who decides what may be scanned? | The owner, through a native folder picker in Chief.app. Code enforces it. No model decides scope. |
| Where is approval stored? | `dev_hq_roots.json` in the private Chief state directory (mode 0600, owner-only). Only Chief.app writes it. `cosd` only reads it, and refuses a file that is a symlink, not owned by the user, or group/world writable. |
| Can a task payload widen the scan? | No. A payload may list roots, but each must lie inside an approved root (checked after resolving symlinks). Unknown payload keys, relative paths, and non-list roots are rejected. Payload limits can only tighten the defaults. |
| Zero approved roots? | The task fails with "no approved development roots" and is not retryable until a root is approved. |
| What can the renderer send? | One boolean (include the process snapshot) or a task id. Never a path, task kind, limit, or command. |

Approval is re-checked at execution time (D-025), not only when the task is created. A stored root
that now resolves to a different location (for example the folder was replaced by a symlink) is
dropped with an `approved_root_moved` warning and must be approved again; Chief.app applies the same
rule when it lists roots. Approvals are paths, not repository lists: a repository that appears under
an approved root later (a clone, an extracted archive) is covered by the existing approval.

## Never inspected

Roots may not be `/`, the home folder or a parent of it, `~/Library`, `~/.Trash`, or anything
overlapping Chief's state directory. Inside an approved root these directory names are never
entered: `.ssh`, `.gnupg`, `.aws`, `.kube`, `.docker`, `.config`, `.npm`, `.claude`, `.cursor`,
`.local`, `.Trash`, `Keychains`, `ChiefOfStaff`, plus any name containing `credential`, `secret`,
`keychain`, `password`, `passwd`, `token(s)`, or `private key`. Symlinks seen while listing a
directory are never followed; a symlink that points outside its root is counted, not entered (see the
traversal race under Known limitations). Project file contents are never opened.

## Defaults (conservative, tightened but never raised by a payload)

| Limit | Default | Hard cap |
|---|---|---|
| Directory depth | 5 | 8 |
| Directory entries visited | 40,000 | 100,000 |
| Repositories | 150 | 300 |
| Wall-clock time | 40 s | 60 s |
| Per-Git-call timeout | 8 s | |
| Git output cap | 256 KiB | |
| Entries measured per build folder | 15,000 (120,000 total) | |
| Serialised result | 30,720 bytes (task-result limit minus headroom) | |

Hitting any limit makes the report `partial` and names the limit in `limits_hit`. When the result
would exceed the size limit, lists are trimmed from the tail with explicit `omitted` counts and the
report is marked `truncated` and `partial`. It is never silently cut while marked complete. Summary
counts always reflect totals, not just the entries that fit.

Measurements are labelled `exact`, `partial` (a lower bound), `bounded_estimate` (the `.git` folder
only, not the working tree), or `unavailable`.

## Git and subprocess safety

Git runs with an argument array and no shell, a minimal environment, `GIT_OPTIONAL_LOCKS=0`,
`--no-optional-locks`, and `GIT_TERMINAL_PROMPT=0`. Only `status`, `worktree list`, and (for duplicate
evidence) `rev-list --max-parents=0` are used on repositories. No `fetch`, `pull`, `push`, `prune`,
`gc`, `clean`, `reset`, `stash`, or `checkout`. Each child runs in its own session with a wall-clock
deadline and output cap; on timeout only that child's process group is terminated.

**Configuration that could make Git run a command or read elsewhere is neutralised or refused:**

* The user's global and system Git config is not loaded (`GIT_CONFIG_GLOBAL=/dev/null`,
  `GIT_CONFIG_NOSYSTEM=1`), and `core.attributesFile` is `/dev/null`. A filter defined globally
  (for example by git-lfs) therefore cannot be run by a repository's `.gitattributes`. So that dirty
  counts still match what the owner sees, the user's global ignore file (`core.excludesFile`, or
  `~/.config/git/ignore`) is passed back explicitly. That is the only global value read, and only as
  a path.
* `core.fsmonitor=false` is forced on the command line.
* A repository whose own config (the shared config, the linked git dir's config, or
  `config.worktree`) contains a `filter`, `include`, or `includeIf` section is **not handed to Git**.
  It is listed with `errors: ["not inspected: ..."]`, and the scan is marked `partial`. Git can run a
  configured clean filter while comparing a changed file, and an include can pull in more config.
* `--git-dir` and `--work-tree` are pinned to validated locations, so `core.worktree` (including a
  per-worktree `config.worktree`) cannot point Git at a tree outside the approved root. For a
  linked worktree or submodule the `.git` pointer file is read (first line only, 4 KiB cap), and the
  git dir and any `commondir` it names must lie inside a scanned root, or the repository is not
  inspected (`linked git directory is outside the approved roots`). A linked worktree whose main
  repository lives under a different, unscanned root is therefore reported as not inspected.

The scanner reads only these Git metadata files for that check: the `.git` pointer, `commondir`, and
the config files above. None of their values are stored or reported. The four filter and redirect
regression tests each first prove with stock Git that their fixture really is dangerous (a filter
marker file is created, or outside files are counted), so a passing test cannot be vacuous.

**Requires Git 2.32 or newer.** `GIT_CONFIG_GLOBAL` (the variable that suppresses the user's global
config) was added in Git 2.32. On an older Git the variable is ignored, so a globally configured
`filter.*.clean` could run again during `git status`; the repository-config refusal, the
`core.fsmonitor` override and the git-dir/work-tree pin still hold. The scanner does not check the
Git version, and the real-Git canary in the test suite is what catches this on a given machine or in
CI. The development machine used for V0 runs Git 2.55.0.

`git status` may compare the content of files whose timestamps changed; that is Git's own check and
nothing is stored or reported from it. No remote URL or config value reaches a result or the audit
log (Git itself necessarily reads `.git/config`).

The process snapshot runs `ps -axo pid=,ppid=,rss=,etime=,comm=` with an empty environment: no
command-line arguments, no environment. It reports PID, executable basename, memory, and a broad
category. `possible_stale_process` is used only for `node`/`python` processes that were re-parented to
launchd and have run over 12 hours, always with evidence and "check it yourself". If `ps` is
unavailable the scan returns a warning and continues.

## Timeouts, retries, and recovery

The scan enforces its own deadline and per-subprocess timeouts. The worker's 90 s timeout is only an
outer backstop: `WorkerRunner` cannot cancel a thread, so a timed-out handler would keep running
until it returned.

* One bounded execution, one durable result stored on the task.
* `recovery_policy = safe_replay`: if the daemon dies mid-scan, recovery re-queues the task and the
  next run starts from scratch. There is no partial-scan continuation and none is claimed. Nothing
  auto-runs; the owner presses Run or Retry scan.
* `retryable`, up to 3 attempts. Permission and validation failures are permanent.
* The kill switch is checked before a task is claimed, so a stopped system leaves the task `QUEUED`.

## Chief.app

The Tasks page has a **Development scan** panel: approved folders (add via folder picker, remove),
a checkbox for the process snapshot, a plain statement of scope and limits, and **Run Development
Scan**. It never runs on open and is never scheduled. The task detail shows status, times, counts,
dirty repositories, largest build folders, possible duplicate groups, memory and stale-process
findings, warnings, partial/incomplete reasons, and suggested next steps. Retry on a scan task
re-queues and runs it.

## Contract fixes made alongside

Reusing the existing execution path exposed three defects that blocked retry, recovery, and display.
They were fixed narrowly:

1. `acquire_lease` violated `worker_leases.task_id UNIQUE` on any second attempt, so retried or
   recovered tasks could never be re-executed. Spent lease rows are now cleared before a re-claim.
2. The kill switch was checked after the claim, stranding the task in `RUNNING`. It is now checked
   first (and a race after the claim fails the attempt cleanly, using the handler's real retry policy,
   not a made-up one).
3. The desktop task and history parsers required fields the daemon never sends (`attempt_count`,
   `ts`/`event`), so the Tasks list was empty against a real daemon. They now accept the real shape.

The worker also refuses to store a result larger than the task-result limit, and a result (or
checkpoint) that cannot be serialised now fails the attempt immediately instead of leaving the task
`RUNNING` until its lease expires. A concurrent claim that loses the `UNIQUE(task_id)` race reports the
defined "already has active lease" conflict instead of a raw `IntegrityError`.

## Known limitations (V0)

* **Same-user trust.** The approved-roots file and the rest of a repository's own config are trusted
  at the level of the owner's own shell. Filters and includes in repository config are refused, and
  `core.fsmonitor`, `core.worktree`, and the global/attribute files are neutralised, but other
  config-driven Git behaviour is not individually enumerated. Someone who can already write a
  repository's `.git/config` runs as the owner.
* **Traversal race (review finding 5, accepted).** Directories are checked with `lstat` semantics when
  listed and opened by path afterwards. A same-user process that swaps a directory for a symlink
  between those two steps could steer one `scandir` call (names and counts of one out-of-root folder
  could enter a report; no privilege boundary is crossed). Closing it needs fd-relative traversal
  (`openat`/`O_NOFOLLOW`). Until then the guarantee is "symlinks observed while listing are never
  followed", not an unconditional "never".
* **Retrying scans show as `FAILED` (review finding 6, accepted).** `_fail` records a retryable failure
  as task state `FAILED` with `retry_after_at` set; there is no separate retry-wait task state, and
  nothing sweeps and re-queues automatically. A scan never retries on its own: the owner presses
  Retry scan. The attempt row does record `RETRY_WAIT`.
* **`/v1/workers` is a snapshot (review finding 9, accepted).** Spent lease rows are deleted when a task
  is re-claimed, so the table no longer keeps per-task lease history. Attempt history is unaffected
  (`execution_attempts`). A short worker list does not mean missing work.
* **Audit write failures are not surfaced (review finding 10, accepted).** The scan's audit event is
  written best-effort; a failed write does not discard a finished scan and is not reported in the
  result. The worker's own claim/complete/fail audit events are unchanged.
* **Kill switch during a scan.** The switch is checked before a task is claimed and again when the
  handler is entered. A scan already running is not interrupted (`WorkerRunner` cannot cancel a
  thread) and finishes within its own deadline (at most 60 s) before a result is stored.
* **Blocked I/O.** The deadline is checked between directory reads. A read that blocks inside the
  kernel (an unresponsive network mount) can outlast the deadline, and `WorkerRunner` cannot cancel
  the thread; the next task may then overlap the old thread. Approve local folders only.
* **Process list size.** `ps` output is capped at 2 MB; on a machine with an unusual number of
  processes the tail of the list could be dropped without being reported.
* **Name-based classification.** Folders called `build`, `out`, `dist`, `target` are reported as
  build output by name; a source folder with one of those names is mis-labelled (and not descended).
* **Process snapshot.** `possible_stale_process` is a heuristic (re-parented to launchd, running over
  12 hours). Legitimate background services can match it. It is advisory and never an instruction.

## Out of scope for V0

Scheduling, background scanning, checkpointed multi-stage scans, Trash/cache/CoreSimulator
inspection, model-written summaries, any cleanup or move action, and any change to an inspected
project. A real inventory of the owner's Mac needs a separate, owner-approved activation.
