#!/usr/bin/env bash
# Negative guardrails for governance-first production registry foundation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running production registry governance guardrail tests..."

governance_doc="docs/curriculum-builder-production-registry-governance-foundation.md"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

[[ -f "${governance_doc}" ]] || { echo "FAIL: governance foundation doc missing"; exit 1; }
grep -q 'Production registry writes: blocked' "${governance_doc}" || {
  echo "FAIL: governance doc must state production writes blocked"
  exit 1
}

[[ -f "${sentinel}" ]] || { echo "FAIL: blocked-write sentinel missing"; exit 1; }

sentinel_doc="docs/curriculum-builder-production-registry-sentinel-semantics.md"
[[ -f "${sentinel_doc}" ]] || { echo "FAIL: sentinel semantics doc missing"; exit 1; }
grep -Fq "sentinel no longer means records count must be zero" "${sentinel_doc}" || {
  echo "FAIL: sentinel semantics must clarify post-first-record state"
  exit 1
}
grep -Fq "sentinel no longer means the production file must be absent" "${sentinel_doc}" || {
  echo "FAIL: sentinel semantics must clarify production file may exist"
  exit 1
}

if grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null; then
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
fi

candidate_records="assistant/curriculum-builder/registry/candidate-v0-2-production/records"
for candidate_file in "${candidate_records}"/*; do
  [[ -e "${candidate_file}" ]] || continue
  base="$(basename "${candidate_file}")"
  [[ "${base}" == ".gitkeep" ]] && continue
  if [[ "${base}" == *.json ]]; then
    echo "FAIL: candidate records must not contain JSON before write mission: ${base}"
    exit 1
  fi
done

bash tests/curriculum-builder-production-registry-governance-status-test.sh >/dev/null

echo "PASS: Production registry governance guardrail tests passed."
