Open your MacBook Pro…

# Teacher AI Workstation

This repository prepares a brand-new MacBook Pro to become a Teacher AI Workstation.

Phase 0A Day 1 is only the core Mac setup. It makes the Mac clean, safe, organized, beginner-friendly, and ready for later Teacher OS development.

It does not build the React app, Canvas tools, agents, Docker services, Supabase, Firestore, MongoDB, or classroom content workflows.

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
- `setup/99-verify-setup.sh`: verifies scriptable setup only.

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

## Phase 0A Completion Checklist

Before moving to later Teacher OS development, confirm:

- [ ] Automated bootstrap complete
- [ ] Manual Day 1 checklist complete
- [ ] Mac restarted once after setup
- [ ] `bash setup/99-verify-setup.sh` rerun after restart
- [ ] Ricoh printer certification scheduled for school
