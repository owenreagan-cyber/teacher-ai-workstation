#!/usr/bin/env bash
# Deterministic dry-run normalizer for fake/local/redacted Canvas LLM Phase 3 packets.
set -euo pipefail

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

if [[ "$#" -ne 1 ]]; then
  fail "explicit packet directory argument required"
fi

packet_arg="$1"
case "${packet_arg}" in
  /|~|~/*|*/..|*/../*|../*|*'/../'*|/Volumes|/Volumes/*) fail "unsafe or broad packet path rejected: ${packet_arg}" ;;
esac
if [[ -n "${HOME:-}" ]]; then
  case "${packet_arg}" in
    "${HOME}"|"${HOME}/"*|"${HOME}/Desktop"|"${HOME}/Desktop/"*|"${HOME}/Documents"|"${HOME}/Documents/"*) fail "home/Desktop/Documents packet paths are rejected" ;;
  esac
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

[[ -d "${packet_arg}" ]] || fail "packet directory missing: ${packet_arg}"
packet_dir="$(cd "${packet_arg}" && pwd -P)"
allowed_root="${repo_root}/fixtures/canvas-llm/manual-evidence-packets"
case "${packet_dir}" in
  "${allowed_root}"/*) ;;
  *) fail "packet directory must be under fixtures/canvas-llm/manual-evidence-packets" ;;
esac

metadata="${packet_dir}/packet.json"
[[ -f "${metadata}" ]] || fail "packet metadata missing: packet.json"

if find "${packet_dir}" -type f ! \( -name '*.json' -o -name '*.md' \) | grep -q .; then
  fail "unsupported evidence file type found; only .json and .md are allowed"
fi

unsafe_patterns='access_token|api_key|client_secret|canvas_token|student_name|student_id|roster|student_submission|submission_body|submission_text|accommodation|analytics|canvas\.instructure\.com|supabase|firebase|credential_secret|session_token'
if find "${packet_dir}" -type f \( -name '*.json' -o -name '*.md' \) -print0 | xargs -0 grep -Eiq "${unsafe_patterns}"; then
  fail "packet contains prohibited student-data, credential, integration, or production-write marker"
fi

python3 - "${metadata}" "${packet_dir}" "${repo_root}" <<'PY'
import json
import os
import sys

metadata_path, packet_dir, repo_root = sys.argv[1:4]
required = [
    "packet_id", "course_label", "school_year_label", "export_type",
    "redaction_status", "source_type", "no_student_data",
    "no_live_canvas_api_oauth", "no_real_curriculum_ingestion",
    "no_production_write", "evidence_files", "allowed_use", "blocked_use",
    "review_status", "created_date", "updated_date",
]
try:
    with open(metadata_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception as exc:
    print(f"FAIL: packet.json parse failed: {exc}", file=sys.stderr)
    sys.exit(1)
missing = [key for key in required if key not in data]
if missing:
    print("FAIL: packet.json missing required fields: " + ", ".join(missing), file=sys.stderr)
    sys.exit(1)
checks = {
    "redaction_status": "redacted_fake_local",
    "source_type": "manual_exported_redacted_fake_local",
    "review_status": "fixture_reviewed",
}
for key, expected in checks.items():
    if data.get(key) != expected:
        print(f"FAIL: {key} must be {expected}", file=sys.stderr)
        sys.exit(1)
for key in ["no_student_data", "no_live_canvas_api_oauth", "no_real_curriculum_ingestion", "no_production_write"]:
    if data.get(key) is not True:
        print(f"FAIL: {key} must be true", file=sys.stderr)
        sys.exit(1)
files = data.get("evidence_files")
if not isinstance(files, list) or not files:
    print("FAIL: evidence_files must be a non-empty list", file=sys.stderr)
    sys.exit(1)
for rel in files:
    if not isinstance(rel, str) or rel.startswith("/") or ".." in rel.split(os.sep):
        print(f"FAIL: unsafe evidence file path: {rel}", file=sys.stderr)
        sys.exit(1)
    full = os.path.realpath(os.path.join(packet_dir, rel))
    if not full.startswith(packet_dir + os.sep) or not os.path.isfile(full):
        print(f"FAIL: evidence file missing or outside packet: {rel}", file=sys.stderr)
        sys.exit(1)
print("Status: canvas_llm_phase_3_packet_normalized_dry_run")
print("Classification: fake/local/manual/redacted fixture packet only")
print("Canvas API/OAuth/live reads: blocked")
print("Student data: blocked")
print("Real curriculum ingestion: blocked")
print("Production writes: blocked")
print(f"Packet ID: {data['packet_id']}")
print(f"Course label: {data['course_label']}")
print("Evidence files:")
for rel in sorted(files):
    print(f"- {rel}")
PY
