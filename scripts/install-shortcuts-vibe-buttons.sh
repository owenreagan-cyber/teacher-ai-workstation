#!/usr/bin/env bash
set -euo pipefail

SHORTCUTS_DIR="$HOME/Shortcuts-Scripts"

mkdir -p "$SHORTCUTS_DIR"

cat >"$SHORTCUTS_DIR/vibe-casual.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Projects/teacher-ai-workstation"
bash scripts/mode-casual.sh --apply
bash scripts/mode-status.sh
SCRIPT

cat >"$SHORTCUTS_DIR/vibe-teacher.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Projects/teacher-ai-workstation"
bash scripts/mode-teacher.sh --apply
bash scripts/mode-status.sh
SCRIPT

cat >"$SHORTCUTS_DIR/vibe-status.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Projects/teacher-ai-workstation"
bash scripts/mode-status.sh
SCRIPT

chmod +x \
  "$SHORTCUTS_DIR/vibe-casual.sh" \
  "$SHORTCUTS_DIR/vibe-teacher.sh" \
  "$SHORTCUTS_DIR/vibe-status.sh"

cat <<STEPS

Apple Shortcuts Vibe Buttons installed.

Local scripts:
- $SHORTCUTS_DIR/vibe-casual.sh
- $SHORTCUTS_DIR/vibe-teacher.sh
- $SHORTCUTS_DIR/vibe-status.sh

Manual next steps in Apple Shortcuts:
1. Open the Shortcuts app.
2. Create a new Shortcut.
3. Add action: Run Shell Script.
4. Set shell to /bin/bash if available.
5. For Casual Anime, use:
   $SHORTCUTS_DIR/vibe-casual.sh
   Name: Vibe: Casual Anime
6. Repeat for Teacher Coding:
   $SHORTCUTS_DIR/vibe-teacher.sh
   Name: Vibe: Teacher Coding
7. Repeat for Status:
   $SHORTCUTS_DIR/vibe-status.sh
   Name: Vibe: Visual Mode Status

This installer does not automate the Shortcuts app, install dependencies,
use network calls, touch accounts or secrets, change Display scaling, or
touch Photos, Spotify, wallpapers, Raycast, browser profiles, or iCloud.

STEPS
