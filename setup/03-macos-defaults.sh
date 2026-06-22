#!/usr/bin/env bash
set -euo pipefail

echo "Applying beginner-friendly macOS defaults..."

mkdir -p "${HOME}/Screenshots"

# Finder: make files and folders easier for a beginner to inspect.
defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder AppleShowAllFiles -bool true
defaults write com.apple.finder ShowPathbar -bool true
defaults write com.apple.finder ShowStatusBar -bool true
defaults write com.apple.finder _FXSortFoldersFirst -bool true
defaults write com.apple.finder _FXSortFoldersFirstOnDesktop -bool true

# Dock: keep the desktop calm and leave more space for work.
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock tilesize -int 36
defaults write com.apple.dock show-recents -bool false

# Screenshots and input: predictable locations and fast typing.
defaults write com.apple.screencapture location -string "${HOME}/Screenshots"
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Keep network and USB folders clean.
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# Disable automatic text substitutions because smart quotes, smart dashes,
# autocorrect, and autocapitalization interfere with code, Markdown, shell
# commands, and prompts.
echo "Disabling smart quotes because they can break code and shell commands..."
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
echo "Disabling smart dashes because they can break CLI flags..."
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
echo "Disabling autocorrect because it can damage prompts, Markdown, and commands..."
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
echo "Disabling autocapitalization because it can damage prompts, Markdown, and commands..."
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false

killall Finder >/dev/null 2>&1 || true
killall Dock >/dev/null 2>&1 || true
killall SystemUIServer >/dev/null 2>&1 || true

echo "PASS: macOS defaults applied."
