#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"
EXPECTED_HTTPS="https://github.com/owenreagan-cyber/teacher-ai-workstation.git"
EXPECTED_SSH="git@github.com:owenreagan-cyber/teacher-ai-workstation.git"
ZSHRC="${HOME}/.zshrc"
START_MARKER="# >>> teacher-ai-workstation >>>"
END_MARKER="# <<< teacher-ai-workstation <<<"
failure_count=0

pass() { echo "PASS: $1"; }
warn() { echo "WARN: $1"; }
fail() {
  echo "FAIL: $1"
  failure_count=$((failure_count + 1))
}

check_command() {
  local name="$1"
  local label="${2:-$1}"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "${label} is installed."
  else
    fail "${label} is missing."
  fi
}

check_default_false() {
  local domain="$1"
  local key="$2"
  local label="$3"
  local value=""

  value="$(defaults read "${domain}" "${key}" 2>/dev/null || true)"
  case "${value}" in
    0|false|FALSE)
      pass "${label} is disabled."
      ;;
    *)
      fail "${label} is not disabled."
      ;;
  esac
}

echo "Verifying Teacher AI Workstation Phase 0 setup..."
echo "This verifies scriptable setup only."
echo "It is not final manual certification."
echo

check_command brew
check_command git
check_command gh
check_command node
check_command python3 "Python 3"
check_command ollama
check_command starship
check_command zoxide
check_command atuin
check_command eza
check_command bat
check_command fzf
check_command rg "ripgrep"
check_command uv
check_command llm
check_command fabric

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

if [[ -d "/Applications/Bambu Studio.app" || -d "/Applications/BambuStudio.app" ]]; then
  pass "Bambu Studio app is installed."
else
  warn "Bambu Studio app was not found in /Applications."
fi

if command -v openscad >/dev/null 2>&1; then
  pass "openscad is installed."
else
  warn "openscad is missing."
fi

[[ -d "${HOME}/3D-Printing" ]] && pass "~/3D-Printing exists." || warn "~/3D-Printing is missing."
[[ -d "${HOME}/3D-Printing/Business" ]] && pass "~/3D-Printing/Business exists." || warn "~/3D-Printing/Business is missing."
[[ -d "${HOME}/3D-Printing/Classroom" ]] && pass "~/3D-Printing/Classroom exists." || warn "~/3D-Printing/Classroom is missing."
[[ -d "${HOME}/3D-Printing/Reference-Only" ]] && pass "~/3D-Printing/Reference-Only exists." || warn "~/3D-Printing/Reference-Only is missing."

[[ -f "3d-agent/README.md" ]] && pass "3d-agent/README.md exists." || warn "3d-agent/README.md is missing."
[[ -f "docs/3d-printing-day-1-setup.md" ]] && pass "docs/3d-printing-day-1-setup.md exists." || warn "docs/3d-printing-day-1-setup.md is missing."
[[ -f "3d-agent/verification/README.md" ]] && pass "3d-agent/verification/README.md exists." || warn "3d-agent/verification/README.md is missing."
[[ -f "3d-agent/verification/pre-slicer-checklist.md" ]] && pass "3d-agent/verification/pre-slicer-checklist.md exists." || warn "3d-agent/verification/pre-slicer-checklist.md is missing."
[[ -f "3d-agent/training/openscad-test-suite.md" ]] && pass "3d-agent/training/openscad-test-suite.md exists." || warn "3d-agent/training/openscad-test-suite.md is missing."
[[ -f "3d-agent/training/llm-routing-for-cad.md" ]] && pass "3d-agent/training/llm-routing-for-cad.md exists." || warn "3d-agent/training/llm-routing-for-cad.md is missing."
[[ -f "bin/chief-of-staff" ]] && pass "bin/chief-of-staff exists." || warn "bin/chief-of-staff is missing."
[[ -x "bin/chief-of-staff" ]] && pass "bin/chief-of-staff is executable." || warn "bin/chief-of-staff is not executable."
[[ -f "docs/interactive-chief-of-staff-cli.md" ]] && pass "docs/interactive-chief-of-staff-cli.md exists." || warn "docs/interactive-chief-of-staff-cli.md is missing."
[[ -f "tests/smoke-chief-of-staff-cli.sh" ]] && pass "tests/smoke-chief-of-staff-cli.sh exists." || warn "tests/smoke-chief-of-staff-cli.sh is missing."
[[ -x "tests/smoke-chief-of-staff-cli.sh" ]] && pass "tests/smoke-chief-of-staff-cli.sh is executable." || warn "tests/smoke-chief-of-staff-cli.sh is not executable."
[[ -f "docs/final-installer-audit.md" ]] && pass "docs/final-installer-audit.md exists." || warn "docs/final-installer-audit.md is missing."
[[ -f "setup/98-final-audit.sh" ]] && pass "setup/98-final-audit.sh exists." || warn "setup/98-final-audit.sh is missing."
[[ -x "setup/98-final-audit.sh" ]] && pass "setup/98-final-audit.sh is executable." || warn "setup/98-final-audit.sh is not executable."
[[ -f "assistant/memory/README.md" ]] && pass "assistant/memory/README.md exists." || warn "assistant/memory/README.md is missing."
[[ -f "assistant/memory/projects.md" ]] && pass "assistant/memory/projects.md exists." || warn "assistant/memory/projects.md is missing."
[[ -f "assistant/memory/teaching-context.md" ]] && pass "assistant/memory/teaching-context.md exists." || warn "assistant/memory/teaching-context.md is missing."
[[ -f "assistant/memory/writing-style-rules.md" ]] && pass "assistant/memory/writing-style-rules.md exists." || warn "assistant/memory/writing-style-rules.md is missing."
[[ -f "assistant/memory/preferences.md" ]] && pass "assistant/memory/preferences.md exists." || warn "assistant/memory/preferences.md is missing."
[[ -f "assistant/memory/decisions.md" ]] && pass "assistant/memory/decisions.md exists." || warn "assistant/memory/decisions.md is missing."
[[ -f "assistant/memory/active-priorities.md" ]] && pass "assistant/memory/active-priorities.md exists." || warn "assistant/memory/active-priorities.md is missing."
[[ -f "assistant/memory/memory-review-checklist.md" ]] && pass "assistant/memory/memory-review-checklist.md exists." || warn "assistant/memory/memory-review-checklist.md is missing."
[[ -f "assistant/memory/memory-log.md" ]] && pass "assistant/memory/memory-log.md exists." || warn "assistant/memory/memory-log.md is missing."
[[ -f "assistant/intake/README.md" ]] && pass "assistant/intake/README.md exists." || warn "assistant/intake/README.md is missing."
[[ -f "assistant/intake/intake-policy.md" ]] && pass "assistant/intake/intake-policy.md exists." || warn "assistant/intake/intake-policy.md is missing."
[[ -f "assistant/intake/review-queue.md" ]] && pass "assistant/intake/review-queue.md exists." || warn "assistant/intake/review-queue.md is missing."
[[ -f "assistant/intake/approved-context.md" ]] && pass "assistant/intake/approved-context.md exists." || warn "assistant/intake/approved-context.md is missing."
[[ -f "assistant/intake/rejected-context.md" ]] && pass "assistant/intake/rejected-context.md exists." || warn "assistant/intake/rejected-context.md is missing."
[[ -f "assistant/intake/quarantine.md" ]] && pass "assistant/intake/quarantine.md exists." || warn "assistant/intake/quarantine.md is missing."
[[ -f "assistant/intake/intake-log.md" ]] && pass "assistant/intake/intake-log.md exists." || warn "assistant/intake/intake-log.md is missing."
[[ -f "assistant/intake/intake-review-checklist.md" ]] && pass "assistant/intake/intake-review-checklist.md exists." || warn "assistant/intake/intake-review-checklist.md is missing."
[[ -f "assistant/intake/templates/intake-item-template.md" ]] && pass "assistant/intake/templates/intake-item-template.md exists." || warn "assistant/intake/templates/intake-item-template.md is missing."
[[ -f "assistant/intake/templates/review-decision-template.md" ]] && pass "assistant/intake/templates/review-decision-template.md exists." || warn "assistant/intake/templates/review-decision-template.md is missing."
[[ -f "assistant/intake/templates/sanitized-summary-template.md" ]] && pass "assistant/intake/templates/sanitized-summary-template.md exists." || warn "assistant/intake/templates/sanitized-summary-template.md is missing."
[[ -f "assistant/intake/raw/.gitkeep" ]] && pass "assistant/intake/raw/.gitkeep exists." || warn "assistant/intake/raw/.gitkeep is missing."
[[ -f "assistant/intake/quarantine-files/.gitkeep" ]] && pass "assistant/intake/quarantine-files/.gitkeep exists." || warn "assistant/intake/quarantine-files/.gitkeep is missing."
[[ -f "assistant/intake/approved-files/.gitkeep" ]] && pass "assistant/intake/approved-files/.gitkeep exists." || warn "assistant/intake/approved-files/.gitkeep is missing."

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

if [[ -f "${ZSHRC}" ]]; then
  pass "~/.zshrc exists."
else
  fail "~/.zshrc is missing."
fi

if [[ -f "${ZSHRC}" ]] && grep -qF "${START_MARKER}" "${ZSHRC}" && grep -qF "${END_MARKER}" "${ZSHRC}"; then
  pass "~/.zshrc contains the teacher-ai-workstation managed block."
else
  fail "~/.zshrc does not contain the teacher-ai-workstation managed block."
fi

check_default_false NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled "Smart quote substitution"
check_default_false NSGlobalDomain NSAutomaticDashSubstitutionEnabled "Smart dash substitution"
check_default_false NSGlobalDomain NSAutomaticSpellingCorrectionEnabled "Autocorrect"
check_default_false NSGlobalDomain NSAutomaticCapitalizationEnabled "Autocapitalization"

echo
echo "Human-verified Day 1 items:"
warn "Focus Modes, widgets, browser profiles, Raycast preferences, Obsidian vault setup, 1Password sign-in, AlDente preferences, iPad/iPhone Focus sync, and Ricoh physical printing are human-verified."
echo "Complete docs/day-1-manual-steps.md, restart once, then rerun: bash setup/99-verify-setup.sh"

if (( failure_count > 0 )); then
  echo
  echo "FAIL: Automated verification found ${failure_count} critical item(s)."
  echo "Fix the FAIL items above, then rerun: bash setup/99-verify-setup.sh"
  exit 1
fi

echo
pass "Automated verification completed without critical FAIL items."
