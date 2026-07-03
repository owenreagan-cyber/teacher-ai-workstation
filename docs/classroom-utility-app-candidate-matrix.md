# Classroom Utility App — Candidate Matrix

Last updated: 2026-07-03

```text
Status: planning-only candidate matrix
Classification: prioritization scaffold — not implementation approval
```

## Purpose

Rank and classify classroom utility app **candidates** for future per-app planning or implementation missions. No app in this matrix is built or authorized by this document alone.

## Matrix

| Candidate | Teacher value | Student-data risk | Runtime risk | Integration risk | Safe planning scope | Blocked implementation | Owen decision | Fake fixture | Next mission type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ClassPass | Hall-pass workflow labels | medium if real logs | high | medium (future LMS) | pass label templates | real pass tracking | per-app mission | `example-pass-template` | planning template ready |
| Smart Seating | Layout planning labels | medium if name-seat map | high | low | seat grid labels | live seating assignments | per-app mission | `example-seat-01` | planning template ready |
| Prize Board | Recognition display planning | medium if real names | high | low | reward label placeholders | live point boards | per-app mission | `example-reward-placeholder` | planning template ready |
| Coin Store Ledger | Classroom economy concepts | **high** if real balances | high | low | fake ledger labels only | real student balances | explicit + privacy review | `example-coin-label` | planning only until gate |
| Noise Meter | Engagement monitoring concept | low (aggregate only) | high | low | threshold labels | live mic/sensor automation | per-app mission | `example-noise-level-label` | planning template ready |
| Classroom Arcade | Review game shell planning | low–medium | high | low | game mode labels | executable game runtime | per-app mission | `example-arcade-mode-label` | planning template ready |
| Spelling Studio | Literacy practice shell | medium (curriculum adjacency) | high | low | fake word-list labels | real curriculum ingestion | per-app + curriculum gate | `example-word-list-label` | planning template ready |
| UA Jobs Management | Classroom job rotation labels | medium if roster-linked | high | low | job role labels | roster-linked automation | per-app mission | `example-line-leader` | planning template ready |
| Email Responder | Parent comms concept | **high** | high | **high** (email/API) | blocked intake doc only | any live email | separate program — out of CAL utility runtime | none in fixtures | blocked — not CAL1 runtime |

## Prioritization Notes

1. **Lowest risk planning-first:** Noise Meter (aggregate labels), Classroom Arcade (mode labels without student binding).
2. **Medium scrutiny:** ClassPass, Smart Seating, Prize Board, UA Jobs — fake labels only until Owen selects one for a scoped mission.
3. **High scrutiny:** Coin Store Ledger, Email Responder — student-data or integration gates dominate.
4. **Curriculum adjacency:** Spelling Studio — keep separate from real curriculum ingestion lanes.

## Relationship to CAL1

| Surface | Role |
| --- | --- |
| CAL1 prototype rescue | Zip/parse/execute blocked; planning foundation |
| Per-app templates | `docs/classroom-utility-templates/` |
| Blocked external ideas | `docs/proposals/blocked/classroom-utility-apps-external-ideas.md` |
| Status | `bin/chief-of-staff --classroom-utility-templates-status` |

## Non-Activation

Matrix rows do not authorize implementation. Each app requires explicit Owen mission.
