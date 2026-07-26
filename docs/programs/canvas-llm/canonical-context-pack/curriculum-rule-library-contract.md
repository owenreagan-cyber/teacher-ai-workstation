# Curriculum Rule Library Contract

```text
Status: active contract (C1J curriculum rule library + teacher configuration)
Authority: canonical-context-pack
Runtime activation: rule loading and validation only — no Canvas publishing
```

## Purpose

Create a teacher-owned **Curriculum Rule Library** so the application understands **"What rules does this teacher use?"** without requiring code changes.

The teacher owns curriculum rules, grading preferences, homework patterns, and assessment behavior. The AI applies rules; it does not invent rules.

## Rule Ownership

- Rules live in teacher-owned JSON configuration under `config/curriculum/canvas/`
- Python modules load and validate rules; they do not hardcode daily assignments
- Missing rules for History, Science, Shurley, and Language Arts return `NEEDS_TEACHER_RULE`
- Never infer or auto-create missing curriculum rules

## Architecture Lifecycle

```text
Curriculum Profile
  ↓
Curriculum Rules (+ Teacher Overrides)
  ↓
Homework Rules Engine (C1I)
  ↓
Assignment Draft Generator
  ↓
Approval Queue
  ↓
Teacher Decision
  ↓
Future Canvas Publishing (disabled)
```

## Curriculum Rule Registry

`CurriculumRule` fields: `rule_id`, `school_year`, `grade_level`, `subject`, `curriculum_program`, `rule_type`, `trigger`, `generation_pattern`, `grading_policy`, `teacher_decision_required`, `active`, `created_at`, `updated_at`.

Rule types: homework, practice, classwork, assessment, grading_policy.

## Trigger Model

Example Math Monday Homework:

```json
{
  "subject": "math",
  "days": ["Monday"],
  "requires_lesson": true
}
```

## Generation Pattern

Human-readable rule description stored in JSON (not Python-only):

`"Saxon Math 5 Lesson {lesson}: Problems #12-30 even"`

## Curriculum Profile

Default profile: **2026-2027 Grade 4 Default Profile**

Programs: Saxon Math 5, Reading Mastery 4, Spelling 4

Active rules: Math homework/practice, Reading workbook/comprehension, Spelling weekly test.

## Teacher Overrides

`RuleOverride` fields: `override_id`, `rule_id`, `school_year`, `field_changed`, `old_value`, `new_value`, `reason`, `created_at`.

Overrides must be explicit, reversible, and audited. No silent changes.

Example: Math Practice Check `counts_toward_final_grade` changed from `false` to `true` with reason documented.

## Rule Validation

| State | Meaning |
| --- | --- |
| PASS | Active curriculum rules configured |
| NEEDS_TEACHER_RULE | No teacher-owned rule for subject |
| INVALID | Configuration error |

Subjects with PASS: Math, Reading, Spelling.

Subjects with NEEDS_TEACHER_RULE: History, Science, Shurley, Language Arts.

## Integration with C1I

C1I homework rules engine loads effective rules from the curriculum profile and applies teacher overrides before generating assignment drafts. Existing C1I behavior is preserved.

## Chief of Staff Commands

| Flag | Output |
| --- | --- |
| `--curriculum-rules-status` | Math/Reading/Spelling PASS; History/Science NEEDS RULE |
| `--curriculum-profile-status` | Active profile, rule count, override count |

## Safety Boundaries

### Forbidden

- Canvas assignment publishing or writes
- Grade or gradebook mutation
- Student data access
- Automatic grading decisions
- Automatic rule creation for missing subjects
- Automatic pacing changes

### Allowed

- Grading policy metadata
- Teacher choice flags
- Rule validation and audit history
- Explicit reversible overrides

## Non-Activation

This contract documents curriculum rule library posture only. No Canvas writes, grade changes, or automatic teacher decisions are activated by C1J.
