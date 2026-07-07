# Canvas LLM Phase 2 Manual Evidence Intake

```text
Status: canvas_llm_phase_2_manual_evidence_intake_complete
Classification: manual/exported/redacted evidence scaffold
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Automatic scanning: blocked
```

## Purpose

Phase 2 creates a safe local pattern for user-provided, manually exported, redacted Canvas evidence. It lets future standards learning use approved evidence without connecting to live Canvas.

## Intake Location

- `evidence/canvas-llm/manual-exported/` - future manual inbox for Owen-approved redacted evidence.
- `evidence/canvas-llm/redacted-examples/` - committed artificial examples used by status checks.

## Redaction Checklist

Before any manual evidence is added, remove:

- student names, IDs, submissions, grades, comments, messages, accommodations, rosters, analytics, family/private information, or identifying classroom data.
- Canvas API tokens, OAuth files, client secrets, cookies, session data, or environment variables.
- full unreviewed course dumps.
- real curriculum folders.
- unrelated private files.

## Allowed Evidence Types

- redacted page HTML snippets.
- redacted assignment metadata.
- redacted module structures.
- redacted screenshot notes.
- exported page content with all student/private data removed.

## Prohibited Evidence Types

- rosters, submissions, grades, comments, messages, accommodations, analytics, private student/family information.
- credentials, API tokens, OAuth files, client secrets, cookies, session data, or `.env` files.
- full unreviewed Canvas course dumps.
- real curriculum folders.
- live Canvas API/OAuth outputs.

## Validator Boundary

`bin/chief-of-staff --canvas-llm-phase-2-status` verifies the scaffold and scans committed redacted example files for obvious prohibited patterns. It does not scan arbitrary manual evidence, connect to Canvas, parse real exports deeply, generate content, or promote evidence into standards.

## Next Approval Gate

Any future use of manually added evidence for standards learning requires an Owen-approved review/promotion mission that names allowed files, redaction proof, review owner, and output location.
