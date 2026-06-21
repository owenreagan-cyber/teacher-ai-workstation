Open your MacBook Pro…

# Teacher AI Workstation

Phase 0 is the beginner-friendly workstation setup skeleton for the Teacher AI Workstation. It prepares a Mac for later phases without building the React app, Canvas tools, agents, Docker services, or cloud databases.

## Start here

Open Terminal, then run:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/owenreagan-cyber/teacher-ai-workstation.git
cd teacher-ai-workstation
chmod +x bootstrap.sh setup/*.sh
./bootstrap.sh
```

## What Phase 0 does

The bootstrap script runs the setup scripts in order:

1. Checks that the machine is a supported Mac with Apple Silicon, internet, enough disk space, and Xcode Command Line Tools.
2. Installs Homebrew if it is missing.
3. Installs workstation apps and command-line tools from `Brewfile`.
4. Applies simple macOS defaults for Finder, Dock, screenshots, keyboard, trackpad, and external volume behavior.
5. Creates teaching, AI, notes, screenshots, media, and archive folders.
6. Verifies the setup and prints `PASS`, `WARN`, or `FAIL` results.

Logs are written to `logs/setup.log`.

## If Xcode Command Line Tools are missing

Run:

```bash
xcode-select --install
```

Then rerun:

```bash
./bootstrap.sh
```

## Verification Workflow

`./bootstrap.sh` runs `setup/99-verify-setup.sh` once at the end as automated setup verification. This checks scriptable setup items only, such as installed commands, folders, selected macOS defaults, Git remote state, SSH key presence, and Ollama reachability.

After bootstrap finishes, complete the manual checklist in `docs/day-1-manual-steps.md`. Manual items include Focus modes, widgets, browser profiles, Raycast preferences, Obsidian vault selection, 1Password sign-in, AlDente preferences, iPad/iPhone Focus sync, and Ricoh physical print certification.

When the manual checklist is complete, restart the Mac once, then run the same verification script again:

```bash
bash setup/99-verify-setup.sh
```

## Phase 0 Completion Checklist

Before moving to Phase 1, confirm:

- [ ] Automated bootstrap complete
- [ ] Manual Focus/profile steps complete
- [ ] Verification passes
- [ ] Ricoh print test completed
- [ ] Ready for Phase 1 Teacher OS app skeleton

## Suggested first commit

```bash
git add README.md .gitignore Brewfile bootstrap.sh machine-spec.md setup/00-check-system.sh setup/01-install-homebrew.sh setup/02-install-apps.sh setup/03-macos-defaults.sh setup/04-folder-structure.sh setup/99-verify-setup.sh logs/.gitkeep
git commit -m "feat: add phase 0 day 1 mac initializer skeleton"
git push origin HEAD
```
