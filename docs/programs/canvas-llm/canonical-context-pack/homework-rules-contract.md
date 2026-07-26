# Homework Rules Contract

```text
Status: active contract (C1I homework, assessment, and pacing rules engine)
Authority: canonical-context-pack
Runtime activation: assignment draft generation only — no Canvas assignment publishing
```

## Purpose

Build teacher-specific instructional rules intelligence that answers **"What assignments should exist?"** before **"How do we publish them?"**

This phase creates **Assignment Drafts**, not Canvas Assignments.

## Rule Ownership

- Rules are teacher-owned and configurable through the rules engine
- Do not hardcode daily assignments directly in generators
- Missing rules for History, Science, Shurley, and Language Arts return `needs_teacher_rule=true`
- Do not guess missing curriculum rules

## Architecture

```text
Curriculum Pacing
  ↓
Pacing Parser (WeeklyInstructionalPlan)
  ↓
Rule Engine (HomeworkRule, AssessmentRule, AssignmentPolicy)
  ↓
Assignment Draft Generator
  ↓
Artifact Registry
  ↓
Approval Queue
  ↓
Teacher Decision
```

## Saxon Math 5 Rules

| Rule | Trigger | Output |
| --- | --- | --- |
| Monday Homework | Math lesson on Monday | Saxon Math 5 - Lesson {X} Homework, Problems #12-30 Even |
| Wednesday Homework | Math lesson on Wednesday | Saxon Math 5 - Lesson {X} Homework, Problems #11-29 Odd |
| Tuesday Practice Check | Math lesson on Tuesday | Saxon Math 5 - Lesson {X} Practice Check, Problems #1-10 |
| Thursday Practice Check | Math lesson on Thursday | Saxon Math 5 - Lesson {X} Practice Check, Problems #1-10 |

Practice checks: 100 points, Percentage grading, teacher choice for final grade (default excluded), `teacher_decision_required=true`.

## Reading Mastery 4 Rules

| Rule | Days | Output |
| --- | --- | --- |
| Workbook and Comprehension | Tuesday, Thursday | Reading Mastery 4 - Lesson {X} Workbook and Comprehension |
| Workbook | Monday, Wednesday | Reading Mastery 4 - Lesson {X} Workbook |

All reading graded items: 100 points, Percentage, teacher choice for final grade (default excluded).

## Spelling Rules

- Spelling Test {N} when test scheduled
- Category: assessment
- 100 points, Percentage grading

## Assessment Rules

Assessments generate draft artifacts only. No automatic rescheduling after snow days. No automatic pacing changes.

## Teacher Decision Points

Practice checks and reading workbook/comprehension items require explicit teacher choice:

- Count toward final grade
- Do not count toward final grade

No automatic selection.

## Approval Queue States

| State | Example |
| --- | --- |
| READY | Homework draft complete |
| NEEDS_REVIEW | Teacher grading choice required |
| BLOCKED | Missing curriculum rule |

## Artifact Registry Integration

Each assignment draft includes:

- artifact_id
- content_hash
- source_rule
- canvas_writes_allowed: false
- preview_only: true

## Future Canvas Assignment Publishing

Canvas assignment publishing remains **disabled** in C1I. Drafts feed the approval and teacher decision pipeline only. Publishing requires a separate approved mission.

## Chief of Staff Commands

| Flag | Output |
| --- | --- |
| `--homework-rules-status` | Math/Reading/Spelling PASS, Missing Rules History/Science |
| `--assignment-draft-preview` | Generated/Needs Review/Blocked counts, no Canvas writes |

## Safety Boundaries

### Forbidden

- Canvas assignment writes
- Grade or gradebook mutation
- Student data access
- Automatic grading selection
- Automatic assessment rescheduling
- Automatic pacing changes

### Allowed

- Grading policy metadata
- Teacher choice flags
- Validation and audit text
- Blocked-state messages

## Non-Activation

This contract documents assignment intelligence posture only. No Canvas writes, grade changes, or automatic teacher decisions are activated by C1I.
