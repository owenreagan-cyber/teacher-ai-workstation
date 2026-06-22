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
  echo "## Manual steps remaining"
  echo "- Complete Focus Modes, widgets, browser profiles, Raycast preferences, Obsidian vault setup, 1Password sign-in, AlDente preferences, iPad/iPhone Focus sync, and Ricoh physical printing."
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
