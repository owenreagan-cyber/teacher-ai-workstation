# Calendar Disruption and Snow-Day Contract

## Contract identity

```text
calendar_disruption.v2026_27
```

Status:

```text
APPROVED
```

## Canonical sources

- `docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent/calendar-disruption-doctrine.md`
- `scripts/canvas_llm_phase24/rule_engine.py`
- owner-approved 2026–2027 snow-day instructions

## Purpose

This contract governs unexpected closures, snow days, and other approved disruptions that change the instructional sequence after a week has already been planned.

## Disruption event

A disruption event must record:

```text
id
event_type
event_date
reason
original_status
new_status
affected_week_codes
affected_subjects
created_at
created_by
reversed_at
reversed_by
revision
```

Supported event types:

```text
snow_day
unexpected_closure
late_start
early_dismissal
schedule_override
reversal
```

Only full-day closure behavior is approved in this contract. Partial-day behavior remains a separate future rule.

## Closed-day display

For a full unexpected closure:

```text
In Class: Snow Day
At Home: none
```

No ordinary assignment should be created for the closed date.

## Lesson cascade

When a date becomes non-instructional:

1. the lesson scheduled for that date moves to the next valid instructional day;
2. later lesson content cascades forward by instructional day;
3. lesson order must remain intact;
4. missed content must not be silently dropped;
5. missed content must not be converted into homework automatically;
6. existing teacher-entered downstream lessons must not be overwritten without preview;
7. all proposed changes must be shown before applying the cascade.

## Test displacement

Tests may not occur on Monday.

When a cascade places a test on Monday:

1. move the test to Tuesday;
2. preserve the logical sequence;
3. adjust review or preparation content as needed;
4. recalculate Study Guide timing using the previous valid instructional day;
5. regenerate all affected assignment, reminder, and announcement dates.

Example:

```text
Original test: Friday
Friday closure: test would shift to Monday
Canonical result: test moves to Tuesday
```

## Affected artifact classes

A disruption may invalidate or regenerate:

```text
weekly plan entries
assignment drafts
assignment due dates
Study Guide dates
Fact Test relationships
resource requirements
agenda page rows
agenda page links
assessment notices
assessment reminders
weekly announcements
Homeroom newsletter content
module placement intent
deployment manifests
Canvas comparison results
approvals
```

## Stale-state behavior

Any affected generated artifact becomes stale.

Required state changes:

- generated artifact → `NEEDS_REGENERATION`
- affected comparison → stale
- affected approval → invalid
- affected publish batch → blocked
- affected verified result → historical only

No revised Canvas operation may proceed until:

1. the new schedule is generated;
2. the teacher reviews it;
3. blockers are resolved;
4. comparison is rerun;
5. approval is renewed.

## Audit history

The system must preserve:

- original schedule;
- proposed revised schedule;
- applied revised schedule;
- affected record IDs;
- old and new dates;
- old and new lesson ordering;
- old and new artifact hashes;
- who approved the change;
- when the change was applied;
- whether the disruption was later reversed.

## Reversal

A mistaken closure entry must be reversible.

Reversal must:

1. preserve the disruption event in history;
2. restore or recompute the original instructional sequence;
3. avoid overwriting later teacher edits silently;
4. mark affected generated artifacts stale again;
5. require renewed review and approval.

## Communication behavior

When an assessment date changes:

- regenerate the first notice;
- regenerate the reminder;
- update the agenda page;
- update Homeroom newsletter content;
- update assignment due dates;
- show old and new dates in the review diff;
- require renewed approval before publication.

## Prohibited behavior

The system must never:

- silently drop a lesson;
- automatically convert the missed lesson into homework;
- keep later lessons on their original dates without evaluating the sequence;
- place a shifted test on Monday;
- retain stale due dates;
- retain stale Study Guide dates;
- retain stale reminders or announcements;
- preserve an approval tied to the old schedule;
- publish the revised schedule without renewed approval;
- add an unapproved extra school day.

## Preview contract

Before applying a disruption, show:

```text
affected weeks
affected subjects
original date
new date
original lesson
new lesson placement
test movements
Study Guide movements
assignment due-date changes
announcement changes
resource changes
approval invalidations
unresolved conflicts
```

Available actions:

```text
Apply
Cancel
Edit proposed sequence
Mark for later review
```

## End-of-quarter and end-of-year overflow

A cascade that reaches:

- track-out;
- quarter boundary;
- summer break;
- the end of the current school year;

must not continue automatically without review.

Status:

```text
OWNER_REVIEW_REQUIRED
```

The system may propose a sequence, but it must not guess whether to compress, omit, combine, or move content across a major boundary.

## Validation requirements

The validator must test:

- snow-day display text;
- no homework on closed date;
- next instructional-day shift;
- downstream cascade;
- no lesson deletion;
- no automatic homework conversion;
- Monday test moves to Tuesday;
- Study Guide recalculation;
- stale artifact marking;
- approval invalidation;
- reversible disruption history;
- blocked publish before renewed approval.
