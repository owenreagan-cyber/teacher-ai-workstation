# Curriculum Builder Registry v0.2 — Dry-Run Validation Rules

Last updated: 2026-07-02

```text
Status: validation rules for dry-run candidates only
Enforced by: scripts/curriculum-builder-registry-v0-2-dry-run.sh
Registry writes: no
```

## Candidate Envelope

Each dry-run file must be a JSON object with:

| Field | Required | Rule |
| --- | --- | --- |
| `dry_run_version` | yes | Must be `"0.2.0"` |
| `dry_run_mode` | yes | Must be `"manual_entry_candidate"` |
| `metadata_only` | yes | Must be `true` |
| `read_only` | yes | Must be `true` |
| `no_registry_write` | yes | Must be `true` |
| `would_write` | yes | Must be `false` |
| `candidate_entry` | yes | Object; see below |

## Candidate Entry Fields

Aligned with A4 resource contract and Registry v0 vocabulary (metadata only):

| Field | Required | Rule |
| --- | --- | --- |
| `resource_id` | yes | Pattern `^example-[a-z0-9-]+$` (e.g. `example-resource-001`) |
| `title` | yes | Non-empty; fictional placeholder text |
| `resource_type` | yes | Registry v0 enum subset |
| `subject` | yes | Non-empty string |
| `grade_band` | yes | Non-empty string |
| `course` | yes | Non-empty string |
| `unit` | yes | Non-empty string |
| `lesson` | yes | Non-empty string |
| `topic` | yes | Non-empty string |
| `source_reference_id` | yes | Pattern `^example-[a-z0-9-]+$` |
| `source_reference` | yes | Placeholder URI only (see below) |
| `source_system` | yes | `google_drive`, `nas`, `icloud`, `local_folder`, `canvas_export`, or `manual_reference` |
| `teacher_only` | yes | Boolean |
| `student_facing_allowed` | yes | Boolean |
| `review_status` | yes | `approved_placeholder`, `not_started`, `in_review`, or `deferred_placeholder` |
| `notes` | yes | Non-empty fictional note |

## Placeholder URI Rules

Allowed schemes:

- `placeholder://curriculum/...`
- `placeholder://source/...`
- `placeholder://canvas/...`
- `gdrive://placeholder/...`
- `nas://placeholder/...`
- `icloud://placeholder/...`
- `local://placeholder/...`

Blocked:

- `http://` or `https://`
- Real Drive/NAS/iCloud/Canvas paths or IDs
- Paths outside placeholder conventions

## Negative Content Guards

Validator must **fail** if candidate text contains:

- `student name`, `real student`, `pupil name` (case-insensitive)
- `http://` or `https://` in any string field

## Dry-Run Output

On success, validator prints:

```text
dry-run only: would_write=false
no_registry_write: true
```

Validator must never modify files or call external services.

## Non-Activation

These rules validate fake candidates only. They do not authorize registry writes.
