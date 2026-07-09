# Calendar Disruption Doctrine

## Snow Day Protocol

When Owen marks a date as a snow day, the app should treat it as a calendar disruption, not as a normal lesson day.

Expected behavior:

```text
In Class: Snow Day
Homework: none / removed for that day
```

The lesson and homework originally planned for the snow day should be pushed forward one school day.

All later lessons and homework should cascade forward one school day.

## Friday Rule During Snow Day Cascades

If a Friday lesson is pushed forward, it should move to Monday.

If a Friday test is pushed forward, it should move to Tuesday, not Monday.

Reason:

```text
Monday should not become the automatic test day after a disruption unless Owen explicitly approves it.
```

## Homework Handling

Homework assigned on the snow day should be deleted/removed for that date.

The original snow-day lesson's homework should move with the displaced lesson unless Owen explicitly removes or changes it.

## Test Date Handling

If a snow day changes a test date, the app should flag the changed test date for parent communication.

The app should prepare an announcement update that notifies parents of changed test dates.

Announcement behavior still requires the normal approval and notification gates.

## Preview Requirement

The app must preview snow day cascades before applying them.

A snow day preview should show:

```text
original date
new date
subject
lesson title
homework
test changes
announcement changes needed
```

## Safety Rule

The app must not silently cascade lessons, homework, tests, or announcements into Canvas without an approval step.

## Classification

The app should classify snow day changes as:

```text
calendar_disruption
snow_day_protocol
requires_preview
requires_owner_approval_before_canvas_write
```
