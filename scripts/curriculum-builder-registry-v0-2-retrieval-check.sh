#!/usr/bin/env bash
# Registry v0.2 fake-record local retrieval. Filter/lookup only — no crawling or RAG.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
filter_subject=""
filter_resource_id=""
filter_course=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --subject)
      filter_subject="${2:-}"
      shift 2
      ;;
    --resource-id)
      filter_resource_id="${2:-}"
      shift 2
      ;;
    --course)
      filter_course="${2:-}"
      shift 2
      ;;
    *)
      printf 'FAIL: unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

printf 'Status: local fake-record retrieval only\n'
printf 'Filesystem crawl: no\n'
printf 'Embeddings/RAG: no\n'
printf 'Production registry writes: no\n'
printf '\n'

if [[ ! -f "${fixture}" ]]; then
  fail "fixture missing: ${fixture}"
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for retrieval check"
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

python3 - "${fixture}" "${filter_subject}" "${filter_resource_id}" "${filter_course}" <<'PY'
import json
import sys

fixture_file, subj, rid, course = sys.argv[1:5]

with open(fixture_file, encoding="utf-8") as handle:
    data = json.load(handle)

records = data.get("records", [])
matches = []
for record in records:
    if subj and record.get("subject") != subj:
        continue
    if rid and record.get("resource_id") != rid:
        continue
    if course and record.get("course") != course:
        continue
    matches.append(record)

if not matches:
    print("WARN: no matching fake records")
    sys.exit(0)

for record in matches:
    print(f"MATCH: {record.get('resource_id')} | {record.get('title')} | {record.get('subject')} | {record.get('course')}")
PY

match_count="$(python3 - "${fixture}" "${filter_subject}" "${filter_resource_id}" "${filter_course}" <<'PY'
import json, sys
fixture_file, subj, rid, course = sys.argv[1:5]
with open(fixture_file, encoding="utf-8") as f:
    data = json.load(f)
count = 0
for record in data.get("records", []):
    if subj and record.get("subject") != subj:
        continue
    if rid and record.get("resource_id") != rid:
        continue
    if course and record.get("course") != course:
        continue
    count += 1
print(count)
PY
)"

if [[ "${match_count}" -gt 0 ]]; then
  pass "retrieval found ${match_count} fake record(s)"
else
  warn "retrieval found no matches (filter may be intentional)"
fi

pass "retrieval check completed without production write"
printf '\nPASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
