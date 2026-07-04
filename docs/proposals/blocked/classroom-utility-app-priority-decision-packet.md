# Classroom Utility App Planning Priority — Owen Decision Packet

Last updated: 2026-07-03

```text
Status: decision packet — not Owen approval
Classification: prioritization prep — does not implement runtime behavior
Templates: docs/classroom-utility-templates/ (complete)
Candidate matrix: docs/classroom-utility-app-candidate-matrix.md
Current default posture: no app selected for next mission
Classroom utility app runtime: blocked
```

## Purpose

Help Owen choose **which per-app planning lane** to build next from the candidate matrix. Per-app mission templates exist; **no app runtime** is authorized by this packet.

**This packet does not choose a priority for Owen.**

## Candidate Summary

| Candidate | Safe planning-only | Student-data risk | Runtime app risk | Integration risk | Best next docs/status mission | Blocked work |
| --- | --- | --- | --- | --- | --- | --- |
| **Noise Meter** | yes (aggregate labels) | low | high | low | Extend planning template + fake fixtures | live mic/sensor automation |
| **Classroom Arcade** | yes (mode labels) | low–medium | high | low | Per-app planning mission | executable game runtime |
| **ClassPass** | yes (pass label templates) | medium if real logs | high | medium (future LMS) | Per-app planning mission | real pass tracking |
| **Smart Seating** | yes (seat grid labels) | medium if name-seat map | high | low | Per-app planning mission | live seating assignments |
| **Prize Board** | yes (reward placeholders) | medium if real names | high | low | Per-app planning mission | live point boards |
| **UA Jobs Management** | yes (job role labels) | medium if roster-linked | high | low | Per-app planning mission | roster-linked automation |
| **Spelling Studio** | partial (fake word labels) | medium (curriculum adjacency) | high | low | Planning mission + curriculum gate doc | real curriculum ingestion |
| **Coin Store Ledger** | partial (fake labels only) | **high** if real balances | high | low | Planning-only until privacy review | real student balances |
| **Email Responder** | blocked intake only | **high** | high | **high** (email/API) | Not CAL1 runtime — separate program | any live email |

## Suggested Planning-First Tiers (Owen Chooses)

| Tier | Candidates | Notes |
| --- | --- | --- |
| Lowest risk | Noise Meter, Classroom Arcade | Aggregate/mode labels without student binding |
| Medium scrutiny | ClassPass, Smart Seating, Prize Board, UA Jobs | Fake labels only until scoped mission |
| High scrutiny | Coin Store Ledger, Email Responder | Privacy/integration gates dominate |
| Curriculum adjacency | Spelling Studio | Keep separate from real curriculum lanes |

## What Each Approval Would Allow

| If Owen selects… | Approved follow-on | Still blocked |
| --- | --- | --- |
| Any single candidate | One per-app **planning** mission from template | App runtime, student data, integrations |
| Email Responder | Boundary/docs mission only | CAL1 runtime, email API |
| None (defer) | Continue other docs/status lanes | All app runtime |

## Blocked Runtime / Product Writes

```text
classroom utility app runtime
student data in apps
LMS/email/API integrations
real curriculum in apps
CAL1 zip parse/execute
```

## What PASS Does Not Mean

- Does **not** approve app implementation
- Does **not** authorize student-facing apps
- Does **not** implement runtime behavior

## Owen Decision Required

Owen must name one candidate (or defer) before a per-app planning mission prompt proceeds.
