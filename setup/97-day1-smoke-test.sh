#!/usr/bin/env bash
set -euo pipefail

# Day 1 Smoke Test
# This script checks the parts of the Mac setup that can be tested automatically
# without requiring private account credentials or making paid-service decisions.
# It is intentionally softer than setup/99-verify-setup.sh:
# - FAIL means a core Day 1 expectation is missing.
# - WARN means optional/manual setup is missing or cannot be verified automatically.

export PATH="/opt/homebrew/bin:${PATH}"

failure_count=0
warning_count=0

pass() { echo "PASS: $1"; }
warn() {
  echo "WARN: $1"
  warning_count=$((warning_count + 1))
}
fail() {
  echo "FAIL: $1"
  failure_count=$((failure_count + 1))
}

check_command_required() {
  local name="$1"
  local label="${2:-$1}"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "${label} command is available."
  else
    fail "${label} command is missing."
  fi
}

check_command_optional() {
  local name="$1"
  local label="${2:-$1}"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "${label} command is available."
  else
    warn "${label} command is missing or not installed yet."
  fi
}

check_app_required() {
  local app_name="$1"
  if [[ -d "/Applications/${app_name}.app" || -d "${HOME}/Applications/${app_name}.app" ]]; then
    pass "${app_name}.app is installed."
  else
    fail "${app_name}.app is missing."
  fi
}

check_app_optional() {
  local app_name="$1"
  if [[ -d "/Applications/${app_name}.app" || -d "${HOME}/Applications/${app_name}.app" ]]; then
    pass "${app_name}.app is installed."
  else
    warn "${app_name}.app is missing or not installed yet."
  fi
}

check_brew_cask_optional() {
  local cask="$1"
  local label="${2:-$1}"
  if command -v brew >/dev/null 2>&1 && brew list --cask "${cask}" >/dev/null 2>&1; then
    pass "${label} Homebrew cask is installed."
  else
    warn "${label} Homebrew cask is not installed."
  fi
}

check_default_value() {
  local domain="$1"
  local key="$2"
  local expected="$3"
  local label="$4"
  local value=""
  value="$(defaults read "${domain}" "${key}" 2>/dev/null || true)"
  if [[ "${value}" == "${expected}" ]]; then
    pass "${label} is ${expected}."
  elif [[ -n "${value}" ]]; then
    warn "${label} is ${value}, expected ${expected}."
  else
    warn "${label} is not set."
  fi
}

section() {
  echo
  echo "== $1 =="
}

echo "Teacher AI Workstation Day 1 smoke test"
echo "This checks what can be tested safely from the command line."

section "Core command line tools"
check_command_required brew Homebrew
check_command_required git Git
check_command_required gh "GitHub CLI"
check_command_required node Node.js
check_command_required python3 "Python 3"
check_command_required starship Starship
check_command_required zoxide Zoxide
check_command_required eza Eza
check_command_required bat Bat
check_command_required rg Ripgrep
check_command_required fzf FZF
check_command_required uv UV
check_command_required llm LLM
check_command_required fabric Fabric

section "Shell profile and prompt"
if [[ -f "${HOME}/.zshrc" ]] && grep -q "teacher-ai-workstation" "${HOME}/.zshrc"; then
  pass "~/.zshrc contains teacher-ai-workstation setup."
else
  fail "~/.zshrc does not contain teacher-ai-workstation setup."
fi

if zsh -lc 'type starship >/dev/null 2>&1' >/dev/null 2>&1; then
  pass "Starship loads in a fresh zsh login shell."
else
  warn "Starship did not load in a fresh zsh login shell."
fi

if zsh -lc 'type z >/dev/null 2>&1 || type zoxide >/dev/null 2>&1' >/dev/null 2>&1; then
  pass "Zoxide is visible in a fresh zsh login shell."
else
  warn "Zoxide is not visible in a fresh zsh login shell."
fi

if zsh -lc 'alias ll >/dev/null 2>&1 || type eza >/dev/null 2>&1' >/dev/null 2>&1; then
  pass "Eza/ll shell convenience appears available."
else
  warn "Eza/ll shell convenience was not found."
fi

section "Required desktop apps"
check_app_required "Cursor"
check_app_required "1Password"
check_app_optional "Raycast"
check_app_optional "Obsidian"
check_app_optional "Google Chrome"
check_app_optional "Arc"
check_app_optional "AlDente"
check_app_optional "Bambu Studio"

section "Optional AI desktop and coding tools"
check_app_optional "ChatGPT"
check_app_optional "Codex"
check_app_optional "Gemini"
check_app_optional "Antigravity"
check_app_optional "Claude"
check_command_optional codex "Codex CLI"
check_command_optional claude "Claude Code CLI"
check_command_optional gemini "Gemini CLI"

section "Homebrew cask cross-checks"
check_brew_cask_optional cursor Cursor
check_brew_cask_optional 1password 1Password
check_brew_cask_optional raycast Raycast
check_brew_cask_optional obsidian Obsidian
check_brew_cask_optional google-chrome "Google Chrome"
check_brew_cask_optional arc Arc
check_brew_cask_optional aldente AlDente
check_brew_cask_optional bambu-studio "Bambu Studio"

section "macOS scriptable settings"
screenshot_location="$(defaults read com.apple.screencapture location 2>/dev/null || true)"
if [[ "${screenshot_location}" == "${HOME}/Screenshots" ]]; then
  pass "Screenshots save to ${HOME}/Screenshots."
else
  warn "Screenshot location is '${screenshot_location:-not set}', expected ${HOME}/Screenshots."
fi

check_default_value com.apple.dock autohide 1 "Dock autohide"

dock_tilesize="$(defaults read com.apple.dock tilesize 2>/dev/null || true)"
if [[ -n "${dock_tilesize}" ]]; then
  pass "Dock icon size is set to ${dock_tilesize}."
else
  warn "Dock icon size could not be read."
fi

finder_icon_size="$(defaults read com.apple.finder DesktopViewSettings 2>/dev/null | awk '/iconSize/ { gsub(/[^0-9]/, "", $3); print $3; exit }' || true)"
if [[ -n "${finder_icon_size}" ]]; then
  pass "Desktop icon size appears to be ${finder_icon_size}."
else
  warn "Desktop icon size could not be read automatically."
fi

section "Folders and repo files"
[[ -d "${HOME}/Screenshots" ]] && pass "~/Screenshots exists." || fail "~/Screenshots is missing."
[[ -d "${HOME}/Teaching" ]] && pass "~/Teaching exists." || fail "~/Teaching is missing."
[[ -d "${HOME}/3D-Printing" ]] && pass "~/3D-Printing exists." || warn "~/3D-Printing is missing."
[[ -f "docs/day-1-manual-steps.md" ]] && pass "docs/day-1-manual-steps.md exists." || warn "docs/day-1-manual-steps.md is missing."
[[ -f "docs/backup-exclusions.md" ]] && pass "docs/backup-exclusions.md exists." || warn "docs/backup-exclusions.md is missing."
[[ -f "3d-agent/verification/pre-slicer-checklist.md" ]] && pass "3d-agent verification checklist exists." || warn "3d-agent verification checklist is missing."

section "Git and GitHub"
if gh auth status >/dev/null 2>&1; then
  pass "GitHub CLI is authenticated."
else
  warn "GitHub CLI is not authenticated. Run: gh auth login"
fi

if git status >/dev/null 2>&1; then
  pass "Current folder is a Git repository."
  if [[ -z "$(git status --porcelain)" ]]; then
    pass "Git working tree is clean."
  else
    warn "Git working tree has local changes. Run: git status"
  fi
else
  warn "Current folder is not a Git repository."
fi

section "Chief of Staff local smoke tests"
if [[ -x "bin/chief-of-staff" ]]; then
  pass "bin/chief-of-staff is executable."
  if bin/chief-of-staff --status >/dev/null 2>&1; then
    pass "Chief of Staff --status succeeded."
  else
    warn "Chief of Staff --status did not succeed."
  fi
  if bin/chief-of-staff --list-workflows >/dev/null 2>&1; then
    pass "Chief of Staff --list-workflows succeeded."
  else
    warn "Chief of Staff --list-workflows did not succeed."
  fi
  if bin/chief-of-staff --memory-status >/dev/null 2>&1; then
    pass "Chief of Staff --memory-status succeeded."
  else
    warn "Chief of Staff --memory-status did not succeed."
  fi
  if bin/chief-of-staff --intake-status >/dev/null 2>&1; then
    pass "Chief of Staff --intake-status succeeded."
  else
    warn "Chief of Staff --intake-status did not succeed."
  fi
else
  warn "bin/chief-of-staff is missing or not executable."
fi

section "Account setup that cannot be safely automated"
warn "1Password sign-in must be confirmed by opening the app."
warn "Cursor sign-in/model provider setup must be confirmed in Cursor."
warn "Apple Account, Google/Gmail, OpenAI/ChatGPT, Claude, Gemini, and Bambu accounts require manual sign-in."
warn "Focus Modes, widgets, browser spaces/profiles, and iPad/iPhone sync require human verification."
warn "Ricoh printing requires physical school network/printer access."

section "Summary"
echo "Warnings: ${warning_count}"
echo "Failures: ${failure_count}"

if (( failure_count > 0 )); then
  echo "FAIL: Day 1 smoke test found ${failure_count} critical issue(s)."
  exit 1
fi

echo "PASS: Day 1 smoke test completed with no critical failures."
