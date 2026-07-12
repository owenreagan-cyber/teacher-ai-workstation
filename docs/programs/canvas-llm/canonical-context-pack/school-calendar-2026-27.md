# 2026–2027 School Calendar Contract

## Purpose

This document records the approved 2026–2027 instructional calendar behavior for the Teacher AI Workstation Canvas LLM builder.

The authoritative week scaffold remains:

```text
config/curriculum/canvas/instructional-weeks-2026-2027.json
```

This contract adds the approved track-in, track-out, holiday, and disruption interpretation.

## School year

```text
2026–2027
```

## Track-in and track-out calendar

| Date range | Status | Notes |
|---|---|---|
| July 20, 2026 – September 18, 2026 | TRACK IN | Instructional period |
| September 19, 2026 – October 11, 2026 | TRACK OUT | Three-week break |
| October 12, 2026 – December 18, 2026 | TRACK IN | Instructional period |
| December 19, 2026 – January 10, 2027 | TRACK OUT | Three-week break |
| January 11, 2027 – March 12, 2027 | TRACK IN | Instructional period |
| March 13, 2027 – April 4, 2027 | TRACK OUT | Three-week break |
| April 5, 2027 – June 11, 2027 | TRACK IN | Instructional period |
| June 12, 2027 – July 18, 2027 | SUMMER BREAK | Five-week break |
| July 19, 2027 | NEXT SCHOOL YEAR | First day of 2027–2028 school year |

## Approved holidays and breaks

| Date or range | Classification |
|---|---|
| September 7, 2026 | CONFIRMED_HOLIDAY — Labor Day |
| September 19 – October 11, 2026 | CONFIRMED_NO_SCHOOL — Track Out |
| November 23 – November 27, 2026 | CONFIRMED_NO_SCHOOL — Thanksgiving Break |
| December 19, 2026 – January 10, 2027 | CONFIRMED_NO_SCHOOL — Track Out |
| January 18, 2027 | CONFIRMED_HOLIDAY — Martin Luther King Jr. Day |
| March 13 – April 4, 2027 | CONFIRMED_NO_SCHOOL — Track Out |
| May 31, 2027 | CONFIRMED_HOLIDAY — Memorial Day |
| June 12 – July 18, 2027 | CONFIRMED_NO_SCHOOL — Summer Break |

## Week-code authority

The exact quarter/week codes, page titles, and weekly date ranges are defined by:

```text
config/curriculum/canvas/instructional-weeks-2026-2027.json
```

The system must not generate a different week code or date range from simple calendar arithmetic.

## Instructional-day model

The canonical instructional weekdays are:

```text
Monday
Tuesday
Wednesday
Thursday
Friday
```

A date is instructional only when all of the following are true:

1. it is Monday through Friday;
2. it falls within an approved track-in range;
3. it is not a confirmed holiday;
4. it is not a confirmed break or closure;
5. it has not been marked non-instructional by an approved disruption event.

## Calendar status vocabulary

```text
CONFIRMED_INSTRUCTIONAL
CONFIRMED_HOLIDAY
CONFIRMED_NO_SCHOOL
CONFIRMED_TEACHER_WORKDAY
UNEXPECTED_CLOSURE
TRACK_OUT
SUMMER_BREAK
OWNER_CONFIRMATION_REQUIRED
```

Dates must not be classified from gaps alone when an authoritative source is missing.

## Current-week selection

The existing selection logic in:

```text
scripts/canvas_llm_phase22/phase22_workstation.py
```

is the current canonical implementation reference.

Required behavior:

- before the school year, show the first week as a chooser suggestion;
- after the school year, show the final week as a chooser suggestion;
- during track-out or break, show the next instructional week;
- on a weekend, resolve to the upcoming instructional week;
- preserve a previously selected week unless the teacher explicitly changes it;
- never overwrite a stored selection with a hard-coded `Q1W5` default.

## Previous instructional day

The previous instructional day is the latest earlier date that:

- is Monday through Friday;
- is inside a track-in period;
- is not a holiday;
- is not a break;
- is not an unexpected closure.

This rule is used for:

- Study Guide placement;
- assessment preparation;
- reminder timing;
- announcement timing;
- rescheduled content.

## Next instructional day

The next instructional day is the earliest later date that:

- is Monday through Friday;
- is inside a track-in period;
- is not a holiday;
- is not a break;
- is not an unexpected closure.

## Friday homework rule

Friday remains an instructional day when school is open.

Default behavior:

- normal Friday homework is omitted;
- Friday tests or assessments may still occur when allowed;
- an explicit teacher override may request homework, but the override must be visible and validated;
- a validator must not silently delete teacher-entered Friday content.

## Weekly announcement scheduling

Weekly agenda announcements are scheduled on the last valid instructional day before the upcoming instructional week.

Rules:

- if Friday is instructional, use Friday;
- if Friday is closed, use the previous instructional day;
- a Monday holiday does not by itself move the announcement to Thursday;
- multi-day closures resolve to the latest valid instructional day before the upcoming week;
- fixed seven-day or calendar-offset logic is prohibited;
- the preferred time remains configurable;
- 4:00 PM Eastern remains legacy/default evidence until explicitly confirmed as current production policy;
- unusual computed schedules must be previewed before scheduling.

## No-Monday-test rule

Tests may not be scheduled on Monday.

If any rule, disruption, or cascade would place a test on Monday:

- move the test to Tuesday;
- preserve the instructional sequence;
- recalculate preparation and Study Guide timing;
- regenerate reminders and announcements;
- invalidate stale generated content and approvals.

## Inclement-weather statement

The school calendar states:

```text
Thales Academy will not make up days when school is closed for inclement weather.
```

For the workstation, this means:

- no extra school day is added to the calendar;
- the instructional sequence may still shift forward within the existing instructional calendar;
- the missed lesson is not silently dropped;
- the missed lesson is not automatically converted to homework;
- any sequence shift must follow the approved calendar-disruption contract;
- quarter or year-end overflow must require teacher review rather than being guessed.

## Validation requirements

The context-pack validator must confirm:

- school year is `2026-2027`;
- all track-in and track-out ranges are present;
- all approved holidays are present;
- instructional-week JSON exists and is valid;
- current-week logic references the instructional calendar;
- previous/next instructional-day logic skips holidays, breaks, weekends, and closures;
- no-Monday-test rule is represented;
- weekly announcement scheduling uses last instructional day;
- no fixed-offset-only scheduling rule is treated as canonical.
