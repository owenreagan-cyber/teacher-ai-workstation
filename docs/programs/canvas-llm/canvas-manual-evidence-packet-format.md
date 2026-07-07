# Canvas Manual Evidence Packet Format

```text
Status: packet_format_v0_fixture_only
Classification: manual/exported/redacted/fake-local packet contract
Production authority: no
```

## Required Directory Shape

```text
fixtures/canvas-llm/manual-evidence-packets/<packet-id>/
  packet.json
  source-notes.md
  redacted-pages/
    page-001.md
  redacted-assignments/
    assignment-001.json
  redacted-modules/
    module-001.json
  redacted-files/
    file-001.json
  redacted-announcements/
    announcement-001.md
```

Phase 3 only normalizes packets under `fixtures/canvas-llm/manual-evidence-packets/`. Evidence packet paths must be explicit; broad filesystem scanning is blocked.

## Required Metadata Fields

`packet.json` must include these exact safety fields for the Phase 3 normalizer:

- `packet_id`
- `course_label`
- `school_year_label`
- `export_type`
- `redaction_status`
- `source_type`
- `no_student_data`
- `no_live_canvas_api_oauth`
- `no_real_curriculum_ingestion`
- `no_production_write`
- `evidence_files`
- `allowed_use`
- `blocked_use`
- `review_status`
- `created_date`
- `updated_date`

## Required Safe Values

- `redaction_status`: `redacted_fake_local`
- `source_type`: `manual_exported_redacted_fake_local`
- `no_student_data`: `true`
- `no_live_canvas_api_oauth`: `true`
- `no_real_curriculum_ingestion`: `true`
- `no_production_write`: `true`
- `review_status`: `fixture_reviewed`

## Allowed Evidence File Types

- `.md` for redacted page, announcement, and source-note examples.
- `.json` for redacted assignment, module, and file metadata examples.

## Blocked Packet Contents

Packets must not contain:

- student names, IDs, rosters, submissions, grades, comments, messages, accommodations, analytics, or family/private information.
- Canvas tokens, OAuth files, cookies, API keys, client secrets, `.env` content, or session data.
- live Canvas URLs or claims of Canvas API/OAuth use.
- real curriculum folders or full unreviewed course dumps.
- production write instructions.

## Future Promotion Gate

A later approval-gated phase may define how reviewed evidence becomes a source-backed knowledge packet. Phase 3 does not approve that promotion and does not learn from packet contents.
