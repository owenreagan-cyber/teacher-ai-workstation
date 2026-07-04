# Manual Text Asset Directory Layout — Owen Decision Packet

Last updated: 2026-07-03

```text
Status: decision packet — not Owen approval
Classification: planning-only — does not implement runtime behavior
Source blocker: docs/external-planning/discovery-classification-memo.md §6
Current default posture: Option 4 — defer layout decision
Directory creation outside repo: blocked
NAS/Drive/iCloud/Canvas access: blocked
File/folder scanning: blocked
```

## Purpose

Help Owen choose a **future** convention for manual text asset storage without creating real directories, scanning files, or accessing external storage. Frontmatter **planning** is complete; active schema/validator/parser remains blocked.

**This packet does not choose a layout for Owen.**

## Option Comparison

### Option 1 — Repo-Local Fake / Manual Examples Only

| Dimension | Detail |
| --- | --- |
| Would allow | Fake fixture paths under `assistant/` or `docs/` illustrations only |
| Would not allow | Real curriculum trees, copied textbook content |
| Risk | **Low** — stays in repo fixtures |
| Validation if approved | Planning doc + fake samples; no parser |
| Follow-on mission | "Manual Text Asset Fake Fixture Layout Planning Mission" |

### Option 2 — Local Non-Repo Teacher Workspace Convention (Docs Only)

| Dimension | Detail |
| --- | --- |
| Would allow | Documented folder naming convention on Owen's Mac (docs only) |
| Would not allow | Chief of Staff scanning Owen's filesystem; auto-indexing |
| Risk | **Low–medium** — docs must not imply scanning |
| Validation if approved | Convention doc + boundary tests |
| Follow-on mission | "Teacher Workspace Directory Convention Docs Mission" |

### Option 3 — NAS / Drive / iCloud-Aware Future Plan (No Access)

| Dimension | Detail |
| --- | --- |
| Would allow | Long-term architecture sketch; Drive-first desire documented |
| Would not allow | API/OAuth, folder access, sync, crawling |
| Risk | **Medium** — integration creep if missions blur planning vs API |
| Validation if approved | Integration posture packet update only |
| Follow-on mission | "Drive-First Manual Metadata Path Planning Mission" (no API) |

### Option 4 — Defer Layout Decision (Current Default)

| Dimension | Detail |
| --- | --- |
| Allows | Continue frontmatter planning artifacts; no layout commitment |
| Does not allow | Directory creation missions, schema activation |
| Risk | **Low** |
| Follow-on mission | Other safe docs/status lanes |
| Owen decision | **None required** to defer |

## Safety Boundaries (All Options)

| Boundary | State |
| --- | --- |
| Real curriculum files | blocked |
| Copied curriculum content | blocked |
| Student data | blocked |
| NAS / Drive / iCloud / Canvas access | blocked |
| Folder scanning / indexing | blocked |
| Schema / validator / parser | blocked |
| Production registry writes | blocked |

## What PASS Does Not Mean

- Does **not** create directories outside the repo
- Does **not** scan Owen's local curriculum folders
- Does **not** approve NAS/Drive/iCloud integration
- Does **not** implement runtime behavior

## Owen Decision Required

Owen must select Option 1–4 before any layout convention mission proceeds beyond planning docs.
