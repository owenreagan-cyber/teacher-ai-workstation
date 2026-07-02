#!/usr/bin/env bash
# Registry v0.2 fake-record metadata preview. Text/markdown only — no generation.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
format="${1:-markdown}"

if [[ ! -f "${fixture}" ]]; then
  printf 'FAIL: fixture missing: %s\n' "${fixture}" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'FAIL: python3 required for render preview\n' >&2
  exit 1
fi

python3 - "${fixture}" "${format}" <<'PY'
import json
import sys

fixture_file, fmt = sys.argv[1], sys.argv[2]

with open(fixture_file, encoding="utf-8") as handle:
    data = json.load(handle)

records = data.get("records", [])
source_refs = {s["source_reference_id"]: s for s in data.get("source_references", []) if isinstance(s, dict)}
lesson_links = {l["lesson_link_id"]: l for l in data.get("lesson_links", []) if isinstance(l, dict)}

if fmt not in ("markdown", "text"):
    print("FAIL: format must be markdown or text", file=sys.stderr)
    sys.exit(1)

print("# Curriculum Registry v0.2 Fake Record Preview")
print()
print("```text")
print("Status: metadata preview only")
print("Lesson generation: no")
print("Production registry writes: no")
print("Network calls: no")
print("```")
print()

for record in records:
    rid = record.get("resource_id", "unknown")
    print(f"## {record.get('title', 'Untitled')} (`{rid}`)")
    print()
    print(f"- **Subject:** {record.get('subject')}")
    print(f"- **Course:** {record.get('course')}")
    print(f"- **Unit / Lesson:** {record.get('unit')} / {record.get('lesson')}")
    print(f"- **Type:** {record.get('resource_type')}")
    print(f"- **Review:** {record.get('review_status')}")
    sid = record.get("source_reference_id")
    if sid in source_refs:
        src = source_refs[sid]
        print(f"- **Source:** {src.get('path_or_url_reference')} ({src.get('source_system')})")
    lid = record.get("lesson_link_id")
    if lid in lesson_links:
        link = lesson_links[lid]
        print(f"- **Lesson link:** {lid} (generation_blocked={link.get('generation_blocked')})")
    print(f"- **Notes:** {record.get('notes')}")
    print()

print("---")
print()
print("*Preview ends — no content generated, no production write.*")
PY
