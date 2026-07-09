# Q/W Week Page Doctrine

## Core Meaning

```text
Q = Quarter
W = Week within that quarter
```

Examples:

```text
Q1W1 = Quarter 1, Week 1
Q1W9 = Quarter 1, Week 9
Q2W1 = Quarter 2, Week 1
Q3W5 = Quarter 3, Week 5
Q4W10 = Quarter 4, Week 10
```

## Week Reset Rule

Weeks reset at the beginning of each quarter or track.

Correct normal transition:

```text
Q1W8
Q1W9
Q2W1
Q2W2
```

Incorrect global-week transition:

```text
Q1W8
Q1W9
Q1W10
Q1W11
```

## True Week 10 Rule

`Q4W10` is the only normal true Week 10 class page currently recognized by owner doctrine.

The app must not infer `Q1W10`, `Q2W10`, or `Q3W10` as normal weekly pages.

A non-Q4 W10 page is valid only if Owen explicitly creates and approves it as a special exception.

## End-of-Track Special Pages

Owen may create an extra end-of-track page, especially at the end of Tracks/Quarters 1 and 3 because conferences happen near those transitions.

Expected naming pattern may include:

```text
Q1END
Q3END
```

These are special owner-created end-of-track pages.

They are not normal weekly pages.

They are not substitutes for `Q1W10`, `Q2W10`, or `Q3W10`.

They may be used for end-of-track newsletters, conference information, transition reminders, or similar special communication.

## Page Classes

### Normal Weekly Page

Examples:

```text
Q1W5
Q2W8
Q3W5
Q4W10
```

Rules:

- page should already exist in production
- app updates existing page
- app does not create real production weekly page
- page may be published/scheduled after approval
- page may be set as front page after approval

### True Week 10 Page

Example:

```text
Q4W10
```

Rules:

- valid normal weekly page only when explicitly present
- currently only `Q4W10` is expected as a true Week 10 class page

### End-of-Track Special Page

Examples:

```text
Q1END
Q3END
```

Rules:

- owner-created special page
- not part of normal W sequence
- should be classified separately from weekly pages
- may be used for conference/end-of-track newsletter workflows
- requires owner approval before production update/publish/front-page behavior

## Classification Guidance

The app should classify page names as:

```text
weekly_page
true_week_10_page
end_of_track_special_page
unknown_or_needs_review
```

Classification examples:

```text
Q1W9 -> weekly_page
Q2W1 -> weekly_page
Q4W10 -> true_week_10_page
Q1END -> end_of_track_special_page
Q3END -> end_of_track_special_page
Q1W10 -> unknown_or_needs_review unless explicitly approved
Q2W10 -> unknown_or_needs_review unless explicitly approved
Q3W10 -> unknown_or_needs_review unless explicitly approved
```

## Production Rule

Production weekly pages are preloaded and updated, not created.

Production special end-of-track pages are owner-created or owner-approved before automation updates them.

The app must never invent extra weekly pages from calendar math alone.
