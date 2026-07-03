# Production Registry Sentinel Semantics (Choice A)

Last updated: 2026-07-03

```text
Status: sentinel_semantics_documented
Classification: governance clarification — not write authorization
Sentinel path: assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel
Choice: A — keep sentinel intact
```

## Purpose

Clarify what `BLOCKED-NO-WRITES.sentinel` means **after** the first governed production registry record exists. The sentinel remains the authoritative block on automated and unapproved mutation paths.

## What the Sentinel Still Blocks

| Blocked path | Status |
| --- | --- |
| Writer scripts | blocked |
| Active `--write` handler | blocked |
| Batch import | blocked |
| Auto-promotion from fixtures | blocked |
| Unapproved mutation tooling | blocked |
| Sentinel removal without explicit write mission | blocked |

## What the Sentinel Does **Not** Mean (Post–First-Record)

| Misread | Correct state |
| --- | --- |
| Production file must be absent | **Wrong** — sentinel no longer means the production file must be absent; `production-registry.json` exists |
| `records` count must be zero | **Wrong** — sentinel no longer means records count must be zero |
| First manual record forbidden | **Wrong** — one governed PR edit record exists |
| All registry edits forever forbidden | **Wrong** — explicit governed PR prompts may edit metadata |

## What Requires Separate Explicit Prompts

| Action | Gate |
| --- | --- |
| Manual governed PR record edit | separate explicit prompt per record mission |
| Second production record | blocked pending explicit Owen decision |
| Writer / `--write` tooling | blocked pending explicit Owen decision |
| Sentinel removal | blocked pending explicit write-tooling mission |

## Coexistence Model

```text
First governed record exists (records count exactly 1).
BLOCKED-NO-WRITES.sentinel remains intact.
Automated writes remain blocked.
Manual governed PR edits require explicit prompts.
```

## Proof

```bash
bin/chief-of-staff --curriculum-production-registry-first-record-status
bin/chief-of-staff --curriculum-production-registry-governance-status
```

## Non-Activation

This document does not authorize writer scripts, `--write`, a second record, or sentinel removal.
