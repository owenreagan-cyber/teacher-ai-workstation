# Curriculum Source Readiness — Fake Inventory Index

Last updated: 2026-07-02

```text
Status: fake_fixture_only
Real curriculum ingestion: blocked
Student data: blocked
Production writes: blocked
```

## Purpose

Human-readable index of the fake curriculum source metadata inventory. This is **not** a real source catalog.

**Canonical JSON:** `assistant/curriculum-builder/samples/curriculum-source-readiness/fake-curriculum-source-inventory.json`

**Boundary plan:** `docs/curriculum-source-readiness-and-intake-boundary-plan.md`

## Fake Sources (Metadata Only)

| source_id | grade_band | subject | unit_label | lesson_label | source_type | review_state |
| --- | --- | --- | --- | --- | --- | --- |
| fake-source-001 | grade-4 | ela | sample-unit-alpha | sample-lesson-one | teacher_created_placeholder | draft_fake_fixture |
| fake-source-002 | grade-5 | math | sample-unit-beta | sample-lesson-two | manual_reference_placeholder | not_started |
| fake-source-003 | grade-6 | science | sample-unit-gamma | sample-lesson-three | draft_fake_fixture | in_review_placeholder |

## What These Records Do Not Contain

- Real curriculum titles or textbook names
- Real file paths or Drive URLs
- Canvas course IDs
- Answer keys, test items, or excerpts
- Student names or identifiers

## Proof

```bash
bin/chief-of-staff --curriculum-source-readiness-status
bash scripts/curriculum-source-readiness-validate.sh
```

## Future Real Pilot

Requires Owen approval per boundary plan § Tiny Pilot Checklist. Fake inventory does not authorize promotion to production.
