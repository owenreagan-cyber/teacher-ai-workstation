# Phase 0 Day 1 Manual Steps

Use this checklist after `./bootstrap.sh` finishes and after you review the automated verification output.

- [ ] Apple first boot completed
- [ ] FileVault enabled
- [ ] Find My Mac enabled
- [ ] Touch ID configured
- [ ] Teacher Focus Mode created
- [ ] Casual Anime Focus Mode created
- [ ] Teacher widgets added
- [ ] Casual widgets added
- [ ] Work browser profile created
- [ ] Casual browser profile created
- [ ] Raycast opened and configured
- [ ] Obsidian vault opened
- [ ] 1Password signed in
- [ ] AlDente charge limit set
- [ ] iPad/iPhone Focus sync enabled
- [ ] Ricoh printer certification completed
- [ ] Restarted Mac after automated setup and manual configuration

After every manual item is complete and the Mac has restarted, run:

```bash
bash setup/99-verify-setup.sh
```

Note: This verification script cannot fully confirm Focus Modes, widgets, browser profiles, AlDente preferences, Raycast preferences, Obsidian vault selection, 1Password sign-in, iPad/iPhone Focus sync, or physical Ricoh printing. Those items must be checked by the user.
