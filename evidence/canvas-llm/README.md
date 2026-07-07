# Canvas LLM Manual Evidence Intake

```text
Status: manual_local_intake_scaffold
Classification: local/manual only
Automatic scanning: blocked
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Credentials/secrets: blocked
Supabase/Firebase: blocked
```

This folder is the local/manual intake home for future Owen-provided, redacted Canvas evidence examples. It is not connected to Canvas and is not an automatic scanner target.

Student data is prohibited. This means student data is prohibited and student data prohibited for every manual intake example.

## Intake Rule

Owen manually places approved, redacted Canvas evidence in `manual-exported/` only after removing student/private data, credentials, tokens, live URLs that are not needed for a fake/redacted example, and unrelated curriculum content.

## Allowed Evidence Types

- redacted page HTML snippets.
- redacted assignment metadata.
- redacted module structures.
- redacted screenshot notes.
- exported page content with all student/private data removed.

## Prohibited Evidence Types

- rosters.
- submissions.
- grades.
- comments.
- messages.
- accommodations.
- analytics.
- private student or family information.
- credentials, API tokens, OAuth files, client secrets, or environment files.
- full unreviewed course dumps.
- real curriculum folders.
- live Canvas API/OAuth outputs.

## Validation Boundary

`bin/chief-of-staff --canvas-llm-phase-2-status` checks the committed scaffold and redacted examples. It does not crawl, import, parse, or summarize manually added evidence.

## Phase 2 Safety Closure

Canvas LLM Phase 2 is manual/exported/redacted evidence intake only. Student data prohibited. Canvas API/OAuth/live reads are blocked. Canvas writes/publishing are blocked. This folder is not an automatic scanner target.
