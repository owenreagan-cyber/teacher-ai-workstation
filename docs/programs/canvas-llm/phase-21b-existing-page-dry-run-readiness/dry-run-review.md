# Phase 21B Existing Page Dry-Run Review

## Review Questions

The dry-run result should answer:

1. Can the agent identify existing preloaded weekly pages in sandbox course `24399`?
2. Can the agent avoid creating production-style pages?
3. Can the agent distinguish normal weekly pages from special pages such as `Q1END`, `Q3END`, and `Q4W10`?
4. Can the agent propose an update plan without writing to Canvas?
5. Can the agent keep reference courses read-only?
6. Can the agent keep all live learning artifacts under ignored `.local` paths?
7. Can the agent avoid student data, grades, people, submissions, gradebook, settings, and analytics?
8. Can the agent preserve existing DesignPlus / `kl_*` page shell assumptions rather than generating random Canvas HTML?

## Readiness Criteria

A future sandbox write experiment should remain blocked unless the dry-run provides:

- target sandbox course is exactly `24399`
- target page already exists
- proposed operation is update-preview, not create
- no production course is targeted
- no reference course is targeted for writes
- no announcement notification is triggered
- no school Canvas URL or token is committed
- rollback/cleanup expectations are clear
- owner approval remains required before any write

## Current Decision

```text
EXISTING_PAGE_DRY_RUN_NEEDS_AGENT_HARDENING
```

## Observed Dry-Run Result

```text
WARN: no sandbox QxWy candidate page found
```

## Interpretation

The inventory phase found sandbox QxWy page candidates in course `24399`, including preloaded weekly pages.

The existing-page dry-run did not select one of those candidates.

This suggests the next implementation step should harden the dry-run selector before any `--allow-writes` experiment.

Canvas writes remain blocked.
