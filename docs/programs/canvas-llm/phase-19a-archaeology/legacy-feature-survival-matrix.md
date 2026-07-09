# Canvas LLM Phase 19A Legacy Feature Survival Matrix

## Status

Analysis-only archaeology report.

This matrix classifies legacy features from available source repositories and recommends whether each should survive, be rewritten, be blocked, or require owner review.

## Source Repositories Reviewed

Available:

```text
~/Projects/Thalescanvasgemini
~/Projects/pacing-sync-pilot-8c50be47
```

Unavailable:

```text
~/Projects/pacing-sync-pilot
```

## Classification Labels

```text
APPROVED_PATTERN
WORKFLOW_EVIDENCE
LEGACY_FORMAT_ONLY
UNKNOWN_NEEDS_REVIEW
```

## Survival Matrix

| Legacy Feature | Source Evidence | Classification | Recommendation | Reason |
|---|---|---:|---|---|
| Phase memory / handoff continuity | Teacher AI Workstation Phase 19A memory foundation | APPROVED_PATTERN | Preserve | Prevents reliance on archived chats or missing sandbox paths. |
| Canvas write gate readiness review | Phase 18 report/status/analyzer | APPROVED_PATTERN | Preserve | Keeps real Canvas mutation blocked until explicit minimum write design exists. |
| Assignment deterministic engine | Thales assignment logic/builders; pacing assignment-build | WORKFLOW_EVIDENCE | Preserve as rules, rewrite as canonical tables | Strong deterministic value, but title/grading drift exists. |
| Math Test triple expansion | Thales assignment-builder; pacing assignment-build/tests | WORKFLOW_EVIDENCE | Preserve | Written Test + Fact Test + Study Guide is repeated and owner-approved direction. |
| Math Study Guide old grading | Thales/pacing assignment logic | LEGACY_FORMAT_ONLY | Replace with owner-approved rule | Legacy shows 100 percent/omit conflict; owner decided 0 points and Does Not Count Toward Final Grade checked. |
| Subject prefixes | Validators, migrations, file organizer, owner decision | APPROVED_PATTERN | Preserve as canonical | SM5/RM4/ELA4/HIST4/SCI4 must be deterministic. |
| Reading + Spelling Together Logic | pacing together-logic, page builder, announcement templates | APPROVED_PATTERN | Preserve | Reading and Spelling share RM4 identity/page/announcement; no standalone Spelling pages. |
| Standalone Spelling announcements | pacing useAutoGenerateAnnouncements conflict | LEGACY_FORMAT_ONLY | Block | Conflicts with Together Logic and owner-approved communication direction. |
| Friday rules | Thales friday-rules; pacing friday-rules; DB trigger; validators | APPROVED_PATTERN | Preserve | Repeated evidence supports no normal Friday homework and omitted At Home section. |
| Friday completion checklist replacement | Thales constants/gemini helper | UNKNOWN_NEEDS_REVIEW | Do not preserve yet | Conflicts with stronger Friday omit-At-Home evidence and FPK simplicity. |
| Resource resolver / content map | Thales resourceResolver; pacing content_map/auto-link | WORKFLOW_EVIDENCE | Preserve concept, redesign local-first | Useful relationship intelligence, but not automatic file mutation authority. |
| Auto-linking from content map | pacing auto-link/canvas-html/assignment-build | WORKFLOW_EVIDENCE | Preserve for preview only | Helpful for resource references; requires deterministic evidence and human review before publish. |
| Canvas Brain suggestions | pacing canvas-brain/canvas-brain-suggest | WORKFLOW_EVIDENCE | Preserve as advisory only | Suggestions must never override safety or owner-approved rules. |
| Teacher Memory | pacing teacher-memory/memory-resolver | WORKFLOW_EVIDENCE | Preserve with privacy/approval gates | Valuable pattern memory, but cannot become unreviewed source of truth. |
| Pre-deploy validator | pacing pre-deploy-validator | APPROVED_PATTERN | Preserve and expand into Medical Center | Strong safety layer before any write. |
| Canvas auditor / grade reviewer | Thales auditor/grade review features | WORKFLOW_EVIDENCE | Preserve as future diagnostics only | Useful health concepts; student/privacy boundaries require review. |
| Diff engine / Safety Diff modal | Thales diffEngine; pacing SafetyDiffModal | APPROVED_PATTERN | Preserve | Future writes must be diff-first and human-approved. |
| Direct deploy pages/assignments/announcements | Thales canvasHelpers/functions; pacing deployment hooks | BLOCKED | Do not inherit directly | Real Canvas mutation remains disabled until explicit write gate. |
| Canvas file rename/move/orphan sweeper | Thales OrphanSweeper/resource services; pacing FileOrganizerPage | WORKFLOW_EVIDENCE | Preview first, future write-gated only | Owner wants file organization soon, but no silent rename/move/delete/upload. |
| Newsletter builder | Thales NewsletterBuilder; pacing NewsletterPage | WORKFLOW_EVIDENCE | Preserve page-first model | Owner approved Newsletter = Homeroom Canvas Page, announcement = notification only. |
| Birthday handling | Newsletter services/pages | UNKNOWN_NEEDS_REVIEW | Privacy-gated only | Student names/private info require separate approval. |
| Hardcoded historical course IDs | constants/canvas-courses/course routing | LEGACY_FORMAT_ONLY | Replace with manifest/governed config | Old IDs are historical evidence, not future target authority. |
| Prompt registry / AI prompt rules | Thales prompts/gemini helper | WORKFLOW_EVIDENCE | Preserve constraints, not as authority | Prompts may help draft text but cannot define rules. |
| CIDI/Canvas HTML generators | Thales/pacing canvas HTML | WORKFLOW_EVIDENCE | Review against FPK guidelines | Some structure is useful, but old body formatting may conflict with current page standards. |
| File Organizer classification patterns | pacing FileOrganizerPage | WORKFLOW_EVIDENCE | Preserve for read-only suggestions | Useful for AI File Assistant; no direct operations yet. |

## Highest-Value Survivors

Preserve and formalize:

1. subject prefix rules
2. Math Test triple logic
3. Reading + Spelling Together Logic
4. Friday rules
5. pre-deploy validation / Medical Center
6. diff-first approval workflow
7. content/resource relationship mapping
8. Teacher Memory with approval boundaries
9. page-first newsletter model
10. write-gated file organization vision

## Features Not Safe to Inherit Directly

Do not inherit directly:

- deploy pages
- deploy assignments
- deploy announcements
- Canvas file rename/move
- orphan sweeper execution
- hardcoded historical course IDs
- prompt-only rule inference
- unreviewed newsletter birthday storage
- standalone Spelling announcement generation
- legacy page body formatting

## Recommendation

Phase 19A should produce architecture/spec reports only.

Phase 19B should convert approved decisions into canonical rule tables before any implementation.

Implementation should wait until:

```text
Evidence Vault
Rule Catalog
Relationship Catalog
Preview Builders
Medical Center
Human Approval Gates
Write Adapter
```

are specified in that order.
