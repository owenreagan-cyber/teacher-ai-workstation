# Owen Architecture Decision Packets

Last updated: 2026-07-03

```text
Status: documentation/status only
Closure: complete_owen_architecture_decision_packets_program
Classification: Owen decision prep — not implementation approval
Proof: bin/chief-of-staff --owen-architecture-decision-packets-status
Chief of Staff chooses options for Owen: no
Production registry writes: blocked
Runtime/product activation: blocked
```

## Purpose

Collect **repo-backed decision packets** for blocked gates that require Owen's explicit choice. Each packet compares options, documents risks and safety boundaries, and states what would be approved **if** Owen selects an option — **without making the decision for Owen. Chief of Staff does not choose options for Owen.**

**PASS on status commands proves documentation coherence only — not Owen approval or runtime activation.**

## Decision Packet Index

| # | Decision | Packet | Status | Owen decision required? | Current default posture |
| --- | --- | --- | --- | --- | --- |
| 1 | Production registry next gate | `docs/proposals/blocked/production-registry-options-decision-packet.md` | ready for review | **yes** | **Option D — parked** (1 record, sentinel intact, no `--write`) |
| 2 | Manual text asset directory layout | `docs/proposals/blocked/manual-text-asset-directory-layout-decision-packet.md` | ready for review | **yes** | **Option 4 — defer** (no layout chosen) |
| 3 | Classroom utility app planning priority | `docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md` | ready for review | **yes** | Owen selected **Classroom Timer & Stopwatch** for planning lane only; runtime blocked |
| 4 | External builder trial | `docs/proposals/blocked/external-builder-trial-decision-packet.md` | ready for review | **yes** | Cursor primary; trials blocked until Owen chooses |
| 5 | Local LLM / Ollama posture | `docs/proposals/blocked/local-llm-ollama-decision-packet.md` | ready for review | **yes** | blocked/inactive — no probing, no inference |
| 6 | Drive / NAS / iCloud / Canvas integration | `docs/proposals/blocked/drive-nas-icloud-canvas-integration-posture-decision-packet.md` | ready for review | **yes** | no access, no API/OAuth, no scanning |

## Canonical Deep References

| Topic | Existing authority (do not duplicate) |
| --- | --- |
| Production registry Options A–D detail | `docs/curriculum-builder-production-registry-next-gate-decision-packet.md` |
| Agent builder classification | `docs/agent-builder-compatibility-and-external-tool-governance.md` |
| Classroom utility candidate matrix | `docs/classroom-utility-app-candidate-matrix.md` |
| App ecosystem inventory (52 apps) | `docs/app-ecosystem-inventory-and-prototype-build-list.md` |
| Classroom Timer & Stopwatch planning | `docs/classroom-utilities/classroom-timer-stopwatch-planning.md` (Owen selected — planning only) |
| Gemini directory-tree blocker | `docs/external-planning/discovery-classification-memo.md` §6 |
| Local LLM boundaries | `docs/local-llm-non-activation-boundaries.md` |
| Canvas LLM planning capstone | `docs/canvas-llm-planning-foundation-capstone.md` |

## What Remains Blocked (All Packets)

| Boundary | State |
| --- | --- |
| Owen's architecture choices | **Owen-owned** — packets do not choose |
| Production registry writes | blocked |
| Active `--write` / writer scripts | blocked |
| Second production record | blocked |
| Schema / validator / parser activation | blocked |
| Real curriculum ingestion / copied content | blocked |
| Student data | blocked — absolute |
| Drive / NAS / iCloud / Canvas access | blocked |
| API / OAuth / network | blocked |
| File / folder scanning | blocked |
| Local LLM / Ollama execution | blocked |
| External agent launch from Chief of Staff | blocked |
| Classroom utility app runtime | blocked |
| Tool installation / probing | blocked |

## Safe Follow-On Mission Types (After Owen Decides)

| If Owen approves… | Safe next mission shape |
| --- | --- |
| Production registry Option A | Read-only write dry-run design mission only |
| Production registry Option B | Single governed second-record PR with worksheet |
| Production registry Option C | Metadata pilot expansion planning mission |
| Production registry Option D | Continue docs/status lanes; no registry writes |
| Directory layout Option 1–3 | Docs-only layout convention mission; no real folders |
| Classroom utility candidate | Per-app planning mission from `docs/classroom-utility-templates/` or Tier 1 from full inventory |
| External builder trial | Trial mission using `docs/agent-builder-safe-tool-trial-checklist.md` |
| Local LLM posture change | Planning-only boundary update mission; no Ollama run |
| Integration posture change | Planning-only integration boundary mission; no API |

## Proof

```bash
bin/chief-of-staff --owen-architecture-decision-packets-status
bash tests/owen-architecture-decision-packets-status-test.sh
```

## Non-Activation

`complete_owen_architecture_decision_packets_program` is a documentation closure marker only. No option is selected for Owen. No runtime, registry write, integration, or tool execution is authorized.
