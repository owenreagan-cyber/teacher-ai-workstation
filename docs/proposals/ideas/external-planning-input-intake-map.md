# External Planning Input Intake Map

Last updated: 2026-07-03

```text
Status: planning_reference_only
Authority: not repo authority — classify only
Implementation: none authorized by this document
```

## Purpose

Classify external planning ideas (Gemini, NotebookLM, ChatGPT transcripts, pasted memos) as planning references only. External input is **not** Owen approval and **not** implementation authority.

## Rules

- Summarize and classify only — do not ingest real curriculum
- Do not inspect connected workspace folders or school directories
- Do not implement runtime/product behavior from external planning
- Maximum five new proposal ledger entries per intake unless Owen approves larger intake

## Classification Key

| Classification | Meaning |
| --- | --- |
| existing repo lane | Already covered by roadmap, capability map, or program lane |
| proposal candidate | Safe to record in ledger for future discovery |
| blocked / needs Owen decision | Requires Owen product/architecture decision |
| duplicate | Overlaps existing doc or lane |
| out of scope | Not Teacher Workstation core or forbidden boundary |
| insufficient evidence | Mentioned externally but no repo anchor |

## Example External Lanes (from planning prompts)

| External Idea | Classification | Repo Anchor / Notes |
| --- | --- | --- |
| Presentation Engine | implemented (planning) | `docs/presentation-engine-renderer-foundation.md`; `--presentation-engine-renderer-foundation-status`; runtime blocked |
| Resource Registry | existing repo lane | Curriculum Builder Registry v0/v0.2, authority map, CB-IMPL |
| Email Responder | out of scope | Parent communication / email workflows blocked |
| UA Noise Meter | proposal candidate | Classroom app lane family — CAL1/G1 adjacent; no app built |
| Classroom Arcade | proposal candidate | Classroom App Lab CAL1 planning surface only |
| Prize Board System | proposal candidate | Classroom engagement app — planning only |
| Spelling Studio | proposal candidate | Curriculum-adjacent app idea — no implementation |
| ClassPass App | proposal candidate | Classroom ops app — blocked until explicit mission |
| Smart Seating App | proposal candidate | Classroom ops app — blocked until explicit mission |
| UA Jobs Management | proposal candidate | Classroom jobs/workflow app — planning only |
| Coin Store Ledger | proposal candidate | Classroom economy app — student-data risk if real; blocked |
| Gemini discovery/classification architecture memo | implemented (intake) | `docs/proposals/ideas/gemini-discovery-classification-architecture-intake.md`; `--gemini-discovery-classification-intake-status`; runtime blocked |

## Gemini Memo Intake (2026-07-03)

External memo title: **Discovery & Classification Architecture: Local-First Teacher AI Workstation**.

| Outcome | Location |
| --- | --- |
| Theme classification | `docs/proposals/ideas/gemini-discovery-classification-architecture-intake.md` |
| Blocked runtime boundaries | `docs/proposals/blocked/gemini-discovery-classification-runtime-boundaries.md` |
| Summary fixture (metadata only) | `assistant/external-planning/intake/gemini-discovery-classification-architecture-summary.json` |
| Status proof | `bin/chief-of-staff --gemini-discovery-classification-intake-status` |

Full memo text is **not** committed to the repo. Filing this intake does not authorize discovery crawlers, classification engines, or Gemini API use.

## Safe Repo Actions from External Input

- Extract metadata-field ideas into fake schemas (this sprint)
- File blocked items under `docs/proposals/blocked/`
- File candidates under `docs/proposals/ideas/`
- Cross-link from ledger when high-value

## Non-Activation

This map does not authorize building listed apps, integrations, or intake pipelines.
