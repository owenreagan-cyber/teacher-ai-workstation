# Curriculum Source Readiness — Fake Fixtures

Planning-only fake curriculum source metadata inventory.

## Authority

- **Not** production registry
- **Not** real curriculum content or student data
- **Not** writable without explicit Owen-approved mission

Validated by `scripts/curriculum-source-readiness-validate.sh`.

Status proof: `bin/chief-of-staff --curriculum-source-readiness-status`

## Files

| File | Purpose |
| --- | --- |
| `curriculum-source-metadata.schema.json` | Fake source record schema |
| `fake-curriculum-source-inventory.json` | Canonical fake inventory envelope |
| `negative/` | Negative test fixtures (must fail validation) |

## ID Pattern

Source IDs must match `fake-source-NNN` (e.g. `fake-source-001`).

## Safety Booleans

On every source record:

- `content_ingestion_allowed`: **false**
- `student_data_allowed`: **false**
- `real_curriculum_content_allowed`: **false**
- `fake_fixture_only`: **true**
- `production_write_allowed`: **false**
