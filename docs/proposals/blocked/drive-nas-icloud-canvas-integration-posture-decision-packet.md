# Drive / NAS / iCloud / Canvas Integration Posture — Owen Decision Packet

Last updated: 2026-07-03

```text
Status: decision packet — not Owen approval
Classification: planning-only — does not implement runtime behavior
Current posture: no access, no scanning, no API/OAuth
Canvas integration status: none
Google Drive integration status: none
Current default posture: remain blocked; manual metadata path before any integration
```

## Purpose

Help Owen choose a **long-term integration posture** without accessing Drive, NAS, iCloud, or Canvas; without API/OAuth; and without folder scanning. Canvas LLM planning is complete as docs-only (`docs/canvas-llm-planning-foundation-capstone.md`).

**This packet does not approve integration for Owen.**

## Current Posture (Verified)

| System | Access | API/OAuth | Scanning | Role |
| --- | --- | --- | --- | --- |
| Google Drive | **blocked** | **blocked** | **blocked** | long-term desire — manual path first |
| NAS | **blocked** | **blocked** | **blocked** | storage/backup concept only |
| iCloud | **blocked** | **blocked** | **blocked** | not active repo input |
| Canvas | **blocked** | **blocked** | **blocked** | inactive until separate mission |

## Option Comparison

### Option 1 — Remain Fully Blocked (Current Default)

| Dimension | Detail |
| --- | --- |
| Allows | Manual copy/paste workflows; planning docs |
| Does not allow | Any automated access |
| Risk | **Low** |
| Follow-on | Decision packets, manual metadata planning |

### Option 2 — Manual Metadata Path First (Drive-First Planning)

| Dimension | Detail |
| --- | --- |
| Would allow | Document how Owen manually references Drive files in metadata (no API) |
| Would not allow | Drive API, folder crawl, OAuth |
| Risk | **Low–medium** |
| Follow-on | "Drive-First Manual Metadata Planning Mission" |

### Option 3 — NAS as Archive/Backup Convention (Docs Only)

| Dimension | Detail |
| --- | --- |
| Would allow | Document NAS backup posture; not repo input |
| Would not allow | NAS mount scanning, sync jobs |
| Risk | **Medium** if confused with curriculum source |
| Follow-on | "NAS Backup Convention Docs Mission" |

### Option 4 — Canvas Integration Mission (Separate Program)

| Dimension | Detail |
| --- | --- |
| Would allow (future explicit mission) | Canvas LLM runtime unfreeze planning |
| Would not allow | Activation from this packet |
| Risk | **High** |
| Follow-on | Separate Canvas API mission with Owen approval |

### Option 5 — Defer All Integration Decisions

| Dimension | Detail |
| --- | --- |
| Allows | Focus on registry parked state + classroom planning |
| Risk | **Low** |
| Follow-on | Other safe lanes |

## Relationship to Manual Text Assets

Gemini memo §6 blocks **technical directory tree** until Owen decides (`docs/proposals/blocked/manual-text-asset-directory-layout-decision-packet.md`). Integration posture should align with directory layout choice — neither is chosen here.

## Blocked Runtime / Product Writes

```text
Drive/NAS/iCloud/Canvas access
API/OAuth/network
folder scanning/indexing
OCR/embeddings/RAG
automated sync
student data export to cloud
```

## What PASS Does Not Mean

- Does **not** access external folders or services
- Does **not** enable API/OAuth
- Does **not** implement runtime behavior

## Owen Decision Required

Owen must select an integration posture option before any integration planning mission proceeds.
