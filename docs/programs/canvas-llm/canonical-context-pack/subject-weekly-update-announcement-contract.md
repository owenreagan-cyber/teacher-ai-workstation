# Subject Weekly Update Announcement Contract

## Status

```text
APPROVED
```

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

Canonical implementation:

```text
scripts/canvas_llm_phase22/subject_weekly_update.py
```

Canonical model example:

```text
docs/programs/canvas-llm/canonical-context-pack/examples/math-canvas-weekly-update-example.html
```

## Purpose

Each **active subject** gets **one combined weekly update announcement** each week. This is separate from assessment reminders, Homeroom, and the weekly agenda page itself.

## Titles

| Subject | Announcement title | Course |
| --- | --- | --- |
| Math | `Math Canvas Weekly Update` | 26404 |
| Reading/Spelling | `Reading/Spelling Canvas Weekly Update` | 26442 |
| Language Arts | `Language Arts Canvas Weekly Update` | 28171 |
| History | `History Canvas Weekly Update` | 28165 |
| Science | `Science Canvas Weekly Update` (only when Science is active) | 28166 |

Science is announced only when Science is active for the quarter.

Homeroom does **not** receive a subject weekly update. Homeroom stays on its separate rolling newsletter + family-announcement workflow (see `newsletter-homeroom-contract.md`).

## Content order

Each subject announcement contains, in order:

1. greeting
2. Week in Review
3. Week Ahead
4. any meaningful agenda/schedule change
5. transition sentence
6. the exact final current weekly agenda HTML used on that course's front page
7. closing

## Canonical HTML shell

```html
<p>Good afternoon,</p>
<p>[Week in Review]</p>
<p>[Week Ahead]</p>
<p>[Schedule/agenda change if applicable]</p>
<p>The Canvas [Subject] page has been updated. Please see the upcoming week ahead.</p>
[EXACT VERIFIED CURRENT WEEKLY AGENDA HTML]
<p>Have a great weekend!</p>
<p>Mr. Reagan</p>
```

The transition sentence uses the subject label exactly:

```text
The Canvas Math page has been updated. Please see the upcoming week ahead.
The Canvas Reading/Spelling page has been updated. Please see the upcoming week ahead.
The Canvas Language Arts page has been updated. Please see the upcoming week ahead.
The Canvas History page has been updated. Please see the upcoming week ahead.
```

## Week in Review

Base the review primarily on the **previous week's live/approved Canvas agenda**, not just the new pacing guide.

Write natural parent-facing prose such as:

> We completed Lessons 12-14 in Math this week.
> Students worked hard on their Chapter 3 Shurley Test.
> We continued reading The Wonderful Wizard of Oz...
> We wrapped up our World Mountains unit...

It is fine to say students "worked hard on" a test or assessment when a test actually occurred.

**Do not** claim scores, mastery, improvement, or performance results unless Owen explicitly provided them.

## Week Ahead

Base the Week Ahead on the current week's final approved agenda. Emphasize tests and assessments with the exact date when one is scheduled.

## Schedule / agenda change rule

Compare prior published agendas/communications with the current approved plan. If a meaningful change affects families, state it explicitly:

- test moved
- project date changed
- review/test sequence changed
- lesson/activity moved to another day

Explain **both the old and new plan** when known. Never claim a change unless supported.

## Curriculum enrichment

When possible, translate lesson numbers into meaningful parent-facing topic/chapter names.

Source priority (highest first):

1. Owen's current instructions
2. previous/current live Canvas weekly agendas
3. Canvas Modules / Files / course resources
4. approved Google Drive curriculum folders
5. previously verified repo mappings

Never guess a lesson title, chapter title, or topic. If a title cannot be verified, keep the known lesson numbers.

Before opening large PDFs, check Canvas Modules/Files first.

Approved Drive curriculum sources:

```text
Reading:   https://drive.google.com/drive/folders/1-qoBm9ny08xYzqvdE4jMMvk0kDO-t1Sh?usp=sharing
Shurley/LA: https://drive.google.com/drive/folders/1n5SFZvJkWboe0JUNNN68_CHjZwdL9mq4?usp=drive_link
Math:      https://drive.google.com/drive/folders/197iYuyPyAUmpATIh6_L_zZC27YZ7u004?usp=sharing
History:   https://drive.google.com/drive/folders/1eQ0Zn-ETxGASiu_tN605R-CXvwLUFo3W?usp=sharing
Science:   https://drive.google.com/drive/folders/16d6H8keBQMybm5v6vfQlYb5derjslzOc?usp=sharing
```

Verified lesson/topic mappings are persisted with source metadata in:

```text
config/curriculum/canvas/subject-weekly-update-curriculum-map.json
```

Do not populate unverified mappings.

## Exact agenda reuse

Do not independently regenerate the agenda inside the announcement.

The source must be:

```text
final verified weekly agenda HTML -> course front page
same exact final weekly agenda HTML -> weekly update announcement
```

This prevents drift. The builder extracts the `kl_wrapper_3` block from the front-page body and embeds it unchanged.

Preserve the approved FPK structure/colors:

```text
kl_wrapper_3
class="kl_circle_left kl_wrapper"
blue #0065a7
pink #c51062
dark gray #333333
white #ffffff
Reminders
Monday-Friday headers
In Class / At Home behavior
```

## Duplicate protection

Before any future create:

1. fresh-GET current course announcements;
2. detect same course/week weekly update;
3. if identical/correct, treat as `ALREADY_APPLIED` and do not create a duplicate;
4. if an existing announcement for the same week has a different embedded agenda, surface drift for Owen rather than creating another one.

## Validation requirements

The validator must confirm:

- one combined weekly update per active subject;
- Week in Review from prior agenda;
- Week Ahead from current agenda;
- test/assessment emphasis;
- schedule-change detection;
- curriculum enrichment source hierarchy and approved Drive folders;
- exact agenda reuse;
- duplicate protection;
- Homeroom exception.
