# Phase 0 Day 1 Manual Steps

Use this beginner-friendly checklist on the first day with the new MacBook Pro.

# Before opening the MacBook

Run from the repo on the existing machine or Codex/local clone:

```bash
bash setup/98-final-audit.sh
```

Then:

- If PASS: proceed to opening the new MacBook with live assistant guidance.
- If PASS WITH WARNINGS: review warnings, then decide.
- If FAIL: fix before opening the MacBook.

## Before running bootstrap

- [ ] Mac was set up as new, not from Migration Assistant
- [ ] WiFi connected
- [ ] Apple ID signed in
- [ ] FileVault enabled with local recovery key saved in 1Password or another trusted password manager
- [ ] Find My Mac enabled
- [ ] Touch ID configured

For a privacy-focused local-first workstation, prefer generating a local FileVault recovery key and storing it securely in 1Password or another trusted password manager. Do not lose this key.

## After `./bootstrap.sh` finishes

- [ ] Opened a new Terminal window after shell profile setup
- [ ] Confirmed Starship prompt loads
- [ ] Confirmed Zoxide works
- [ ] Confirmed Eza/Bat aliases work
- [ ] Teacher Focus Mode created
- [ ] Casual Anime Mode created
- [ ] Teacher widgets added
- [ ] Casual widgets added
- [ ] Arc Teacher Space created
- [ ] Arc Casual Space created
- [ ] Chrome available as fallback
- [ ] Raycast configured
- [ ] Obsidian vault opened
- [ ] 1Password signed in
- [ ] AlDente charge limit set
- [ ] iPad/iPhone Focus sync enabled
- [ ] Reviewed `docs/backup-exclusions.md`
- [ ] Ricoh printer certification completed later at school

## Optional 3D readiness

- [ ] Open Bambu Studio once if installed
- [ ] Sign in only if desired
- [ ] Confirm printer/profile setup later
- [ ] Do not configure printer automation on Day 1
- [ ] Confirm `~/3D-Printing` folders exist
- [ ] Review `docs/3d-printing-day-1-setup.md`
- [ ] Review `3d-agent/verification/pre-slicer-checklist.md` before printing AI-generated designs
- [ ] Remember: verification checklists are advisory and do not block printing

## Optional Chief of Staff CLI test

After bootstrap finishes and you open a new Terminal window, run:

```bash
bin/chief-of-staff --status
```

Then run:

```bash
bin/chief-of-staff --list-workflows
```

Then try:

```bash
bin/chief-of-staff \
  --workflow request-training-materials \
  --question "What should I give you first?" \
  --dry-run
```

`--dry-run` does not call a model. It only shows the prompt/context that would be sent. `--status` helps confirm the CLI found the repo and required docs.

## Optional Chief of Staff memory test

Run:

```bash
bin/chief-of-staff --memory-status
```

Then run:

```bash
bin/chief-of-staff --validate-memory
```

Try a dry run with memory:

```bash
bin/chief-of-staff \
  --workflow project-review \
  --include-memory \
  --question "What should I work on next?" \
  --dry-run
```

This only prints or checks local Markdown context. It does not call a model. Use `--show-context` to confirm memory files are included.

## Optional Chief of Staff intake test

Run:

```bash
bin/chief-of-staff --intake-status
```

Then run:

```bash
bin/chief-of-staff --intake-summary
```

Then run:

```bash
bin/chief-of-staff --validate-intake
```

Try an intake dry run:

```bash
bin/chief-of-staff \
  --workflow intake-review \
  --include-intake-policy \
  --include-intake-queue \
  --include-intake-checklist \
  --question "What needs review?" \
  --dry-run
```

These commands do not scan the Mac. They do not call a model when `--dry-run` is used. They only inspect repo Markdown files.

## Finish Day 1

- [ ] Mac restarted after automated setup and manual configuration
- [ ] Reran `bash setup/99-verify-setup.sh`

When every item is checked, run:

```bash
bash setup/99-verify-setup.sh
```
