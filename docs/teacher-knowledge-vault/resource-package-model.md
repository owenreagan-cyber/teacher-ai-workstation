# Teacher Knowledge Vault — Resource Package Model

Last updated: 2026-07-04

```text
Status: virtual grouping model — not folders
Canvas publishing: candidates only — no automatic writes
```

## Definition

Resource packages are teaching bundles, not folders. They group related resources and representations for a lesson, unit, or assessment.

## Example Packages (Fake)

| Package | Scope |
| --- | --- |
| Math/Saxon Lesson 21 | Saxon IM5 lesson bundle |
| Reading Mastery lesson package | RM unit materials |
| CKHG American Revolution chapter | History chapter bundle |
| CKSci Energy Transfer unit | Science unit bundle |
| Spelling Test 12 | Spelling assessment bundle |

## Package Members May Include

- Student textbook/reader
- Teacher guide
- Worksheet/homework
- Slides
- Blank/completed study guide
- Assessment
- Answer key (teacher-only)
- Canvas-ready representation
- AI-generated adapted resource
- Review game/activity
- Pacing guide reference

## Rules

- Packages are virtual collections — see M1 `fake-collections.json` pattern
- One representation may appear in multiple packages
- teacher-only items are visible in teacher mode but blocked from student-facing package output
- Canvas-ready packages are publishing **candidates** only

Fixture: `assistant/teacher-knowledge-vault/m3/fake-resource-packages.json`
