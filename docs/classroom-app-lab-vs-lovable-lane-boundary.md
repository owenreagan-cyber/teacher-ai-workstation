# Classroom App Lab vs Lovable Classroom App Builder — Lane Boundary

Last updated: 2026-07-02

```text
Status: planning_only
Programs: CAL1 (Classroom App Lab) · G1 (Lovable Classroom App Builder)
Classification: boundary documentation — no runtime
```

## Purpose

Clarify the separation between **Classroom App Lab prototype rescue planning (CAL1)** and **Lovable Classroom App Builder read-only planning (G1)**. Both lanes remain documentation/status only.

## CAL1 — Classroom App Lab

| Aspect | Boundary |
| --- | --- |
| Scope | Prototype rescue workflow planning, fake inventory template |
| Inputs | Fake prototype metadata rows only — no zip archives |
| Outputs | Planning docs, status commands, rescue stage taxonomy |
| Runtime | blocked — no app execution |
| LLM/API | blocked |
| Status | `bin/chief-of-staff --classroom-app-lab-status` |

## G1 — Lovable Classroom App Builder

| Aspect | Boundary |
| --- | --- |
| Scope | Lovable integration planning surface |
| Inputs | Planning references only — no Lovable API |
| Outputs | Planning docs, status commands, approval gates |
| Runtime | blocked — no Lovable API calls |
| OAuth/network | blocked |
| Status | `bin/chief-of-staff --lovable-classroom-app-status` |

## Shared Rules

- Both lanes are **read-only planning foundations**
- Neither lane authorizes app generation, deployment, or student-data workflows
- External planning ideas (Classroom Arcade, ClassPass, etc.) remain proposal/blocked until explicit missions
- AI Tool Routing (R0) may reference both lanes in planning matrices only

## Cross-Links

| Document | Role |
| --- | --- |
| `docs/classroom-app-lab-prototype-rescue-foundation.md` | CAL1 closure |
| `docs/lovable-classroom-app-builder-foundation.md` | G1 closure |
| `docs/ai-tool-routing-foundation.md` | R0 routing separation |
| `docs/proposals/lane-reviews/classroom-app-lab-lane-discovery-review.md` | CAL1 Level 2 review |
| `docs/proposals/lane-reviews/lovable-classroom-app-builder-lane-discovery-review.md` | G1 Level 2 review |

## Non-Activation

No zip handling, Lovable API calls, OAuth, network, app execution, generation, or student data.
