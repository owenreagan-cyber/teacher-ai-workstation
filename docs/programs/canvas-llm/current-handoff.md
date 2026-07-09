# Canvas LLM Current Handoff

## Current Phase

Phase 19A — Legacy Intelligence Extraction / Archaeology Report

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: 5af1ecd
Latest merged PR: #300 — Add Canvas LLM phase memory foundation
```

## Current Working Branch

```text
canvas-llm-phase-19a-legacy-archaeology-report
```

## Current Rule

Use repo-tracked memory files as the active handoff source.

Do not rely on archived chats, temporary Codex folders, assistant memory, or pasted inventories unless the contents have been converted into a repo-tracked memory or rule file.

## Active Memory File

```text
docs/programs/canvas-llm/memory/phase-19a-memory.md
```

## Latest Completed Phase

```text
Phase 18 — Canvas Setup Write Gate Readiness Review
Decision: NEEDS_ONE_MORE_PREVIEW_REFINEMENT
```

## Latest Continuity PR

```text
PR #300 — Add Canvas LLM phase memory foundation
```

## Current Work

Create Phase 19A archaeology reports from verified evidence.

Current report directory:

```text
docs/programs/canvas-llm/phase-19a-archaeology/
```

Current reports:

```text
source-availability.md
owner-canonical-decisions.md
legacy-feature-survival-matrix.md
business-rules-catalog.md
legacy-risks.md
unanswered-questions.md
future-architecture-recommendation.md
```

## Verified Source Availability

Available:

```text
~/Projects/Thalescanvasgemini
main @ b75ce84

~/Projects/pacing-sync-pilot-8c50be47
main @ ea6ecbc
```

Unavailable:

```text
~/Projects/pacing-sync-pilot
```

Treat the missing repo as an evidence gap, not a blocker.

## Current Recommendation

Do not implement Canvas LLM Center yet.

Next phase should be:

```text
Phase 19B — Canonical Rule Constitution
```

Phase 19B should convert owner-approved archaeology decisions into durable canonical rule tables before code implementation.

## Boundaries

Do not:

- call Canvas APIs
- write to Canvas
- fetch live Canvas data
- move, rename, upload, delete, or publish files
- commit raw `.local` metadata
- commit school Canvas URLs
- expose tokens
- access student data
- enable generation or automation
- implement app behavior
- refactor legacy code
