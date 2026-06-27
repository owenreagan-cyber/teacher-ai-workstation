# Safe Local Lesson Review Checklist

## Purpose

This checklist helps Owen verify local lesson briefs and supporting drafts before classroom use. It is a human review guide only. It does not generate lesson content, edit drafts, mark lessons reviewed, or decide readiness automatically.

## Safety Boundaries

- Local only
- Read-only
- No student-sensitive data
- No real student names
- No grades, behavior, medical, IEP, 504, parent communication, or private student information
- No Gmail
- No Google Drive
- No Google Calendar
- No APIs
- No OAuth
- No secrets
- No LLM calls by default
- No school systems
- No publishing, sharing, or sending
- Human review required before classroom use

## Before You Review

1. Confirm files are local drafts under `assistant/lesson-planning/briefs/` and `assistant/lesson-planning/drafts/`.
2. Run workspace and workflow status helpers to confirm the planning context is intact.
3. Open only the lesson files you intend to review.
4. Do not paste student-specific information into lesson files during review.

Suggested commands:

```bash
bin/chief-of-staff --lesson-status
bin/chief-of-staff --lesson-workflow-status
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --lesson-queue-status
```

## Student Privacy Check

- [ ] No real student names
- [ ] No student IDs, contact information, or family details
- [ ] No grades tied to identifiable students
- [ ] No behavior notes about identifiable students
- [ ] No medical, IEP, 504, or accommodation details about identifiable students
- [ ] No parent communication content or private school situations
- [ ] Examples use generic placeholders only

If any item fails, stop and remove or rewrite the sensitive content before continuing.

## Source and Accuracy Check

- [ ] Standards, sources, and factual claims are identified
- [ ] Claims that need verification are marked for Verify Before Use
- [ ] Links, citations, or references are appropriate for classroom use
- [ ] No secrets, credentials, or internal system details appear in lesson files

## Curriculum Fit Check

- [ ] Lesson objective is clear
- [ ] Grade/subject fit matches the planning queue row
- [ ] Activities, assessments, and materials align with the objective
- [ ] Pacing and scope are reasonable for the intended class period

## Classroom Readiness Check

- [ ] Materials list is complete enough for prep
- [ ] Instructions are clear for the teacher
- [ ] Assessment or check-for-understanding matches the objective
- [ ] Transitions, grouping, and timing are workable
- [ ] Backup plan or simplification is noted if needed

## Accessibility and Safety Check

- [ ] Instructions consider common accessibility needs where relevant
- [ ] Physical activity, tools, or materials appear safe for the classroom setting
- [ ] Sensitive topics are handled appropriately for the audience
- [ ] No instructions that would publish, send, share, or upload student work

## Materials Check

- [ ] Required materials are listed
- [ ] Digital or printable materials are identified
- [ ] Prep steps are clear
- [ ] Nothing in the materials section requires unauthorized external services

## Human Review Decision

After completing the checks above, Owen makes the decision. This checklist does **not** decide readiness automatically.

Choose one outcome:

```text
READY FOR CLASSROOM USE AFTER HUMAN REVIEW
NEEDS REVISION
HOLD
DO NOT USE
```

Meaning:

- **READY FOR CLASSROOM USE AFTER HUMAN REVIEW** — Owen has reviewed the local files and accepts them for classroom use after any noted edits are complete.
- **NEEDS REVISION** — Useful structure exists, but changes are required before classroom use.
- **HOLD** — Pause until more information, sources, or supporting drafts are available.
- **DO NOT USE** — Do not use in the classroom; rewrite or discard the draft.

Record the decision in your own trusted notes if needed. This repo does not store review approvals.

## Commands Reference

```bash
bin/chief-of-staff --lesson-status
bin/chief-of-staff --lesson-workflow-status
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --dashboard
```

## What This Does Not Do

- Does not generate lesson content
- Does not edit lesson drafts
- Does not mark lessons reviewed
- Does not publish, send, share, export, or upload anything
- Does not call Gmail, Google Drive, Google Calendar, APIs, OAuth, secrets, school systems, or LLMs by default
- Does not inspect lesson file content deeply or score quality automatically
- Does not approve a lesson without Owen's human review

## Future Ideas Not Included

The following are intentionally not part of this PR:

```text
mark-reviewed workflow
single-slug review view
review notes template
JSON output
Google Docs export
Gmail/Drive integrations
AI lesson revision
rubric scoring
```

These may be considered in separate future PRs with explicit approval and safety review.
