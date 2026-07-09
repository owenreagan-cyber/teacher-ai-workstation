# Canvas LLM Phase 19A Memory

## Phase

Phase 19A — Legacy Intelligence Extraction / Memory Foundation

## Purpose

Recover useful intelligence from prior Teacher AI Workstation, Canvas LLM, and Thales Canvas prototypes without treating legacy implementations as automatically authoritative.

This phase is analysis, memory, and specification preparation only.

## Current Production Repo State

Repository:

```text
~/Projects/teacher-ai-workstation
```

Current verified main:

```text
main
154b47a Merge pull request #299 from owenreagan-cyber/canvas-llm-phase-18-write-gate-readiness-review
```

Phase 18 feature commit:

```text
513014f Add Canvas LLM Phase 18 write gate readiness review
```

Previous Phase 17 main commit:

```text
86b72d9 Add Canvas LLM Phase 17 preview setup action packet (#298)
```

Latest completed production phase:

```text
Phase 18 — Canvas Setup Write Gate Readiness Review
```

Latest completed PR:

```text
PR #299 — Add Canvas LLM Phase 18 write gate readiness review
```

Phase 18 decision:

```text
NEEDS_ONE_MORE_PREVIEW_REFINEMENT
```

## Phase 18 Files

Phase 18 added or changed:

```text
bin/chief-of-staff
docs/programs/canvas-llm/canvas-llm-phase-plan.md
docs/programs/canvas-llm/canvas-phase-18-write-gate-readiness-review.md
scripts/canvas-llm-phase-18-status.sh
scripts/canvas-llm-phase-18-write-gate-readiness-review.py
```

## Prior Phase Chain

Known recent phase chain:

```text
Phase 12 — Fake/local sandbox metadata import artifact gate
Phase 13 — Historical academic + Homeroom fetch approval gate
Phase 14A — Course approval manifest
Phase 14B — Read-only approved course metadata fetch
Phase 15 — Historical-to-current readiness and relationship report
Phase 16 — Preview-only Canvas module/file/page relationship map
Phase 17 — Preview-only Canvas setup action packet
Phase 18 — Canvas Setup Write Gate Readiness Review
Phase 19A — Legacy Intelligence Extraction / Memory Foundation
```

## Active Direction

Canvas is not the brain.

Canvas is a downstream preview/publishing destination after:

```text
teacher evidence
canonical rules
curriculum/resource registry
teacher memory
AI suggestions
safety checks
human approval
```

The future system should behave as a local-first Teacher AI Workstation / Canvas LLM Center, not as a live Canvas automation bot.

## Phase 19A Scope

Allowed:

- inspect local legacy repositories
- inspect approved local artifacts
- inspect uploaded teacher-rule files
- extract business rules
- compare historical implementations
- identify conflicts
- create analysis reports
- prepare canonical-rule work

Not allowed:

- no application implementation
- no refactors
- no Canvas API calls
- no Canvas writes
- no live Canvas fetches
- no network integrations
- no OAuth
- no student data
- no raw `.local` metadata commits
- no token exposure
- no school Canvas URLs committed unless explicitly approved
- no file moves, renames, deletions, or uploads
- no automatic scanning/indexing/OCR/embeddings

## Valid Evidence Sources

Use these as Phase 19A evidence:

```text
~/Projects/teacher-ai-workstation
~/Projects/Thalescanvasgemini
~/Projects/pacing-sync-pilot
~/Projects/pacing-sync-pilot-8c50be47
uploaded teacher-rule files
approved local Canvas metadata from prior phases
current chat handoff notes
```

## Rejected or Unavailable Evidence Sources

A pasted inventory referenced:

```text
./.teacher-ai-workstation/canvas-llm-center-spec/
```

A targeted local search under `~/Projects` found no such directory and no matching spec files.

Therefore:

```text
Status: unavailable local evidence
Action: do not depend on it
Use: idea only; regenerate intentionally if needed
```

## Legacy Repositories

### Thalescanvasgemini

Path:

```text
~/Projects/Thalescanvasgemini
```

Role:

```text
AI + Canvas automation prototype
```

Known recovered areas:

- assignment builder
- assignment logic
- announcement service
- prompt registry
- diff engine
- deployment concepts
- grade guard
- resource resolver concepts
- Canvas HTML generation concepts

### pacing-sync-pilot-8c50be47

Path:

```text
~/Projects/pacing-sync-pilot-8c50be47
```

Role:

```text
pacing + teacher memory + resource + safety prototype
```

Known recovered areas:

- Teacher Memory Layer
- Content Map Registry
- Canvas Brain
- auto-linking
- pre-deploy validator
- Friday rules
- Reading + Spelling Together Logic
- Safety Diff concepts
- Smart Paste / Google Sheets import history
- File Organizer concepts

### pacing-sync-pilot

Path:

```text
~/Projects/pacing-sync-pilot
```

Role:

```text
original pacing / Canvas sync prototype
```

Status:

```text
still needs final inventory and extraction
```

## Core Owner Decisions

- No standards alignment engine is needed.
- Historical Canvas data is evidence, not authority.
- FPK 2025–2026 Canvas Page Guidelines govern Canvas page formatting.
- Canvas should be downstream, not the source of curriculum intelligence.
- AI may suggest wording, but deterministic rules decide whether assignments exist.
- Human approval is required before publishing or mutating external systems.
- File organization must begin read-only and suggestion-only.

## Canonical Owner Decisions Ready for Phase 19B

Subject prefixes:

```text
Math = SM5
Reading = RM4
Spelling = RM4
Language Arts / Shurley = ELA4
History = HIST4
Science = SCI4
```

Math assessment titles:

```text
SM5: Test {number}
SM5: Fact Test {number}
SM5: Study Guide {number}
```

Study Guide grading:

```text
0 points
Does Not Count Toward Final Grade = TRUE
Does not affect final grade calculation
Purpose is preparation/review
```

Newsletter model:

```text
Newsletter = Homeroom Canvas Page
Announcement = notification only
Announcement text = "The newsletter has been updated for the week of {date range}."
```

File management model:

```text
Near-term: read-only AI File Assistant
Future: write-gated AI File Organizer
Never: automatic rename/move/delete/upload without preview, approval, execution, and verification
```

## Historical Evidence Classification

Use these labels:

```text
APPROVED_PATTERN
WORKFLOW_EVIDENCE
LEGACY_FORMAT_ONLY
UNKNOWN_NEEDS_REVIEW
```

Authority order:

```text
1. Safety boundaries
2. Owner-approved rules
3. FPK 2025–2026 Canvas Guidelines
4. Verified post-guideline Canvas examples
5. Historical workflow evidence
6. AI suggestions
```

## Current Phase 19A Need

Before creating the formal archaeology report, finish inventory of:

```text
~/Projects/pacing-sync-pilot
```

Then compare all three legacy repos with current Canvas LLM docs and teacher-approved rules.

## Expected Phase 19A Outputs

Create or prepare:

```text
legacy-feature-survival-matrix.md
business-rules-catalog.md
teacher-memory-model.md
resource-intelligence-model.md
communication-intelligence-model.md
canvas-history-analysis-policy.md
conflicts-and-decisions-needed.md
future-architecture-recommendation.md
```

## Next Recommended Step

Run a targeted inventory of:

```text
~/Projects/pacing-sync-pilot
```

Then generate the Phase 19A archaeology report from verified evidence only.

## Handoff Summary

Start future chats with:

```text
Teacher AI Workstation / Canvas LLM Center is on Phase 19A.
Production repo is main @ 154b47a.
Phase 18 PR #299 is complete and cleaned up.
Phase 19A is analysis only.
Do not write to Canvas, call APIs, scan folders broadly, or commit raw local metadata.
Use docs/programs/canvas-llm/memory/phase-19a-memory.md as the active source of truth.
```

---

## Phase 19A Archaeology Report Update

A Phase 19A archaeology branch was created:

```text
canvas-llm-phase-19a-legacy-archaeology-report
```

Baseline main:

```text
5af1ecd Merge pull request #300 from owenreagan-cyber/canvas-llm-phase-19a-memory-foundation
```

## Verified Source Availability Update

Available legacy sources:

```text
~/Projects/Thalescanvasgemini
main @ b75ce84

~/Projects/pacing-sync-pilot-8c50be47
main @ ea6ecbc
```

Missing or unavailable source:

```text
~/Projects/pacing-sync-pilot
```

Decision:

```text
Treat ~/Projects/pacing-sync-pilot as unavailable evidence for Phase 19A unless Owen provides a checkout or archive.
Use pacing-sync-pilot-8c50be47 as the available pacing-sync evidence source.
```

## Phase 19A Archaeology Reports Created

Current report directory:

```text
docs/programs/canvas-llm/phase-19a-archaeology/
```

Reports:

```text
source-availability.md
owner-canonical-decisions.md
legacy-feature-survival-matrix.md
business-rules-catalog.md
legacy-risks.md
unanswered-questions.md
future-architecture-recommendation.md
```

## Verified Findings Added

The Phase 19A archaeology reports capture:

- source availability and missing evidence
- owner-approved canonical decisions
- legacy feature survival recommendations
- business rules separated by authority level
- legacy risk register
- unanswered decision queue
- future architecture recommendation

## Updated Recommendation

Do not implement Canvas LLM Center yet.

Next phase:

```text
Phase 19B — Canonical Rule Constitution
```

Phase 19B should convert approved decisions into canonical rule tables before any generator, preview builder, Medical Center, or write adapter implementation.

## Updated Handoff Summary

Start future chats with:

```text
Teacher AI Workstation / Canvas LLM Center is on Phase 19A.
Production main is at least 5af1ecd after PR #300.
Current Phase 19A archaeology branch is canvas-llm-phase-19a-legacy-archaeology-report.
Use docs/programs/canvas-llm/current-handoff.md and docs/programs/canvas-llm/memory/phase-19a-memory.md as active source of truth.
Do not write to Canvas, call APIs, scan broadly, commit raw local metadata, or implement app behavior.
Next recommended phase is Phase 19B — Canonical Rule Constitution.
```
