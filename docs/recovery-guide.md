# Recovery Guide

The Phase 0 initializer is designed to be safe to rerun.

The scripts create folders with `mkdir -p`, avoid deleting user files, and skip or warn on optional steps that cannot complete automatically.

## Rerun the initializer safely

From the repo root, run:

```bash
./bootstrap.sh
```

If setup stops, read the last `FAIL` or `WARN` message first. It should explain the next step.

## Rerun only one setup script

Run a single script from the repo root. For example:

```bash
setup/99-verify-setup.sh
```

or:

```bash
setup/06-wallpapers.sh
```

## Check the setup log

Open the setup log with:

```bash
cat logs/setup.log
```

Search for warnings with:

```bash
rg "WARN|FAIL" logs/setup.log
```

## Run verification

Run:

```bash
setup/99-verify-setup.sh
```

`setup/99-verify-setup.sh` verifies scriptable setup only. Focus Modes, widgets, browser profiles, Raycast preferences, Obsidian vault setup, 1Password sign-in, AlDente preferences, iPad/iPhone Focus sync, and Ricoh physical printing are human-verified in `docs/day-1-manual-steps.md`.

## Reinstall apps with Brewfile

Run:

```bash
brew bundle --file=./Brewfile
```

If Homebrew reports a cask problem, rerun verification afterward:

```bash
bash setup/99-verify-setup.sh
```

## Recover if Xcode Command Line Tools interrupted setup

If setup stopped because Xcode Command Line Tools were missing, run:

```bash
xcode-select --install
```

Wait for the installer to finish. Then rerun:

```bash
./bootstrap.sh
```

## Finish after manual recovery

After any recovery work, restart once and run:

```bash
bash setup/99-verify-setup.sh
```
