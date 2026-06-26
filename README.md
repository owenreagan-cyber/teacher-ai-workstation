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

See `docs/interactive-chief-of-staff-cli.md`.

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
