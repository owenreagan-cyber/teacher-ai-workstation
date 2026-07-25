# Canonical Weekly Agenda Page Contract

## Purpose

This contract defines the generated Canvas weekly agenda pages for the 2026–2027 Teacher AI Workstation.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

The authoritative machine-readable sources are:

```text
config/curriculum/canvas/instructional-weeks-2026-2027.json
config/curriculum/canvas/weekly-agenda-standard-2026-2027.json
config/curriculum/canvas/agenda-page-rules.json
config/curriculum/canvas/quarter-subject-activation-2026-2027.json
```

The current rendering references are:

```text
scripts/canvas_llm_phase22/phase22_workstation.py
scripts/canvas_llm_phase23/phase23_content_engine.py
```

Generator alignment with this contract is scheduled for C0L and later phases. The recovered production implementation must converge on one weekly model and one canonical renderer.

## Page groups

Current page groups:

```text
math
reading-spelling
language-arts
history
science
```

Homeroom is not a standard academic agenda page. It is governed by:

```text
newsletter-homeroom-contract.md
```

## History and Science quarter activation

Quarter-subject activation is machine-readable in:

```text
config/curriculum/canvas/quarter-subject-activation-2026-2027.json
```

Rules:

- Q1 and Q3: History active; Science inactive and untouched.
- Q2 and Q4: Science active; History inactive and untouched.

The inactive subject page must remain untouched. The system must not regenerate, rewrite, publish, unpublish, change front-page state, or create assignments, announcements, or reminders for the inactive subject.

## Page identity

Each generated agenda page must include internal metadata:

```text
local_object_id
week_code
school_year
subject_group
source_subjects
source_entry_ids
source_revisions
title
page_title
display_subtitle
body_html
body_text
content_hash
dependencies
blockers
approval_state
approval_revision
snapshot_id
deployment_status
verification_status
```

## Canvas page title

The Canvas page title must come directly from:

```text
instructional-weeks-2026-2027.json
```

Examples:

```text
Q1W1 - July 20-24, 2026
Q1W5 - August 17–21, 2026
Q2W3 - October 26–30, 2026
Q4W10 - June 7–11, 2027
```

The system must preserve the exact approved page title from configuration rather than rebuilding it from date arithmetic.

## Display subtitle

The subtitle also comes from the instructional-week configuration.

Examples:

```text
Quarter 1, Week 1 | July 20-24, 2026
Quarter 4, Week 10 | June 7–11, 2027
```

## Subject-page display names

Current approved display titles:

```text
Math Weekly Agenda
Reading and Spelling Weekly Agenda
Language Arts Weekly Agenda
History Weekly Agenda
Science Weekly Agenda
```

## Required page anatomy

The rendered page must include, in this order:

1. Quarter/week heading and preloaded date range
2. Reminders
3. Monday
4. Tuesday
5. Wednesday
6. Thursday
7. Friday

Each weekday block contains:

```text
In Class
Homework
```

There is no Resources section on subject agenda pages.

## Reminders

Reminders may list upcoming assessment names and dates only.

Reminders must not contain:

- links
- attachments
- study-guide references
- resource references
- detailed preparation directions
- book or workbook locations
- objectives or standards

## Homework display label

The parent-facing column label is `Homework`, not `At Home`.

When there is no homework, write:

```text
Homework: No Homework
```

No homework entry may contain a curriculum-resource link.

## Weekday composition

For each weekday, the page generator reads from persisted daily subject entries.

Preferred source fields:

```text
in_class
at_home
title
lesson
reminders
```

The internal weekly model may retain `at_home` as the storage field; rendered output uses the `Homework` label.

The renderer should prefer explicit `in_class` text.

Blank content must not be replaced with invented instructional text.

## Approved homework schedules

Math classwork goal every day: `#1-10`.

Math homework:

- Monday: `#12-30 evens`
- Tuesday: No Homework
- Wednesday: `#11-29 odds`
- Thursday: No Homework
- Friday: No Homework

Reading classwork goal every day: `Workbook`.

Reading homework:

- Monday: No Homework
- Tuesday: Comprehension Questions
- Wednesday: No Homework
- Thursday: Comprehension Questions
- Friday: No Homework

## Empty-state behavior

When a weekday has no In Class content:

- preserve the weekday block;
- render a blank placeholder or explicitly approved empty state;
- do not remove the weekday.

When Homework is empty for Monday–Thursday, show an empty placeholder or `Homework: No Homework` per subject rules.

## No-school behavior

For a full closure:

```text
In Class: Snow Day
Homework: No Homework
```

The page must reflect the approved calendar-disruption result.

## Reading and Spelling page

The `reading-spelling` page combines both subjects while retaining separate source records.

Recommended content order per weekday:

```text
Reading
Spelling
```

The page must preserve separate lesson/test identity, assignments, validation, and approval for linked assignments.

Editing either source subject invalidates the shared page approval.

## Assignment links on academic agendas

Subject agenda pages must not contain curriculum-resource links, assignment links, attachments, or verified URL dependencies.

Historical Phase 23/25 behavior that regenerated pages with verified assignment URLs is superseded and non-authoritative for the 2026–2027 workflow.

## Page dependencies

A page may depend on:

```text
assessment reminders
calendar-disruption state
current course metadata
module placement metadata
quarter-subject activation state
```

Resource resolution is not a current publication dependency.

## Revision and approval

Any source edit affecting visible page content must create or update the page draft, change its content hash, mark the old comparison stale, invalidate its approval, and require review again.

## Canvas REST page payload

Conceptual structure:

```json
{
  "wiki_page": {
    "title": "Q1W1 - July 20-24, 2026",
    "body": "<div>...</div>",
    "published": false,
    "front_page": false,
    "editing_roles": "teachers"
  }
}
```

Exact supported fields must follow the official Canvas Pages API used by the Phase 27 transport boundary.

## Front-page behavior

Setting a page as the course front page is a separate controlled operation requiring current target verification, explicit intent, comparison, approval, dependency order, and read-back verification.

## Phase 23 convergence requirement

Phase 23 currently maintains its own generated packet and page model.

The recovered implementation must ensure pages read from the real persisted weekly model, teacher corrections feed page generation, selected week drives page generation, and fixture data is test-only.

## Validation requirements

The validator must confirm:

- all configured week titles are available;
- five page groups exist;
- Reading/Spelling share one page group;
- Homeroom is excluded from academic agenda groups;
- Monday–Friday blocks exist;
- In Class and Homework columns exist;
- Reminders section exists without a Resources section;
- quarter activation rules match `quarter-subject-activation-2026-2027.json`;
- inactive History/Science pages remain untouched;
- page approval becomes stale after a source edit;
- fixture data is not the production page source.
