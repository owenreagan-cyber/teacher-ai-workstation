# Lovable Classroom App Builder — Non-Activation Boundaries

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Lovable Classroom App Builder — Program G1
Lovable API: blocked
OAuth: blocked
Network calls: blocked
Live app generation: blocked
Automation: no
```

## Purpose

Define hard boundaries for Program G1 and all future Lovable integration work until explicit implementation approval.

## Blocked Now (Program G1 and Default)

| Capability | Status |
| --- | --- |
| Lovable API use | blocked |
| OAuth and credentials | blocked |
| Network calls to Lovable | blocked |
| Live app generation | blocked |
| Classroom app deployment | blocked |
| Student-facing app generation | blocked |
| Automation / background jobs | blocked |
| Student data handling | blocked |
| Chief of Staff becoming Lovable | blocked — architecture rule |

## Allowed Now (Program G1)

- Repo-local documentation and integration planning concepts
- Cross-links to AI Tool Routing matrix and model routing docs
- Deterministic status script reporting planning boundaries
- Chief of Staff read-only status via `--lovable-status`
- Manual browser profile references (paste-only, human-operated)

## Relationship to Other Programs

| Program | Boundary |
| --- | --- |
| Classroom App Lab (CAL1) | Prototype rescue planning — no Lovable connection |
| AI Tool Routing (R0) | Lovable lane documented — no live routing |
| Integration Layer (G) | G1 is first integration planning surface |
| Renderer Foundation | Future contract patterns — no Lovable consume yet |

## Future Stages (Approval-Gated)

| Stage | Requires |
| --- | --- |
| G1 Read-only planning surface | **implemented read-only** |
| G2 Manual link workflows | Explicit approval |
| G3 Read-only integration probes | Explicit approval |
| G4 Write integration | Blocked |
| G5 Automation | Blocked |

Program G1 must not blur into any future stage.
