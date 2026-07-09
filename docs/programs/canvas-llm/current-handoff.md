# Canvas LLM Current Handoff

## Current Phase

Phase 19A — Legacy Intelligence Extraction / Memory Foundation

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: 154b47a
Latest merged PR: #299 — Add Canvas LLM Phase 18 write gate readiness review
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

## Current Work

Create a durable Phase 19A memory foundation, then continue verified legacy archaeology.

## Next Recommended Action

Inspect the remaining legacy repository:

```text
~/Projects/pacing-sync-pilot
```

Then build the Phase 19A archaeology report from verified evidence only.

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
