# Teacher Knowledge Vault — Human Review Workspace

Last updated: 2026-07-04

Review is a **workspace/inbox**, not a popup.

## Review States

`new_discovery`, `needs_ocr`, `needs_native_extraction`, `needs_classification`, `possible_duplicate`, `possible_version`, `ready_to_organize`, `needs_manual_review`, `approved`, `rejected`, `blocked`, `archived`

## Rules

- No suggestion becomes an operation without teacher approval
- `99_DO_NOT_SCAN` items never enter normal review
- Smart rename suggestions wait for approval

M1 fixture: `assistant/teacher-knowledge-vault/m1/fake-review-queue.json`
