#!/usr/bin/env bash
set -euo pipefail

echo "Checking your Mac before installing anything..."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "FAIL: This setup is for macOS only."
  exit 1
fi
echo "PASS: macOS detected."

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "FAIL: Apple Silicon is required for this workstation setup."
  exit 1
fi
echo "PASS: Apple Silicon detected."

if ! ping -c 1 -W 5 1.1.1.1 >/dev/null 2>&1; then
  echo "FAIL: Internet connection check failed. Please connect to the internet and rerun ./bootstrap.sh."
  exit 1
fi
echo "PASS: Internet connection detected."

available_kb="$(df -k / | awk 'NR==2 {print $4}')"
required_kb=$((100 * 1024 * 1024))
if (( available_kb < required_kb )); then
  echo "FAIL: At least 100GB free disk space is required."
  exit 1
fi
echo "PASS: At least 100GB free disk space is available."

if ! xcode-select -p >/dev/null 2>&1; then
  echo "FAIL: Xcode Command Line Tools are missing."
  echo "Run: xcode-select --install"
  echo "Then rerun:"
  echo "./bootstrap.sh"
  exit 1
fi
echo "PASS: Xcode Command Line Tools are installed."
