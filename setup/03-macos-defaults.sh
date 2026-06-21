#!/usr/bin/env bash
set -euo pipefail

echo "Applying beginner-friendly macOS defaults..."

mkdir -p "${HOME}/Screenshots"

defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder ShowPathbar -bool true
defaults write com.apple.finder ShowStatusBar -bool true
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock tilesize -int 36
defaults write com.apple.dock show-recents -bool false
defaults write com.apple.screencapture location -string "${HOME}/Screenshots"
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

killall Finder >/dev/null 2>&1 || true
killall Dock >/dev/null 2>&1 || true
killall SystemUIServer >/dev/null 2>&1 || true

echo "PASS: macOS defaults applied."
