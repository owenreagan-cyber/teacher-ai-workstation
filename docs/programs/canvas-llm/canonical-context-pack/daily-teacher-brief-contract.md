# Daily Teacher Brief Contract

## Purpose

The Daily Teacher Brief is a teacher-only, local-first, preview-only planning artifact.

It summarizes one instructional school day for the teacher. It is separate from:

- Canvas announcements
- Homeroom newsletter pages
- academic agenda pages
- assignments
- deployment publication operations
- email delivery

## Title format

```text
Daily Teacher Brief — {Weekday, Month D, YYYY}
```

Example:

```text
Daily Teacher Brief — Monday, August 17, 2026
```

## Audience and channel

```text
audience: teacher-only
channel: local_preview
delivery_state: blocked_preview
```

## Instructional-day rules

Generate a Daily Brief only for:

- Monday through Friday
- dates inside the instructional calendar
- dates not marked as explicit no-school days

Do not generate for:

- weekends
- holidays
- breaks
- explicit no-school dates
- dates outside the instructional calendar

## Required section order

1. Today at a Glance
2. Lessons and Activities
3. Tests and Checkouts
4. Materials to Prepare
5. Planning Alerts
6. Scheduled Events
7. Weather
8. Classroom-Safe Joke

## Deterministic generation

Daily Brief content must be generated deterministically from structured weekly planning state.

Repeated generation from unchanged source state must produce identical:

- stable local object ID
- content hash
- title
- section order
- scheduling intent

## Recipient privacy

Approved local recipient:

```text
owen.reagan@thalesacademy.org
```

That address may remain in local default settings and direct local API responses for the authenticated local user.

Committed artifacts must use:

```text
recipientConfigured: true
recipientDisplay: Teacher
```

Committed artifacts must not serialize the real email address.

## Scheduling intent

Schedule intent:

```text
6:15 AM America/New_York
instructional school days only
```

Rules:

- store actual scheduling instants in UTC
- display schedule in Eastern Time
- scheduling intent must never trigger delivery
- no SMTP, Gmail, SendGrid, Mailgun, or other transport

## Weather boundary

Weather is optional structured input only.

Rules:

- no live weather API
- no network call
- no fabricated forecast
- when absent, show `Weather not provided`
- missing weather is informational, not WARN or FAIL

## Classroom-safe joke boundary

Rules:

- exactly one deterministic joke per instructional date
- use a small committed, age-appropriate list
- deterministic selection by date
- no network or model call
- avoid sarcasm directed at students, violence, adult themes, politics, religion, or ridicule

## Approval separation

Daily Brief approval is independent from other artifacts.

Saving, editing, or approving another artifact must not approve the Daily Brief.

## Safety fields

Every generated Daily Brief must include equivalent fields:

```text
preview_only: true
teacher_approval_required: true
approved: false
canvas_writes_allowed: false
email_sends_allowed: false
delivery_authorized: false
delivery_status: blocked_preview
contains_student_data: false
```

## Prohibited content

Daily Briefs must not contain:

- student names or student data
- exact spelling words
- exact Reading passage locations
- study-guide language
- curriculum resource links
- local filesystem paths
- tokens
- hidden diagnostics

Reading Test 14 must never generate Checkout 14 wording.

Spelling Test 25 remains excluded until approved source data exists.

## No authorization

This contract does not authorize:

- email delivery
- Canvas writes
- live calendar connector calls
- transport implementation
