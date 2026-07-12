# Canonical Weekly Agenda Page Contract

## Purpose

This contract defines the generated Canvas weekly agenda pages for the 2026–2027 Teacher AI Workstation.

The authoritative machine-readable sources are:

```text
config/curriculum/canvas/instructional-weeks-2026-2027.json
config/curriculum/canvas/weekly-agenda-standard-2026-2027.json
config/curriculum/canvas/agenda-page-rules.json
```

The current rendering references are:

```text
scripts/canvas_llm_phase22/phase22_workstation.py
scripts/canvas_llm_phase23/phase23_content_engine.py
```

The recovered production implementation must converge on one weekly model and one canonical renderer.

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

Whitespace and HTML entities in imported source values may be normalized for display, but the canonical normalized value must be deterministic and validated.

## Display subtitle

The subtitle also comes from the instructional-week configuration.

Examples:

```text
Quarter 1, Week 1 | July 20-24, 2026
Quarter 4, Week 10 | June 7–11, 2027
```

The fallback form:

```text
Quarter {quarter}, Week {week}
```

may be used only when the configured subtitle is genuinely unavailable and the page remains blocked for review.

## Subject-page display names

Current approved display titles:

```text
Math Weekly Agenda
Reading and Spelling Weekly Agenda
Language Arts Weekly Agenda
History Weekly Agenda
Science Weekly Agenda
```

The Canvas page's week-specific title remains the configured Q/W title.

The subject display name may appear in:

- local preview;
- internal artifact name;
- page metadata;
- module item label where approved.

## Required page anatomy

The rendered page must include, in this order:

1. Weekly Agenda banner
2. Week subtitle
3. Reminders & Resources
4. Monday
5. Tuesday
6. Wednesday
7. Thursday
8. Friday

Each weekday block contains:

```text
In Class
At Home
```

## Current HTML structure

The current validated rendering includes:

```text
id="kl_wrapper_3"
class="kl_circle_left kl_wrapper"
```

The current layout uses:

- a blue agenda banner;
- a magenta Reminders & Resources heading;
- blue weekday headings;
- dark gray In Class / At Home headings;
- two approximately 49% width columns;
- inline Canvas-compatible HTML styles.

A future visual redesign may change styling only after:

- preserving semantic structure;
- preserving Canvas compatibility;
- browser proof;
- accessibility review;
- explicit owner approval.

## Reminders & Resources

Current canonical behavior:

```text
combinedRemindersAndResources: true
sectionTitle: Reminders & Resources
separateRemindersAndResourcesSections: false
```

This section may include:

- upcoming assessments;
- assessment dates;
- verified Study Guide links;
- verified practice resources;
- schedule changes;
- teacher-approved reminders.

It must not include:

- invented links;
- unresolved URLs shown as active links;
- teacher-only resources;
- secure answer materials;
- student data;
- hidden diagnostics.

## Weekday composition

For each weekday, the page generator reads from persisted daily subject entries.

Preferred source fields:

```text
in_class
at_home
title
lesson
materials
reminders
resources
```

The renderer should prefer explicit `in_class` text.

A title or lesson may be used as a fallback only when the contract for that subject allows it.

Blank content must not be replaced with invented instructional text.

## Empty-state behavior

When a weekday has no In Class content:

- preserve the weekday block;
- render a blank placeholder or explicitly approved empty state;
- do not remove the weekday.

When At Home is empty:

- Monday–Thursday may show an empty placeholder according to the approved layout;
- Friday may omit the At Home column;
- explicit teacher-entered Friday content must still display.

## Friday behavior

Friday instruction remains allowed.

Default:

```text
Friday homework: none
```

The page must not silently discard teacher-entered Friday homework.

When explicit Friday At Home content exists:

- show it;
- validate it;
- preserve its teacher-override provenance.

## No-school behavior

For a full closure:

```text
In Class: Snow Day
At Home: none
```

The page must reflect the approved calendar-disruption result.

It must not show the displaced lesson as if it still occurred that day.

## Reading and Spelling page

The `reading-spelling` page combines both subjects while retaining separate source records.

Recommended content order per weekday:

```text
Reading
Spelling
```

The page must preserve:

- separate lesson/test identity;
- separate assignments;
- separate resource dependencies;
- separate validation;
- separate approval for linked assignments.

Editing either source subject invalidates the shared page approval.

## History and Science pages

History and Science may generate agenda pages.

Their assignment generation remains disabled by default.

Agenda-page capability must not be interpreted as assignment authorization.

## Assignment links

When At Home content references a Canvas assignment:

1. create or resolve the assignment;
2. capture the verified Canvas URL;
3. regenerate the page with the verified link;
4. compare the page to current Canvas state;
5. review;
6. approve;
7. publish;
8. verify by read-back.

Before the assignment URL is verified:

- retain the intended local reference;
- mark the dependency unresolved;
- block final page publication when the link is required;
- never invent a URL.

## Page dependencies

A page may depend on:

```text
assignment creation
assignment URLs
resource URLs
assessment reminders
calendar-disruption state
current course metadata
module placement metadata
```

A failed required dependency blocks publication.

## Revision and approval

Any source edit affecting visible page content must:

- create or update the page draft;
- change its content hash;
- mark the old comparison stale;
- invalidate its approval;
- require review again.

A page approval must bind to:

```text
local_object_id
source_revisions
content_hash
manifest_revision
snapshot_id
approved_by
approved_at
```

## Canvas REST page payload

The page payload should use Canvas-compatible page fields.

Conceptual structure:

```json
{
  "wiki_page": {
    "title": "Q1W1 - July 20-24, 2026",
    "body": "<div id=\"kl_wrapper_3\">...</div>",
    "published": false,
    "front_page": false,
    "editing_roles": "teachers"
  }
}
```

Exact supported fields must follow the official Canvas Pages API used by the Phase 27 transport boundary.

## Front-page behavior

Setting a page as the course front page is a separate controlled operation.

It must not be implied by page creation.

It requires:

- current target verification;
- explicit intent;
- comparison;
- approval;
- dependency order;
- read-back verification.

## Phase 23 convergence requirement

Phase 23 currently maintains its own generated packet and page model.

The recovered implementation must ensure:

- pages read from the real persisted weekly model;
- teacher corrections feed page generation;
- selected week drives page generation;
- fixture data is test-only;
- Phase 23 output and Phase 26/27 review state describe the same artifacts.

## Validation requirements

The validator must confirm:

- all configured week titles are available;
- all configured subtitles are available;
- five page groups exist;
- Reading/Spelling share one page group;
- Homeroom is excluded from academic agenda groups;
- Monday–Friday blocks exist;
- In Class exists;
- At Home behavior follows Friday rules;
- Reminders & Resources is combined;
- `kl_wrapper_3` exists in the current canonical renderer;
- required unresolved links block publication;
- page approval becomes stale after a source edit;
- fixture data is not the production page source.
