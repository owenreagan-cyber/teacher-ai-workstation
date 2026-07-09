# Canvas LLM Phase 19C — Evidence Vault Schema

## Status

Preview-only schema specification.

## Purpose

The Evidence Vault is the durable place where Canvas LLM Center stores reviewed evidence before it becomes a rule, preview, diagnostic, or write-gate candidate.

The Evidence Vault prevents future implementation from relying on:

- memory-only decisions
- hidden chat context
- legacy code guesses
- raw historical Canvas assumptions
- AI-generated inference without source links

## Core Principle

```text
No rule without evidence.
No evidence without classification.
No classification without source authority.
```

## Evidence Record Schema

Each evidence record should contain:

| Field | Required | Description |
|---|---:|---|
| evidence_id | yes | Stable unique ID, for example `EV-CANVAS-0001` |
| title | yes | Human-readable evidence title |
| phase_added | yes | Phase that added the evidence |
| source_type | yes | owner_decision, canonical_doc, legacy_repo, historical_metadata, school_guideline, generated_review, unknown |
| source_ref | yes | File path, doc path, commit hash, or owner decision reference |
| source_quote_or_summary | yes | Short quoted/summarized evidence |
| authority_level | yes | one of the canonical authority levels |
| classification | yes | APPROVED_PATTERN, WORKFLOW_EVIDENCE, LEGACY_FORMAT_ONLY, UNKNOWN_NEEDS_REVIEW |
| subject_area | yes | Math, Reading, Spelling, ELA, History, Science, Homeroom, Files, Cross-Course, Governance |
| applies_to | yes | assignment, page, announcement, file, module, diagnostic, write_gate, memory, rule |
| canonical_rule_refs | no | Rule IDs this evidence supports |
| conflict_refs | no | Conflicts or unresolved questions |
| privacy_risk | yes | none, low, medium, high, blocked |
| canvas_write_relevance | yes | none, preview_only, possible_future_write, blocked |
| reviewed_by | no | Owen or reviewer name/role |
| review_status | yes | proposed, reviewed, approved, rejected, superseded |
| notes | no | Additional notes |

## Evidence ID Pattern

```text
EV-CANVAS-0001
EV-CANVAS-0002
EV-CANVAS-0003
```

## Evidence Storage Recommendation

Phase 19C does not create a database.

Future storage options may include:

```text
docs/programs/canvas-llm/evidence-vault/*.md
data/canvas-llm/evidence-vault/*.json
local SQLite evidence table
```

The first implementation should remain local-first.

## Required Safety Defaults

Every evidence record defaults to:

```text
canvas_write_relevance = preview_only
privacy_risk = low or higher until reviewed
review_status = proposed
```

No evidence record authorizes Canvas mutation by itself.

## Boundary

This schema does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- raw `.local` metadata commits
- student data access
- body ingestion
- file mutation
- implementation work
