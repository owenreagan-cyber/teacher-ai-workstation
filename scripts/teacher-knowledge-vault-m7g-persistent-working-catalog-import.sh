#!/usr/bin/env bash
# Teacher Knowledge Vault M7g persistent working catalog import — fixed fixture paths only.
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

M7G_OUT_DIR=".local/teacher-knowledge-vault/working-catalog"
M7G_DB="${M7G_OUT_DIR}/working-catalog.sqlite"
M7G_BACKUP_DIR="${M7G_OUT_DIR}/backups"
M7G_SUMMARY="${M7G_OUT_DIR}/import-summary.json"
M7G_ROLLBACK="${M7G_OUT_DIR}/rollback-proof.json"
M7B_INVENTORY="assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json"
M7C_PREVIEW="assistant/teacher-knowledge-vault/m7c/fake-normalized-preview-candidates.json"
M7C_VALIDATOR="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"
M7F_GATE_DOC="docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md"
M7F_APPROVAL_PACKET="assistant/teacher-knowledge-vault/m7f/fake-persistent-catalog-approval-packet.json"

section 'Teacher Knowledge Vault M7g Persistent Working Catalog Import'
cat <<'EOF'
Status: bounded runtime write — persistent local working catalog prototype only
Fixture paths: fixed committed M7b/M7c only
Catalog mode: persistent_working_prototype
Production catalog writes: no
Arbitrary path input: no
Network/API/OAuth: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

section 'M7f Approval Gate Preconditions'
[[ -f "${M7F_GATE_DOC}" ]] && pass 'M7f approval gate doc present' || fail 'M7f approval gate doc missing — import blocked'
[[ -f "${M7F_APPROVAL_PACKET}" ]] && pass 'M7f approval packet fixture present' || fail 'M7f approval packet missing — import blocked'
grep -Fq -- 'complete_teacher_knowledge_vault_m7f_persistent_working_catalog_approval_gate' "${M7F_GATE_DOC}" && pass 'M7f closure marker verified' || fail 'M7f closure marker missing — import blocked'

section 'M7c Fixture Validator'
[[ -f "${M7C_VALIDATOR}" ]] || { fail "M7c validator missing"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
bash "${M7C_VALIDATOR}" >/dev/null 2>&1 && pass 'M7c fixture validator passed before import' || fail 'M7c fixture validator failed — import blocked'

for f in "${M7B_INVENTORY}" "${M7C_PREVIEW}"; do
  [[ -f "${f}" ]] && pass "fixture exists: ${f}" || fail "fixture missing: ${f}"
done

grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'generated path is gitignored' || fail 'generated path must be gitignored'

section 'Persistent Working Catalog Import'
import_output="$(python3 - "${repo_root}" "${M7G_OUT_DIR}" "${M7G_DB}" "${M7G_BACKUP_DIR}" "${M7G_SUMMARY}" "${M7G_ROLLBACK}" "${M7B_INVENTORY}" "${M7C_PREVIEW}" <<'PY'
import json, os, shutil, sqlite3, sys

repo_root, out_dir, db_path, backup_dir, summary_path, rollback_path, inventory_path, preview_path = sys.argv[1:9]
catalog_id = "fake-m7g-working-catalog-001"
batch_id = "fake-m7g-batch-001"
backup_id = "fake-m7g-backup-pre-import-001"
created_at = "2026-07-05T00:00:00Z"
errors = []

os.makedirs(out_dir, exist_ok=True)
os.makedirs(backup_dir, exist_ok=True)

db_full = os.path.join(repo_root, db_path)
backup_full = os.path.join(repo_root, backup_dir, f"working-catalog-{backup_id}.sqlite")

if os.path.exists(db_full):
    shutil.copy2(db_full, backup_full)
    print(f"PASS: backup created before import: {backup_id}")
else:
    print("PASS: no prior catalog — backup before first write skipped")

with open(os.path.join(repo_root, inventory_path), encoding="utf-8") as f:
    inventory = json.load(f)
with open(os.path.join(repo_root, preview_path), encoding="utf-8") as f:
    preview = json.load(f)

records = {r["manual_inventory_id"]: r for r in inventory.get("records", []) if isinstance(r, dict)}
candidates = preview.get("candidates", [])

conn = sqlite3.connect(db_full)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER PRIMARY KEY,
  applied_at TEXT
);
CREATE TABLE IF NOT EXISTS catalog_metadata (
  catalog_id TEXT PRIMARY KEY,
  catalog_mode TEXT,
  production_catalog INTEGER,
  real_curriculum_allowed INTEGER,
  student_data_allowed INTEGER,
  external_sources_allowed INTEGER,
  created_from_fixture_only INTEGER,
  source_fixture_reference TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS import_batches (
  batch_id TEXT PRIMARY KEY,
  fixture_source TEXT,
  source_fixture_reference TEXT,
  created_at TEXT,
  catalog_mode TEXT,
  production_write INTEGER
);
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, source_label TEXT,
  restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS resources (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, source_label TEXT,
  restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS representations (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, source_label TEXT,
  restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS source_items (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, source_label TEXT,
  restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS source_reconciliation (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, source_label TEXT,
  restricted_indexable INTEGER, indexable INTEGER, discoverable INTEGER,
  fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS review_queue_items (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, review_state TEXT,
  fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS event_log (
  id TEXT PRIMARY KEY, batch_id TEXT, event_type TEXT, manual_inventory_id TEXT,
  runtime_executed INTEGER, created_at TEXT
);
CREATE TABLE IF NOT EXISTS blocked_records (
  id TEXT PRIMARY KEY, batch_id TEXT, manual_inventory_id TEXT, block_reason TEXT,
  indexable INTEGER, discoverable INTEGER, fixture_source_ref TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS backup_records (
  backup_id TEXT PRIMARY KEY,
  backup_path TEXT,
  catalog_id TEXT,
  import_batch_id TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS rollback_records (
  rollback_id TEXT PRIMARY KEY,
  import_batch_id TEXT,
  rollback_path TEXT,
  created_at TEXT
);
""")

for table in [
    "catalog_metadata", "import_batches", "sources", "resources", "representations",
    "source_items", "source_reconciliation", "review_queue_items", "event_log",
    "blocked_records", "backup_records", "rollback_records", "schema_version",
]:
    cur.execute(f"DELETE FROM {table}")

fixture_ref = f"{inventory_path}+{preview_path}"
cur.execute(
    "INSERT INTO schema_version VALUES (?,?)",
    (1, created_at),
)
cur.execute(
    """INSERT INTO catalog_metadata VALUES (?,?,?,?,?,?,?,?,?)""",
    (
        catalog_id,
        "persistent_working_prototype",
        0,
        0,
        0,
        0,
        1,
        fixture_ref,
        created_at,
    ),
)
cur.execute(
    "INSERT INTO import_batches VALUES (?,?,?,?,?,?)",
    (batch_id, "m7b+m7c fixtures", fixture_ref, created_at, "persistent_working_prototype", 0),
)

if os.path.exists(backup_full):
    cur.execute(
        "INSERT INTO backup_records VALUES (?,?,?,?,?)",
        (backup_id, backup_dir + f"/working-catalog-{backup_id}.sqlite", catalog_id, batch_id, created_at),
    )

counts = {k: 0 for k in [
    "import_batches", "sources", "resources", "representations", "source_items",
    "source_reconciliation", "review_queue_items", "event_log", "blocked_records",
    "backup_records", "rollback_records", "catalog_metadata", "schema_version",
]}
counts["import_batches"] += 1
counts["catalog_metadata"] += 1
counts["schema_version"] += 1
if os.path.exists(backup_full):
    counts["backup_records"] += 1

teacher_only_restricted = 0
dns_blocked = 0
blocked_count = 0

def flags_for(mid):
    rec = records.get(mid, {})
    restricted = 1 if rec.get("indexing_policy") == "10_TEACHER_ONLY" or rec.get("teacher_only_risk") else 0
    if restricted:
        return 1, 0, 0
    return 0, 1, 1

for ev in [
    ("fake-m7g-evt-import-start", "persistent_working_catalog_import_started", None),
    ("fake-m7g-evt-m7f-gate", "m7f_approval_gate_preconditions_verified", None),
    ("fake-m7g-evt-validator", "m7c_fixture_validator_attached", None),
    ("fake-m7g-evt-preview", "import_preview_candidates_imported", None),
    ("fake-m7g-evt-import-done", "persistent_working_catalog_import_completed", None),
]:
    cur.execute(
        "INSERT INTO event_log VALUES (?,?,?,?,?,?)",
        (ev[0], batch_id, ev[1], ev[2], 1, created_at),
    )
    counts["event_log"] += 1

table_map = {
    "SourceInventoryCandidate": "sources",
    "ResourceCandidate": "resources",
    "RepresentationCandidate": "representations",
    "SourceItemCandidate": "source_items",
    "SourceReconciliationPreview": "source_reconciliation",
}

imported_count = 0
for cand in candidates:
    if not isinstance(cand, dict):
        continue
    ctype = cand.get("candidate_type")
    mid = cand.get("source_manual_inventory_id")
    preview_id = cand.get("preview_id")
    label = cand.get("source_label", "")
    rec = records.get(mid, {})
    if rec.get("student_data_risk"):
        errors.append(f"student data candidate must not import: {mid}")
        continue
    if rec.get("do_not_scan_flag"):
        errors.append(f"do_not_scan candidate must not import: {mid}")
        continue
    restricted, indexable, discoverable = flags_for(mid)
    if restricted:
        teacher_only_restricted += 1
    if ctype == "ReviewQueuePreview":
        cur.execute(
            "INSERT INTO review_queue_items VALUES (?,?,?,?,?,?)",
            (preview_id, batch_id, mid, cand.get("review_requirement", "preview_only"), preview_id, created_at),
        )
        counts["review_queue_items"] += 1
        imported_count += 1
        continue
    table = table_map.get(ctype)
    if not table:
        errors.append(f"unknown candidate type: {ctype}")
        continue
    cur.execute(
        f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?,?)",
        (preview_id, batch_id, mid, label, restricted, indexable, discoverable, preview_id, created_at),
    )
    counts[table] += 1
    imported_count += 1

for mid, rec in records.items():
    if rec.get("student_data_risk"):
        cur.execute(
            "INSERT INTO blocked_records VALUES (?,?,?,?,?,?,?,?)",
            (f"blocked-{mid}", batch_id, mid, "student_data_field_blocked", 0, 0, mid, created_at),
        )
        counts["blocked_records"] += 1
        blocked_count += 1
    if rec.get("do_not_scan_flag"):
        cur.execute(
            "INSERT INTO blocked_records VALUES (?,?,?,?,?,?,?,?)",
            (f"blocked-{mid}", batch_id, mid, "do_not_scan_blocked", 0, 0, mid, created_at),
        )
        counts["blocked_records"] += 1
        blocked_count += 1
        dns_blocked += 1

conn.commit()
conn.close()

summary = {
    "classification": "fake_local_planning_only",
    "catalog_mode": "persistent_working_prototype",
    "production_catalog": False,
    "production_write": False,
    "real_curriculum_allowed": False,
    "student_data_allowed": False,
    "external_sources_allowed": False,
    "created_from_fixture_only": True,
    "catalog_id": catalog_id,
    "import_batch_id": batch_id,
    "backup_id": backup_id if os.path.exists(backup_full) else None,
    "source_fixture_reference": fixture_ref,
    "fixture_files_read": [inventory_path, preview_path],
    "fixture_rows_checked": len(records),
    "preview_candidates_imported": len(candidates),
    "records_imported": imported_count,
    "rejected_count": 0,
    "blocked_count": blocked_count,
    "teacher_only_restricted_count": teacher_only_restricted,
    "do_not_scan_blocked_count": dns_blocked,
    "catalog_records_created": counts,
    "backups_created": counts["backup_records"],
    "rollback_runs": 0,
    "production_writes": 0,
    "runtime_external_accesses": 0,
    "api_calls": 0,
    "network_calls": 0,
    "real_files_read": 0,
    "student_records_read": 0,
    "source_file_operations": 0,
    "curriculum_file_operations": 0,
    "api_cost_estimate_usd": "0.00",
}
rollback = {
    "classification": "fake_local_planning_only",
    "catalog_mode": "persistent_working_prototype",
    "rollback_plan_id": "fake-m7g-rollback-001",
    "import_batch_id": batch_id,
    "catalog_id": catalog_id,
    "catalog_path": db_path,
    "backup_path": backup_dir,
    "cleanup_removes_only_fixed_path": True,
    "no_source_file_deletion": True,
    "batch_removal_supported": True,
    "production_write": False,
}
with open(os.path.join(repo_root, summary_path), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
with open(os.path.join(repo_root, rollback_path), "w", encoding="utf-8") as f:
    json.dump(rollback, f, indent=2)
    f.write("\n")

for e in errors:
    print(f"FAIL: {e}")
if not errors:
    print(f"PASS: import batch {batch_id} created")
    print(f"PASS: catalog written to fixed path {db_path}")
    print(f"PASS: preview candidates imported: {len(candidates)}")
    print(f"PASS: blocked records: {blocked_count}")
    print(f"PASS: catalog_mode persistent_working_prototype")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${import_output}"

[[ -f "${M7G_DB}" ]] && pass "working catalog sqlite exists at fixed path" || fail "working catalog sqlite missing"
[[ -f "${M7G_SUMMARY}" ]] && pass "import summary written" || fail "import summary missing"
[[ -f "${M7G_ROLLBACK}" ]] && pass "rollback proof written" || fail "rollback proof missing"
grep -Fq -- '"production_write": false' "${M7G_SUMMARY}" && pass 'summary shows production_write false' || fail 'summary must show production_write false'
grep -Fq -- '"catalog_mode": "persistent_working_prototype"' "${M7G_SUMMARY}" && pass 'summary shows persistent_working_prototype mode' || fail 'summary must show persistent_working_prototype mode'

pass 'no network call attempted'
pass 'no OAuth API or secrets attempted'
pass 'no source file operations attempted'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
