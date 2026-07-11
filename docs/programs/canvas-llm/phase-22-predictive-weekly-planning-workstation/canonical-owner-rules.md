# Phase 22 Canonical Owner Rules

Status: owner-approved product and workflow requirements.

Date: 2026-07-10

## Source hierarchy

1. Owner-approved configuration under `config/curriculum/`
2. Owner-approved workflow decisions in this document
3. Current-year read-only Canvas evidence
4. Archived reference-course evidence
5. Legacy implementation evidence
6. AI suggestions

Legacy code never overrides an owner-approved rule.

## Canvas environments

- 2026-2027 mappings are current production targets.
- Course 24399 is the Math Automation Sandbox.
- 2025-2026 and 2024-2025 mappings are archived, read-only evidence.
- Archived courses may provide resource and historical-pattern evidence.
- Archived courses must never become deployment targets.
- Reading and Spelling share one Canvas course but retain separate prefixes.
- Missing mappings must never be inferred.
- Course lookup requires both school year and environment.

## Math lesson homework

Standard Math lessons use deterministic suggested parity:

- odd lesson number: Odds homework
- even lesson number: Evens homework

The teacher may override the suggestion.

The teacher-selected homework pattern is authoritative.

## Math assessment family

A Math Test N produces one related assessment family:

- Written Test N on the test day
- Fact Test N on the test day
- Study Guide N on the previous instructional day
- one linked Math test announcement draft

The previous instructional day is used rather than the previous calendar date.

When a Math test is scheduled on the next instructional day:

- suppress ordinary lesson Odds/Evens homework
- generate Study Guide N as the only Math homework
- do not generate both Study Guide N and ordinary lesson homework
- allow explicit teacher override

Study Guide N requires distinct structured resources:

- Study Guide N Blank
- Study Guide N Completed

Both resources belong in:

- Math agenda Resources section
- Study Guide assignment description
- Math Test assignment description
- Math Test announcement

The Fact Test map supplies:

- Power Up code
- fact-practice description
- verified practice resource reference

## Reading and Spelling

- Reading and Spelling use Together Logic.
- They share one Canvas course and one weekly agenda page.
- They retain separate subject identities and prefixes.
- Standard Reading lessons do not create gradebook assignments automatically.
- Reading homework uses the owner-approved comprehension letter/page map.
- Reading Checkouts are valid for numbers 1-13 only.
- Reading Test 14 has no Checkout.
- Spelling parent announcements use positions 21-25 of the approved cumulative list.
- Reading fluency bands are complete and owner-confirmed for Checkouts 1-13.
  - Checkouts 1-7: 100 WPM, 2 or fewer errors
  - Checkouts 8-10: 115 WPM, 2 or fewer errors
  - Checkouts 11-13: 130 WPM, 2 or fewer errors

## History and Science

History and Science participate in:

- pacing
- agenda pages
- resources
- newsletters
- announcements

They do not generate Canvas assignment drafts under the current owner-approved policy.

Any History/Science alternating-track behavior remains school-year configurable.

## Friday

- Friday instruction is allowed.
- Standard homework defaults to off.
- The At Home agenda section defaults to omitted.
- Explicit tests may create assessment-related assignments and notices.
- Friday instructional content must never be deleted by a global rule.

## Agenda pages

Required order:

1. Header/banner
2. Week/date subtitle
3. Reminders
4. Resources
5. Monday-Friday daily blocks
6. In Class and At Home sections where applicable

Resources must be structured verified resource objects.

At Home assignment links must use real assignment URLs when available.

Unresolved links must render as warnings, never fake anchors.

Agenda rules are versioned by school year.

## Weekly planning states

Each weekly plan has one durable state:

- not_started
- in_progress
- ready_for_review
- approved
- scheduled
- partially_deployed
- deployed
- needs_revision
- archived

Deployment status is tracked separately for:

- each subject page
- assignment families
- newsletter
- announcements
- daily brief

## Startup behavior

- Open the current instructional week if it is not deployed.
- If the current week is deployed and next week is unstarted, offer to start next week.
- If the current week is deployed and next week has saved work, offer to continue next week.
- Reopen partial or failed deployment states with a warning.
- Skip breaks and no-school weeks when selecting the next instructional week.

## Durable autosave

Canonical teacher work lives in SQLite, not browser cache.

Every editable field must autosave.

Autosave must:

- patch only the changed record or field
- save before changing subject or week
- save on tab change, visibility change, and window blur
- retain unsaved editor content after a failed request
- retry safely
- survive browser refresh
- survive browser restart
- survive local-server restart
- display Saving, Saved, Unsaved, Failed, Retrying, and Conflict states

Moving between subjects must never replace or erase another subject's work.

## Revision and conflict protection

Mutable records contain:

- version
- updatedAt
- updatedBy

Stale writes return a conflict instead of overwriting newer work.

Create durable revisions for:

- pacing entries
- weekly plans
- assignment drafts
- page drafts
- newsletter drafts
- announcement drafts
- deployment plans

Support:

- undo
- compare
- restore
- crash recovery

## Scheduling

Timezone: `America/New_York`.

Store instants in UTC and display scheduled activity in Eastern Time.

Friday 4:00 PM is the default intended weekly release window for:

- approved assignments
- agenda-page publication
- front-page activation
- page-update announcements

No action occurs solely because the clock reaches the scheduled time.

Every future scheduled operation must also be:

- owner-approved
- validated
- current-year mapped
- not stale
- not previously deployed
- free of unresolved dependencies

Phase 22 records and previews scheduling intent only.

Phase 22 performs no Canvas writes.

## Daily brief

Generate and persist a local daily-brief preview for:

`owen.reagan@thalesacademy.org`

Suggested default:

- 6:15 AM Eastern Time
- instructional school days only

Possible content:

- today's lessons
- tests and checkouts
- materials to prepare
- missing resources
- unresolved planning work
- scheduled events
- optional weather
- one classroom-safe joke
- optional approved image

Phase 22 must not send email.

## Deployment ordering

Future deployment order:

1. Validate resources
2. Create or update assignments
3. Capture assignment URLs
4. Render agenda pages with verified links
5. Publish approved pages
6. Set approved pages as front pages
7. Send approved page-update announcements
8. Send separately scheduled assessment reminders
9. Verify and record results

A failed dependency blocks downstream operations.

## Explicit unresolved decisions

The following must not be guessed:

- final Canvas assignment due-time convention
- exact Study Guide blank/completed Canvas resource IDs
- final current-year assignment-group mappings
