# Classroom Utility App Planning Priority — Owen Decision Packet

Last updated: 2026-07-03

```text
Status: decision packet — not Owen approval
Classification: prioritization prep — does not implement runtime behavior
Master inventory: docs/app-ecosystem-inventory-and-prototype-build-list.md (52 apps — authoritative scope)
Legacy 9-app matrix: docs/classroom-utility-app-candidate-matrix.md (templates built)
Templates: docs/classroom-utility-templates/ (complete)
Current default posture: Owen selected Classroom Timer & Stopwatch for planning lane only; runtime blocked
Classroom utility app runtime: blocked
```

## Owen Selection (Planning Lane Only)

Owen selected **Classroom Timer & Stopwatch** (Tier 1) for the first single-app planning lane. See `docs/classroom-utilities/classroom-timer-stopwatch-planning.md`. **Runtime implementation is not approved.**

## Purpose

Help Owen choose **which per-app planning lane** to build next from the **full 52-app ecosystem inventory**. The earlier 9-app summary below was **incomplete** — it remains valid for apps with existing planning templates but is **superseded for priority decisions** by the master inventory.

**This packet does not choose a priority for Owen.**

## Master Inventory Cross-Link

| Resource | Role |
| --- | --- |
| `docs/app-ecosystem-inventory-and-prototype-build-list.md` | **52 canonical apps**, deduplicated aliases, risk tiers 1–7 |
| `bin/chief-of-staff --app-ecosystem-inventory-status` | Read-only proof all 52 concepts represented |
| Tier 1 safest candidates | Timer, Bingo, Desk Layout, Schedule Card, Pyramid, Word Scramble, Code Cracker, Curtain Game, Classroom Arcade, Note-Taking Prompt Engine, iPad Optimizer |

Owen should select from the **full inventory tiers**, not only the 9 template apps.

## Legacy 9-App Template Summary (Subset — Not Exhaustive)

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

## Suggested Planning-First Tiers (Owen Chooses — See Full Inventory)

| Tier | Scope | Examples from 52-app inventory |
| --- | --- | --- |
| Tier 1 (safest) | Fake labels / wireframes only | Timer, Bingo, Desk Layout, Pyramid, Trivia Showdown, iPad Optimizer |
| Tier 2 | Careful boundaries | Noise Meter, Charades, Trivia Showdown, Morning Preview Banner |
| Tier 3 | Owen decision needed | Spelling Studio, Shurley tools, Power Up Packet Maker |
| Tier 4 | Student/behavior/grade risk | ClassPass, Smart Seating, GradeMate, Reading Test Maker |
| Tier 5 | API/integration/generation | Canvas Creator, Thales Academic OS, Canvas Link Extractor |

Full tier definitions: `docs/app-ecosystem-inventory-and-prototype-build-list.md`

## What Each Approval Would Allow

| If Owen selects… | Approved follow-on | Still blocked |
| --- | --- | --- |
| Any single candidate from inventory | One per-app **planning** mission (fake fixtures) | App runtime, student data, integrations |
| Tier 1 candidate | Safest next planning mission template | Live data binding |
| Email Responder | Boundary/docs mission only | CAL1 runtime, email API |
| None (defer) | Continue other docs/status lanes | All app runtime |

## Blocked Runtime / Product Writes

```text
classroom utility app runtime
student data in apps
LMS/email/API integrations
real curriculum in apps
CAL1 zip parse/execute
databases / Firebase / Supabase
OCR / camera / microphone / WebRTC
AI generation / local models
```

## What PASS Does Not Mean

- Does **not** approve app implementation
- Does **not** authorize student-facing apps
- Does **not** choose priority for Owen
- Does **not** implement runtime behavior

## Owen Decision Required

Owen must name one canonical app from the **52-app inventory** (or defer) before a per-app planning mission prompt proceeds.
