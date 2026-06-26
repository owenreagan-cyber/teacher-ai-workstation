#!/usr/bin/env bash
set -euo pipefail

SHORTCUTS_DIR="$HOME/.teacher-ai-workstation/shortcuts"
REPO_DIR="$HOME/Projects/teacher-ai-workstation"

mkdir -p "$SHORTCUTS_DIR"

cat >"$SHORTCUTS_DIR/phase-0e-status.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/Projects/teacher-ai-workstation"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this generated script.\n'
  exit 1
fi

cd "$REPO_DIR"
bash scripts/phase-0e-summary.sh
SCRIPT

cat >"$SHORTCUTS_DIR/image-review-status.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/Projects/teacher-ai-workstation"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this generated script.\n'
  exit 1
fi

cd "$REPO_DIR"
python3 scripts/image-review-status.py
SCRIPT

cat >"$SHORTCUTS_DIR/phase-0e-verify.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/Projects/teacher-ai-workstation"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this generated script.\n'
  exit 1
fi

cd "$REPO_DIR"
bash scripts/verify-phase-0e.sh
SCRIPT

chmod +x \
  "$SHORTCUTS_DIR/phase-0e-status.sh" \
  "$SHORTCUTS_DIR/image-review-status.sh" \
  "$SHORTCUTS_DIR/phase-0e-verify.sh"

cat <<STEPS

Phase 0E Shortcuts status tools installed.

Generated scripts:
- $SHORTCUTS_DIR/phase-0e-status.sh
- $SHORTCUTS_DIR/image-review-status.sh
- $SHORTCUTS_DIR/phase-0e-verify.sh

These scripts are status/verification only. They do not use --apply, modify Photos,
set wallpaper, require admin, call APIs, use secrets, or change Display scaling.

Manual Shortcuts setup:
1. Open Shortcuts app.
2. Create a new shortcut.
3. Add "Run Shell Script".
4. Set shell to zsh or bash.
5. Paste the full path to one generated script, for example:
   $SHORTCUTS_DIR/phase-0e-status.sh
6. Set "Pass Input" to stdin or ignore input.
7. Leave "Run as Administrator" off.
8. Name the shortcut, for example:
   Phase 0E Status
9. Run it once to test.

Repeat for:
- Phase 0E Status: $SHORTCUTS_DIR/phase-0e-status.sh
- Image Review Status: $SHORTCUTS_DIR/image-review-status.sh
- Phase 0E Verify: $SHORTCUTS_DIR/phase-0e-verify.sh

Note: older Vibe Buttons use ~/Shortcuts-Scripts. These Phase 0E tools use:
$SHORTCUTS_DIR

Repo path expected by generated scripts:
$REPO_DIR

STEPS
