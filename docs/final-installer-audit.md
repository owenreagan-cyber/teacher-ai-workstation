# Phase 0D Final Installer Audit

## Purpose

This is the final repo audit before opening the new MacBook Pro M5 Pro.

It checks script readiness, docs readiness, CLI readiness, memory readiness, intake readiness, 3D readiness, `.gitignore` safety, and safety boundaries.

It does not run Apple Setup Assistant. It does not install anything by itself. It does not call a model. It prepares Owen for the physical setup checkpoint.

Use this alongside `README.md`, `docs/day-1-manual-steps.md`, and `docs/recovery-guide.md`.

## Current Completed Phases

- Phase 0A - Day 1 Core Installer
- Phase 0B - Hardening Injector
- Phase 0C - 3D Design Agent Readiness + Verification Foundation
- Phase 1A - Chief of Staff Safety + Training Layer
- Phase 1B - Interactive Chief of Staff CLI
- Phase 1C - Project Memory + Writing Style Memory
- Phase 1D - Intake Review Queue

## Next Physical Checkpoint

After this audit passes, the next checkpoint is:

Open new MacBook Pro M5 Pro.

At that point Owen should be given literal setup directions beginning with:

1. Open the MacBook Pro lid.
2. If the setup screen does not appear, press any key.
3. Follow Apple Setup Assistant screen by screen.

Do not use this file as the full Apple Setup Assistant walkthrough. This file prepares for that step; the live walkthrough should guide the physical setup screen by screen.

## Audit Areas

### Git Repository Readiness

- [ ] Repo root resolves correctly.
- [ ] Git is installed.
- [ ] Origin remote points to the Teacher AI Workstation repository.
- [ ] Current branch is `main`.
- [ ] Tracked working tree is clean.
- [ ] Staged changes are clean.
- [ ] Untracked files are intentional.
- [ ] Local `main` is not obviously behind `origin/main`.

### bootstrap.sh Readiness

- [ ] `bootstrap.sh` exists.
- [ ] `bootstrap.sh` is executable.
- [ ] `bootstrap.sh` syntax passes.
- [ ] `setup/98-final-audit.sh` is not part of the normal bootstrap run.

### Setup Script Readiness

- [ ] All expected setup scripts exist.
- [ ] Setup scripts that run directly are executable.
- [ ] Every setup script passes `bash -n`.
- [ ] `setup/99-verify-setup.sh` remains the installed-Mac verification script.

### Brewfile Readiness

- [ ] Essential command-line tools are present in `Brewfile`.
- [ ] Optional but desired teaching/workstation tools are present or intentionally omitted.
- [ ] No installer step requires secrets committed to the repo.

### README Day 1 Flow Readiness

- [ ] `README.md` tells Owen to run the final audit before opening the MacBook.
- [ ] The Day 1 flow remains beginner-friendly.
- [ ] The bootstrap and verification commands are easy to copy.

### Manual Setup Docs Readiness

- [ ] `docs/day-1-manual-steps.md` includes the final audit preflight.
- [ ] Manual steps remain clearly separate from automated setup.
- [ ] Apple Setup Assistant is reserved for the live walkthrough.

### Verification Script Readiness

- [ ] `setup/99-verify-setup.sh` verifies the installed Mac.
- [ ] It checks for the final audit doc and script.
- [ ] It does not run the final audit automatically.

### Setup Report Readiness

- [ ] `setup/09-generate-report.sh` records whether the final audit doc and script are present.
- [ ] The report explains that final audit is run manually before opening the MacBook.

### Chief of Staff CLI Readiness

- [ ] `bin/chief-of-staff` is executable.
- [ ] CLI help, status, workflow listing, dry-run, and smoke tests work without calling a model.
- [ ] Optional diagnostic flags warn rather than block if unavailable.

### Memory Readiness

- [ ] Memory files exist or missing files are called out as WARN items.
- [ ] Memory is not automatically loaded.
- [ ] Memory validation can be run before memory-assisted prompts.

### Intake Readiness

- [ ] Intake files exist or missing files are called out as WARN items.
- [ ] Raw intake is not automatically loaded.
- [ ] Approved intake summaries are explicit.
- [ ] Raw, quarantine-file, and approved-file folders are protected by `.gitignore`.

### 3D Readiness

- [ ] Foundational 3D docs and verification checklists exist.
- [ ] 3D verification says designs are only slicer-ready pending human verification.
- [ ] 3D guidance makes clear the system cannot block, stop, disable, or prevent printing.

### .gitignore Safety

- [ ] `logs/*.log` and `logs/*.md` are ignored.
- [ ] Intake raw files are ignored.
- [ ] Intake quarantine files are ignored.
- [ ] Intake approved files are ignored.
- [ ] `.gitkeep` placeholders remain trackable.

### Old PR / Branch Cleanup

- [ ] Work is on `main`.
- [ ] `main` is pushed to `origin/main`.
- [ ] Old branches or PRs do not block the fresh-machine setup.

### Recovery Docs Readiness

- [ ] `docs/recovery-guide.md` explains what to do if final audit fails.
- [ ] Recovery commands are copyable.
- [ ] Secret handling and `.gitignore` recovery are covered.

### No-Secrets Check

- [ ] The repo does not contain obvious assigned credentials.
- [ ] Private key block markers are absent.
- [ ] Documentation mentions of passwords, tokens, or API keys are treated as safety guidance, not secrets.

### No Unsafe Automation Check

- [ ] No Drive, Gmail, Canvas, desktop-control, or autonomous agent behavior runs during the audit.
- [ ] No model call runs during the audit.
- [ ] No installer runs during the audit.

## PASS / WARN / FAIL Meaning

- PASS means ready.
- WARN means review before proceeding but may not block setup.
- FAIL means fix before opening the MacBook.

## Manual Final Decision

Owen should only open the new MacBook Pro after:

- the final audit script passes or only has acceptable WARN items
- `README.md` Day 1 flow is clear
- `docs/day-1-manual-steps.md` is clear
- `docs/recovery-guide.md` is clear
- `git status` is clean or only has intentional untracked local scratch files
- `main` is pushed to `origin/main`

Run:

```bash
bash setup/98-final-audit.sh
```

If the result is `FAIL`, fix the FAIL items before opening the MacBook. If the result is `PASS WITH WARNINGS`, review the WARN items and decide whether they are acceptable for the physical setup checkpoint.
