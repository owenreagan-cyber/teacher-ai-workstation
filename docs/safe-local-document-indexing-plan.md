# Safe Local Document Indexing Plan

## Purpose

This document plans a future safe local document indexing workflow for the Teacher AI Workstation. It defines approval gates, safety boundaries, and phased rollout ideas.

**This PR does not index documents.** It is planning-only.

## Current Status

- Planning document: present
- Read-only status helper: present
- Actual indexing: not implemented
- Folder scanning: not implemented
- Document content reading: not implemented
- Embeddings: not implemented
- Vector database: not implemented
- Connected sources: not implemented

## Safety Boundaries

- Local only
- Read-only planning
- No student-sensitive data
- No real student names
- No grades, behavior, medical, IEP, 504, parent communication, or private student information
- No Gmail
- No Google Drive
- No Google Calendar
- No APIs
- No OAuth
- No secrets
- No LLM calls by default
- No embeddings yet
- No vector database yet
- No school systems
- No publishing, sharing, or sending
- No background scanning
- Human approval required before future indexing

Sensitive student information is excluded by default. Any future indexing must be opt-in and allowlist-based.

## What This Plan Allows Later

Future work may eventually support:

- approved local folders only
- explicit human approval before indexing
- quarantine and review before use
- allowlist-first design
- human-readable index manifests
- phased rollout from inventory to optional metadata and content steps
- separate approval for connected sources

## What This Plan Does Not Implement

This PR does not:

- index documents
- scan folders
- read file contents
- create embeddings
- create a vector database
- connect to Gmail, Drive, Calendar, APIs, OAuth, secrets, or school systems
- run network calls
- run LLM calls
- run background watchers or automatic sync

## Approved Folder Model

Future indexing should use an explicit allowlist of approved local folders.

Rules:

1. Owen approves each folder path before it becomes indexable.
2. Default is no folders approved.
3. Folders containing student-sensitive data should not be approved.
4. Personal, classroom, and business folders should be separated in planning notes.
5. Allowlist changes require explicit human approval and documentation.

## Quarantine and Review Model

Before any indexed material is used by assistant workflows:

1. New or changed files may be held in quarantine conceptually.
2. Human review checks for student-sensitive data and policy fit.
3. Only reviewed material may move to approved context.
4. Rejected material stays out of indexes and assistant context.

This follows the same human-review spirit as intake review and lesson review workflows.

## Index Manifest Concept

A future index manifest should be human-readable and local, for example Markdown or JSON stored in-repo only if Owen explicitly approves.

A manifest may later record:

- approved folder path
- approval date
- reviewer
- allowed file types
- indexing phase enabled
- last inventory run date
- quarantine notes

No manifest writer is implemented in this PR.

## Human Approval Gates

Any future indexing phase requires explicit Owen approval:

1. Approve folder allowlist
2. Approve inventory-only scan
3. Approve metadata-only index
4. Approve content extraction, if ever needed
5. Approve local embeddings, if ever needed
6. Approve connected sources, if ever needed

## Future Phase 1: Read-Only Inventory

Possible future scope:

- list file names and paths in approved folders only
- no content reading
- no hashing beyond optional size/mtime if approved
- output to human-readable manifest
- read-only command with dry-run default

## Future Phase 2: Metadata-Only Index

Possible future scope:

- index filename, path, extension, size, modified date
- no body content extraction
- no OCR
- no PDF parsing
- still allowlist-only and human-approved

## Future Phase 3: Local Content Extraction

Possible future scope:

- extract text from approved local files only
- still no network calls
- still no LLM calls by default
- quarantine/review before use
- explicit approval required

## Future Phase 4: Optional Local Embeddings

Possible future scope:

- optional local embeddings for approved extracted text only
- still no vector database requirement in early drafts
- still no cloud services by default
- separate explicit approval gate

## Future Phase 5: Permissioned Connected Sources

Possible future scope:

- Gmail, Drive, or other connected sources only after separate approved PRs
- capability broker and secrets handling required
- not part of this planning PR

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Hidden background scanning | No watchers; explicit commands only |
| Student-sensitive data exposure | Default deny; quarantine/review; no student data by default |
| Cloud leakage | No network calls in early phases |
| Over-automation | Human approval gates for every phase |
| Unclear scope creep | Phased plan with planning-only baseline |

## Commands Reference

```bash
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --dashboard
bash scripts/document-indexing-plan-status.sh
```

## Future Ideas Not Included

The following are intentionally not part of this PR:

```text
actual indexing
recursive folder scanning
metadata extraction
content extraction
OCR
embedding generation
vector database
connected Gmail/Drive indexing
background file watchers
automatic sync
search UI
```
