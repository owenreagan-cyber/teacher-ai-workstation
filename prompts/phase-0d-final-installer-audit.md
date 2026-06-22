# Phase 0D Final Installer Audit Prompt

You are continuing work in `https://github.com/owenreagan-cyber/teacher-ai-workstation.git`.

Task: add Phase 0D Final Installer Audit before opening the new MacBook Pro M5 Pro.

Purpose:

- Confirm the repo is ready for fresh-machine setup.
- Add `docs/final-installer-audit.md`.
- Add `setup/98-final-audit.sh`.
- Keep this audit read-only: no installs, no model calls, no external connectors, no desktop control, no broad local scans.
- Do not add major new features.

Update:

- `README.md` with a preflight section before opening the MacBook.
- `docs/day-1-manual-steps.md` with the preflight command.
- `docs/recovery-guide.md` with recovery steps if final audit fails.
- `docs/chief-of-staff-roadmap.md` so Phase 1A through 1D are complete, Phase 0D is now, and opening the MacBook comes after Phase 0D.
- `assistant/memory/active-priorities.md` with Phase 0D as the current priority.
- `assistant/memory/memory-log.md` with a Phase 0D sample entry.
- `setup/09-generate-report.sh` and `setup/99-verify-setup.sh` with documentation/readiness checks for Phase 0D.
- `bootstrap.sh` with a comment that `setup/98-final-audit.sh` is intentionally not run by bootstrap.

Audit script requirements:

- Use `PASS`, `WARN`, and `FAIL`.
- Resolve repo root safely.
- Check Git repo state.
- FAIL on tracked dirty files and staged changes.
- WARN on untracked files.
- WARN if optional CLI flags are missing, including `--preflight`.
- Capture smoke test output without aborting the audit early.
- Use `git check-ignore` for `.gitignore` safety.
- Treat `3d-agent/partner-workflow.md` as WARN if missing, not FAIL.
- Check script syntax one file at a time.
- Scan only repo text files for obvious credential patterns.
- Exclude `.git`, `node_modules`, `vendor`, `logs`, and intake raw/quarantine/approved file folders.

Validation:

- `bash -n bootstrap.sh`
- `bash -n` each `setup/*.sh`
- `bash -n bin/chief-of-staff`
- `bash -n tests/smoke-chief-of-staff-cli.sh`
- `tests/smoke-chief-of-staff-cli.sh`
- `bash setup/98-final-audit.sh`
- `git diff --check`
- `git status --short`

Suggested commit message:

`chore: add final installer audit before mac setup`
