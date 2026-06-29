Open your MacBook Pro…

# Teacher AI Workstation

This repository prepares a brand-new MacBook Pro to become a Teacher AI Workstation.

Phase 0A Day 1 is only the core Mac setup. It makes the Mac clean, safe, organized, beginner-friendly, and ready for later Teacher OS development.

It does not build the React app, Canvas tools, agents, Docker services, Supabase, Firestore, MongoDB, or classroom content workflows.

## Before Opening the New MacBook Pro

Run the final repo audit before physically opening the new MacBook.

This confirms the repo is ready. It does not install anything. It does not call a model. It checks docs, scripts, CLI, memory, intake, 3D readiness, `.gitignore` safety, and obvious secret patterns.

From the repo root, run:

```bash
bash setup/98-final-audit.sh
```

If it passes, move to the live MacBook setup walkthrough. If it fails, fix the FAIL items before opening the MacBook. WARN items should be reviewed but may not block setup.

Open the MacBook only after Phase 0D passes, then follow live instructions from the assistant.

## Exact Day 1 Flow

Follow these steps in order on the unopened MacBook Pro.

1. Open MacBook.
2. Set up as a new Mac, not from Migration Assistant.
3. Connect WiFi.
4. Sign into Apple ID.
5. Enable FileVault.
6. Enable Find My Mac.
7. Set up Touch ID.
8. Open Terminal.
9. Run Xcode Command Line Tools installation:

   ```bash
   xcode-select --install
   ```

   Wait for the Apple installer to finish before continuing.

10. Clone the repo:

    ```bash
    mkdir -p ~/Projects
    cd ~/Projects
    git clone https://github.com/owenreagan-cyber/teacher-ai-workstation.git
    cd teacher-ai-workstation
    ```

11. Run:

    ```bash
    chmod +x bootstrap.sh setup/*.sh
    ```

12. Run:

    ```bash
    ./bootstrap.sh
    ```

13. Complete the manual checklist:

    ```bash
    open docs/day-1-manual-steps.md
    ```

14. Restart once.
15. Rerun automated verification:

    ```bash
    bash setup/99-verify-setup.sh
    ```

## What The Automated Setup Does

The bootstrap script runs the setup scripts in order:

- `setup/00-check-system.sh`: checks macOS, Apple Silicon, internet, disk space, and Xcode Command Line Tools.
- `setup/01-install-homebrew.sh`: installs or verifies Homebrew.
- `setup/02-install-apps.sh`: installs command-line tools and apps from `Brewfile`.
- `setup/03-macos-defaults.sh`: applies beginner-friendly Finder, Dock, screenshot, keyboard, trackpad, and text settings.
- `setup/04-folder-structure.sh`: creates the teaching, AI, notes, screenshots, media, and archive folders.
- `setup/05-dock-layout.sh`: sets a simple shared Dock layout when `dockutil` is available.
- `setup/06-wallpapers.sh`: prepares Teacher Mode and Casual Anime Mode wallpaper folders.
- `setup/07-git-github.sh`: helps configure Git and GitHub basics without adding secrets.
- `setup/08-local-ai.sh`: checks Ollama and asks before any model download.
- `setup/09-generate-report.sh`: writes a local setup report.
- `setup/10-shell-profile.sh`: activates safe zsh terminal enhancements in `~/.zshrc`.
- `setup/99-verify-setup.sh`: verifies scriptable setup only.

`setup/98-final-audit.sh` is intentionally not part of the bootstrap run. It is a preflight repo audit to run before opening the new MacBook.

Logs are written to `logs/setup.log`.

Teacher Workstation Mode and Casual Anime Mode stay conceptually present on Day 1, but Focus Modes, widgets, browser Spaces, and personal app preferences are manual checklist items.

## If Xcode Command Line Tools are missing

Run:

```bash
xcode-select --install
```

Then rerun:

```bash
./bootstrap.sh
```

## Important Verification Note

`setup/99-verify-setup.sh` is automated verification only. It is not final manual certification.

Focus Modes, widgets, browser profiles, Raycast preferences, Obsidian vault setup, 1Password sign-in, AlDente preferences, iPad/iPhone Focus sync, and Ricoh physical printing must be checked by a human in `docs/day-1-manual-steps.md`.

## Shell profile and terminal enhancements

Phase 0 installs modern CLI tools including Starship, Zoxide, Atuin, Eza, Bat, FZF, Ripgrep, UV, LLM, and Fabric.

`setup/10-shell-profile.sh` activates them in `~/.zshrc` using a clearly marked managed block. It is safe to rerun and does not delete personal shell customizations outside that block.

After bootstrap finishes, open a new Terminal window or run:

```bash
source ~/.zshrc
```

## FileVault and backups

Enable FileVault during Apple setup.

For a privacy-focused local-first workstation, prefer generating a local FileVault recovery key and storing it securely in 1Password or another trusted password manager. Do not lose this key.

Review `docs/backup-exclusions.md` before setting up Time Machine or cloud backup exclusions.

## Next Major Priority: Teacher AI Chief of Staff

Phase 0 prepares the Mac. Phase 1 builds the assistant foundation.

The Teacher AI Chief of Staff is the primary post-Phase-0 product. It starts as an interactive, permission-based assistant, not an autonomous system.

Teaching is the primary focus: lesson support, project memory, writing style, planning, and guided troubleshooting. App development and technical debugging support are secondary. 3D printing will become a future specialist agent, with the Chief of Staff coordinating notes and handoffs later.

Phase 1A adds safety, training, permissions, memory, sensitivity, source, workflow, and evaluation docs before any app implementation.

See:

- `assistant/README.md`
- `docs/chief-of-staff-roadmap.md`
- `docs/assistant-training-guide.md`
- `docs/lesson-brief-helper.md`

Local lesson brief commands:

```bash
bin/chief-of-staff --lesson-brief-status
bin/chief-of-staff --create-lesson-brief LESSON_SLUG
```

Local lesson activity, assessment, and materials draft commands:

```bash
bin/chief-of-staff --lesson-draft-status
bin/chief-of-staff --create-lesson-draft TYPE LESSON_SLUG
```

Local lesson pack status command:

```bash
bin/chief-of-staff --lesson-pack-status
```

Local lesson queue status command:

```bash
bin/chief-of-staff --lesson-queue-status
```

Local lesson workflow status command:

```bash
bin/chief-of-staff --lesson-workflow-status
```

Local lesson review checklist status command:

```bash
bin/chief-of-staff --lesson-review-checklist-status
```

See `docs/safe-local-lesson-review-checklist.md`.

Local single-slug lesson review view command:

```bash
bin/chief-of-staff --lesson-review-view LESSON_SLUG
```

See `docs/single-slug-lesson-review-view.md`.

Local review notes template status command:

```bash
bin/chief-of-staff --review-notes-template-status
```

See `docs/review-notes-template.md`.

Local document indexing plan status command:

```bash
bin/chief-of-staff --document-indexing-plan-status
```

See `docs/safe-local-document-indexing-plan.md`.

Local document indexing follow-up status command:

```bash
bin/chief-of-staff --local-document-indexing-follow-up-status
```

See `docs/local-document-indexing-follow-up.md`.

Project memory cleanup status command:

```bash
bin/chief-of-staff --project-memory-cleanup-status
```

See `docs/project-memory-cleanup.md`.

Testing/checklist consolidation status command:

```bash
bin/chief-of-staff --testing-checklist-status
```

See `docs/testing-checklist-consolidation.md`.

Command/check bundle reference status command:

```bash
bin/chief-of-staff --command-check-bundle-reference-status
```

See `docs/command-check-bundle-reference-polish.md` and `docs/testing-checklist-consolidation.md`.

Command and check bundles (reference only):

```bash
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --checklist-driven-prompt-template-status
bin/chief-of-staff --dashboard
```

See `docs/checklist-driven-prompt-template-tightening.md`, `docs/command-check-bundle-reference-polish.md`, `docs/testing-checklist-consolidation.md`, and `docs/pr-lifecycle-guardrail-consolidation.md`.

PR lifecycle guardrails (every PR):

```bash
bin/chief-of-staff --pr-lifecycle-guardrail-status
```

```text
Every PR prompt must verify preflight on main.
Every PR prompt must verify the feature branch.
Every PR prompt must include no-commit review.
Every PR prompt must verify PR state is OPEN and mergedAt is null before merge.
Every PR prompt must verify merged state is MERGED and mergedAt is non-null after merge.
Every PR prompt must verify local main is synced after merge.
Every PR prompt must end with clean working tree and dashboard passing.
Reusable bundles do not replace these lifecycle guardrails.
```

Project memory and roadmap (status only):

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --project-memory-cleanup-status
bin/chief-of-staff --testing-checklist-status
```

Document indexing status (planning only; no scanning or indexing):

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
```

Appearance & Vibe wallpaper/photo curator plan status command:

```bash
bin/chief-of-staff --wallpaper-photo-curator-plan-status
```

See `docs/appearance-vibe-wallpaper-photo-curator-plan.md`.

Wallpaper/photo rotation folder design status command:

```bash
bin/chief-of-staff --wallpaper-photo-folder-design-status
```

See `docs/wallpaper-photo-rotation-folder-design.md`.

Wallpaper/photo dry-run folder validator command:

```bash
bin/chief-of-staff --wallpaper-photo-dry-run-folder-validator
```

See `docs/wallpaper-photo-dry-run-folder-validator.md`.

Wallpaper/photo folder creation helper commands:

```bash
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
bin/chief-of-staff --wallpaper-photo-create-folders --create
```

See `docs/wallpaper-photo-manual-folder-creation-helper.md`.

Wallpaper/photo metadata schema status command:

```bash
bin/chief-of-staff --wallpaper-photo-metadata-status
```

See `docs/wallpaper-photo-metadata-schema.md`.

Wallpaper/photo temp queue rules status command:

```bash
bin/chief-of-staff --wallpaper-photo-temp-queue-status
```

See `docs/wallpaper-photo-temp-queue-rules.md`.

Wallpaper/photo queue file format status command:

```bash
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-queue-file-validator
```

See `docs/wallpaper-photo-queue-file-format.md`.

Wallpaper/photo Approve/Dismiss UI design status command:

```bash
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
```

See `docs/wallpaper-photo-approve-dismiss-ui-design.md`.

Wallpaper/photo image processing rules status command:

```bash
bin/chief-of-staff --wallpaper-photo-image-processing-status
```

See `docs/wallpaper-photo-image-processing-rules.md`.

Wallpaper/photo local automation scheduler plan status command:

```bash
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
```

See `docs/wallpaper-photo-local-automation-scheduler-plan.md`.

Wallpaper/photo approved-source fetcher plan status command:

```bash
bin/chief-of-staff --wallpaper-photo-source-fetcher-plan-status
```

See `docs/wallpaper-photo-approved-source-fetcher-plan.md`.

Wallpaper/photo source allowlist foundation status command:

```bash
bin/chief-of-staff --wallpaper-photo-source-allowlist-status
```

Wallpaper/photo source allowlist dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-source-allowlist-validator
```

See `docs/wallpaper-photo-source-allowlist-foundation.md`.

Wallpaper/photo simulated discovery status command:

```bash
bin/chief-of-staff --wallpaper-photo-simulated-discovery-status
```

Wallpaper/photo simulated discovery dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-simulated-discovery-validator
```

See `docs/wallpaper-photo-simulated-approved-source-discovery-plan.md`.

Wallpaper/photo review UI prototype status command:

```bash
bin/chief-of-staff --wallpaper-photo-review-ui-prototype-status
```

Wallpaper/photo review UI state dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-review-ui-state-validator
```

See `docs/wallpaper-photo-live-local-review-ui-prototype-plan.md`.

Wallpaper/photo image processor foundation status command:

```bash
bin/chief-of-staff --wallpaper-photo-image-processor-foundation-status
```

Wallpaper/photo image processing plan dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-image-processing-plan-validator
```

See `docs/wallpaper-photo-image-processor-foundation.md`.

Wallpaper/photo scheduler foundation status command:

```bash
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
```

Wallpaper/photo scheduler run plan dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-scheduler-run-plan-validator
```

See `docs/wallpaper-photo-scheduler-foundation.md`.

Wallpaper/photo notification foundation status command:

```bash
bin/chief-of-staff --wallpaper-photo-notification-foundation-status
```

Wallpaper/photo notification plan dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-notification-plan-validator
```

See `docs/wallpaper-photo-notification-foundation.md`.

Wallpaper/photo rotation handoff safety audit status command:

```bash
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
```

Wallpaper/photo rotation handoff dry-run validator command:

```bash
bin/chief-of-staff --wallpaper-photo-rotation-handoff-validator
```

See `docs/wallpaper-photo-rotation-handoff-safety-audit.md`.

Return to Chief of Staff / Teacher Workstation core status command:

```bash
bin/chief-of-staff --return-to-core-status
```

See `docs/return-to-chief-of-staff-core.md`.

Chief of Staff dashboard readability pass status command:

```bash
bin/chief-of-staff --dashboard-readability-status
```

See `docs/chief-of-staff-dashboard-readability-pass.md`.

Chief of Staff command map cleanup status command:

```bash
bin/chief-of-staff --command-map-status
```

See `docs/chief-of-staff-command-map-cleanup.md`.

Chief of Staff help examples polish status command:

```bash
bin/chief-of-staff --help-examples-status
```

See `docs/chief-of-staff-help-examples-polish.md`.

Chief of Staff workflow quick-start guide status command:

```bash
bin/chief-of-staff --workflow-quick-start-status
```

See `docs/chief-of-staff-workflow-quick-start-guide.md`.

Dashboard section summary polish status command:

```bash
bin/chief-of-staff --dashboard-section-summary-status
```

See `docs/dashboard-section-summary-polish.md`.

Teacher planning command organization status command:

```bash
bin/chief-of-staff --teacher-planning-command-status
```

See `docs/teacher-planning-command-organization.md`.

Lesson review workflow polish status command:

```bash
bin/chief-of-staff --lesson-review-workflow-status
```

See `docs/lesson-review-workflow-polish.md`.

Review notes workflow polish status command:

```bash
bin/chief-of-staff --review-notes-workflow-status
```

See `docs/review-notes-workflow-polish.md`.

Lesson review workflow (safe sample slug only; no student data):

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
```

Review notes workflow (safe sample slug only; no student data):

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --lesson-review-view fractions-review
```

Teacher planning commands (safe sample slug only; no student data):

```bash
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --document-indexing-plan-status
```

Quick start (start here):

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --list-workflows
bin/chief-of-staff --workflow-quick-start-status
```

Common examples (daily health check, teacher review, developer/Cursor verification):

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --list-workflows
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --cursor-workflow-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
```

Local command launcher status command:

```bash
bin/chief-of-staff --command-launcher-status
```

See `docs/chief-of-staff-command-launcher-refinement.md`.

Dashboard and grouped command discovery:

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --command-launcher-status
bin/chief-of-staff --list-workflows
```

See `docs/dashboard-polish-command-grouping-follow-up.md`.

## Future Specialist: 3D Design Agent

Phase 0 now prewires the Mac for future 3D design work.

The 3D Design Agent is a future specialist for classroom and business 3D printing. It is separate from, but coordinated by, the Chief of Staff.

Bambu Studio and OpenSCAD are installed/prepared. Personal/reference work is separated from commercial product work. The 3D Agent can warn, classify, and recommend review, but cannot block or stop printing.

Full 3D Agent implementation comes after the teaching Chief of Staff foundation.

See:

- `docs/3d-printing-day-1-setup.md`
- `docs/3d-printing-roadmap.md`
- `3d-agent/README.md`

## Phase 1B: Interactive Chief of Staff CLI

The CLI is the first runnable Chief of Staff interface.

It uses approved Markdown context and explicit files only. It does not scan Drive, Gmail, or local folders. It supports dry-run mode so Owen can inspect the exact prompt/context before any model call.

It also supports `--status` and `--show-context` for debugging, making it safe to test before connecting any external data sources.

Example:

```bash
bin/chief-of-staff --workflow request-training-materials --question "What should I give you first?"
```

Dashboard:

```bash
bin/chief-of-staff --dashboard
```

Lesson Planning Workspace:

```bash
bin/chief-of-staff --lesson-status
```

Developer Mode Project Templates:

```bash
bin/chief-of-staff --developer-status
bin/chief-of-staff --create-developer-project TEMPLATE_NAME PROJECT_SLUG
```

## Cursor Workflow

Local Cursor workflow status command:

```bash
bin/chief-of-staff --cursor-workflow-status
```

See `docs/cursor-workflow-operating-system.md`.

See `docs/interactive-chief-of-staff-cli.md`.
See `docs/chief-of-staff-dashboard.md`.
See `docs/lesson-planning-workspace.md`.
See `docs/lesson-activity-assessment-helper.md`.
See `docs/lesson-pack-status-planner.md`.
See `docs/lesson-brief-queue-integration.md`.
See `docs/lesson-planning-workflow-guide.md`.
See `docs/developer-mode-project-templates.md`.

## Phase 1C: Project Memory + Writing Style Memory

The Chief of Staff now has approved Markdown memory files.

Memory is optional and explicit. Use `--include-memory` to include all approved memory, or targeted flags to include only project, writing style, teaching context, preferences, decisions, or active priorities memory.

Memory does not scan personal files, Drive, Gmail, Canvas, or local folders.

Use `--memory-status` to inspect memory freshness. Use `--validate-memory` as a quick warning check before important memory-assisted runs.

Example:

```bash
bin/chief-of-staff --workflow project-review --include-memory --question "What should I work on next?"
```

## Phase 1D: Intake Review Queue

The Chief of Staff now has a Markdown-based intake queue for reviewing candidate context before approval.

Raw intake is not approved context. Approved intake summaries can be included explicitly with `--include-approved-intake`.

Raw, quarantine, and approved file folders are ignored by Git except for `.gitkeep`. This prepares the repo for later selected local folder indexing and connected-source workflows without unsafe automatic ingestion.

Examples:

```bash
bin/chief-of-staff --intake-status
```

```bash
bin/chief-of-staff --intake-summary
```

```bash
bin/chief-of-staff --validate-intake
```

```bash
bin/chief-of-staff \
  --workflow intake-review \
  --include-intake-policy \
  --include-intake-queue \
  --include-intake-checklist \
  --question "What needs review?" \
  --dry-run
```

## Phase 0D: Final Installer Audit

Phase 0D adds the final repository preflight before opening the new MacBook Pro M5 Pro.

Run:

```bash
bash setup/98-final-audit.sh
```

The audit checks repo cleanliness, setup scripts, CLI readiness, memory and intake safety checks, 3D readiness, `.gitignore` protection, recovery docs, and obvious secret patterns. It does not install anything and does not call a model.

### Phase 0E Vibe Engine handoff

Phase 0E adds the visual/vibe/image-safety layer for the Teacher AI Workstation. For the current completion status, verification command, and handoff into Phase 1, see:

* [Phase 0E Completion Handoff](docs/phase-0e-completion-handoff.md)
* [Phase 0E Quick Commands](docs/phase-0e-quick-commands.md)
* [Phase 1 Readiness Checklist](docs/phase-1-readiness-checklist.md)
* [Phase 1 Chief of Staff Status Audit](docs/phase-1-chief-of-staff-status-audit.md)
* [Developer Mode Readiness](docs/developer-mode-readiness.md)
* [Build Queue](docs/build-queue.md)
* [Open Threads](docs/open-threads.md)

## Phase 0A Completion Checklist

Before moving to later Teacher OS development, confirm:

- [ ] Automated bootstrap complete
- [ ] Manual Day 1 checklist complete
- [ ] Mac restarted once after setup
- [ ] `bash setup/99-verify-setup.sh` rerun after restart
- [ ] Ricoh printer certification scheduled for school
