# Canvas LLM Phase 19A Source Availability

## Status

Analysis-only source availability report.

## Production Repository

```text
~/Projects/teacher-ai-workstation
```

Current Phase 19A branch:

```text
canvas-llm-phase-19a-legacy-archaeology-report
```

Baseline main commit:

```text
5af1ecd Merge pull request #300 from owenreagan-cyber/canvas-llm-phase-19a-memory-foundation
```

## Available Legacy Sources

### Thalescanvasgemini

```text
Path: ~/Projects/Thalescanvasgemini
Branch: main
Commit: b75ce84 feat: Add Canvas auditor and grade reviewer features
Status: available
```

Use as:

```text
WORKFLOW_EVIDENCE
```

Known value:

- assignment logic
- announcement logic
- prompt registry
- resource resolver ideas
- Canvas HTML generation concepts
- diff/deploy concepts
- grade guard/auditor concepts

Known risk:

- direct Canvas mutation paths
- older architecture assumptions
- possible hardcoded course/config values
- legacy formatting that may conflict with FPK guidelines

### pacing-sync-pilot-8c50be47

```text
Path: ~/Projects/pacing-sync-pilot-8c50be47
Branch: main
Commit: ea6ecbc commiy
Status: available
```

Use as:

```text
WORKFLOW_EVIDENCE
```

Known value:

- Teacher Memory Layer
- Content Map Registry
- Canvas Brain concepts
- auto-linking
- pre-deploy validator
- Friday rules
- Reading + Spelling Together Logic
- Safety Diff / Medical Center concepts
- Smart Paste / Google Sheets import history
- File Organizer concepts

Known risk:

- Supabase-era architecture assumptions
- direct Canvas/file mutation concepts
- memory overreach if not approval-gated
- possible historical-course assumptions

## Missing or Unavailable Sources

### pacing-sync-pilot

```text
Path: ~/Projects/pacing-sync-pilot
Status: missing
```

A targeted availability check found no local directory at this path.

Decision:

```text
Treat as unavailable evidence for Phase 19A.
Do not infer contents from the missing repo.
Use pacing-sync-pilot-8c50be47 as the available pacing-sync evidence source unless Owen provides a separate checkout or archive.
```

### Hidden canvas-llm-center-spec packet

```text
Path: ~/.teacher-ai-workstation/canvas-llm-center-spec or ./ .teacher-ai-workstation/canvas-llm-center-spec
Status: missing
```

A targeted local search under `~/Projects` found no such directory and no matching spec files.

Decision:

```text
Treat as unavailable local evidence.
Do not depend on it.
Regenerate needed specs intentionally from verified sources.
```

## Source Classification Policy

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
2. Owner-approved canonical rules
3. FPK 2025-2026 Canvas Page Guidelines
4. Current Teacher AI Workstation Canvas LLM governance docs
5. Verified deterministic business rules
6. Historical metadata and legacy app evidence
7. AI suggestions
```

## Phase 19A Boundary

This report does not authorize:

- Canvas writes
- Canvas API calls
- live fetches
- file downloads
- body ingestion
- student data access
- app implementation
- refactors
- migrations
- source-of-truth changes
- file rename/move/delete/upload
