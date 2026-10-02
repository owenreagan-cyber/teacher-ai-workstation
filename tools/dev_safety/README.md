# D1 — developer safety for Claude Code sessions in this repo

D1 keeps a Claude Code agent working in this repo away from student data, credentials,
Claude Code's own configuration and transcripts, and destructive or outward-facing commands
(push, force, privilege escalation).

## What it protects

- **Student data:** `~/.teacher-ai-workstation` and the Chief of Staff state directory
  (`~/Library/Application Support/ChiefOfStaff`).
- **Credentials:** `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.config/gh`.
- **Downloads:** `~/Downloads`.
- **Claude memory:** `~/.claude/projects/**/memory`.
- **The profile itself:** `<project>/.claude` and the installed hook directory
  `~/.claude/hooks/cos`.
- **Git:** push, config, clean, gc, update-ref, `reset --hard`, force flags, `-c alias.*`, and
  worktree add/remove/move/prune outside `$COS_FEATURE_WORKTREE`.
- **Process listings** that print full command lines (`ps aux`, `pgrep -fl`, and similar).
- **Privilege escalation:** `sudo`, `doas`, `su`.

## The layers

1. **Claude Code permission rules** in `.claude/settings.json` (`permissions.deny`). These
   match tool names and command prefixes.
2. **The PreToolUse hook** `dev_guard.py`, installed read-only to `~/.claude/hooks/cos/`. It
   parses each Bash command and file-tool path and denies what the rules above would miss
   (normalized git forms, symlinks, `$HOME`, `~`, nested `bash -c`).

## Known limits

- **A command denylist is a speed bump, not a boundary.** An agent that can write a file and
  then run it with an allowed program (`python3 x.py`, `npm test`, `make`) can run anything,
  and the hook cannot see what that program does. Only an OS-level boundary can contain that.
- Inline interpreters (`python3 -c`, `node -e`, `perl -e`, `osascript -e`) are not inspected
  by this version.
- Only absolute, `~`, and `$HOME` Bash arguments are path-checked; relative paths such as
  `../../.ssh` are not.

## Files

| File | Role |
|---|---|
| `dev_guard.py` | The hook (stdlib only). Source of truth; never edit the installed copy. |
| `install_dev_guard.py` | Copies the hook to `~/.claude/hooks/cos/`, read-only, and records its SHA-256. Owen runs it, outside an agent session. |
| `dev_safety_probe.py` | Integrity, synthetic hook, and tool-boundary probes. |
| `../../tests/test_dev_guard.py` | Unit tests. |
