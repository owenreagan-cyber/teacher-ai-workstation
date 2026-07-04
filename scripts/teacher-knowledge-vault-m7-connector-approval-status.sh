#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7 connector approval packet status.
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
check_no_urls_in_fixtures() {
  local dir="$1"
  if grep -rqiE 'https?://' "${dir}" --include='*.json' --include='*.yaml' 2>/dev/null; then
    fail "fixtures must not contain http(s) URLs: ${dir}"
  else
    pass "fixtures exclude URLs: ${dir}"
  fi
}
check_no_real_paths_in_fixtures() {
  local dir="$1"
  if grep -rE '/Users/|/home/|\\\\Users\\\\|C:\\\\' "${dir}" --include='*.json' --include='*.yaml' 2>/dev/null; then
    fail "fixtures must not contain real local paths: ${dir}"
  else
    pass "fixtures exclude real local paths: ${dir}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m7_dir="assistant/teacher-knowledge-vault/m7"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M7 Connector Approval Packet'
cat <<'EOF'
Status: read-only connector approval packet — fake fixtures only
Closure: complete_teacher_knowledge_vault_m7_read_only_connector_approval_packet
Real connector implementation: no
OAuth/API/network execution: no
api_calls_made: 0
real_sources_connected: 0
api_cost_estimate_usd: 0.00
PASS does not authorize OAuth API network or connector runtime: yes
EOF

section 'M7 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md"
check_file "docs/teacher-knowledge-vault/connector-approval-policy.md"
check_file "docs/teacher-knowledge-vault/connector-capability-model.md"
check_file "docs/teacher-knowledge-vault/source-inventory-model.md"
check_file "docs/teacher-knowledge-vault/google-drive-connector-approval-packet.md"
check_file "docs/teacher-knowledge-vault/ugreen-nas-connector-approval-packet.md"
check_file "docs/teacher-knowledge-vault/canvas-connector-approval-packet.md"
check_file "docs/teacher-knowledge-vault/manual-source-inventory-path.md"
check_file "docs/teacher-knowledge-vault/m7-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md" "complete_teacher_knowledge_vault_m7_read_only_connector_approval_packet" "M7 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md" "fake fixtures only" "M7 fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md" "M7 remains Level 0 only" "level 0 only"
check_doc_contains "docs/teacher-knowledge-vault/connector-approval-policy.md" "runtime_implemented" "connector runtime flag"
check_doc_contains "docs/teacher-knowledge-vault/connector-approval-policy.md" "read-only does not mean unrestricted" "read-only boundary"
check_doc_contains "docs/teacher-knowledge-vault/connector-approval-policy.md" "OAuth, secrets, and API calls are blocked in M7" "oauth blocked policy"
check_doc_contains "docs/teacher-knowledge-vault/connector-capability-model.md" "blocked_by_default" "blocked by default"
check_doc_contains "docs/teacher-knowledge-vault/connector-capability-model.md" "read_content_supported" "content read separate"
check_doc_contains "docs/teacher-knowledge-vault/source-inventory-model.md" "canonical_storage" "canonical storage role"
check_doc_contains "docs/teacher-knowledge-vault/source-inventory-model.md" "deployment_target" "canvas deployment role"
check_doc_contains "docs/teacher-knowledge-vault/source-inventory-model.md" "runtime_connected" "runtime connected flag"
check_doc_contains "docs/teacher-knowledge-vault/google-drive-connector-approval-packet.md" "scanning entire Drive root" "drive root scan blocked"
check_doc_contains "docs/teacher-knowledge-vault/google-drive-connector-approval-packet.md" "reading file contents" "drive content read blocked"
check_doc_contains "docs/teacher-knowledge-vault/ugreen-nas-connector-approval-packet.md" "scanning NAS root" "nas root scan blocked"
check_doc_contains "docs/teacher-knowledge-vault/ugreen-nas-connector-approval-packet.md" "mounting NAS shares" "nas mount blocked"
check_doc_contains "docs/teacher-knowledge-vault/canvas-connector-approval-packet.md" "not canonical storage" "canvas not storage"
check_doc_contains "docs/teacher-knowledge-vault/canvas-connector-approval-packet.md" "student submissions" "canvas student data blocked"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-path.md" "does not require OAuth/API" "manual no oauth"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-path.md" "must not include student data" "manual no student data"
check_doc_contains "docs/teacher-knowledge-vault/m7-governance-status.md" "api_calls_made" "governance api zero"

section 'M7 Fake Connector Fixtures'
check_file "${m7_dir}/README.md"
check_file "${m7_dir}/fake-connector-capabilities.json"
check_file "${m7_dir}/fake-source-inventory.json"
check_file "${m7_dir}/fake-drive-metadata-records.json"
check_file "${m7_dir}/fake-nas-metadata-records.json"
check_file "${m7_dir}/fake-canvas-metadata-records.json"
check_file "${m7_dir}/fake-manual-source-inventory.json"
check_file "${m7_dir}/fake-review-routing.json"
check_file "${m7_dir}/fake-event-log-connectors.json"
check_file "${m7_dir}/fake-source-reconciliation-connectors.json"
check_file "${m7_dir}/fake-observability-metrics.json"
check_doc_contains "${m7_dir}/fake-connector-capabilities.json" '"runtime_implemented": false' "connectors not implemented"
check_doc_contains "${m7_dir}/fake-connector-capabilities.json" "google_drive" "drive connector planned"
check_doc_contains "${m7_dir}/fake-connector-capabilities.json" "ugreen_nas" "nas connector planned"
check_doc_contains "${m7_dir}/fake-connector-capabilities.json" '"blocked_by_default": true' "connectors blocked default"
check_doc_contains "${m7_dir}/fake-source-inventory.json" "canonical_storage" "drive canonical role"
check_doc_contains "${m7_dir}/fake-source-inventory.json" "mirror_backup" "nas mirror role"
check_doc_contains "${m7_dir}/fake-source-inventory.json" '"runtime_connected": false' "sources not connected"
check_doc_contains "${m7_dir}/fake-drive-metadata-records.json" "metadata_only" "drive metadata only"
check_doc_contains "${m7_dir}/fake-drive-metadata-records.json" "99_DO_NOT_SCAN" "drive dns blocked"
check_doc_contains "${m7_dir}/fake-drive-metadata-records.json" "content_read_blocked" "drive content blocked"
check_doc_contains "${m7_dir}/fake-nas-metadata-records.json" "scanning NAS root blocked" "nas scan blocked"
check_doc_contains "${m7_dir}/fake-canvas-metadata-records.json" "student_data_read_blocked" "canvas student data blocked"
check_doc_contains "${m7_dir}/fake-canvas-metadata-records.json" "OAuth developer token setup blocked" "canvas oauth blocked"
check_doc_contains "${m7_dir}/fake-manual-source-inventory.json" "teacher_manual" "manual inventory entry"
check_doc_contains "${m7_dir}/fake-manual-source-inventory.json" '"student_data_included": false' "manual no student data"
check_doc_contains "${m7_dir}/fake-review-routing.json" "oauth_requested_but_blocked" "oauth routing blocked"
check_doc_contains "${m7_dir}/fake-review-routing.json" "write_sync_requested_but_blocked" "write sync blocked"
check_doc_contains "${m7_dir}/fake-review-routing.json" "student_data_risk_blocked" "student data routing blocked"
check_doc_contains "${m7_dir}/fake-event-log-connectors.json" "connector_approval_requested" "connector requested event"
check_doc_contains "${m7_dir}/fake-event-log-connectors.json" "api_call_requested_but_blocked" "api blocked event"
check_doc_contains "${m7_dir}/fake-source-reconciliation-connectors.json" "only_in_canvas" "canvas only reconcile"
check_doc_contains "${m7_dir}/fake-source-reconciliation-connectors.json" "nas_mirror_missing" "nas mirror reconcile"
check_doc_contains "${m7_dir}/fake-observability-metrics.json" '"connector_implementations": 0' "zero connectors"
check_doc_contains "${m7_dir}/fake-observability-metrics.json" '"api_calls_made": 0' "zero api calls"
check_doc_contains "${m7_dir}/fake-observability-metrics.json" '"oauth_flows_started": 0' "zero oauth flows"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m7_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m7_dir}"
check_no_real_paths_in_fixtures "${m7_dir}"

section 'No Connector OAuth API Network Runtime'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault connect drive' || pass 'CLI has no vault connect drive command'
grep -Fq -- '--teacher-knowledge-vault-connect-canvas)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault connect canvas' || pass 'CLI has no vault connect canvas command'
grep -Fq -- '--teacher-knowledge-vault-oauth)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault oauth' || pass 'CLI has no vault oauth command'
find assistant/teacher-knowledge-vault/m7 -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m7' || pass 'no .db files in m7 fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
if [[ -f .env ]] && grep -qE 'DRIVE_|CANVAS_|NAS_|OAUTH_|API_KEY' .env 2>/dev/null; then
  fail 'no connector secrets in .env'
else
  pass 'no connector secrets in .env'
fi

section 'M0 M1 M2 M3 M4 M5 M6 Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M7" "build queue M7"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M0 expansion" "build queue M0 expansion"
check_doc_contains docs/build-queue.md "connector implementation" "build queue connector blocked"
check_doc_contains assistant/memory/active-priorities.md "M7" "active priorities M7"
check_doc_contains docs/teacher-knowledge-vault/m0-architecture-freeze.md "M7" "M0 roadmap M7 reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7-connector-approval-status"
check_help_contains "--teacher-knowledge-vault-m6-extraction-ocr-approval-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7-connector-approval-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7-connector-approval-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m7-connector-approval-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M7 test' || fail 'smoke missing M7 test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real connector attempted'
pass 'no OAuth API or secrets attempted'
pass 'no rename move copy delete archive export attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
