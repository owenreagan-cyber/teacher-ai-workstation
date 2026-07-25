# Canvas Announcement Contract

## Purpose

This contract defines announcement generation, combination, scheduling, approval, publication, and verification for the Teacher AI Workstation Canvas LLM builder.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

Announcements are separate artifacts from assignments, weekly agenda pages, Homeroom newsletter pages, email, and daily teacher briefs.

Saving, approving, or publishing one artifact does not automatically save, approve, or publish another.

Generator alignment is scheduled for C0L and later phases.

## Announcement types

Supported logical announcement types:

```text
newsletter_update
math_assessment
reading_assessment
spelling_assessment
reading_spelling_combined_assessment
history_assessment
science_assessment
schedule_change
custom
```

Historical note: `weekly_page_update` and `resource_update` types remain dormant evidence from earlier roadmap phases.

## Assessment announcement content

Assessment announcements are prepared for the Friday 4:00 PM update.

The teacher enters assessment coverage.

Announcements may contain only:

- test number, name, or topic
- what it covers
- test date
- approved general practice language when applicable

Announcements must not contain:

- study guides or study-guide links
- attachments
- book-page or workbook-page references
- exact Reading checkout locations
- exact Spelling words
- curriculum-resource links

### Reading fluency language

Use general guidance such as:

> Have your child continue to practice fluency by reading a short paragraph of about 100 words aloud in less than one minute. They should make no more than 2 errors.

Do not identify the checkout passage or its page.

### Spelling practice language

For a test on lesson `N`, the practice range is `N - 4` through `N - 1`.

Do not list the exact Spelling words.

## Standalone Spelling announcements

Standalone Spelling announcements are allowed.

Use a standalone Spelling announcement when a Spelling assessment occurs during the week and no Reading assessment occurs during that same instructional week.

## Standalone Reading announcements

Standalone Reading announcements are allowed.

Use a standalone Reading announcement when a Reading assessment occurs during the week and no Spelling assessment occurs during that same instructional week.

## Combined Reading and Spelling announcement

Combine Reading and Spelling assessment communication only when both subjects have an assessment in the same instructional week.

The combination decision is based on:

```text
same canonical week_code
```

It is not based merely on sharing Canvas course `26442` or the `reading-spelling` agenda.

## Reading Test 14 exception

Reading Test 14 has no Checkout.

Any standalone or combined announcement for Reading Test 14 must omit Checkout 14 content.

## Spelling Test coverage

The current canonical Spelling source supports Tests 1–24.

Spelling Test 25 must not be announced until:

- the exact owner-approved word list exists;
- focus words are confirmed;
- JSON is updated;
- validation is updated;

## Math assessment announcement

A Math assessment announcement may include Written Assessment number, Fact Assessment number, assessment date, and teacher-entered coverage.

Study guides are not part of the 2026–2027 workflow. Historical Study Guide date and link references remain superseded evidence only.

## Scheduling rule

Assessment announcements are prepared for:

```text
Friday 4:00 PM America/New_York
```

When Friday is not instructional, use the previous valid instructional day per calendar-disruption logic.

## Timezone

Canonical timezone:

```text
America/New_York
```

## Announcement dependencies

An announcement may depend on newsletter page, academic agenda page, assessment family, or calendar state.

Verified assignment URLs and resource resolution are not current publication dependencies.

Historical dependency chains that required verified assignment links remain superseded evidence only.

## Canvas payload

Conceptual Canvas-compatible structure:

```json
{
  "announcement": {
    "title": "Assessment Reminder",
    "message": "<p>...</p>",
    "delayed_post_at": "2026-08-14T16:00:00-04:00",
    "published": false
  }
}
```

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

## Current transport limitation

Phase 27 transport is read-only, preview-only, and mutation-blocked.

## Validation requirements

The validator must confirm:

- standalone Spelling announcements are allowed;
- standalone Reading announcements are allowed;
- announcements combine only when Reading and Spelling assessments share the same `week_code`;
- Reading Test 14 omits Checkout 14;
- Spelling Test 25 is excluded until approved;
- Friday 4:00 PM America/New_York intent is documented;
- timezone is `America/New_York`;
- study guides are absent from current announcement rules;
- Phase 27 mutation methods remain blocked.
