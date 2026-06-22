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

To rerun only the shell profile setup, run:

```bash
bash setup/10-shell-profile.sh
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

## Inspect shell profile changes

The installer manages only one marked block in `~/.zshrc`.

To inspect that block, run:

```bash
sed -n '/# >>> teacher-ai-workstation >>>/,/# <<< teacher-ai-workstation <<</p' ~/.zshrc
```

To remove only the Teacher AI Workstation managed block if needed, first make a backup:

```bash
cp ~/.zshrc ~/.zshrc.backup-before-teacher-ai-workstation
```

Then remove the managed block:

```bash
awk '
  $0 == "# >>> teacher-ai-workstation >>>" { in_block = 1; next }
  $0 == "# <<< teacher-ai-workstation <<<" { in_block = 0; next }
  !in_block { print }
' ~/.zshrc > ~/.zshrc.tmp && mv ~/.zshrc.tmp ~/.zshrc
```

Open a new Terminal window afterward, or run:

```bash
source ~/.zshrc
```

## Reinstall apps with Brewfile

Run:

```bash
brew bundle --file=./Brewfile
```

If Homebrew reports a cask problem, rerun verification afterward:

```bash
bash setup/99-verify-setup.sh
```

If OpenSCAD is missing, rerun:

```bash
brew bundle --file=./Brewfile
```

If Bambu Studio is missing, rerun `brew bundle --file=./Brewfile` or install it manually.

If 3D folders are missing, rerun:

```bash
bash setup/04-folder-structure.sh
```

If commercial/reference files get mixed, move unapproved or downloaded reference files to:

```bash
~/3D-Printing/Reference-Only
```

Reference-Only is a warning/category folder, not a software restriction.

## Recover Chief of Staff CLI

If `bin/chief-of-staff` is not executable, run:

```bash
chmod +x bin/chief-of-staff tests/smoke-chief-of-staff-cli.sh
```

If `llm` is missing, rerun:

```bash
brew bundle --file=./Brewfile
```

or rerun:

```bash
./bootstrap.sh
```

If a workflow name fails, run:

```bash
bin/chief-of-staff --list-workflows
```

If the CLI includes the wrong context, rerun with `--dry-run` and inspect the included files.

If the CLI cannot find the repo, run it from inside the repo or set:

```bash
export CHIEF_OF_STAFF_REPO="/path/to/teacher-ai-workstation"
```

If a large context file is refused, choose a smaller file or intentionally rerun with `--force-large-context`.

## Recover Chief of Staff memory

If memory files are missing, rerun the repo update or restore `assistant/memory` from Git.

If memory is accidentally included, rerun without `--include-memory`.

If memory seems stale, edit the Markdown file directly and label uncertain facts as "needs review."

If sensitive information is accidentally added to memory, remove it immediately and do not use that file as context until reviewed.

If `--memory-status` shows stale files, review and update the relevant Markdown file or label the facts "needs review."

If `--validate-memory` warns, inspect the file manually before including memory.

If `memory-log.md` is missing, restore it from Git or recreate it from `assistant/memory/README.md` guidance.

## Recover Chief of Staff intake

If intake files are missing, restore `assistant/intake` from Git.

If intake validation warns, inspect the named file manually before using it as context.

If raw intake was accidentally added, move it to quarantine or delete it if inappropriate.

If sensitive material is found, do not include it in model context.

If approved intake is stale, update `assistant/intake/approved-context.md` or mark it needs review.

If `--context` refuses raw intake, use a sanitized summary instead.

If approved, raw, or quarantine files appear in `git status`, confirm `.gitignore` rules are present and remove accidental staged files before committing.

If `rejected-context.md` or `quarantine.md` must be reviewed in model context, rerun with `--force-sensitive-context` and treat the result as review-only.

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

## Restart Ollama after `aiflush`

The `aiflush` alias stops LM Studio and Ollama without using force-kill mode. To restart Ollama later, run:

```bash
brew services start ollama
```

Or open the Ollama app from Applications.
