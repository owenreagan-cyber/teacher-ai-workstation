#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"

echo "Checking apps and tools from Brewfile..."
if ! command -v brew >/dev/null 2>&1; then
  echo "FAIL: Homebrew is not available. Rerun ./bootstrap.sh so setup/01-install-homebrew.sh can finish."
  exit 1
fi

brew bundle check --file=./Brewfile || echo "WARN: Some Brewfile items are missing and will be installed if available."

echo "Installing any missing apps and tools from Brewfile..."
if brew bundle --file=./Brewfile; then
  echo "PASS: Brewfile install completed."
else
  echo "WARN: Homebrew reported one or more install problems."
  echo "WARN: This is often caused by optional apps, cask availability, or apps that need manual attention."
  echo "WARN: The setup will continue. Automated verification will flag critical command-line tools that are still missing."
fi
