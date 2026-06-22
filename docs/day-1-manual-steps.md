# Phase 0 Day 1 Manual Steps

Use this beginner-friendly checklist on the first day with the new MacBook Pro.

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

## Finish Day 1

- [ ] Mac restarted after automated setup and manual configuration
- [ ] Reran `bash setup/99-verify-setup.sh`

When every item is checked, run:

```bash
bash setup/99-verify-setup.sh
```
