# Recovery Guide

The Phase 0 initializer is designed to be safe to rerun.

## Rerun the initializer safely

From the repo root, run:

```bash
./bootstrap.sh
```

The scripts create folders with `mkdir -p`, avoid deleting user files, and skip optional steps when they cannot complete.

## Rerun only one setup script

Run a single script from the repo root. For example:

```bash
setup/99-verify-setup.sh
```

or:

```bash
setup/06-wallpapers.sh
```

## Automated verification vs final manual verification

`./bootstrap.sh` runs automated verification once at the end. That first verification checks scriptable setup items only.

After bootstrap, complete the manual checklist in `docs/day-1-manual-steps.md`, restart the Mac once, and rerun:

```bash
bash setup/99-verify-setup.sh
```

Some items are human-verified only, including Focus modes, widgets, browser profiles, AlDente preferences, Raycast preferences, Obsidian vault selection, 1Password sign-in, iPad/iPhone Focus sync, and physical Ricoh printing.

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

## Reinstall apps with Brewfile

Run:

```bash
brew bundle --file=./Brewfile
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
