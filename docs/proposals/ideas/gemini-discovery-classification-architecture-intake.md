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

Classify themes from the external Gemini planning memo about **discovery and classification architecture** for a local-first Teacher AI Workstation. This intake maps memo ideas to existing repo lanes — it does **not** ingest real curriculum, activate discovery/classification engines, or create schemas.

## Source Posture

| Property | Value |
| --- | --- |
| Source type | External planning memo (Gemini) |
| Filed memo | `docs/external-planning/discovery-classification-memo.md` (guardrail header present) |
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

Themes from the filed memo (`docs/external-planning/discovery-classification-memo.md`), classified against current repo state:

| Memo theme | Classification | Repo anchor / notes |
| --- | --- | --- |
| External planning input boundary banner | existing repo lane | Memo §1; intake map; implementation gate |
| Three workflow lanes (curriculum design, asset management, admin text) | existing repo lane | Lesson planning, curriculum builder, capability map lanes |
| Static template / blueprint planning (no generation) | existing repo lane | Lesson brief/draft helpers; planning-only posture |
| "Clean Markdown" formatting pain point | proposal candidate | Manual template planning note — no parsers |
| High-friction metadata cataloging pain point | existing repo lane | Curriculum Source Readiness; A4–A7 contracts; fake fixtures |
| Static metadata field ideas (`asset_domain`, `pedagogical_layer`, etc.) | proposal candidate | Field ideas only — not schemas, keys, or validators |
| Markdown frontmatter planning note | proposal candidate | Memo §6 — no schema/validator/fixture activation |
| Empty static UI wireframe layouts | proposal candidate | Planning-only wireframes — no runtime UI |
| Refining metadata field list (elementary coverage) | existing repo lane | Safe planning-only per memo §6 |
| Manual tagging / naming convention guidelines | existing repo lane | Manual metadata boundary docs; Owen checklist |
| Local-first, human-reviewed posture | existing repo lane | Engineering constitution |
| Three-level discovery governance | existing repo lane | Cursor operating modes |
| A4–A7 resource/source contracts | existing repo lane | Registry metadata contracts; enriched fixtures |
| Production registry manual metadata (parked) | existing repo lane | One governed record; Option D |
| Safe local document indexing (planning) | existing repo lane | `docs/safe-local-document-indexing-plan.md` — indexing blocked |
| Student data (rosters, grades, IEP, behavior) | blocked — absolute | Memo §5; student-data gates |
| Real curriculum ingestion / copied content | blocked | Memo §5; intake boundary plan |
| Drive/NAS/iCloud/Canvas access | blocked | Integration planning foundation |
| API/OAuth/network | blocked | Constitution |
| File/folder scanning, OCR | blocked | Document indexing plan; memo §5 |
| Embeddings / RAG | blocked | Constitution; memo §5 |
| AI generation / runtime behavior | blocked | Implementation gate; memo §5 |
| Local model / Ollama execution | blocked | Local LLM readiness plan — no inference |
| Production registry writes / `--write` | blocked | Parked registry; sentinel |
| Technical directory tree for text assets | blocked pending Owen decision | Memo §6 — architecture choice required |
| LMS sync protocols | blocked | Integrations blocked |
| Ollama controller / parsing / generation scripts | blocked | Memo §6 runtime section |

## Overlap With Existing External Intake

| Prior external idea | Relation to Gemini memo |
| --- | --- |
| Classroom utility apps | Admin/routine text lane adjacent — CAL templates exist |
| Presentation Engine | Asset display planning — renderer foundation complete |
| Resource Registry | Asset management lane maps to Curriculum Builder registry |
| Email Responder | Admin text lane — remains blocked |

## Safe Repo Actions Allowed From This Intake

- Maintain filed memo, classification doc, and summary fixture
- Cross-link from external intake map and proposal ledger
- File blocked runtime themes under `docs/proposals/blocked/gemini-discovery-classification-runtime-boundaries.md`
- Record proposal candidates in ledger (max five per intake rule)

## Blocked Actions

- Converting field ideas into active schemas, validators, fixtures, or parsers
- Implementing discovery crawlers, classifiers, or orchestrators
- Reading real curriculum files or student data
- Activating Gemini API or network classification pipelines
- Mutating production registry based on memo suggestions

## Recommended Next Missions (Ranked)

1. **Whole-system coherence maintenance** — safest; no runtime risk
2. **Markdown frontmatter planning note (proposal only)** — if Owen wants a docs-only candidate
3. **Owen architecture decision** — directory tree layout for manual text assets
4. **Blocked** — any runtime discovery/classification or schema activation

## Proof

```bash
bin/chief-of-staff --gemini-discovery-classification-intake-status
bash tests/gemini-discovery-classification-intake-status-test.sh
```

## Non-Activation

`complete_gemini_discovery_classification_intake` is a documentation closure marker only. Filing this intake does not approve Gemini API use, automated discovery, metadata schemas, or real curriculum classification.
