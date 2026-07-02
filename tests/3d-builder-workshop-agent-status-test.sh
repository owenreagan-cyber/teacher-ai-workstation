#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"
echo "Running 3D Builder Workshop Agent status tests..."
tmp="$(mktemp "${TMPDIR:-/tmp}/3d-builder-status.XXXXXX")"
bash scripts/3d-builder-workshop-agent-status.sh >"${tmp}" 2>&1 || { cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"
bin/chief-of-staff --3d-builder-status >/dev/null
echo "PASS: 3D Builder Workshop Agent status tests passed."
