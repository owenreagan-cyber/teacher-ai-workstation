#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"
REPORT="logs/setup-report.md"
EXPECTED_HTTPS="https://github.com/owenreagan-cyber/teacher-ai-workstation.git"
EXPECTED_SSH="git@github.com:owenreagan-cyber/teacher-ai-workstation.git"

mkdir -p logs

github_status="Incomplete"
remote="$(git remote get-url origin 2>/dev/null || true)"
if [[ "${remote}" == "${EXPECTED_HTTPS}" || "${remote}" == "${EXPECTED_SSH}" ]]; then
  github_status="Remote configured"
fi
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  github_status="Authenticated and ${github_status}"
fi

ollama_status="Not reachable"
if command -v ollama >/dev/null 2>&1; then
  if curl -fsS http://localhost:11434 >/dev/null 2>&1; then
    ollama_status="CLI installed and service reachable"
  else
    ollama_status="CLI installed, service not reachable"
  fi
else
  ollama_status="CLI missing"
fi

openscad_status="Missing"
if command -v openscad >/dev/null 2>&1; then
  openscad_status="Available"
fi

bambu_studio_status="Missing"
if [[ -d "/Applications/Bambu Studio.app" || -d "/Applications/BambuStudio.app" ]]; then
  bambu_studio_status="Installed"
fi

macos_version="$(sw_vers -productVersion 2>/dev/null || echo 'unknown')"
architecture="$(uname -m)"

{
  echo "# Teacher AI Workstation Setup Report"
  echo
  echo "- Date/time: $(date)"
  echo "- macOS version: ${macos_version}"
  echo "- Machine architecture: ${architecture}"
  echo "- Scope: automated Phase 0A Day 1 setup report only"
  echo
  echo "## Installed apps summary"
  for app in brew git gh node python3 ollama dockutil starship zoxide atuin eza bat fzf rg uv llm fabric; do
    if command -v "${app}" >/dev/null 2>&1; then
      echo "- PASS: ${app} found"
    else
      echo "- WARN: ${app} not found"
    fi
  done
  echo
  echo "## Folders created"
  for folder in "${HOME}/Projects" "${HOME}/Teaching" "${HOME}/Teaching/Print-Certified" "${HOME}/AI" "${HOME}/Notes" "${HOME}/Screenshots" "${HOME}/Pictures/Teacher OS Wallpapers/Teacher Mode" "${HOME}/Pictures/Teacher OS Wallpapers/Casual Anime Mode"; do
    if [[ -d "${folder}" ]]; then
      echo "- PASS: ${folder}"
    else
      echo "- WARN: ${folder} missing"
    fi
  done
  echo
  echo "## Settings applied"
  echo "- Finder file extensions, hidden files, path bar, status bar, and folders-on-top requested"
  echo "- Dock autohide, Dock tile size, and hidden recent apps requested"
  echo "- Screenshot location requested: ${HOME}/Screenshots"
  echo "- Fast keyboard repeat and tap-to-click requested"
  echo "- .DS_Store prevention on network and USB volumes requested"
  echo "- Smart quotes, smart dashes, autocorrect, and autocapitalization disabled for code, Markdown, shell commands, and prompts"
  echo "- Teacher AI Workstation managed zsh block requested in ~/.zshrc"
  echo
  echo "## GitHub status"
  echo "- ${github_status}"
  echo "- origin: ${remote:-not configured}"
  echo
  echo "## Ollama status"
  echo "- ${ollama_status}"
  echo
  echo "## 3D readiness"
  echo "- OpenSCAD: ${openscad_status}"
  echo "- Bambu Studio: ${bambu_studio_status}"
  for folder in "${HOME}/3D-Printing" "${HOME}/3D-Printing/Business" "${HOME}/3D-Printing/Classroom" "${HOME}/3D-Printing/Reference-Only"; do
    if [[ -d "${folder}" ]]; then
      echo "- PASS: ${folder}"
    else
      echo "- WARN: ${folder} missing"
    fi
  done
  for doc in "3d-agent/verification/README.md" "3d-agent/verification/pre-slicer-checklist.md"; do
    if [[ -f "${doc}" ]]; then
      echo "- PASS: ${doc}"
    else
      echo "- WARN: ${doc} missing"
    fi
  done
  echo
  echo "## Chief of Staff CLI readiness"
  if [[ -f "bin/chief-of-staff" ]]; then
    echo "- PASS: bin/chief-of-staff present"
  else
    echo "- WARN: bin/chief-of-staff missing"
  fi
  if [[ -x "bin/chief-of-staff" ]]; then
    echo "- PASS: bin/chief-of-staff executable"
  else
    echo "- WARN: bin/chief-of-staff is not executable"
  fi
  if [[ -f "docs/interactive-chief-of-staff-cli.md" ]]; then
    echo "- PASS: docs/interactive-chief-of-staff-cli.md present"
  else
    echo "- WARN: docs/interactive-chief-of-staff-cli.md missing"
  fi
  if [[ -f "tests/smoke-chief-of-staff-cli.sh" ]]; then
    echo "- PASS: tests/smoke-chief-of-staff-cli.sh present"
  else
    echo "- WARN: tests/smoke-chief-of-staff-cli.sh missing"
  fi
  echo
  echo "## Final Audit"
  if [[ -f "docs/final-installer-audit.md" ]]; then
    echo "- PASS: docs/final-installer-audit.md present"
  else
    echo "- WARN: docs/final-installer-audit.md missing"
  fi
  if [[ -f "setup/98-final-audit.sh" ]]; then
    echo "- PASS: setup/98-final-audit.sh present"
  else
    echo "- WARN: setup/98-final-audit.sh missing"
  fi
  if [[ -x "setup/98-final-audit.sh" ]]; then
    echo "- PASS: setup/98-final-audit.sh executable"
  else
    echo "- WARN: setup/98-final-audit.sh is not executable"
  fi
  echo "- Note: final audit is run manually before opening the MacBook."
  echo
  echo "## Chief of Staff memory readiness"
  if [[ -d "assistant/memory" ]]; then
    echo "- PASS: assistant/memory present"
  else
    echo "- WARN: assistant/memory missing"
  fi
  for doc in "assistant/memory/projects.md" "assistant/memory/teaching-context.md" "assistant/memory/writing-style-rules.md" "assistant/memory/preferences.md" "assistant/memory/decisions.md" "assistant/memory/active-priorities.md" "assistant/memory/memory-log.md"; do
    if [[ -f "${doc}" ]]; then
      echo "- PASS: ${doc}"
    else
      echo "- WARN: ${doc} missing"
    fi
  done
  echo
  echo "## Chief of Staff intake readiness"
  if [[ -d "assistant/intake" ]]; then
    echo "- PASS: assistant/intake present"
  else
    echo "- WARN: assistant/intake missing"
  fi
  for doc in "assistant/intake/review-queue.md" "assistant/intake/approved-context.md" "assistant/intake/intake-policy.md" "assistant/intake/intake-log.md" "assistant/intake/intake-review-checklist.md" "assistant/intake/raw/.gitkeep" "assistant/intake/quarantine-files/.gitkeep" "assistant/intake/approved-files/.gitkeep"; do
    if [[ -f "${doc}" ]]; then
      echo "- PASS: ${doc}"
    else
      echo "- WARN: ${doc} missing"
    fi
  done
  echo
  echo "## Manual steps remaining"
  echo "- Complete Focus Modes, widgets, browser profiles, Raycast preferences, Obsidian vault setup, 1Password sign-in, AlDente preferences, iPad/iPhone Focus sync, and Ricoh physical printing."
  echo "- Review docs/3d-printing-day-1-setup.md and 3d-agent/verification/pre-slicer-checklist.md before using AI-generated 3D designs."
  echo "- Review docs/backup-exclusions.md before applying Time Machine or cloud backup exclusions."
  echo "- Complete docs/day-1-manual-steps.md, restart once, then rerun bash setup/99-verify-setup.sh."
  echo
  echo "## Optional failures"
  echo "- Review logs/setup.log for WARN messages from optional apps, GitHub authentication, Dock items, wallpaper setup, or Ollama model pulls."
  echo
  echo "## Next recommended action"
  echo "- Open docs/day-1-manual-steps.md and complete the Phase 0 Day 1 manual checklist."
} > "${REPORT}"

echo "PASS: Local setup report generated at ${REPORT}. This file is intentionally ignored by Git."
