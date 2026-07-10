# Phase 21D Safety Boundary

Phase 21D is sandbox-only.

## Allowed

- read sandbox course `24399`
- read existing page `q1w1`
- read People/enrollments for course `24399` only as a safety gate
- update existing page `q1w1` only after write approval
- create sandbox assignments in course `24399` only after write approval
- write ignored local snapshots and ledgers under `.local`

## Blocked

- production writes
- reference course writes
- announcement send/notify
- module writes
- file writes
- deletion
- page creation
- publish/unpublish changes
- People writes
- grades
- settings
- submissions
- gradebook
- analytics
- student data

## Tokens

CANVAS_TOKEN must never be printed or committed.
