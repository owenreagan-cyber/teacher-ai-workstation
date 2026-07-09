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
8275c77 Merge pull request #309 from owenreagan-cyber/canvas-llm-phase-21-codex-autonomous-sandbox-learning-agent
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
Phase 21 — Codex Autonomous Sandbox Learning Agent
```

Latest completed PR:

```text
PR #309 — Add Canvas LLM Phase 21 autonomous sandbox learning agent
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

---

## Phase 19B Canonical Rule Constitution Update

A Phase 19B branch was created:

```text
canvas-llm-phase-19b-canonical-rule-constitution
```

Baseline main:

```text
f61dae2 Merge pull request #301 from owenreagan-cyber/canvas-llm-phase-19a-legacy-archaeology-report
```

## Phase 19B Purpose

Convert owner-approved Phase 19A archaeology decisions into canonical rule tables before any implementation.

Phase 19B remains documentation/status only.

## Phase 19B Canonical Rule Specs Created

Current rule directory:

```text
docs/programs/canvas-llm/phase-19b-canonical-rules/
```

Specs:

```text
canonical-rule-constitution.md
canonical-subject-prefixes.md
canonical-assignment-title-rules.md
canonical-study-guide-grading.md
canonical-reading-spelling-together.md
canonical-friday-rules.md
canonical-newsletter-rules.md
canonical-file-management-policy.md
canonical-source-authority-policy.md
canonical-medical-center-diagnostics.md
canonical-write-gate-policy.md
```

## Phase 19B Decisions Captured

Phase 19B formalizes:

- source authority order
- evidence classification labels
- canonical subject prefixes
- Math assessment title rules
- Math Study Guide grading rule
- Reading/Spelling Together rule
- Friday rule
- newsletter page-first rule
- file management safety policy
- Medical Center diagnostic model
- write gate policy

## Phase 19B Boundary

Phase 19B does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- refactors
- migrations

## Updated Handoff Summary

Start future chats with:

```text
Teacher AI Workstation / Canvas LLM Center is on Phase 19B.
Production main is at least f61dae2 after PR #301.
Current Phase 19B branch is canvas-llm-phase-19b-canonical-rule-constitution.
Use docs/programs/canvas-llm/current-handoff.md and docs/programs/canvas-llm/memory/phase-19a-memory.md as active source of truth.
Do not write to Canvas, call APIs, scan broadly, commit raw local metadata, or implement app behavior.
Phase 19B canonical rules live in docs/programs/canvas-llm/phase-19b-canonical-rules/.
```

---

## Handoff Regression Rule Added During Phase 19B

A recurring problem was identified:

```text
New phases update current-handoff.md and accidentally remove historical breadcrumbs required by older status scripts.
```

A governance rule was added:

```text
docs/programs/canvas-llm/handoff-regression-rule.md
```

Future prompts should include:

```text
Preserve historical handoff breadcrumbs required by prior phase status scripts.
When updating current-handoff.md, move the current phase forward but do not delete older PR/commit markers that regressions validate.
If a prior status fails because a breadcrumb moved, restore the historical breadcrumb in a dedicated Historical Baselines section rather than weakening the status script.
```

This rule is documentation/governance only and authorizes no Canvas/API/write/student-data behavior.


---

## Phase 19C Evidence Vault + Rule Catalog Schema Update

A Phase 19C branch was created:

```text
canvas-llm-phase-19c-evidence-vault-rule-catalog-schema
```

Baseline main:

```text
f2d99a9 Merge pull request #302 from owenreagan-cyber/canvas-llm-phase-19b-canonical-rule-constitution
```

## Phase 19C Purpose

Define preview-only Evidence Vault and Rule Catalog schemas before implementation.

Phase 19C remains documentation/status only.

## Phase 19C Schema Directory

```text
docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/
```

## Phase 19C Schema Specs Created

```text
evidence-vault-schema.md
evidence-classification-schema.md
rule-catalog-schema.md
rule-review-workflow.md
rule-source-linking-schema.md
diagnostic-readiness-schema.md
preview-only-boundary.md
phase-19c-next-step-recommendation.md
```

## Phase 19C Decisions Captured

Phase 19C formalizes:

- Evidence Vault record schema
- evidence classification lifecycle
- Rule Catalog record schema
- rule review workflow
- rule source linking schema
- diagnostic readiness levels
- preview-only safety boundary
- Phase 19D recommendation

## Phase 19C Boundary

Phase 19C does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- refactors
- migrations
- database creation
- RAG
- embeddings
- local model/Ollama execution

## Updated Handoff Summary

Start future chats with:

```text
Teacher AI Workstation / Canvas LLM Center is on Phase 19C.
Production main is at least f2d99a9 after PR #302.
Current Phase 19C branch is canvas-llm-phase-19c-evidence-vault-rule-catalog-schema.
Use docs/programs/canvas-llm/current-handoff.md and docs/programs/canvas-llm/memory/phase-19a-memory.md as active source of truth.
Preserve historical handoff breadcrumbs required by prior phase status scripts.
Do not write to Canvas, call APIs, scan broadly, commit raw local metadata, or implement app behavior.
Phase 19C schemas live in docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/.
```


---

## Phase 19D Machine-Readable Seed Rule Catalog + Title Cleaner Preview Update

A Phase 19D branch was created:

```text
canvas-llm-phase-19d-seed-rule-catalog-title-cleaner
```

Baseline main:

```text
3e04771 Merge pull request #303 from owenreagan-cyber/canvas-llm-phase-19c-evidence-vault-rule-catalog-schema
```

## Phase 19D Purpose

Create preview-only machine-readable seed data for the Evidence Vault, Rule Catalog, source links, and Canonical Title Cleaner.

Phase 19D remains documentation/data/status only.

## Phase 19D Directory

```text
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/
```

## Phase 19D Files Created

```text
README.md
evidence.json
rules.json
links.json
title-normalization-rules.json
title-normalization-fixtures.md
preview-only-boundary.md
phase-19d-next-step-recommendation.md
```

## Title Cleaner Rule Captured

The system should identify and preview normalized canonical titles for close or mislabeled inputs.

Examples:

```text
SM5 Test 1 -> SM5: Test 1
SM 5: Test 1 -> SM5: Test 1
SM5 - Test 1 -> SM5: Test 1
SM5 Fact Test 1 -> SM5: Fact Test 1
SM5 Study Guide 1 -> SM5: Study Guide 1
ELA4 Test 1 -> ELA4: Test 1
RM4 Test 1 -> RM4: Test 1
Spelling Test 1 -> RM4: Spelling Test 1
RM4 Spelling Test 1 -> RM4: Spelling Test 1
SP4 Spelling Test 1 -> RM4: Spelling Test 1
```

Ambiguous inputs, such as `Test 4`, require review.

## Phase 19D Boundary

Phase 19D does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- refactors
- migrations
- database creation
- RAG
- embeddings
- local model/Ollama execution

## Updated Handoff Summary

Start future chats with:

```text
Teacher AI Workstation / Canvas LLM Center is on Phase 19D.
Production main is at least 3e04771 after PR #303.
Current Phase 19D branch is canvas-llm-phase-19d-seed-rule-catalog-title-cleaner.
Use docs/programs/canvas-llm/current-handoff.md and docs/programs/canvas-llm/memory/phase-19a-memory.md as active source of truth.
Preserve historical handoff breadcrumbs required by prior phase status scripts.
Do not write to Canvas, call APIs, scan broadly, commit raw local metadata, or implement app behavior.
Phase 19D preview data lives in docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/.
```


---

## Phase 19E Title Cleaner Validator Preview Update

A Phase 19E branch was created:

```text
canvas-llm-phase-19e-title-cleaner-validator-preview
```

Baseline main:

```text
ed52100 Merge pull request #304 from owenreagan-cyber/canvas-llm-phase-19d-seed-rule-catalog-title-cleaner
```

## Phase 19E Purpose

Create a local preview validator that proves Phase 19D title cleaner rules and fixtures are machine-checkable.

## Phase 19E Directory

```text
docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/
```

## Phase 19E Validator

```text
scripts/canvas-llm-phase-19e-title-cleaner-validator-preview.py
```

The validator checks:

```text
SM5: Test {number}
SM5: Fact Test {number}
SM5: Study Guide {number}
ELA4: Test {number}
RM4: Test {number}
RM4: Spelling Test {number}
never_silently_mutate_canvas
ambiguous_input_requires_review
known rule references
known evidence references
known source links
```

## Phase 19E Boundary

Phase 19E does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- database creation
- RAG
- embeddings
- local model/Ollama execution


---

## Phase 19F Title Cleaner Deterministic Prototype Preview Update

A Phase 19F branch was created:

```text
canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview
```

Baseline main:

```text
375b649 Merge pull request #305 from owenreagan-cyber/canvas-llm-phase-19e-title-cleaner-validator-preview
```

## Phase 19F Purpose

Create a local deterministic prototype that proves committed Phase 19D title-cleaner fixture examples can normalize into preview-only canonical outputs.

## Phase 19F Directory

```text
docs/programs/canvas-llm/phase-19f-title-cleaner-deterministic-prototype-preview/
```

## Phase 19F Prototype

```text
scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview.py
```

The prototype checks:

```text
SM5 Test 1 -> SM5: Test 1
SM 5: Test 1 -> SM5: Test 1
SM5 Fact Test 2 -> SM5: Fact Test 2
SM5 Study Guide 3 -> SM5: Study Guide 3
ELA4 Test 4 -> ELA4: Test 4
RM4 Test 5 -> RM4: Test 5
Spelling Test 6 -> RM4: Spelling Test 6
SP4 Spelling Test 6 -> RM4: Spelling Test 6
Test 7 -> needs_review
```

## Phase 19F Boundary

Phase 19F does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata reads or commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- database creation
- RAG
- embeddings
- local model/Ollama execution


---

## Phase 19G-I Completion Update

A bundled Phase 19G-I branch was created:

```text
canvas-llm-phase-19g-19i-title-cleaner-review-medical-write-gate
```

Baseline main:

```text
004aa88 Merge pull request #306 from owenreagan-cyber/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview
```

## Phase 19G

Create a title-cleaner review packet preview.

Directory:

```text
docs/programs/canvas-llm/phase-19g-title-cleaner-review-packet-preview/
```

## Phase 19H

Create Medical Center title-cleaner diagnostic expansion preview.

Directory:

```text
docs/programs/canvas-llm/phase-19h-medical-center-diagnostic-expansion-preview/
```

## Phase 19I

Create minimum Canvas write gate design packet and close Phase 19.

Directory:

```text
docs/programs/canvas-llm/phase-19i-minimum-write-gate-design-packet/
```

## Phase 19 Final Decision

```text
CANVAS_WRITES_REMAIN_BLOCKED
```

## Recommended Next Phase

```text
Phase 20 — Canvas LLM Minimum Write Gate Approval Packet
```

## Phase 19G-I Boundary

Phase 19G-I does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata reads or commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- database creation
- RAG
- embeddings
- local model/Ollama execution


---

## Phase 20 Demo Sandbox Write Gate Approval Packet Update

A Phase 20 branch was created:

```text
canvas-llm-phase-20-demo-sandbox-write-gate-approval-packet
```

Baseline main:

```text
42d4077 Merge pull request #307 from owenreagan-cyber/canvas-llm-phase-19g-19i-title-cleaner-review-medical-write-gate
```

## Owner Correction

Owen clarified that course `24399` is an owner-created demo sandbox course intended for safe Canvas automation testing.

## Owner Safety Statement

```text
Course 24399 is a sandbox demo course.
It has never had students.
It has no grades.
It has no personal information.
It contains copied sample math data, pages, files, announcements, assignments, and modules for testing.
It is safe for controlled edit, delete, write, and automation testing.
```

## Phase 20 Approval Phrase Recorded

```text
I APPROVE THIS ONE CANVAS WRITE FOR COURSE <24399>: create one unpublished test page titled <Math Automation Sandbox>
```

## Phase 20 Decision

```text
APPROVAL_PACKET_PREPARED_WRITE_NOT_EXECUTED
```

## Recommended Next Phase

```text
Phase 21 — Execute One Approved Demo Sandbox Canvas Write
```

Phase 21 may execute only:

```text
Create one unpublished Canvas page in course 24399 titled Math Automation Sandbox.
```

Phase 20 itself does not call Canvas APIs and does not write to Canvas.

---

## Phase 21 Codex Autonomous Sandbox Learning Agent Update

A Phase 21 branch was created:

```text
canvas-llm-phase-21-codex-autonomous-sandbox-learning-agent
```

Baseline main:

```text
96d9ed5 Merge pull request #308 from owenreagan-cyber/canvas-llm-phase-20-demo-sandbox-write-gate-approval-packet
```

Phase 21 merged through:

```text
PR #309 — Add Canvas LLM Phase 21 autonomous sandbox learning agent
8275c77 Merge pull request #309 from owenreagan-cyber/canvas-llm-phase-21-codex-autonomous-sandbox-learning-agent
```

Phase 21 directory:

```text
docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent/
```

Phase 21 status command:

```text
bin/chief-of-staff --canvas-llm-phase-21-codex-autonomous-sandbox-learning-agent-status
```

Approved runtime Canvas base domain:

```text
https://thalesacademy.instructure.com
```

Future local operator commands:

```bash
export CANVAS_BASE_URL="https://thalesacademy.instructure.com"
export CANVAS_TOKEN="<set locally only; never paste into chat>"

python3 scripts/canvas-llm/canvas_learning_agent.py --mode inventory
python3 scripts/canvas-llm/canvas_learning_agent.py --mode reference-inventory
python3 scripts/canvas-llm/canvas_learning_agent.py --mode questions
python3 scripts/canvas-llm/canvas_learning_agent.py --mode existing-page-dry-run
python3 scripts/canvas-llm/canvas_learning_agent.py --mode experiment --allow-writes
python3 scripts/canvas-llm/canvas_learning_agent.py --mode cleanup --allow-writes
```

Phase 21 safety state:

```text
Default mode is read-only inventory.
Reference-inventory mode reads only courses 21944, 21957, and 21919.
Canvas writes are locked to course 24399 and require --allow-writes.
Announcement notification behavior remains blocked unless a later explicit approval names the exact action.
Raw Canvas output remains under .local/canvas-llm/sandbox-learning-runs/phase-21/.
No CANVAS_TOKEN, raw Canvas object URL, token-bearing URL, or raw Canvas response may be committed.
```

Phase 21 does not need to call Canvas during implementation. The operator must supply credentials locally before any inventory run, and experiment/cleanup mode must be intentionally invoked with `--allow-writes`.
