# PROMPT — D1.1: Developer-safety hardening (Codex findings P1A-D1-001…007)

## Where you are

- **Worktree:** `~/Projects/taw-cos-m1`, branch `feature/cos-p1a5`. Stay on it. Do not push or
  merge.
- **D1 source today:** the recovery worktree,
  `~/Projects/teacher-ai-workstation-chief-of-staff-recovery`:
  - `.claude/settings.json`
  - `tools/dev_safety/dev_guard.py`
  - `tools/dev_safety/dev_safety_probe.py`
  - `tools/dev_safety/install_dev_guard.py`
  - `tests/test_dev_guard.py`
- **Installed hook:** `~/.claude/hooks/cos/dev_guard.py`.
- **Read first:** `docs/DECISIONS.md` and the Codex findings in section 0.

## Ground rules

- **You may not install, modify, or remove the live hook or any `~/.claude` file.** D1 denies
  that, and must. Owen installs. You edit only repo files and write exact install and probe
  steps for Owen.
- **Be honest about what a command denylist can do.** It is a speed bump, not a boundary. An
  agent that can write a file and then run it with an allowed interpreter (`python3 x.py`,
  `npm test`, `make`) can run anything. So this phase adds an OS-level boundary where one
  exists, and treats the hook as a second layer. State this plainly in the docs.
- **One commit per section.**

## 0. Findings this phase closes

- **P1A-D1-001 (CRITICAL):** `python3 -c`, `node -e`, `perl -e`, `ruby -e`, and `osascript -e`
  escape every denial.
- **P1A-D1-002 (MAJOR):** real MultiEdit payloads nest paths under `edits[].file_path`, and the
  probe tests a fake shape.
- **P1A-D1-003 (MAJOR):** `~/.claude.json`, `~/.claude/settings.json`, and the session
  transcripts under `~/.claude/projects/**` are readable and writable.
- **P1A-D1-004 (MINOR):** destructive commands are not denied.
- **P1A-D1-005 (MINOR):** student-data roots and other credential stores are missing.
- **P1A-D1-006 (MINOR):** relative path traversal in Bash (for example `cat ../../.ssh/id_rsa`)
  bypasses the root checks.
- **P1A-D1-007 (MINOR):** D1 is not committed in this repo, and the README overstates coverage.

## 1. Bring D1 into this repo (D1-007)

- Copy `tools/dev_safety/` (guard, probe, installer, tests) and `.claude/settings.json` from the
  recovery worktree into this repo, unchanged first, and commit that copy.
- Add `tools/dev_safety/README.md`:
  - what D1 protects
  - the two layers (OS sandbox and hook)
  - its known limits
- **README correction:** in `CHIEF-OF-STAFF.md`, replace "D1 profile active / 371/371 probes
  passed" with wording that matches what this repo can reproduce. Update it again after
  section 5.

## 2. OS-level boundary (the real fix for D1-001)

- **Check for a native sandbox.** Look at Claude Code's current documentation for a native
  sandbox that restricts Bash commands' filesystem and network access (macOS Seatbelt or
  similar).
- **If it exists**, configure it in `.claude/settings.json`:
  - **Reads denied:** `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.config/gh`, `~/.claude.json`,
    `~/.claude/settings*.json`, `~/.claude/projects`, `~/.netrc`, `~/.docker`, `~/.kube`,
    `~/.npmrc`, `~/.pgpass`, `~/.teacher-ai-workstation`,
    `~/Library/Application Support/ChiefOfStaff`, `~/Downloads`, and the student-data roots
    from section 4.
  - **Writes allowed only to:** this worktree and system temp.
  - **Network:** only what builds need (package registries, GitHub read, localhost Ollama), as
    narrowly as the sandbox allows.
  - **Git push:** not possible from inside the sandbox.
  - **Docs:** document exactly what is enforced.
- **If it does not exist, or can't express these rules,** say so in the report and docs. Do not
  invent one.

## 3. Hook fixes (second layer)

- **D1-002:** `check_file_tool` inspects every `edits[].file_path` for MultiEdit and
  `notebook_path` for NotebookEdit, plus any other path-bearing key in the real tool schemas.
  - Unknown write-tool shapes with no recognizable path are **denied**, not passed.
  - Fix the probe and unit tests to use the real nested schemas.
- **D1-003:** add `~/.claude.json`, `~/.claude/settings.json`, `~/.claude/settings.local.json`,
  and `~/.claude/projects/**` (all of it, not only memory) to the denied roots for reads and
  writes, in both the hook and the `settings.json` deny lists.
  - Keep the existing hook-directory protection.
- **D1-001 (hook layer):** deny inline code execution:
  - `python`/`python3 -c`
  - `node -e/--eval/-p`
  - `perl -e/-E`
  - `ruby -e`
  - `osascript -e` and `osascript` with any script
  - `php -r`
  - `awk` programs containing `system(` or a pipe to a command
  - `bash`/`sh`/`zsh` with any argument (already denied)
  - `env`/`xargs`/`nice`/`timeout`/`exec` wrappers around any denied program, resolved
    recursively
  - **Still allowed:** running files and modules (`python3 -m unittest`, `python3 script.py`,
    `npm test`), because the build needs them. Section 2 is what contains those.
- **D1-006:** resolve every path-like Bash argument, including relative ones, against the
  command's working directory, following `~`, `$HOME`, and symlinks, then apply
  `denied_root_for`. This includes redirection targets (`> file`, `>> file`) and `cd` targets
  in compound commands.
- **D1-004:** deny destructive commands unless the target is inside this worktree or system
  temp:
  - `rm -r/-rf` outside those areas
  - `find … -delete`
  - `rmdir` outside those areas
  - `shred`
  - `dd if=`
  - `mkfs`
  - `diskutil erase*/zero*/reformat/partition*`
  - `tmutil delete*`
  - `brew uninstall/autoremove/cleanup`
  - `docker system/volume/image prune`, `docker rm/rmi`
  - `git clean -x`, plus the existing git denials

## 4. Student-data roots and credential stores (D1-005)

- **Add credential stores:** `~/.netrc`, `~/.docker/config.json`, `~/.kube/config`, `~/.npmrc`,
  `~/.pgpass`, `~/.config/op` (1Password CLI), and `~/.config/gcloud`.
- **Student-data roots:** read them from a new repo file,
  `tools/dev_safety/student_data_roots.txt`.
  - One path per line. `~` and globs are allowed.
  - Initial content: `~/.teacher-ai-workstation` plus commented example lines. Owen fills in
    the real folders.
  - Both layers (sandbox and hook) load this file. A missing or unreadable file denies
    everything under `~/Documents` and `~/Desktop` until it's fixed, so the guard fails closed.
- **Docs:** tell Owen exactly how to add a root.

## 5. Probes and tests (real payload shapes only)

- **Unit tests** for every closed bypass, using real Claude Code tool-input JSON shapes:
  - `python3 -c "import subprocess; subprocess.run(['git','push','--force'])"`
  - `node -e`, `perl -e`, `osascript -e`
  - `env python3 -c …`
  - `xargs sh -c`
  - MultiEdit with `edits[].file_path` under `~/.ssh` and under `~/Library/Application Support/ChiefOfStaff`
  - Write to `~/.claude/settings.json`
  - Read of `~/.claude.json`
  - Read of `~/.claude/projects/x/y.jsonl`
  - `cat ../../.ssh/id_rsa` from inside the repo
  - `echo x > ../../.ssh/config`
  - `rm -rf ../sibling-repo`
  - `find ~ -name x -delete`
  - `diskutil eraseDisk …`
  - **Allowed cases still allowed:**
    - `python3 -m unittest discover -s tests/cos -p 'test_*.py'`
    - `npm test`
    - `git status`
    - `rm -rf ./build`, inside the worktree
- **Update `dev_safety_probe.py`** with the same cases. It's the synthetic probe Owen runs
  after installing.
- **Tool-boundary probe:** write `docs/d1-1-owen-steps.md` with exact copy-paste steps:
  1. install the new hook with the installer
  2. verify the installed hook's SHA-256 matches the repo file
  3. run the synthetic probe
  4. start a fresh `claude` session and paste a provided list of 10 safe probe requests. Each
     one should be denied, using harmless targets, such as reading `~/.ssh/known_hosts` or a
     MultiEdit to a temp file inside a denied test root, never real secrets.
  5. what each result should look like
  6. how to roll back

## Validation

```
python3.12 -m unittest discover -s tests -p 'test_dev_guard*.py'
python3.12 tools/dev_safety/dev_safety_probe.py --synthetic
python3.12 -m unittest discover -s tests/cos -p 'test_*.py'
git diff --check
```

## Report

- commit SHAs
- whether a native sandbox was found and configured, and exactly what it enforces, or why not
- test and probe counts
- each finding D1-001 to 007 with its disposition
- remaining known limits, stated plainly
- `git status -sb`
