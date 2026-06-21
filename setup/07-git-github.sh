#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"
EXPECTED_HTTPS="https://github.com/owenreagan-cyber/teacher-ai-workstation.git"
EXPECTED_SSH="git@github.com:owenreagan-cyber/teacher-ai-workstation.git"
SSH_KEY="${HOME}/.ssh/id_ed25519"

ask() {
  local prompt="$1"
  local value=""
  if [[ -t 0 ]]; then
    read -r -p "${prompt}" value
  fi
  printf '%s' "${value}"
}

yes_no() {
  local prompt="$1"
  local answer=""
  if [[ -t 0 ]]; then
    read -r -p "${prompt} [y/N] " answer
    [[ "${answer}" =~ ^[Yy]$ ]]
  else
    return 1
  fi
}

echo "Checking Git and GitHub setup..."

if ! git config --global user.name >/dev/null 2>&1; then
  name="$(ask "Enter your Git name, or press Return to skip for now: ")"
  if [[ -n "${name}" ]]; then
    git config --global user.name "${name}"
    echo "PASS: Git name saved."
  else
    echo "WARN: Git name was skipped. GitHub setup is incomplete."
  fi
else
  echo "PASS: Git name is already configured."
fi

if ! git config --global user.email >/dev/null 2>&1; then
  email="$(ask "Enter your Git email, or press Return to skip for now: ")"
  if [[ -n "${email}" ]]; then
    git config --global user.email "${email}"
    echo "PASS: Git email saved."
  else
    echo "WARN: Git email was skipped. GitHub setup is incomplete."
  fi
else
  echo "PASS: Git email is already configured."
fi

git config --global init.defaultBranch main
git config --global pull.rebase false
echo "PASS: Git defaults configured."

mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
if [[ ! -f "${SSH_KEY}" ]]; then
  email_for_key="$(git config --global user.email 2>/dev/null || true)"
  ssh-keygen -t ed25519 -f "${SSH_KEY}" -N "" -C "${email_for_key:-teacher-ai-workstation}" >/dev/null
  echo "PASS: SSH key generated at ${SSH_KEY}."
else
  echo "PASS: SSH key already exists at ${SSH_KEY}."
fi

eval "$(ssh-agent -s)" >/dev/null
ssh-add "${SSH_KEY}" >/dev/null 2>&1 || echo "WARN: Could not add SSH key to ssh-agent."

if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    echo "PASS: GitHub CLI is authenticated."
    if yes_no "Do you want to upload this SSH key to GitHub now?"; then
      gh ssh-key add "${SSH_KEY}.pub" --title "Teacher AI Workstation MacBook Pro" || echo "WARN: Could not upload SSH key with gh."
    else
      echo "WARN: SSH key upload skipped. GitHub setup may be incomplete."
    fi
  else
    echo "WARN: GitHub CLI is not authenticated. Login is optional for this setup."
    if yes_no "Do you want to run gh auth login now?"; then
      gh auth login || echo "WARN: gh auth login did not complete. GitHub setup is incomplete."
    else
      echo "WARN: GitHub login skipped. GitHub setup is incomplete."
    fi
  fi
else
  echo "WARN: gh is not installed yet. GitHub authentication was skipped."
fi

remote="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "${remote}" ]]; then
  git remote add origin "${EXPECTED_HTTPS}"
  echo "PASS: Added origin remote ${EXPECTED_HTTPS}."
elif [[ "${remote}" == "${EXPECTED_HTTPS}" || "${remote}" == "${EXPECTED_SSH}" ]]; then
  echo "PASS: origin remote points to the Teacher AI Workstation repository."
else
  echo "WARN: origin remote points to ${remote}, not the expected repository."
  if yes_no "Do you want to change origin to ${EXPECTED_HTTPS}?"; then
    git remote set-url origin "${EXPECTED_HTTPS}"
    echo "PASS: origin remote updated."
  else
    echo "WARN: origin remote was not changed. GitHub setup is incomplete."
  fi
fi
