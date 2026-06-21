#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"

echo "Checking apps and tools from Brewfile..."
brew bundle check --file=./Brewfile || true

echo "Installing any missing apps and tools from Brewfile..."
brew bundle --file=./Brewfile
