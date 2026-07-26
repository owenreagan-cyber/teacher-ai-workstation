# Homeroom Newsletter Contract

## Purpose

This contract defines the Homeroom family newsletter as a distinct, page-first Canvas communication artifact.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

Homeroom is not an academic subject agenda.

## Cadence

The Homeroom newsletter is updated once per month, not weekly.

## Current course routing

```text
Subject: Homeroom
Canvas course ID: 26427
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
2026–2027 target Homeroom course: 26427
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

## Delivery channels

Confirmed:

```text
Homeroom Canvas Page
Canvas update announcement
```

No email-send behavior is approved in this contract.

## Privacy and safety

The newsletter must not contain student names, grades, accommodations, behavior information, teacher-only resources, secure assessments, answer keys, local filesystem paths, or hidden diagnostics.

## Validation requirements

The validator must confirm:

- Homeroom routes to `26427`;
- Homeroom remains separate from academic agenda groups;
- newsletter cadence is monthly;
- required sections match the operating contract;
- school/event links are permitted only in Homeroom;
- update announcement uses canonical notification wording;
- page and announcement have separate approvals;
- preview-only posture remains active;
- Reading Test 14 contains no Checkout 14 wording;
- Spelling Test 25 is excluded until approved.
