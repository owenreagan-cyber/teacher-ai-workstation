# Homeroom Newsletter Contract

## Purpose

This contract defines the Homeroom family newsletter as a distinct, page-first Canvas communication artifact.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

Homeroom is not an academic subject agenda.

## Cadence

The Homeroom newsletter is a rolling monthly artifact (title pattern
`August Newsletter`). It is also included automatically in every weekly build
unless Owen explicitly says to skip it. The weekly build starts from the last
correct HTML newsletter page in Canvas, preserves standing sections and styling,
applies Owen-supplied updates, removes only expired dates, preserves future
dates, and updates upcoming birthdays when provided. When Owen gives no specific
update, only a light generic current-week/track message is applied. Subject
pacing summaries are never added. The updated newsletter is always made the
Homeroom front page and its front-page state is verified live. Each weekly
build also creates one Homeroom family announcement: a short family-facing
intro followed by the full current newsletter HTML, with duplicate protection
against an already-posted current-week announcement.

## Current course routing

```text
Subject: Homeroom
Canvas course ID: 26429
newsletterTarget: true
```

The authoritative routing source is:

```text
config/curriculum/canvas-course-mappings.json
```

## Canonical model

```text
Newsletter = Homeroom Canvas Page
```

Homeroom is an HTML newsletter workflow. A PDF or Google Doc must not be used as
the content source. The last correct HTML newsletter page in Canvas is the
canonical template/base, and it is updated in place (never duplicated
unnecessarily).

The newsletter page owns the substantive monthly family communication.

A newsletter-update announcement only notifies families that the page changed.

It does not replace the newsletter page.

## Required newsletter sections

The operating contract retains these sections:

```text
Important Dates
Homeroom News
School News
School Information and Event Links
```

School and event links are permitted in the Homeroom newsletter.

This is an explicit exception to the no-link rule for subject agenda pages, assignments, and assessment announcements.

Subject curriculum-resource links remain prohibited elsewhere.

## Current implementation status

Phase C0O generates a structured, deterministic, preview-only monthly Homeroom newsletter draft from persisted monthly state.

Current runtime posture:

```text
previewOnly: true
canvasWritesAllowed: false
emailSendsAllowed: false
teacherApprovalRequired: true
```

It must not be described as production-ready or publishable without teacher approval and verified Canvas metadata.

## Historical evidence

Approved read-only historical references:

```text
2024–2025 Homeroom course: 19424
2025–2026 Homeroom course: 22254
2026–2027 target Homeroom course: 26427 (superseded — current is 26429)
```

Historical body content must not be ingested or copied into production without a separate approved review gate.

Historical weekly newsletter title patterns such as `Weekly Newsletter — July 20-24, 2026` remain superseded evidence only.

## Newsletter identity

Each newsletter draft must include:

```text
local_object_id
month_code
school_year
course_id
title
date_range
body_text
body_html
sections
source_entry_ids
source_revisions
content_hash
dependencies
blockers
approval_state
approval_revision
snapshot_id
deployment_status
verification_status
preview_only
```

## Newsletter page title

Owner-approved current monthly title pattern:

```text
Homeroom Newsletter — {Month YYYY}
```

Examples:

```text
Homeroom Newsletter — August 2026
Homeroom Newsletter — September 2026
```

## Source behavior

Newsletter content must come from structured, persisted monthly state.

It must not be generated solely from the Phase 23 fixture.

## Canvas page identity (page_id vs slug)

For an already-known Canvas page, the canonical identity model is:

```text
PAGE ID   = canonical, stable object identity (primary)
SLUG/URL  = mutable navigation/compatibility identity (secondary)
TITLE     = mutable content metadata
```

- `page_id` continuity proves object continuity.
- A title update may cause Canvas to auto-derive a new canonical slug.
- Canvas **may** retain the former slug as a redirect alias (observed; not
  guaranteed for every historical slug).
- A slug change — or an old slug still resolving to the same `page_id` — does
  **not** indicate page replacement, duplication, or broken identity.
- Readback verification must key on `page_id`; a slug mismatch when `page_id` is
  unchanged, the course is correct, and title/body/module identity is correct is
  INFO/WARN, never a hard FAIL.
- Automation must never create a replacement page solely because the canonical
  slug changed. Normal weekly pages are update-in-place only.

Slug classification (see `scripts/canvas_llm_deploy/page_identity.py`):

```text
UNCHANGED_SLUG                       clean
CANONICAL_SLUG_CHANGED_SAME_PAGE     WARN (compatible)
LEGACY_SLUG_REDIRECTS_SAME_PAGE      PASS (alias; one page, not two)
SLUG_IDENTITY_CONFLICT               FAIL (different page_id involved)
PAGE_ID_NOT_RESOLVED                 FAIL (known page no longer resolves)
```

### Implementation lesson (Homeroom page 798072)

On 2026-10-17 a title update on the Homeroom newsletter (page_id `798072`)
caused Canvas to auto-derive the canonical slug from
`q1w2-july-27-31-2026` to `class-4a-newsletter-october-19-23-2026`. The former
slug remained resolvable as a redirect alias to the same `page_id`; a corrective
`wiki_page[url]` PUT did not revert the canonical slug. Link stability was
preserved (the old slug still resolves to `798072`). This is encoded as the
identity rule above so future updates do not mistake a slug change for page
replacement or duplication.

## Assessment reminders

Newsletter assessment content may include assessment name, date, and teacher-entered coverage.

It must not include:

- study guides or study-guide links;
- exact Reading checkout page or passage location;
- exact Spelling words;
- verified curriculum-resource links on academic surfaces.

Reading Test 14 must omit all Checkout 14 content.

Spelling Test 25 must not appear without approved source data.

## Newsletter-update announcement

Owner-approved notification text:

```text
The newsletter has been updated for {Month YYYY}.
```

Owner-approved announcement title:

```text
Homeroom Newsletter Updated — {Month YYYY}
```

This announcement:

- points families to the newsletter page;
- does not duplicate the full newsletter;
- may use the verified newsletter page URL;
- remains blocked until the page exists and the URL is verified.

## Page-first dependency order

Required order:

1. generate newsletter draft;
2. validate content;
3. compare newsletter page to Canvas;
4. review and approve page;
5. create or update page;
6. read back and verify page;
7. capture verified page URL;
8. generate update announcement with that URL;
9. compare announcement;
10. review and approve announcement;
11. publish/schedule announcement;
12. verify announcement.

Resource resolution is not a current publication dependency.

Historical Phase 25 resource-resolution steps remain dormant evidence only.

## Preview behavior

```text
previewOnly: true
canvasWritesAllowed: false
emailSendsAllowed: false
```

## Family announcement

Each weekly build (unless Owen says to skip Homeroom) creates exactly one
Homeroom family announcement for the current week. The announcement reuses the
exact verified newsletter HTML that is live on the Homeroom front page — it is
never rewritten into a separate newsletter.

Announcement body order:

1. a short family-facing intro;
2. the full current newsletter HTML beneath the intro.

Canonical intro:

```text
Hound Families,

Please see this week's classroom newsletter below for important dates,
reminders, birthdays, and classroom updates.

Have a great week!

Mr. Reagan
```

Announcement title follows the established `4th Grade Happenings - {suffix}`
naming convention, e.g. `4th Grade Happenings - Week 6`, or the current monthly
`4th Grade Happenings - August Update` form where that convention is already
established in live Canvas.

Duplicate protection: before creating, fresh-GET current Homeroom announcements
and search for an exact/current-week duplicate (same title or same newsletter
body). If one exists with the same intended content, reconcile it as
`ALREADY_APPLIED` and perform zero writes. Never create a duplicate family
announcement.

Subject pacing summaries (Math, Reading, Spelling, Language Arts, History, or
Science) are never added to the family announcement.

## Birthday tiles

The birthday section uses the canonical "one birthday student = one birthday tile" layout. Each tile shows, in order:

1. one or two birthday emojis;
2. the student's first name (first name only unless Owen explicitly says otherwise);
3. the exact known birthday date.

Section structure:

- one section header for the month, e.g. `🎂 September Birthdays 🎉`;
- one individual tile per listed student.

Styling rules:

- a soft rotating color palette so each tile can carry a different light tint;
- strong text contrast and the current polished family-newsletter style;
- responsive layout using `display:flex; flex-wrap:wrap`;
- tiles visually coordinate with the Important Dates cards without copying them
  exactly.

Future monthly birthday sections must:

- create one tile per listed student;
- use first name only unless Owen explicitly says otherwise;
- show the exact known birthday date;
- rotate among the approved soft color treatments;
- use appropriate birthday emojis;
- omit the entire birthday section when no birthdays are supplied for that period;
- never invent birthdays.

The reusable builder is `scripts/canvas_llm_phase22/homeroom_newsletter.py`:

- `render_birthday_section(month_label, students)` returns the full section, or
  an empty string when `students` is empty;
- `replace_birthday_section(body, month_label, students)` swaps the existing
  single-card birthday section for the tile layout in place.

Canonical example:

```text
docs/programs/canvas-llm/canonical-context-pack/examples/homeroom-birthday-tiles-example.html
```

## Delivery channels

Confirmed:

```text
Homeroom Canvas Page
Homeroom family announcement (intro + full current newsletter HTML)
Canvas update announcement
```

No email-send behavior is approved in this contract.

## Privacy and safety

The newsletter must not contain student names, grades, accommodations, behavior information, teacher-only resources, secure assessments, answer keys, local filesystem paths, or hidden diagnostics.

## Validation requirements

The validator must confirm:

- Homeroom routes to `26429`;
- Homeroom remains separate from academic agenda groups;
- newsletter cadence is rolling monthly with weekly auto-include;
- required sections match the operating contract;
- school/event links are permitted only in Homeroom;
- update announcement uses canonical notification wording;
- page and announcement have separate approvals;
- preview-only posture remains active;
- Reading Test 14 contains no Checkout 14 wording;
- Spelling Test 25 is excluded until approved.
