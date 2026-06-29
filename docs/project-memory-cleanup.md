# Project Memory Cleanup

## Purpose

This document defines a project memory cleanup pass after local document indexing follow-up. It tightens active priorities and project memory so the current roadmap stays readable without changing feature behavior.

This PR improves project memory clarity only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: project memory cleanup in progress.
```

Active priorities and project memory are being tightened so current work, completed work, parked work, and safety boundaries are easy to scan.

## Why This Cleanup Exists

After local document indexing follow-up, workflow polish and foundation work were complete but active priorities and project memory had grown long and repetitive. This cleanup makes the roadmap scannable without losing useful project history.

## Memory Cleanup Goals

```text
make current priorities easy to scan
make completed work easy to distinguish from active work
make next recommended PR easy to find
keep parked work visible but not distracting
keep Appearance & Vibe foundation status clear
keep Teacher Workstation core status clear
keep safety boundaries explicit
avoid stale or contradictory roadmap notes
preserve useful project history
```

## Active Priorities Rules

```text
active-priorities should focus on current and next work
completed work should be summarized, not repeated in full
parked work should stay clearly labeled
future-only work should stay clearly labeled
safety boundaries should remain visible
next recommended PR should match build queue
```

## Project Memory Rules

```text
projects memory should show major project areas
projects memory should distinguish foundation complete from implementation started
projects memory should not imply live wallpaper/photo curator exists
projects memory should not imply document indexing exists
projects memory should not imply lesson generation changed
projects memory should not imply student data is present
```

## Recently Completed Work

```text
Review notes workflow polish: complete
Lesson review workflow polish: complete
Teacher planning command organization: complete
Dashboard section summary polish: complete
Workflow quick-start guide: complete
Help examples polish: complete
Command map cleanup: complete
Dashboard readability pass: complete
Return to Chief of Staff / Teacher Workstation core: complete
Local document indexing follow-up: complete
Appearance & Vibe wallpaper/photo foundation stack: complete for now
```

## Current Roadmap

```text
Current active build: Project memory cleanup
Next recommended PR: Testing/checklist consolidation
```

Testing/checklist consolidation should reduce repeated manual check blocks by documenting grouped check sets. It must preserve every existing command and status check. No checks removed, no behavior changes, no lesson generation changes, no document scanning/indexing implementation, no student data, no live integrations, no network calls, and no automation.

## Parked Work

```text
3D Design Factory Agent remains parked.
Reddit remains a possible future source only.
Devvit remains a possible future Reddit-native companion only.
Live wallpaper/photo curator implementation is not started.
```

## Not Implemented Yet

```text
no live wallpaper/photo curator
no real fetcher
no real image downloading
no real image processing
no live review UI
no scheduler
no notifications
no macOS wallpaper automation
no Photos automation
no Reddit integration
no Devvit integration
no document scanning
no file indexing
no OCR
no embeddings
no vector database
no lesson generation changes
no student data
```

## Safety Boundaries

```text
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
no document scanning
no folder scanning
no file indexing
no content parsing
no OCR
no embeddings
no vector database
no lesson generation changes
no new lesson briefs
no new lesson drafts
no real review notes
no student data
no student-sensitive data
no live integrations
no network calls
no APIs
no OAuth
no secrets
no automation
no scheduler implementation
no notifications
no image processing
no wallpaper/photo curator implementation
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not remove existing status checks
```

## What This PR Does Not Implement

- This PR improves project memory clarity only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Commands Reference

```bash
bin/chief-of-staff --project-memory-cleanup-status
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --dashboard
bash scripts/project-memory-cleanup-status.sh
```
