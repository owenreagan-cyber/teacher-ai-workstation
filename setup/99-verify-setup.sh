#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"
EXPECTED_HTTPS="https://github.com/owenreagan-cyber/teacher-ai-workstation.git"
EXPECTED_SSH="git@github.com:owenreagan-cyber/teacher-ai-workstation.git"

pass() { echo "PASS: $1"; }
warn() { echo "WARN: $1"; }
fail() { echo "FAIL: $1"; }

check_command() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "${name} is installed."
  else
    fail "${name} is missing."
  fi
}

echo "Automated Setup Verification"
echo "This checks scriptable setup items only."
echo "Manual items like Focus Modes, widgets, browser profiles, AlDente settings, Raycast preferences, Obsidian vault setup, 1Password sign-in, iPad/iPhone Focus sync, and Ricoh physical printing must be checked manually in docs/day-1-manual-steps.md."
echo ""

check_command brew
check_command git
check_command gh
check_command node
check_command python
check_command ollama

if command -v dockutil >/dev/null 2>&1; then
  pass "dockutil is installed."
else
  warn "dockutil is not installed, so automated Dock layout may be skipped."
fi

[[ -d "${HOME}/Screenshots" ]] && pass "~/Screenshots exists." || fail "~/Screenshots is missing."
[[ -d "${HOME}/Teaching" ]] && pass "~/Teaching exists." || fail "~/Teaching is missing."
[[ -d "${HOME}/Teaching/Print-Certified" ]] && pass "~/Teaching/Print-Certified exists." || fail "~/Teaching/Print-Certified is missing."
[[ -d "${HOME}/Pictures/Teacher OS Wallpapers/Teacher Mode" ]] && pass "Teacher Mode wallpaper folder exists." || fail "Teacher Mode wallpaper folder is missing."
[[ -d "${HOME}/Pictures/Teacher OS Wallpapers/Casual Anime Mode" ]] && pass "Casual Anime Mode wallpaper folder exists." || fail "Casual Anime Mode wallpaper folder is missing."

screenshot_location="$(defaults read com.apple.screencapture location 2>/dev/null || true)"
if [[ "${screenshot_location}" == "${HOME}/Screenshots" ]]; then
  pass "Screenshot location is ${HOME}/Screenshots."
else
  warn "Screenshot location is '${screenshot_location:-not set}', expected ${HOME}/Screenshots."
fi

dock_autohide="$(defaults read com.apple.dock autohide 2>/dev/null || true)"
if [[ "${dock_autohide}" == "1" ]]; then
  pass "Dock autohide is enabled."
else
  warn "Dock autohide is not enabled."
fi

if git config --global user.name >/dev/null 2>&1 && git config --global user.email >/dev/null 2>&1; then
  pass "Git name and email are configured."
else
  warn "Git name and/or email are not configured yet."
fi

remote="$(git remote get-url origin 2>/dev/null || true)"
if [[ "${remote}" == "${EXPECTED_HTTPS}" || "${remote}" == "${EXPECTED_SSH}" ]]; then
  pass "Git origin remote points to the Teacher AI Workstation repository."
elif [[ -n "${remote}" ]]; then
  warn "Git origin remote points to ${remote}, not the expected Teacher AI Workstation repository."
else
  warn "Git origin remote is not configured."
fi

if compgen -G "${HOME}/.ssh/id_*.pub" >/dev/null; then
  pass "SSH public key is present."
else
  warn "No SSH public key found in ~/.ssh."
fi

if command -v ollama >/dev/null 2>&1; then
  if curl -fsS http://localhost:11434 >/dev/null 2>&1; then
    pass "Ollama service is reachable."
  else
    warn "Ollama CLI is installed, but the service is not reachable right now."
  fi
else
  warn "Ollama CLI is missing, so the service could not be checked."
fi

echo ""
echo "If this was run immediately after bootstrap, complete docs/day-1-manual-steps.md next."
echo "If this was run after manual setup and restart, review any WARN/FAIL items above."
