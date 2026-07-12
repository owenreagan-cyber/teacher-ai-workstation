# Canvas Announcement Contract

## Purpose

This contract defines announcement generation, combination, scheduling, approval, publication, and verification for the Teacher AI Workstation Canvas LLM builder.

Announcements are separate artifacts from:

- assignments;
- weekly agenda pages;
- Homeroom newsletter pages;
- email;
- daily teacher briefs.

Saving, approving, or publishing one artifact does not automatically save, approve, or publish another.

## Announcement types

Supported logical announcement types:

```text
weekly_page_update
newsletter_update
math_assessment
reading_assessment
spelling_assessment
reading_spelling_combined_assessment
schedule_change
resource_update
custom
```

## Announcement identity

Each announcement draft must include:

```text
local_object_id
week_code
school_year
subject_scope
announcement_type
title
body_text
body_html
target_course_ref
target_course_id
linked_object_ids
source_entry_ids
source_revisions
content_hash
scheduled_for
timezone
dependencies
blockers
approval_state
approval_revision
snapshot_id
deployment_status
verification_status
preview_only
```

## Current runtime status

The generic Phase 22 weekly update announcement currently contains:

```text
Title: Weekly Page Update
Body: Preview announcement; unsent.
previewOnly: true
```

Therefore:

```text
Generic weekly announcement runtime status: PLACEHOLDER_ONLY
```

This placeholder must not be described as complete, production-ready, scheduled, sent, or published.

## Weekly page-update announcement

A weekly page-update announcement may notify families that an academic weekly agenda page has been updated.

The exact final wording remains subject to the approved announcement-template matrix.

Until that template is approved:

- generate preview-only content;
- show that wording is unresolved;
- block Canvas publication;
- never substitute the placeholder body as production content.

## Newsletter update announcement

Canonical notification text:

```text
The newsletter has been updated for the week of {date range}.
```

The announcement:

- notifies families that the Homeroom newsletter page changed;
- depends on a successfully verified newsletter page;
- may include the verified newsletter page URL;
- does not reproduce the complete newsletter body;
- requires separate comparison and approval.

## Standalone Spelling announcements

Standalone Spelling announcements are allowed.

Spelling tests typically occur once during an instructional week, so a standalone Spelling assessment announcement is normal expected behavior.

Use a standalone Spelling announcement when:

```text
a Spelling assessment occurs during the week
and
no Reading assessment occurs during that same instructional week
```

The announcement may include:

```text
Spelling Test number
assessment date
approved cumulative list
approved five focus words
teacher-approved practice guidance
verified student-facing resource links
```

It must not include:

- invented words;
- unapproved Test 25 content;
- answer keys;
- secure assessment files;
- teacher-only resources;
- fake links.

## Standalone Reading announcements

Standalone Reading announcements are allowed.

Use a standalone Reading announcement when:

```text
a Reading assessment occurs during the week
and
no Spelling assessment occurs during that same instructional week
```

The announcement may include:

```text
Reading Test number
assessment date
covered lesson range
vocabulary review
story-detail review
tracking and tapping
read-aloud practice
Checkout details when applicable
verified student-facing resources
```

## Combined Reading and Spelling announcement

Combine Reading and Spelling assessment communication only when both subjects have an assessment in the same instructional week.

The combination decision is based on:

```text
same canonical week_code
```

It is not based merely on:

- sharing Canvas course `26442`;
- sharing the `reading-spelling` agenda;
- being displayed on the same page;
- occurring near one another across different weeks.

A combined announcement may contain separately labeled sections:

```text
Reading Test
Reading Checkout, when applicable
Spelling Test
```

Combined communication does not merge:

```text
assessment family IDs
assignment IDs
resource requirements
source entries
revisions
content hashes
dependencies
validation
approvals
deployment records
```

## Reading Test 14 exception

Reading Test 14 has no Checkout.

Any standalone or combined announcement for Reading Test 14 must omit:

```text
Checkout 14
Checkout 14 passage
Checkout 14 resource
Checkout 14 dependency
Checkout 14 preparation instructions
```

The absence of Checkout 14 is canonical and must not create a warning.

## Spelling Test coverage

The current canonical Spelling source supports:

```text
Tests 1–24
```

Spelling Test 25 must not be announced until:

- the exact owner-approved word list exists;
- focus words are confirmed;
- JSON is updated;
- validation is updated;
- the context-pack contract is updated.

## Math assessment announcement

A Math assessment announcement may include:

```text
Math Test number
Fact Test number
assessment date
Study Guide date
verified Study Guide links
Power Up practice information
```

It must not expose:

- teacher answer keys;
- secure assessment resources;
- teacher-only guides;
- unresolved links.

## Scheduling rule

The canonical scheduling rule is:

```text
Schedule on the last valid instructional day before the upcoming instructional week.
```

Resolution:

- use Friday when Friday is instructional;
- otherwise use the previous valid instructional day;
- skip weekends;
- skip holidays;
- skip track-out periods;
- skip unexpected closures;
- recalculate after a disruption.

## Current default schedule intent

Current configuration evidence includes:

```text
Friday 4:00 PM America/New_York
```

Interpretation:

- `4:00 PM America/New_York` is the current default time intent;
- Friday is used only when it is a valid instructional day;
- the date must be recalculated through instructional-calendar logic;
- a fixed calendar offset must not replace the instructional-day rule.

## Timezone

Canonical timezone:

```text
America/New_York
```

Scheduled timestamps must include:

- an explicit timezone;
- or a valid UTC offset.

## Announcement dependencies

An announcement may depend on:

```text
newsletter page
academic agenda page
assignment
verified assignment URL
verified page URL
resource resolution
assessment family
calendar state
```

Required sequence:

1. generate the upstream artifact;
2. validate it;
3. publish it through the future approved transport;
4. read it back;
5. verify it;
6. capture the verified Canvas URL;
7. regenerate the announcement with that URL;
8. compare the announcement;
9. review and approve it;
10. publish or schedule it;
11. read it back and verify it.

A failed required dependency blocks the announcement.

## Canvas payload

Conceptual Canvas-compatible structure:

```json
{
  "announcement": {
    "title": "Spelling Test 4",
    "message": "<p>...</p>",
    "delayed_post_at": "2026-08-14T16:00:00-04:00",
    "published": false
  }
}
```

The eventual production implementation must use fields supported by the official Canvas Announcements API.

Unsupported IMS package fields must not be inserted into the REST payload.

## Body requirements

Announcement HTML may include:

- concise approved text;
- verified Canvas links;
- approved assessment details;
- approved student-facing resource links.

It must not include:

- invented links;
- raw local filesystem paths;
- student data;
- teacher-only resources;
- answer keys;
- secure assessments;
- hidden diagnostics;
- unresolved placeholders presented as real content.

## Comparison states

Announcements use the Phase 27 comparison vocabulary:

```text
CREATE
UPDATE
UNCHANGED
BLOCKED
CONFLICT
OMIT
DELETE_CANDIDATE
```

Rules:

- `CREATE` requires review;
- `UPDATE` requires review of the exact diff;
- `UNCHANGED` requires no write;
- `BLOCKED` cannot be approved;
- `CONFLICT` cannot be approved;
- `OMIT` cannot be approved;
- `DELETE_CANDIDATE` is review-only and never automatically deleted.

## Approval identity

Approval must bind to:

```text
local_object_id
manifest_revision
snapshot_id
content_hash
scheduled_for
approved_by
approved_at
```

Changing any of the following invalidates approval:

- title;
- body;
- schedule;
- target course;
- linked URL;
- dependency;
- source revision;
- manifest revision;
- snapshot.

## Current transport limitation

Phase 27 transport is:

```text
read-only
preview-only
mutation-blocked
```

Mutating announcement calls must remain rejected, including:

```text
create_announcement
update_announcement
publish_announcement
```

A later write phase must explicitly introduce and validate the controlled transport.

## Read-back verification

After a future approved write, verification must confirm:

- announcement exists;
- target course is correct;
- title matches;
- body matches;
- verified links match;
- delayed-post timestamp matches;
- publish state matches;
- no prohibited content appears;
- combined/standalone behavior matches the canonical week rule.

## Publish blockers

Publication is blocked when:

- content is placeholder-only;
- target course is unresolved;
- required upstream artifact is unverified;
- required URL is unresolved;
- schedule is invalid;
- schedule became stale after a disruption;
- prohibited resource content is present;
- Spelling Test 25 is referenced without approved data;
- Reading Test 14 contains Checkout 14 content;
- comparison is blocked or conflicted;
- approval is missing or stale;
- snapshot is not fresh;
- transport remains preview-only.

## Validation requirements

The validator must confirm:

- standalone Spelling announcements are allowed;
- standalone Reading announcements are allowed;
- announcements combine only when Reading and Spelling assessments share the same `week_code`;
- sharing course `26442` alone does not force combination;
- combined announcements preserve separate assessment identities;
- Reading Test 14 omits Checkout 14;
- Spelling Test 25 is excluded until approved;
- scheduling uses the last valid instructional day;
- default time intent is documented;
- timezone is `America/New_York`;
- newsletter-update wording is exact;
- generic placeholder content remains preview-only;
- dependency URLs must be verified;
- announcement approvals remain independent;
- Phase 27 mutation methods remain blocked.
