#!/usr/bin/env bash
set -euo pipefail

BREW_PATH="/opt/homebrew/bin/brew"

echo "Checking Homebrew..."

if [[ ! -x "${BREW_PATH}" ]]; then
  echo "Homebrew is missing. Installing Homebrew now..."
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "PASS: Homebrew is already installed at ${BREW_PATH}."
fi

if [[ ! -x "${BREW_PATH}" ]]; then
  echo "FAIL: Homebrew was not found at ${BREW_PATH} after installation."
  exit 1
fi

export PATH="/opt/homebrew/bin:${PATH}"
echo "PASS: Homebrew is configured at ${BREW_PATH}."
"${BREW_PATH}" --version
