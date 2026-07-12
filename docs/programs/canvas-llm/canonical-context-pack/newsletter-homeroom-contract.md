# Homeroom Newsletter Contract

## Purpose

This contract defines the Homeroom family newsletter as a distinct, page-first Canvas communication artifact.

Homeroom is not an academic subject agenda.

## Current course routing

```text
Subject: Homeroom
Canvas course ID: 26427
Canonical routing prefix: NEWSLETTER
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

The newsletter page owns the substantive weekly family communication.

A newsletter-update announcement only notifies families that the page changed.

It does not replace the newsletter page.

## Current implementation status

The current Phase 22 newsletter draft is only:

```text
Title: Newsletter Draft
Body: Preview newsletter; unsent.
previewOnly: true
```

Therefore:

```text
Current newsletter runtime status: PLACEHOLDER_ONLY
```

It must not be described as complete, production-ready, or publishable.

## Historical evidence

Approved read-only historical references:

```text
2024–2025 Homeroom course: 19424
2025–2026 Homeroom course: 22254
2026–2027 target Homeroom course: 26427
```

Current evidence ranking:

```text
19424 → primary historical newsletter structure reference
22254 → supporting historical reference
26427 → current target shell
```

Historical metadata may inform:

- page structure;
- layout evolution;
- section order;
- reminder categories;
- title patterns;
- module placement;
- page/announcement relationships.

Historical body content must not be ingested or copied into production without a separate approved review gate.

## Newsletter identity

Each newsletter draft must include:

```text
local_object_id
week_code
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

The exact current title pattern is not yet approved.

Candidate historical patterns must remain evidence only.

Status:

```text
OWNER_DECISION_REQUIRED
```

Possible future forms:

```text
Weekly Newsletter — July 20-24, 2026
Q1W1 Newsletter
Homeroom Newsletter — July 20-24, 2026
```

No title pattern may be made canonical without owner approval and historical comparison.

## Required newsletter sections

The final section schema remains under review.

The model should support structured sections such as:

```text
Welcome / Weekly Overview
Important Dates
Assessment Reminders
Math
Reading
Spelling
Language Arts
History
Science
Classroom Reminders
Materials or Supplies
Upcoming Events
Closing Note
```

Not every section must appear every week.

Empty sections should be omitted rather than filled with invented content.

## Source behavior

Newsletter content must come from structured, persisted weekly state.

Potential sources:

```text
weekly plan
assessment families
approved reminders
calendar disruptions
teacher-entered Homeroom notes
subject newsletter_include flags
verified resource links
upcoming school events
```

It must not be generated solely from the Phase 23 fixture.

## Subject inclusion

Each subject/day entry may carry:

```text
newsletter_include
```

Default inclusion rules must remain explicit by subject and entry type.

The system must not automatically copy every daily agenda line into the newsletter.

## Assessment reminders

Newsletter assessment content may include:

- assessment name;
- date;
- covered lesson range;
- approved preparation instructions;
- verified Study Guide links;
- Reading Checkout passage details when applicable;
- Spelling focus words when approved.

Reading Test 14 must omit all Checkout 14 content.

Spelling Test 25 must not appear without approved source data.

## Calendar disruption behavior

When dates change:

- update the newsletter draft;
- show old/new dates in the review diff;
- invalidate the previous newsletter approval;
- regenerate the update announcement;
- block publication until renewed approval.

## Newsletter-update announcement

Canonical announcement text:

```text
The newsletter has been updated for the week of {date range}.
```

This announcement:

- points families to the newsletter page;
- does not duplicate the full newsletter;
- must use the verified newsletter page URL;
- remains blocked until the page exists and the URL is verified.

## Page-first dependency order

Required order:

1. generate newsletter draft;
2. validate content;
3. resolve required resources;
4. compare newsletter page to Canvas;
5. review and approve page;
6. create or update page;
7. read back and verify page;
8. capture verified page URL;
9. generate update announcement with that URL;
10. compare announcement;
11. review and approve announcement;
12. publish/schedule announcement;
13. verify announcement.

The announcement must never be published before its page dependency succeeds.

## Preview behavior

Until the real newsletter generator is built:

```text
previewOnly: true
canvasWritesAllowed: false
emailSendsAllowed: false
```

The UI must clearly label placeholder content.

A button labeled Publish must not merely save a local file.

## Delivery channels

Confirmed:

```text
Homeroom Canvas Page
Canvas update announcement
```

Possible future channels requiring separate approval:

```text
email
print/PDF
daily brief inclusion
external family messaging
```

No email-send behavior is approved in this contract.

## Newsletter and announcements

The newsletter page and its update announcement are separate artifacts.

They must have separate:

```text
local IDs
content hashes
comparison results
approvals
deployment records
verification results
```

Approval of one does not approve the other.

## Privacy and safety

The newsletter must not contain:

- student names;
- grades;
- accommodations;
- behavior information;
- birthdays unless separately approved;
- private family information;
- teacher-only resources;
- secure assessments or answer keys;
- local filesystem paths;
- unverified links;
- hidden diagnostics.

## AI usage

The first production newsletter generator should be deterministic and structured.

Optional AI assistance may later:

- improve wording;
- summarize teacher-approved structured fields;
- suggest a friendly closing.

AI must not:

- invent events;
- invent assessment dates;
- invent resources;
- invent student information;
- publish without review.

## Historical comparison requirement

Before approving a final layout:

- compare metadata and approved visual structure from courses `19424` and `22254`;
- identify repeated section patterns;
- identify page/module relationships;
- document what is reused, adapted, or rejected;
- do not ingest historical private body content without a separate gate.

## Publish blockers

Publishing is blocked when:

- title pattern is unresolved;
- required date range is missing;
- required source content is stale;
- required page resources are unresolved;
- student-sensitive content is detected;
- page comparison is stale;
- approval is missing or stale;
- target course is not verified;
- newsletter page dependency fails;
- current content is still placeholder-only.

## Validation requirements

The validator must confirm:

- Homeroom routes to `26427`;
- Homeroom remains separate from academic agenda groups;
- newsletter is page-first;
- update announcement uses canonical notification wording;
- page and announcement have separate approvals;
- current placeholder is labeled preview-only;
- no email send is authorized;
- historical courses remain read-only evidence;
- Reading Test 14 contains no Checkout 14 wording;
- Spelling Test 25 is excluded until approved;
- student data and secure resources are prohibited.
