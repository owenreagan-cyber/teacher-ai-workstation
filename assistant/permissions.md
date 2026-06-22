# Permissions Model

The Chief of Staff starts with minimal access and earns access through explicit grants.

## Permission levels

| Level | Name | Meaning |
| --- | --- | --- |
| Level 0 | No external access | The assistant uses only the current conversation and committed docs. |
| Level 1 | User-selected files only | Owen provides or selects exact files for this task. |
| Level 2 | Approved local folders | Owen grants access to specific local folders. |
| Level 3 | Approved Google Drive folders | Later only: selected Drive folders, never all Drive by default. |
| Level 4 | Approved Gmail labels/threads or email exports | Later only: selected labels, threads, or exports, never all inbox by default. |
| Level 5 | Tool actions | Drafting files or emails, always with confirmation before modifying, sending, publishing, or deleting. |

## Grant types

- One-time grant: applies to one request only.
- Session grant: applies until the current session ends.
- Persistent grant: saved permission, inspectable and revocable by Owen.

## Phase 1A rule

Phase 1A starts with Level 0 and Level 1 only.

Drive and Gmail scanning are not allowed until later phases. Full-drive or full-inbox scanning should never be the default.
