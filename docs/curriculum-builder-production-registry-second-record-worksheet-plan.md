# Production Registry Second-Record Worksheet Plan

Last updated: 2026-07-03

```text
Status: second_record_worksheet_planning_only
Classification: blank worksheet template plan — no second record
Usage: Owen prepares manual metadata before a future governed second-record write mission
```

## Non-Activation

This plan is **not** a production record. Do not add a second `resource-*` entry to `production-registry.json` without a separate explicit governed write mission.

## One-Record-at-a-Time Rule

| Rule | Detail |
| --- | --- |
| Current state | Exactly one production record exists |
| Second write | Adds exactly one additional record (total becomes 2) |
| Third record | Requires another separate mission — never bulk-approved |

## Second-Record Input Worksheet (Blank Template)

Copy locally when preparing. Replace `<placeholder>` only with Owen-approved manual labels.

| Field | Value (Owen enters) |
| --- | --- |
| `id` | `<resource-placeholder-second-001>` |
| `title` | `<short-placeholder-title>` |
| `subject` | `<placeholder-subject-label>` |
| `grade_band` | `<placeholder-grade-band>` |
| `unit_label` | `<placeholder-unit-label>` |
| `lesson_label` | `<placeholder-lesson-label>` |
| `resource_type` | `<placeholder-resource-type>` |
| `audience` | `<teacher_facing \| student_facing>` |
| `review_state` | `<draft \| pending_review \| approved>` |
| `manual_tags` | `<tag-one>, <tag-two>` |
| `notes` | `<short-planning-note-only>` |

## Source Reference (Non-Resolving)

| Field | Value (Owen enters) |
| --- | --- |
| `source_reference.display_label` | `<placeholder-source-label>` |
| `source_reference.source_type` | `manual_label` (recommended) |
| `source_reference.location_note` | `<non-resolving-location-note>` |
| `source_reference.citation_note` | `<non-resolving-citation-note>` |

## ID Uniqueness Rule

- Must use `resource-*` namespace.
- Must not duplicate `resource-math-lesson-108-presentation`.
- Must not use `sample-*` or `example-*` in production.

## Blocked-Content Checklist (Owen Sign-Off)

| Check | Pass? |
| --- | --- |
| No curriculum excerpts in any field | |
| No student names or roster data | |
| No URLs in title, notes, or source_reference | |
| No file paths, Drive IDs, or Canvas IDs | |
| No OAuth tokens or API keys | |
| source_reference is non-resolving manual label | |
| Worksheet reviewed against acceptance criteria | |

## Audience Decision Warning

`student_facing` records carry higher review burden. Default recommendation: `teacher_facing` unless Owen explicitly approves student-facing metadata scope.

## Review State Requirements

Production records should use `review_state: approved` only after Owen sign-off. Draft/pending values belong in local worksheet copies until mission approval.

## Required Safety Review Before Write Prompt

1. Complete this worksheet with placeholders only in repo; real values stay local until mission.
2. Run `--curriculum-production-registry-first-record-status` — must PASS (one record unchanged).
3. Capture pre-write snapshot with `records` count 1.
4. Issue separate explicit governed second-record write mission prompt.

## Pre-Write Snapshot Expectation

Before any second-record mission:

```text
assistant/curriculum-builder/registry/audit/snapshots/
  production-registry-YYYYMMDDTHHMMSSZ-pre-second-write.json
```

Baseline: current one-record state.

## Non-Activation

No second record in repo. Worksheet is template-only.
