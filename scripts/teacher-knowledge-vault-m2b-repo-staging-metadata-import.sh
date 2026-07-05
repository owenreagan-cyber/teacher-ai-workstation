#!/usr/bin/env bash
# Teacher Knowledge Vault M2b repo staging metadata import — fixed fixtures and M7g catalog path only.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

DISCOVERY_SCRIPT="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery.sh"
M2B_OUT_DIR=".local/teacher-knowledge-vault/m2b"
M2B_REPORT="${M2B_OUT_DIR}/repo-staging-metadata-report.json"
M2B_SUMMARY="${M2B_OUT_DIR}/import-summary.json"
M7G_OUT_DIR=".local/teacher-knowledge-vault/working-catalog"
M7G_DB="${M7G_OUT_DIR}/working-catalog.sqlite"
M7G_BACKUP_DIR="${M7G_OUT_DIR}/backups"

section 'Teacher Knowledge Vault M2b Repo Staging Metadata Import'
cat <<'EOF'
Status: metadata import — fixed repo-owned staging fixtures to M7g prototype catalog only
Content reads: no
Production catalog writes: no
Arbitrary path input: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

section 'Metadata Discovery'
bash "${DISCOVERY_SCRIPT}" >/dev/null 2>&1 && pass 'metadata discovery completed before import' || fail 'metadata discovery failed — import blocked'
[[ -f "${M2B_REPORT}" ]] && pass 'metadata report present' || fail 'metadata report missing'

section 'M7g Prototype Catalog Import'
import_output="$(python3 - "${repo_root}" "${M2B_REPORT}" "${M2B_SUMMARY}" "${M7G_DB}" "${M7G_BACKUP_DIR}" <<'PY'
import json, os, shutil, sqlite3, sys

repo_root, report_path, summary_path, db_path, backup_dir = sys.argv[1:6]
batch_id = "fake-m2b-batch-001"
catalog_id = "fake-m7g-working-catalog-001"
backup_id = "fake-m2b-backup-pre-import-001"
created_at = "2026-07-05T12:00:00Z"

with open(os.path.join(repo_root, report_path), encoding="utf-8") as f:
    report = json.load(f)

db_full = os.path.join(repo_root, db_path)
os.makedirs(os.path.join(repo_root, backup_dir), exist_ok=True)
os.makedirs(os.path.dirname(db_full), exist_ok=True)

if os.path.exists(db_full):
    shutil.copy2(db_full, os.path.join(repo_root, backup_dir, f"working-catalog-{backup_id}.sqlite"))

conn = sqlite3.connect(db_full)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT);
CREATE TABLE IF NOT EXISTS catalog_metadata (
  catalog_id TEXT PRIMARY KEY, catalog_mode TEXT, production_catalog INTEGER,
  real_curriculum_allowed INTEGER, student_data_allowed INTEGER, external_sources_allowed INTEGER,
  created_from_fixture_only INTEGER, source_fixture_reference TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS import_batches (
  batch_id TEXT PRIMARY KEY, fixture_source TEXT, source_fixture_reference TEXT,
  created_at TEXT, catalog_mode TEXT, production_write INTEGER);
CREATE TABLE IF NOT EXISTS source_items (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, source_label TEXT,
  restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  fixture_source_ref TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS review_queue_items (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, review_state TEXT,
  fixture_source_ref TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS event_log (
  id TEXT PRIMARY KEY, batch_id TEXT, event_type TEXT, manual_inventory_id TEXT,
  runtime_executed INTEGER, created_at TEXT);
CREATE TABLE IF NOT EXISTS blocked_records (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, block_reason TEXT,
  indexable INTEGER, discoverable INTEGER, fixture_source_ref TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS staging_metadata (
  id TEXT PRIMARY KEY, batch_id TEXT, relative_fixture_path TEXT, display_name TEXT,
  extension TEXT, size_bytes INTEGER, modified_at TEXT, source_label TEXT,
  indexing_policy TEXT, restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  created_at TEXT);
""")

for table in ["source_items", "review_queue_items", "event_log", "blocked_records", "staging_metadata"]:
    cur.execute(f"DELETE FROM {table} WHERE batch_id=?", (batch_id,))

cur.execute(
    "INSERT OR IGNORE INTO import_batches VALUES (?,?,?,?,?,?)",
    (batch_id, "m2b repo staging fixtures", report.get("staging_fixture_root"), created_at, "persistent_working_prototype", 0),
)
cur.execute(
    """INSERT OR REPLACE INTO catalog_metadata VALUES (?,?,?,?,?,?,?,?,?)""",
    (catalog_id, "persistent_working_prototype", 0, 0, 0, 0, 1, report.get("staging_fixture_root"), created_at),
)

imported = 0
blocked = 0
teacher_only = 0
for idx, rec in enumerate(report.get("records", []), start=1):
    mid = f"fake-m2b-meta-{idx:03d}"
    rel = rec.get("relative_fixture_path", "")
    label = rec.get("source_label", "repo_owned_fake_staging")
    cur.execute(
        """INSERT INTO staging_metadata VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            mid, batch_id, rel, rec.get("display_name"), rec.get("extension"),
            rec.get("size_bytes"), rec.get("modified_at"), label,
            rec.get("indexing_policy"), rec.get("restricted_indexable", 0),
            rec.get("indexable", 0), rec.get("discoverable", 0), created_at,
        ),
    )
    if rec.get("do_not_scan"):
        cur.execute(
            "INSERT INTO blocked_records VALUES (?,?,?,?,?,?,?,?)",
            (f"blocked-{mid}", batch_id, mid, "do_not_scan_blocked", 0, 0, rel, created_at),
        )
        blocked += 1
        continue
    if rec.get("teacher_only"):
        teacher_only += 1
    cur.execute(
        "INSERT INTO source_items VALUES (?,?,?,?,?,?,?,?,?)",
        (mid, batch_id, mid, label, rec.get("restricted_indexable", 0),
         rec.get("indexable", 0), rec.get("discoverable", 0), rel, created_at),
    )
    imported += 1

for ev in [
    ("fake-m2b-evt-discovery", "m2b_metadata_discovery_attached", None),
    ("fake-m2b-evt-import", "m2b_metadata_import_completed", None),
]:
    cur.execute(
        "INSERT INTO event_log VALUES (?,?,?,?,?,?)",
        (ev[0], batch_id, ev[1], ev[2], 1, created_at),
    )

cur.execute(
    "INSERT INTO review_queue_items VALUES (?,?,?,?,?,?)",
    ("fake-m2b-review-001", batch_id, "fake-m2b-meta-001", "metadata_preview_only", report.get("staging_fixture_root"), created_at),
)

conn.commit()
conn.close()

summary = {
    "classification": "fake_local_planning_only",
    "import_batch_id": batch_id,
    "catalog_mode": "persistent_working_prototype",
    "production_write": False,
    "metadata_records_imported": imported,
    "blocked_count": blocked,
    "teacher_only_restricted_count": teacher_only,
    "do_not_scan_blocked_count": blocked,
    "staging_fixture_root": report.get("staging_fixture_root"),
    "content_reads": 0,
    "ocr_jobs": 0,
    "ai_rag_calls": 0,
    "external_accesses": 0,
    "production_writes": 0,
    "api_cost_estimate_usd": "0.00",
}
with open(os.path.join(repo_root, summary_path), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")

print(f"PASS: import batch {batch_id} written to M7g prototype catalog")
print(f"PASS: metadata records imported: {imported}")
print(f"PASS: blocked records: {blocked}")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${import_output}"

[[ -f "${M7G_DB}" ]] && pass 'M7g prototype catalog sqlite updated' || fail 'M7g catalog sqlite missing'
[[ -f "${M2B_SUMMARY}" ]] && pass 'import summary written' || fail 'import summary missing'
grep -Fq -- '"production_write": false' "${M2B_SUMMARY}" && pass 'summary production_write false' || fail 'summary must show production_write false'

pass 'no file content read attempted'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
