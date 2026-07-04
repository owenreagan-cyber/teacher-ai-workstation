# External Builder Trial — Owen Decision Packet

Last updated: 2026-07-03

```text
Status: decision packet — not Owen approval
Classification: trial posture prep — does not implement runtime behavior
Governance authority: docs/agent-builder-compatibility-and-external-tool-governance.md
Chief of Staff launches external agents: blocked
Tool installation: blocked
Current default posture: Cursor primary; all trials blocked until Owen chooses
```

## Purpose

Help Owen decide whether and how to trial external AI builders beyond Cursor, using the agent-builder governance program. Trials remain **manual, mission-scoped, and outside Chief of Staff runtime**.

**This packet does not choose a trial for Owen.**

## Option Comparison

### Keep Cursor Only (Current Default)

| Dimension | Detail |
| --- | --- |
| Allows | Cursor as sole repo implementation builder |
| Does not allow | CoS launching other agents |
| Risk | **Low** |
| Proof | PR + dashboard + validate-all per mission |
| Follow-on | Continue standard Cursor missions |

### Trial Google Antigravity (Tier 2 — Stop at PR)

| Dimension | Detail |
| --- | --- |
| Would allow (if Owen approves trial mission) | Manual Antigravity session; repo edits via PR only |
| Would not allow | CoS invocation, API wiring, unattended runs |
| Risk | **Medium** — boundary drift vs Cursor workflow |
| Proof | `docs/agent-builder-safe-tool-trial-checklist.md` + mission proof template |
| Follow-on | "Antigravity Tier-2 Trial Mission (PR-only)" |

### Trial Claude Code (Repo-Connected, If Available)

| Dimension | Detail |
| --- | --- |
| Would allow | Focused repo-connected implementation trials |
| Would not allow | CoS launch, policy decisions without Owen |
| Risk | **Medium** |
| Proof | PR + validation stack |
| Follow-on | "Claude Code Repo-Connected Trial Mission" |

### Trial Codex (Repo-Connected Only)

| Dimension | Detail |
| --- | --- |
| Would allow | Narrow code implementation/review tasks |
| Would not allow | Autonomous multi-lane execution |
| Risk | **Medium** |
| Proof | PR + targeted tests |
| Follow-on | "Codex Focused Implementation Trial Mission" |

### Gemini — Planning-Only (No Trial Change)

| Dimension | Detail |
| --- | --- |
| Posture | Remains planning-only (curriculum architecture) |
| Would not allow | Repo writes as source of truth, API |
| Risk | **Low** if kept planning-only |
| Proof | External planning intake classification |
| Follow-on | Planning memos only |

## Cross-Links

| Document | Role |
| --- | --- |
| `docs/agent-builder-compatibility-and-external-tool-governance.md` | Builder classification |
| `docs/agent-builder-safe-tool-trial-checklist.md` | Trial staging checklist |
| `docs/agent-builder-mission-proof-template.md` | Mission proof format |
| `docs/proposals/blocked/agent-builder-external-tool-runtime-boundaries.md` | Blocked runtime summary |
| `docs/ai-tool-routing-matrix.md` | Tool routing matrix |

## Blocked Runtime / Product Writes

```text
Chief of Staff launching external agents
tool installation / probing
API/OAuth/network from CoS
unattended external agent runs
student data in external tool prompts
```

## What PASS Does Not Mean

- Does **not** install Antigravity, Claude Code, or Codex
- Does **not** invoke external agents from Chief of Staff
- Does **not** implement runtime behavior

## Owen Decision Required

Owen must approve a specific trial mission (or affirm Cursor-only) before any external builder trial proceeds.
