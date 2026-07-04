# Curriculum Library File Classification Approval Gate

Last updated: 2026-07-04

```text
Status: planning-only — gate documentation only
Auto-classification runtime: blocked
AI/OCR/embeddings classification: blocked
Student data: blocked — absolute
Proof: assistant/curriculum-library/samples/fake-classification-suggestion.json
```

## Purpose

Establish the approval gate before **any** runtime that suggests or applies file classifications in the Curriculum Library — whether rule-based, AI-assisted, or integration-driven.

## Gate Levels

| Level | State | Meaning |
| --- | --- | --- |
| 0 | Unclassified | Default; no suggestion applied |
| 1 | Suggestion only | Fake/local fixture or future read-only suggest — **no write** |
| 2 | Owen reviewed | Human confirmed classification |
| 3 | Registry linked | Row updated in manual registry (future manual mission) |

**Current repo state: Level 0–1 planning fixtures only.**

## Allowed Now (This Mission)

- Fake classification suggestion JSON with `fake_local_planning_only`
- Documentation of gate rules
- Status script verification that no classification runtime exists

## Blocked Until Owen Approves Separate Mission

```text
Automatic file type detection on real folders
MIME sniffing / content parsing of real curriculum files
Gemini/ChatGPT/NotebookLM classification of real files
OCR or embeddings on real documents
Applying suggestions without human review
Writing classifications to live registry without approval
```

## Suggestion Fixture Rules

`assistant/curriculum-library/samples/fake-classification-suggestion.json` must:

- Use fictional file ids and placeholder paths
- Set `"repo_authority": false`
- Set `"runtime_approved": false`
- Include `"classification_status": "suggestion_planning_only"`

## Owen Decision Required For

- Any script that reads real files outside approved fake fixtures
- Any model call for classification
- Any auto-apply of labels to registry CSV

## Non-Activation

Gate documentation and fake suggestion fixture only. PASS on status does not authorize classification runtime.
