# Canonical Weekly Input Contract

## Purpose

This contract defines the teacher-editable source data for a real instructional week.

The editable weekly model is the production source of truth for planning. It must not be reconstructed from the Phase 23 synthetic fixture.

The model must:

- support every 2026–2027 instructional week;
- always expose Monday through Friday;
- support blank and partially completed weeks;
- persist in local SQLite;
- survive browser refresh and local service restart;
- preserve revision history;
- feed prediction, resource resolution, generation, comparison, approval, and deployment;
- invalidate affected approvals when edited;
- keep fixtures test-only.

## Existing canonical storage surfaces

The current Teacher AI Workstation already defines:

- `weekly_plans`
- `subject_weekly_plans`
- `daily_subject_entries`
- `assignment_families`
- `drafts`
- `resources`
- `resource_relationships`
- `deployment_items`
- `revisions`

The future recovered weekly model should extend or normalize these existing surfaces rather than introduce a disconnected schema.

## Weekly-plan identity

| Field | UI label | Type | Required | Editable | Source | Notes |
|---|---|---:|---:|---:|---|---|
| `id` | — | string | yes | no | derived | Stable local identifier |
| `school_year` | School Year | string | yes | limited | canonical calendar | Must be `2026-2027` for current production work |
| `week_code` | Week | string | yes | yes | instructional-week map | Example: `Q1W1` |
| `quarter` | Quarter | integer | yes | no | derived | Derived from week code/calendar |
| `starts_on` | Week Starts | ISO date | yes | no | canonical calendar | Must match instructional-week source |
| `ends_on` | Week Ends | ISO date | yes | no | canonical calendar | Must match instructional-week source |
| `state` | Week Status | enum | yes | controlled | workflow | Existing Phase 22 weekly states |
| `validation_state` | Validation | enum | yes | no | validator | Derived |
| `version` | Revision | integer | yes | no | persistence | Increments on accepted edit |
| `updated_at` | Last Saved | timestamp | yes | no | persistence | Local time display may be derived |
| `updated_by` | Updated By | string | yes | no | local identity | Single teacher; normally `owen` |

## Week states

Existing canonical values:

```text
not_started
in_progress
ready_for_review
approved
scheduled
partially_deployed
deployed
needs_revision
archived
```

An edit to an approved, scheduled, partially deployed, or deployed week must create a new revision and return affected content to an appropriate review-required state.

## Subject-plan identity

Each instructional subject receives one plan per week.

| Field | UI label | Type | Required | Editable | Notes |
|---|---|---:|---:|---:|---|
| `id` | — | string | yes | no | Stable identifier |
| `weekly_plan_id` | — | string | yes | no | Parent reference |
| `subject` | Subject | enum | yes | no | Canonical subject key |
| `payload` | Subject Settings | object | yes | controlled | Subject-level options only |
| `version` | Revision | integer | yes | no | Increments on subject-level changes |

## Canonical subjects

```text
homeroom
math
reading
spelling
language_arts
history
science
```

Reading and Spelling may share a Canvas course and agenda artifact while remaining distinct subject identities in the weekly model.

## Daily subject entry

Every subject plan must expose one row for each weekday:

```text
Monday
Tuesday
Wednesday
Thursday
Friday
```

A missing instructional activity is represented by an empty or explicit no-class row, not by omitting the weekday.

## Teacher-editable daily fields

| Canonical field | UI label | Type | Required | Default | Editable | Current storage relation |
|---|---|---:|---:|---|---:|---|
| `subject` | Subject | enum | yes | inherited | no | `daily_subject_entries.subject` |
| `entry_date` | Date | ISO date | yes | calendar date | limited | `daily_subject_entries.entry_date` |
| `weekday` | Day | enum | yes | derived | no | `daily_subject_entries.weekday` |
| `lesson` | Lesson / Number | string | no | empty | yes | `daily_subject_entries.lesson` |
| `title` | Topic / Title | string | no | empty | yes | `daily_subject_entries.title` |
| `entry_type` | Entry Type | enum | yes | `lesson` | yes | currently derivable; should become explicit |
| `sequence_number` | Lesson / Test Number | string or integer | conditional | null | yes | pacing/prediction models |
| `in_class` | In Class | text | no | empty | yes | `daily_subject_entries.in_class` |
| `at_home` | At Home / Homework | text | no | empty | yes | `daily_subject_entries.at_home` |
| `materials` | Materials | text or structured list | no | empty | yes | `daily_subject_entries.materials` |
| `reminders` | Reminders | text or structured list | no | empty | yes | `daily_subject_entries.reminders` |
| `tests` | Assessment Number / Test | string | no | empty | yes | `daily_subject_entries.tests` |
| `resources` | Resources | list of resource references | no | `[]` | yes | `daily_subject_entries.resources` |
| `notes` | Teacher Notes | text | no | empty | yes | `daily_subject_entries.notes` |
| `no_class` | No Class | boolean | yes | false | yes | should be explicit in recovered model |
| `assignment_intent` | Create Assignment | enum | yes | derived | yes | should be explicit in recovered model |
| `announcement_intent` | Announcement | enum | yes | derived | yes | should be explicit in recovered model |
| `newsletter_include` | Include in Newsletter | boolean | yes | subject default | yes | should be explicit in recovered model |
| `teacher_override` | Teacher Override | object | no | null | yes | Phase 24 correction model |
| `resolver_output` | Resource Resolution | object | yes | `{}` | no | `daily_subject_entries.resolver_output` |
| `validation` | Validation Results | list | yes | `[]` | no | `daily_subject_entries.validation` |
| `version` | Revision | integer | yes | 1 | no | persistence |
| `updated_at` | Last Saved | timestamp | yes | generated | no | persistence |
| `updated_by` | Updated By | string | yes | `owen` | no | persistence |

## Entry types

The normalized controlled vocabulary should include:

```text
lesson
review
written_test
fact_test
study_guide
investigation
classroom_practice
reading_test
reading_checkout
spelling_test
project
assessment
holiday
snow_day
no_class
custom
```

Subject validators must restrict invalid combinations.

Examples:

- `classroom_practice` is normally Language Arts.
- `fact_test` is Math.
- `reading_checkout` is Reading and only valid for Checkouts 1–13.
- `spelling_test` is Spelling.
- History and Science assignment creation remains disabled unless separately approved.

## Teacher shorthand normalization

The system may normalize unambiguous shorthand.

| Input | Normalized |
|---|---|
| `l1` | `Lesson 1` |
| `L1` | `Lesson 1` |
| `lesson 1` | `Lesson 1` |
| `Lesson 1` | `Lesson 1` |

Normalization may derive:

- normalized lesson wording;
- known lesson number;
- known subject rule family;
- deterministic Math parity when no override exists;
- known canonical resource requirements.

Normalization must not guess:

- an unknown test number;
- an unknown topic;
- a due time;
- assignment-group IDs;
- module IDs;
- resource URLs;
- a teacher override;
- an unresolved assessment relationship.

## Assignment intent values

```text
derived
create
do_not_create
review_required
blocked
```

Rules:

- Math, Reading, Spelling, and Language Arts may derive assignment intent from entry type.
- History and Science default to `do_not_create`.
- Missing required metadata yields `review_required` or `blocked`.
- An explicit teacher choice is recorded separately from a derived default.

## Announcement intent values

```text
none
weekly_update
assessment_first_notice
assessment_reminder
schedule_change
resource_update
custom
```

Announcement intent creates a draft request only. It does not authorize publication.

## Save-state behavior

Teacher-visible save states:

```text
Unsaved
Saving
Saved
Failed
Retrying
Conflict
```

These are UI states, not deployment states.

Required behavior:

1. A local edit immediately becomes `Unsaved`.
2. A successful SQLite transaction becomes `Saved`.
3. Validation rejection becomes `Failed` with a plain-language reason.
4. A version conflict becomes `Conflict`.
5. Saving must never imply approval or publication.
6. Edits invalidate affected generated artifacts and approvals.

## No-class and closure behavior

When `no_class` is true:

- no ordinary in-class lesson is generated;
- no ordinary homework is generated;
- assignment intent defaults to `do_not_create`;
- the displayed reason must be explicit.

For a snow day:

```text
In Class: Snow Day
At Home: none
```

The calendar-disruption contract governs lesson cascading and regeneration.

## Resource selections

Teacher resource choices must reference stable resource identities, not arbitrary URLs.

A selected resource record should include:

```text
resource_id
selection_source
selected_by
selected_at
purpose
```

Allowed `selection_source` values:

```text
teacher_selected
canonical_registry
verified_alias
deterministic_match
suggested_candidate
```

Only verified resources may be treated as resolved.

## Correction and precedence

Canonical precedence:

1. hard owner-approved rule;
2. explicit teacher correction or override;
3. current canonical map;
4. verified teacher-memory preference;
5. deterministic prediction;
6. unresolved suggestion.

A teacher correction must preserve:

```text
subject
week_code
day
field
original_value
corrected_value
scope
reason
source_rule
revision
created_at
created_by
```

## Revision requirements

Before changing a persisted planning record:

- create a revision snapshot;
- apply the accepted edit;
- increment the record version;
- update `updated_at`;
- record `updated_by`;
- invalidate dependent generated artifacts;
- invalidate affected approval records.

## Production-source rule

The visible planner must read from this local persisted weekly model.

The Phase 23 synthetic fixture may be used only for:

- tests;
- golden snapshots;
- regression comparison;
- demonstrations clearly labeled synthetic.

It must not be the production source for a selected real week.
