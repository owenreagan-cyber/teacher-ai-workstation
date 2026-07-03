# Gemini — Discovery & Classification Architecture Intake

Last updated: 2026-07-03

```text
Status: external_planning_reference_only
Source: Gemini memo — "Discovery & Classification Architecture: Local-First Teacher AI Workstation"
Closure: complete_gemini_discovery_classification_intake
Authority: not repo authority — classification only
Implementation: none authorized by this document
Owen approval: not granted by filing this intake
```

## Purpose

Classify themes from an external Gemini planning memo about **discovery and classification architecture** for a local-first Teacher AI Workstation. This intake summarizes and maps memo ideas to existing repo lanes — it does **not** ingest the memo into runtime, copy curriculum content, or activate discovery/classification engines.

## Source Posture

| Property | Value |
| --- | --- |
| Source type | External planning memo (Gemini) |
| Filed in repo | Classification summary only — full memo text not committed |
| Repo authority | No — see `docs/proposals/ideas/external-planning-input-intake-map.md` |
| Implementation approval | No — see `docs/implementation-approval-gate.md` |

## Classification Key

Same key as `docs/proposals/ideas/external-planning-input-intake-map.md`:

| Classification | Meaning |
| --- | --- |
| existing repo lane | Already covered by merged docs, status scripts, or governance |
| proposal candidate | Safe to record for future discovery; no runtime |
| blocked / needs Owen decision | Requires explicit Owen mission or architecture choice |
| duplicate | Overlaps existing lane without new evidence |
| out of scope | Forbidden or non-workstation boundary |
| insufficient repo evidence | Memo mentions capability with no repo anchor yet |

## Memo Theme Classification

Architectural themes commonly present in discovery/classification memos, classified against current repo state:

| Memo theme | Classification | Repo anchor / notes |
| --- | --- | --- |
| Local-first, human-reviewed posture | existing repo lane | `docs/engineering-constitution.md`; local-first foundation plans |
| Discovery ≠ implementation banner | existing repo lane | `docs/cursor-operating-modes-and-approval-gates.md`; `--cursor-operating-modes-status` |
| Three-level discovery governance (L1/L2/L3) | existing repo lane | Operating modes § Three-Level Discovery; proposal ledger |
| External planning intake classification | existing repo lane | This doc + `external-planning-input-intake-map.md` |
| Proposal ledger + lane reviews | existing repo lane | `docs/proposals/index.md`; 15 lane reviews |
| Curriculum metadata vs content boundary | existing repo lane | `docs/curriculum-source-readiness-and-intake-boundary-plan.md` |
| A4–A7 resource/source/review/lesson-link contracts | existing repo lane | Metadata contract schemas; fake fixtures enriched |
| Production registry metadata labels (manual) | existing repo lane | Parked registry; one governed record; Option D |
| Chief of Staff intake quarantine workflow | existing repo lane | `assistant/intake/`; intake review workflow |
| Safe local document indexing (planning) | existing repo lane | `docs/safe-local-document-indexing-plan.md` — indexing blocked |
| Classroom utility app discovery (planning) | existing repo lane | `docs/classroom-utility-app-candidate-matrix.md` |
| Presentation / renderer planning labels | existing repo lane | Presentation Engine renderer-foundation planning |
| Gemini as manual curriculum-architecture tool | existing repo lane | `docs/ai-tool-routing-matrix.md` — manual browser only |
| Unified discovery orchestrator service | insufficient repo evidence | No repo-backed orchestrator; memo-only concept |
| Auto-discovery of Drive/NAS/iCloud folders | blocked | Integrations blocked; `docs/integration-planning-foundation-v0.md` |
| Folder crawling / filesystem watchers | blocked | Constitution; document indexing plan blocks scanning |
| OCR / PDF text extraction for classification | blocked | Hard boundary — not approved |
| Embeddings / vector DB / RAG classification | blocked | Constitution; indexing plan blocks embeddings |
| AI auto-labeling of real curriculum files | blocked | Real curriculum ingestion + AI generation blocked |
| Auto-promotion of classified items to production registry | blocked | Registry parked; no writer/`--write` |
| Student roster / grade / behavior classification | blocked | Student-data absolute prohibition |
| Gemini API / OAuth routing for classification | blocked | Cloud API routing inactive |
| Live classification schema activation | blocked pending Owen decision | Inactive A4–A7 samples only |
| Per-source discovery agents (one per integration) | proposal candidate | Record in ledger if Owen wants architecture review |

## Overlap With Existing External Intake

| Prior external idea | Relation to Gemini memo |
| --- | --- |
| Classroom utility apps | Memo may mention classroom tools — covered by `docs/classroom-utility-app-candidate-matrix.md` |
| Presentation Engine | Memo may mention slide/resource display — planning complete, runtime blocked |
| Resource Registry | Memo classification maps to Curriculum Builder registry lanes — not new authority |
| Email Responder | out of scope — remains blocked |

## Safe Repo Actions Allowed From This Intake

- Maintain this classification doc and summary fixture
- Cross-link from external intake map and proposal ledger
- File blocked runtime themes under `docs/proposals/blocked/gemini-discovery-classification-runtime-boundaries.md`
- Record proposal candidates in ledger (max five per intake rule)

## Blocked Actions

- Implementing discovery crawlers, classifiers, parsers, or orchestrators
- Reading real curriculum files or student data for classification experiments
- Activating Gemini API or any network classification pipeline
- Mutating production registry based on memo suggestions

## Recommended Next Missions (Ranked)

1. **Whole-system coherence maintenance** — safest; no runtime risk
2. **Safe local document indexing planning refinement** — if Owen wants indexing scope doc only
3. **Owen architecture decision** — unified discovery orchestrator vs lane-specific status only
4. **Blocked** — any runtime discovery/classification implementation without explicit mission

## Proof

```bash
bin/chief-of-staff --gemini-discovery-classification-intake-status
bash tests/gemini-discovery-classification-intake-status-test.sh
```

## Non-Activation

`complete_gemini_discovery_classification_intake` is a documentation closure marker only. Filing this intake does not approve Gemini API use, automated discovery, or real curriculum classification.
