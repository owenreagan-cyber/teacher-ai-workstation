# Phase 21D Rollback Plan

## Rollback Preview Mode

```text
phase21d-sandbox-week-rollback-preview
```

This mode reads the ignored local prewrite snapshot and reports what rollback would do.

## Rollback Write Mode

Rollback requires:

```text
--allow-writes
--target-course-id 24399
--target-page-slug q1w1
--approval-phrase PHASE_21D_SANDBOX_WEEK_ROLLBACK_APPROVED
```

## Rollback Behavior

Rollback restores the page body from:

```text
phase21d-prewrite-page-snapshot.json
```

Assignments are not deleted in Phase 21D rollback unless explicitly approved in a later phase.
