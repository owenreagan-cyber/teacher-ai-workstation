# Rule Catalog Schema

## Status

Preview-only schema specification.

## Purpose

The Rule Catalog converts approved evidence into deterministic rules that future preview builders and diagnostics can use.

Rules are not code yet.

Rules are durable specifications.

## Rule Record Schema

| Field | Required | Description |
|---|---:|---|
| rule_id | yes | Stable ID, for example `RULE-CANVAS-0001` |
| title | yes | Human-readable rule title |
| status | yes | proposed, approved, rejected, superseded |
| rule_type | yes | prefix, title, grading, schedule, page, announcement, file, diagnostic, write_gate, authority |
| subject_area | yes | Math, Reading, Spelling, ELA, History, Science, Homeroom, Files, Cross-Course, Governance |
| statement | yes | Clear deterministic rule |
| rationale | yes | Why the rule exists |
| evidence_refs | yes | Evidence IDs supporting the rule |
| source_authority_level | yes | Highest authority supporting the rule |
| allowed_actions | yes | What future systems may do with this rule |
| blocked_actions | yes | What future systems may not do |
| validation_requirements | yes | How status/diagnostics should check it |
| examples | no | Approved examples |
| aliases | no | Legacy aliases recognized but not generated |
| unresolved_questions | no | Related review questions |
| supersedes | no | Previous rule IDs |
| created_in_phase | yes | Phase ID |
| last_reviewed_in_phase | yes | Phase ID |

## Rule ID Pattern

```text
RULE-CANVAS-0001
RULE-CANVAS-0002
RULE-CANVAS-0003
```

## Initial Rule Families

Phase 19C prepares these rule families:

```text
PREFIX
ASSIGNMENT_TITLE
STUDY_GUIDE_GRADING
READING_SPELLING_TOGETHER
FRIDAY
NEWSLETTER
FILE_MANAGEMENT
SOURCE_AUTHORITY
MEDICAL_CENTER
WRITE_GATE
```

## Required Rule Safety

Every rule must list blocked actions.

Every rule must distinguish between:

```text
preview use
diagnostic use
future write-gate use
```

No rule may imply current Canvas write approval.

## Example Rule

```text
rule_id: RULE-CANVAS-0001
title: Math prefix is SM5
status: approved
rule_type: prefix
subject_area: Math
statement: Future Math assignment/page generation uses canonical prefix SM5.
evidence_refs: EV-CANVAS-...
allowed_actions: preview, validation, diagnostic
blocked_actions: Canvas write, direct mutation, unreviewed publish
```

## Boundary

The Rule Catalog schema does not implement rules in code.
