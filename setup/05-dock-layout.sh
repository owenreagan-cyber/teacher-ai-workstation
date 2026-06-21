#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"

warn() { echo "WARN: $1"; }
pass() { echo "PASS: $1"; }

# Casual Anime Mode uses the same macOS user account as Teacher Workstation Mode.
# macOS does not reliably provide a built-in public command-line way to maintain
# a fully separate Dock per Focus mode without extra tooling. Casual Mode should
# be handled through Focus mode, wallpaper, browser profile, and manual Dock
# preferences instead of this shared Dock initializer.

echo "Setting up the Teacher Workstation Dock layout..."

if ! command -v dockutil >/dev/null 2>&1; then
  warn "dockutil is not installed yet, so Dock layout setup was skipped."
  exit 0
fi

add_app() {
  local label="$1"
  local path="$2"

  if [[ ! -e "${path}" ]]; then
    warn "${label} was not found at ${path}; skipping this Dock item."
    return 0
  fi

  if dockutil --find "${label}" >/dev/null 2>&1; then
    echo "${label} is already in the Dock."
  else
    dockutil --add "${path}" --no-restart >/dev/null 2>&1 || warn "Could not add ${label} to the Dock."
  fi
}

add_app "Finder" "/System/Library/CoreServices/Finder.app"
add_app "Google Chrome" "/Applications/Google Chrome.app"
add_app "Arc" "/Applications/Arc.app"
add_app "Cursor" "/Applications/Cursor.app"
add_app "Ghostty" "/Applications/Ghostty.app"
add_app "Obsidian" "/Applications/Obsidian.app"
add_app "Raycast" "/Applications/Raycast.app"
add_app "Calendar" "/System/Applications/Calendar.app"
add_app "Notes" "/System/Applications/Notes.app"
add_app "Reminders" "/System/Applications/Reminders.app"

if [[ -e "/Applications/Canva.app" ]]; then
  add_app "Canva" "/Applications/Canva.app"
else
  warn "Canva is not installed; skipping optional Dock item."
fi

if [[ -e "/System/Applications/System Settings.app" ]]; then
  add_app "System Settings" "/System/Applications/System Settings.app"
elif [[ -e "/Applications/System Preferences.app" ]]; then
  add_app "System Preferences" "/Applications/System Preferences.app"
else
  warn "System Settings was not found; skipping this Dock item."
fi

killall Dock >/dev/null 2>&1 || true
pass "Teacher Workstation Dock layout step completed."
