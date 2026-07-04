#!/usr/bin/env bash
# Lightweight tests for the Vibe / Wallpaper / Widgets planning gate status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Vibe / Wallpaper / Widgets planning status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/vibe-wallpaper-widgets-planning-status.XXXXXX")"
bash scripts/vibe-wallpaper-widgets-planning-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: vibe-wallpaper-widgets-planning-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: vibe-wallpaper-widgets-planning-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^PASS: [1-9][0-9]*$' "${tmp}" || {
  echo "FAIL: status command did not emit PASS summary count"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
for needle in \
  'planning gate closure' \
  'fake examples include required concept fields' \
  'lane has no executable UI, shortcut, plist, app, or script artifacts' \
  'production registry records count exactly 1' \
  'BLOCKED-NO-WRITES.sentinel intact' \
  'Timer remains the only runtime-approved app' \
  'status script does not shell-invoke Shortcuts CLI' \
  'status script does not shell-invoke osascript' \
  'status script does not invoke network fetch commands' \
  'PASS/WARN/FAIL summary semantics preserved'; do
  grep -q "${needle}" "${tmp}" || {
    echo "FAIL: missing status proof: ${needle}"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
done
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/vibe-wallpaper-widgets-planning-cli.XXXXXX")"
bin/chief-of-staff --vibe-wallpaper-widgets-planning-status >"${tmp}" 2>&1 || {
  echo "FAIL: --vibe-wallpaper-widgets-planning-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --vibe-wallpaper-widgets-planning-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

grep -q -- '--vibe-wallpaper-widgets-planning-status' bin/chief-of-staff || {
  echo "FAIL: command is not discoverable through bin/chief-of-staff"
  exit 1
}
grep -q -- '"--vibe-wallpaper-widgets-planning-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || {
  echo "FAIL: command manifest missing vibe/wallpaper/widgets status"
  exit 1
}
grep -q 'vibe-wallpaper-widgets-planning-status.sh' scripts/chief-of-staff-validate-all.sh || {
  echo "FAIL: validate-all missing vibe/wallpaper/widgets status"
  exit 1
}
grep -q 'vibe-wallpaper-widgets-planning' tests/smoke-chief-of-staff-cli.sh || {
  echo "FAIL: smoke missing vibe/wallpaper/widgets status"
  exit 1
}

echo "PASS: Vibe / Wallpaper / Widgets planning status tests passed."
