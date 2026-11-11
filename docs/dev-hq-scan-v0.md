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

Approval is re-checked at execution time (D-025), not only when the task is created.

## Never inspected

Roots may not be `/`, the home folder or a parent of it, `~/Library`, `~/.Trash`, or anything
overlapping Chief's state directory. Inside an approved root these directory names are never
entered: `.ssh`, `.gnupg`, `.aws`, `.kube`, `.docker`, `.config`, `.npm`, `.claude`, `.cursor`,
`.local`, `.Trash`, `Keychains`, `ChiefOfStaff`, plus any name containing `credential`, `secret`,
`keychain`, `password`, `passwd`, `token(s)`, or `private key`. Symlinks are never followed; a
symlink that points outside its root is counted, not entered. File contents are never opened.

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
`--no-optional-locks`, `GIT_TERMINAL_PROMPT=0`, and `core.fsmonitor=false` on the command line (so a
repository's own config cannot make Git execute a command). Only `status`, `worktree list`, and (for
duplicate evidence) `rev-list --max-parents=0` are used. No `fetch`, `pull`, `push`, `prune`, `gc`,
`clean`, `reset`, `stash`, `checkout`, or remote/config reads. Each child runs in its own session with
a wall-clock deadline and output cap; on timeout only that child's process group is terminated.

For an ordinary repository (`.git` is a real directory, not a link) `--git-dir` and `--work-tree` are
pinned to the discovered folder, so `core.worktree` or a redirected git dir cannot point Git at a
location outside the approved root (verified: unpinned, Git counted files from the redirected tree).

`git status` may compare the content of files whose timestamps changed; that is Git's own check and
nothing is stored or reported from it. Remote URLs and config values are never read, so credentials
embedded in them cannot reach a result.

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
   first (and a race after the claim fails the attempt cleanly).
3. The desktop task and history parsers required fields the daemon never sends (`attempt_count`,
   `ts`/`event`), so the Tasks list was empty against a real daemon. They now accept the real shape.

The worker also refuses to store a result larger than the task-result limit instead of persisting it.

## Known limitations (V0)

* **Same-user trust.** The approved-roots file, repository config, and `.gitattributes` are trusted at
  the level of the owner's own shell. `core.fsmonitor` is forced off and the git dir is pinned, but
  other config-driven Git behaviour (for example a configured `filter.*.clean` command, which
  `git status` can run while comparing a changed file) is not individually neutralised. An attacker
  who can write a repository's `.git/config` already runs as the owner.
* **Traversal race.** Directories are checked with `lstat` semantics when listed and opened by path
  afterwards. A same-user process that swaps a directory for a symlink between those two steps could
  steer one `scandir` call. Closing this needs fd-relative traversal (`openat`/`O_NOFOLLOW`).
* **Blocked I/O.** The deadline is checked between directory reads. A read that blocks inside the
  kernel (an unresponsive network mount) can outlast the deadline, and `WorkerRunner` cannot cancel
  the thread. Approve local folders only.
* **Name-based classification.** Folders called `build`, `out`, `dist`, `target` are reported as
  build output by name; a source folder with one of those names is mis-labelled (and not descended).
* **Process snapshot.** `possible_stale_process` is a heuristic (re-parented to launchd, running over
  12 hours). Legitimate background services can match it. It is advisory and never an instruction.

## Out of scope for V0

Scheduling, background scanning, checkpointed multi-stage scans, Trash/cache/CoreSimulator
inspection, model-written summaries, any cleanup or move action, and any change to an inspected
project. A real inventory of the owner's Mac needs a separate, owner-approved activation.
