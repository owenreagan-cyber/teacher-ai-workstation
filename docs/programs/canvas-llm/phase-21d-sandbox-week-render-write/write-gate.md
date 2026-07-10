# Phase 21D Write Gate

## Required Phrase

```text
PHASE_21D_SANDBOX_WEEK_WRITE_APPROVED
```

## Required Target

```text
course_id: 24399
page_slug: q1w1
```

## Required Flags

```text
--allow-writes
--target-course-id 24399
--target-page-slug q1w1
--approval-phrase PHASE_21D_SANDBOX_WEEK_WRITE_APPROVED
```

## Required Prewrite Snapshot

Before updating the page, the agent must write an ignored local snapshot:

```text
.local/canvas-llm/sandbox-learning-runs/phase-21/phase21d-prewrite-page-snapshot.json
```

## Required People Gate

Before updating the page or creating assignments, the agent must verify:

```text
People list is empty OR contains only Owen Reagan / owen.reagan@thalesacademy.com.
```

Unexpected People block the write.
