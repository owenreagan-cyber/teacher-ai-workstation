# Curriculum Registry v0

Last updated: 2026-07-01

## Purpose

Curriculum Registry v0 is the repository's first approved implementation subsystem under Phase 2 Mission 1. It provides a **local-first, read-only, manual metadata registry** that becomes the foundation for future contracts, renderers, retrieval, Canvas packaging, and lesson generation.

Registry v0 is **metadata only**. It does not store curriculum file contents, resolve source locations, or perform ingestion.

## Scope (v0)

Registry v0 supports:

- manual metadata entries
- metadata only
- read-only operation
- deterministic validation
- stable identifiers (`sample-` prefix for fictional v0 records)
- versioning (`registry_version: 0.1.0`)
- future extensibility via schema and envelope fields

Registry v0 does **not** support:

- Drive scanning, NAS scanning, or folder crawling
- OCR, embeddings, vector database, or RAG
- lesson generation or review generation
- Canvas publishing, Canvas API, Google Drive API, or OAuth
- network access, automation, or background jobs
- student data or live curriculum parsing
- registry writes from CLI or automation

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Registry store | `assistant/curriculum-builder/registry/v0/registry.json` |
| Record schema | `assistant/curriculum-builder/registry/v0/registry-schema.json` |
| Local README | `assistant/curriculum-builder/registry/v0/README.md` |
| Validator | `scripts/curriculum-registry-v0-validator.sh` |
| Status proof | `scripts/curriculum-registry-v0-status.sh` |

Planning vocabulary alignment:

- `docs/curriculum-builder-manual-registry-schema-plan.md` — field definitions
- `docs/curriculum-builder-manual-registry-sample-proof.md` — fictional sample provenance

## Envelope Format

The registry file is a versioned envelope with fictional placeholder records:

```json
{
  "registry_version": "0.1.0",
  "registry_status": "active_v0",
  "metadata_only": true,
  "read_only": true,
  "records": []
}
```

- `registry_version` — semantic version for the v0 envelope contract
- `registry_status` — `active_v0` for the operational read-only store
- `metadata_only` / `read_only` — must be `true`
- `records` — array of manual metadata entries (`activation_status: registry_v0`)

## Record Contract

Each record follows the manual registry schema plan. Required fields include:

`registry_id`, `title`, `resource_type`, `source_system`, `source_reference`, `source_reference_type`, `subject`, `grade_band`, `course`, `unit`, `lesson`, `pacing_reference`, `teacher_only`, `student_facing_allowed`, `review_status`, `approval_status`, `local_first_safety_flags`, `notes`, `created_by_manual_entry`, `activation_status`

v0 safety rules enforced by the validator:

- `registry_id` must match `sample-[a-z0-9-]+`
- `source_reference` must use placeholder URI schemes only (`gdrive://placeholder/`, `nas://placeholder/`, `local://placeholder/`, `icloud://placeholder/`)
- no `http://` or `https://` URLs
- `created_by_manual_entry` must be `true`
- `activation_status` must be `registry_v0`
- required safety flags must be present
- reserved blocked fields (`parsed_text_status`, `ocr_status`, `embedding_status`, etc.) must not appear
- `teacher_only: true` cannot pair with `student_facing_allowed: "true"`

## Read-Only Boundary

Registry v0 is validated read-only. Status and validator scripts:

- do not write to the registry file
- do not scan folders or resolve references
- do not make network calls
- do not ingest or parse curriculum content

Chief of Staff commands report PASS/WARN/FAIL only; they do not mutate registry data.

## Validation

```bash
bash scripts/curriculum-registry-v0-validator.sh
bin/chief-of-staff --curriculum-registry-v0-validate
bin/chief-of-staff --curriculum-registry-v0-status
```

Optional custom file path for validator:

```bash
bash scripts/curriculum-registry-v0-validator.sh path/to/registry.json
```

## Versioning and Future Work

| Version | Status |
| --- | --- |
| v0.1.0 | Active — manual metadata, fictional samples, read-only validation |
| v0.2+ | Not started — requires separate approved mission |

Future versions may add: output contract binding, renderers, retrieval indexes, Canvas packaging hooks, and bounded ingestion — each approval-gated.

## Related Governance

- `docs/engineering-constitution.md` — Phase 2 implementation authority
- `docs/implementation-approval-gate.md` — track intake and approval boundaries
- `docs/curriculum-builder-section-completion-audit.md` — planning closure plus Registry v0 activation note

## no scanning

Registry v0 explicitly excludes scanning, crawling, indexing, and external resolution. This document restates that boundary for status-script verification.

## no student data

All v0 records use fictional placeholder titles and references. No real student names or student-sensitive data belong in the registry.
