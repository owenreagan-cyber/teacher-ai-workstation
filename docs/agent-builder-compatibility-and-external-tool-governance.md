# Agent Builder Compatibility and External Tool Governance

Last updated: 2026-07-03

```text
Status: documentation/status only
Closure: complete_agent_builder_compatibility_governance_program
Classification: permanent governance reference — not implementation approval
Chief of Staff launches external agents: blocked
Tool integrations/API/OAuth: blocked
Production registry writes: blocked
Student data: blocked — absolute
```

## Purpose

Define how **external AI builder tools** may help Owen build the Teacher AI Workstation without becoming unsafe runtime dependencies. Chief of Staff and future agents use this program to classify tools, required proof, and preserved boundaries.

**This document does not install tools, invoke external agents, or authorize API/OAuth/network flows.**

## Relationship to Prior Governance

| Document | Role |
| --- | --- |
| `AGENTS.md` | Repo-wide agent quick-start |
| `docs/ai-tool-routing-matrix.md` | Tool routing matrix (R0) — who does what |
| `docs/cursor-operating-modes-and-approval-gates.md` | Cursor autonomous execution boundaries |
| `docs/implementation-approval-gate.md` | Repo-wide implementation gate |
| `docs/proposals/ideas/external-planning-input-intake-map.md` | External planning classification |
| `docs/agent-builder-safe-tool-trial-checklist.md` | Safe trial staging |
| `docs/agent-builder-mission-proof-template.md` | Builder mission proof format |

## Builder Role Classification

| Tool | Classification | CoS may launch? | Network/API | Proof required |
| --- | --- | --- | --- | --- |
| **Cursor** | approved external builder (repo-local) | **no** — Owen/Cursor IDE only | local repo work | PR + dashboard + validate-all |
| **ChatGPT** | planning / review / mission prompts | **no** | manual browser only | mission prompt + classification |
| **Gemini** | planning-only (curriculum architecture) | **no** | manual browser only | external intake classification doc |
| **Claude** (browser) | planning / long-form review | **no** | manual browser only | planning reference only |
| **Codex** | experimental focused code builder | **no** | local CLI optional | PR + validation when used for repo |
| **Claude Code** | experimental agentic builder | **no** | blocked until mission | trial checklist + Owen approval |
| **Google Antigravity** | experimental agentic builder | **no** | blocked until mission | trial checklist + Owen approval |
| **Lovable** | blocked app builder (G1) | **no** | blocked | mission approval gate |
| **Future agentic tools** | experimental until classified | **no** | blocked default | trial checklist + ledger row |

**Chief of Staff never launches Cursor, Antigravity, Codex CLI, Claude Code, Gemini CLI, or any external agent.** CoS verifies repo state via read-only status commands only.

## Full Autonomous Run Approval Scope

When a mission grants **full autonomous run approval**, that approval applies to:

| Approved | Not approved |
| --- | --- |
| Repo-local docs/status/tests/scripts | Runtime product behavior |
| Read-only status commands | Tool install or invocation |
| PR lifecycle on feature branches | API/OAuth/network |
| Dashboard/validate-all proof | Production registry writes |
| Roadmap/coherence updates | Student data workflows |
| | Real curriculum ingestion |
| | AI generation / Ollama execution |

**PASS on status commands proves documentation coherence — not tool activation.**

## Required Proof by Builder Type

| Builder class | Minimum proof |
| --- | --- |
| Cursor repo mission | PR merged; dashboard 0 FAIL; validate-all 0 FAIL; branch deleted |
| External planning memo | Intake classification doc; guardrail header; no runtime |
| Experimental tool trial | Completed trial checklist; Owen decision recorded |
| Planning-only reference | Proposal/backlog row; blocked runtime doc cross-link |

See `docs/agent-builder-mission-proof-template.md` for the standard report format.

## Chief of Staff Role (Read-Only)

| CoS may | CoS must not |
| --- | --- |
| Run `--dashboard`, `--validate-all`, status scripts | Launch external agents |
| Report parked registry state | Invoke Cursor/Antigravity/Codex/Claude Code APIs |
| Cross-link governance docs | Install tools or Mac changes |
| Verify branch/PR/validation proof | Read real curriculum or student data |

## Safe Tool Trial Staging

1. Classify tool in builder table (experimental default)
2. Complete `docs/agent-builder-safe-tool-trial-checklist.md`
3. File planning reference under `docs/proposals/ideas/` if high-value
4. File blocked runtime items under `docs/proposals/blocked/`
5. Owen approves separate implementation mission before any API/network use

## Blocked Capabilities (All External Builders)

| Capability | State |
| --- | --- |
| Chief of Staff agent launch | blocked |
| Tool API/OAuth integration | blocked |
| Automated routing to external tools | blocked |
| Student data in builder prompts | blocked — absolute |
| Real curriculum ingestion | blocked |
| Production registry writes / `--write` | blocked |
| Drive/NAS/iCloud/Canvas access | blocked |
| AI generation runtime | blocked |
| Ollama/local model execution | blocked |

## Proof

```bash
bin/chief-of-staff --agent-builder-compatibility-governance-status
bash tests/agent-builder-compatibility-governance-status-test.sh
```

## Non-Activation

`complete_agent_builder_compatibility_governance_program` is a documentation closure marker only.
