#!/usr/bin/env bash
# Read-only Antigravity 2.0 evaluation status. Documentation/status only.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() { local file="$1" phrase="$2" label="$3"; [[ -f "$file" ]] || { fail "$file must mention $label"; return; }; grep -F -- "$phrase" "$file" >/dev/null && pass "doc mentions $label" || fail "$file must mention $label"; }
check_absent() { [[ ! -e "$1" ]] && pass "absent as required: $1" || fail "must not exist in primary repo: $1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$repo_root" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "$repo_root"

section 'Antigravity 2.0 Evaluation Status'
cat <<'EOT'
Status: antigravity_2_evaluation_policy_complete
Classification: documentation/status only
Install or execution authorized: no
Primary repo activation: blocked
Manual-copy-only: yes
EOT

section 'Docs'
for path in docs/programs/toolchain/README.md docs/programs/toolchain/antigravity-2-evaluation-plan.md docs/programs/toolchain/antigravity-sandbox-policy.md docs/programs/toolchain/agent-tool-permission-matrix.md docs/programs/toolchain/antigravity-validation-journal-template.md docs/programs/toolchain/antigravity-sandbox-setup-guide.md; do check_file "$path"; done

section 'Required Labels'
for label in '[CANDIDATE]' '[SANDBOX-ONLY]' '[BLOCKED-IN-PRIMARY]' '[MANUAL-COPY-ONLY]'; do check_doc_contains docs/programs/toolchain/README.md "$label" "Antigravity label $label"; done

section 'Primary Repo Non-Activation'
check_absent .antigravity
check_absent .antigravity.json
if find . -path ./.git -prune -o -type f \( -iname '*agy*config*' -o -iname '*agy*migration*' -o -iname '*antigravity*migration*' \) -print -quit | grep -q .; then
  fail 'agy config/migration file must not exist in primary repo'
else
  pass 'no agy config/migration file exists in primary repo'
fi

section 'Sandbox Evidence Requirements'
check_file docs/programs/toolchain/antigravity-validation-journal-template.md
check_file docs/programs/toolchain/antigravity-sandbox-setup-guide.md
check_doc_contains docs/programs/toolchain/antigravity-sandbox-setup-guide.md 'remove origin' 'sandbox removes origin'
check_doc_contains docs/programs/toolchain/antigravity-sandbox-setup-guide.md 'SANDBOX_ONLY_DO_NOT_MERGE.md' 'sandbox sentinel'
check_doc_contains docs/programs/toolchain/antigravity-sandbox-setup-guide.md 'VALIDATION_JOURNAL.md' 'sandbox validation journal'

section 'Policy Blocks'
policy=docs/programs/toolchain/antigravity-sandbox-policy.md
check_doc_contains "$policy" 'blocks credentials' 'credentials block'
check_doc_contains "$policy" 'Canvas API/OAuth/live reads/writes' 'Canvas API/OAuth/live reads/writes block'
check_doc_contains "$policy" 'Drive/NAS/iCloud' 'Drive/NAS/iCloud block'
check_doc_contains "$policy" 'Supabase/Firebase' 'Supabase/Firebase block'
check_doc_contains "$policy" 'Direct sandbox-to-main merge is blocked' 'direct sandbox-to-main merge block'
check_doc_contains "$policy" 'manual' 'manual-copy-only migration'
check_doc_contains "$policy" 'Docs do not authorize install or execution' 'docs do not authorize install or execution'

section 'CLI and Manifest'
check_doc_contains bin/chief-of-staff '--antigravity-evaluation-status' 'CLI flag'
check_doc_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--antigravity-evaluation-status"' 'command manifest flag'
check_doc_contains docs/chief-of-staff-command-index-v1.md '--antigravity-evaluation-status' 'command index flag'

section 'Summary'
printf 'PASS: %s\n' "$PASS_COUNT"; printf 'WARN: 0\n'; printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -gt 0 ]] && exit 1

exit 0
