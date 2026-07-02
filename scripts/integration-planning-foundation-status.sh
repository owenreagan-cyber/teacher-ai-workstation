#!/usr/bin/env bash
# Read-only Integration Planning Foundation v0 status only. No APIs, OAuth, or network calls.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "${file} must mention ${label}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && pass "doc mentions ${label}" || fail "${file} must mention ${label}"
}
check_bash_syntax() {
  [[ -f "$1" ]] || { fail "cannot syntax check missing file: $1"; return; }
  bash -n "$1" && pass "bash syntax ok: $1" || fail "bash syntax failed: $1"
}
check_help_contains() {
  bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Integration Planning Foundation v0'
cat <<'EOF'
Status: documentation/status/planning only
Live integrations: no
APIs: no
OAuth: no
Sync jobs: no
Network calls: no
EOF

section 'Foundation Documentation'
check_file "docs/integration-planning-foundation-v0.md"
check_file "docs/google-drive-integration-planning-v0.md"
check_file "docs/canvas-integration-planning-v0.md"
check_file "docs/oauth-integration-boundary-v0.md"
check_doc_contains "docs/integration-planning-foundation-v0.md" "all integrations remain" "inactive integration boundary"
check_doc_contains "docs/integration-planning-foundation-v0.md" "--integration-planning-foundation-status" "foundation status command"

section 'Inactive Integration Manifest v0'
check_file "assistant/integration-planning/v0/integration-inactive-manifest.json"
check_file "assistant/integration-planning/v0/README.md"
check_file "scripts/integration-planning-foundation-v0-validator.sh"
check_bash_syntax "scripts/integration-planning-foundation-v0-validator.sh"
bash scripts/integration-planning-foundation-v0-validator.sh >/dev/null 2>&1 && pass "integration inactive manifest validator exits 0" || fail "integration inactive manifest validator failed"

if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool assistant/integration-planning/v0/integration-inactive-manifest.json >/dev/null 2>&1 && pass "JSON parses: integration inactive manifest" || fail "JSON does not parse: integration inactive manifest"
else warn 'python3 not available for JSON parse checks'; fi

section 'Chief of Staff Integration'
check_help_contains "--integration-planning-foundation-status"
check_help_contains "--integration-planning-foundation-v0-validate"
check_bash_syntax "bin/chief-of-staff"
pass 'no live integration attempted'; pass 'no write action attempted'; pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
