# Owen § J — Production Registry Checklist Review Packet

Last updated: 2026-07-02

```text
Status: owen_review_packet
Audience: Owen Reagan
Classification: product-decision support — not implementation authority
Implementation: blocked until Owen explicitly approves checklist items
```

## Non-Approval Statement (Read First)

```text
Documenting an option does not approve it.
Any checklist item not explicitly approved by Owen remains blocked.
Preparing this packet does not authorize implementation.
Production registry writes are not approved.
Real metadata intake is not approved.
Real curriculum access is not approved.
Student data handling is not approved.
Integrations, APIs, OAuth, scanning, generation, and runtime behavior are not approved.
```

Cursor may maintain docs, status surfaces, and fake fixtures. Only Owen may authorize production registry **implementation** missions.

---

## 1. Current Status Summary

| Surface | Proof | Typical result |
| --- | --- | --- |
| Dashboard | `bin/chief-of-staff --dashboard` | 121 PASS / 0 WARN / 0 FAIL |
| Registry lane aggregate | `bin/chief-of-staff --curriculum-registry-lane-status` | 38 PASS / 0 WARN / 0 FAIL (aggregate script) |
| Owen § J checklist tracker | `bin/chief-of-staff --curriculum-production-registry-owen-checklist-status` | 30 PASS / **1 WARN** / 0 FAIL |
| Curriculum source readiness | `bin/chief-of-staff --curriculum-source-readiness-status` | 45 PASS / 0 WARN / 0 FAIL |
| A4–A7 fixture cross-validation | `bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status` | 17 PASS / **7 WARN** / 0 FAIL |

The **1 WARN** on the Owen checklist command is **expected and non-blocking**. It means **5 checklist items remain `deferred`** (items 1, 2, 3, 4, 10). Governance affirmations for items 5, 6, 7, 8, 9, 11 were recorded 2026-07-02 — **approved governance rows do not authorize production writes**. See `docs/curriculum-builder-registry-expected-warns.md`.

---

## 2. Why the Project Is Owen-Decision-Blocked

Safe-local scaffolding for the Curriculum Builder registry lane is largely complete:

- CB-IMPL-1 dry-run validation (fake candidates only)
- CB-IMPL-2–4 fake fixture records, renderer preview, retrieval hooks
- CB-PROD-PLAN production workflow planning brief
- CB-REG-HARDEN authority map, aggregate lane status, A4–A7 cross-validation
- Curriculum Source Readiness fake metadata inventory (no real intake)
- Owen § J checklist tracker with read-only status proof (PR #216)

**The project has reached a product-decision wall on path, namespace, write behavior, and metadata intake.**

Governance affirmation batch recorded 2026-07-02: items 5, 6, 7, 8, 9, 11 approved. Items 1, 2, 3, 4, 10 deferred. The next high-value step is a **path + namespace decision session** (items 1 and 10). Item 2 (write behavior) remains deferred. Generic autopilot or further docs/status foundations do not unlock production registry work without these decisions.

---

## 3. What PR #216 Completed

PR #216 (Master Build Plan Safe Autopilot) delivered planning/status foundations only:

| Deliverable | Purpose |
| --- | --- |
| Registry lane aggregate includes source readiness + Owen checklist | Single proof surface for CB registry foundations |
| `--curriculum-production-registry-owen-checklist-status` | Read-only tracker: 6 approved, 5 deferred (2026-07-02) |
| Owen checklist tracker doc | Mirrors planning brief § J |
| F1 fake widget/shortcut catalog | Unrelated lane; planning only |
| CAL1 prototype inventory + G1 boundary | Unrelated lane; planning only |
| Dry-run PASS≠promotion banner | Clarifies dry-run does not authorize writes |
| Expected WARN documentation | Owen + A4–A7 WARNs registered |

**PR #216 did not approve any checklist item and did not implement production writes.**

## 3b. What Governance-First Foundation Completed (Post–PR #217)

CB-PROD-GOV (`docs/curriculum-builder-production-registry-governance-foundation.md`) delivers planning brief § I scaffolding:

| Deliverable | Purpose |
| --- | --- |
| `--curriculum-production-registry-governance-status` | Blocked-write proof |
| Candidate path skeleton + sentinel | Manual-only path shape — no records |
| Path options, review states, audit stub, local-first model | Owen decision support |
| Guardrail tests | No writes; no auto-promotion |

**Governance foundation does not approve checklist items or authorize writes.**

## 3c. Decision Readiness (Post–PR #218)

| Deliverable | Purpose |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-decision-worksheet.md` | Owen worksheet + routing |
| `docs/curriculum-builder-production-registry-post-decision-implementation-map.md` | Post-decision mission phases |
| Expanded write-mission preflight | `docs/proposals/backlog/production-registry-write-mission.md` |

## 3d. Governance Affirmation Batch (2026-07-02)

| Batch | Items | Status | Effect |
| --- | --- | --- | --- |
| Approved | 5, 6, 7, 8, 9, 11 | recorded | Governance principles affirmed; CB-PROD-GOV scope acknowledged |
| Deferred | 1, 2, 3, 4, 10 | pending Owen | Path, namespace, writes, metadata intake remain blocked |

**This batch does not authorize production writes, real metadata intake, or integrations.**

---

## 4. What Remains Blocked (Until Owen Approves)

| Category | Blocked today |
| --- | --- |
| Production registry writes | `--curriculum-registry-write` manifest-blocked; no handler |
| Active `--write` | Not implemented |
| Real metadata intake | No real titles, paths, or source labels in registry |
| Real curriculum intake | No file read, copy, parse, summarize, embed, or index |
| Student data | Absolute prohibition |
| Drive / Canvas / NAS / iCloud / API / OAuth / network | Blocked in v1 production workflow |
| Scanning / crawling / OCR / embeddings / RAG | Blocked |
| Generation | Blocked |
| Dry-run → production auto-promotion | Blocked (recommended: stay blocked) |
| v0.2 fixtures as production authority | Blocked — `fake_fixture_only` |

---

## 5. The 11 Checklist Items in Plain Language

| # | Checklist item | Plain English |
| ---: | --- | --- |
| 1 | Production registry path | Where will real records live — extend v0 JSON, new v0.2 production file, or directory of record files? |
| 2 | Write behavior allowed | Is any governed write to a production registry authorized at all? If yes, manual-only only. |
| 3 | Real curriculum metadata allowed | May Owen enter real resource titles/labels (subject, unit, lesson) — metadata only, no file content? |
| 4 | Real source references allowed | May Owen manually label where a resource lives (path/URL text) without auto-fetch or resolution? |
| 5 | Source systems permitted | Which source systems are in scope for v1 — manual entry only, or also labeled Drive/NAS/etc.? |
| 6 | Rollback requirements | Accept snapshot + diff + restore procedure before any future write mission? |
| 7 | Review states | Accept the draft → candidate → validated → teacher_reviewed → approved gate model (or revise)? |
| 8 | Student-data prohibition | Confirm student data remains absolutely prohibited in registry metadata? |
| 9 | Canvas/Drive/NAS/iCloud/API/OAuth/network | Confirm these stay blocked in v1 unless each is separately approved later? |
| 10 | ID namespace | Choose ID pattern for real records (e.g. `owen-*`, `resource-*`, course-prefixed). |
| 11 | First implementation PR scope | Accept governance-only first PR (blocked proof + planning stubs, no write code)? |

Tracker source: `docs/curriculum-builder-production-registry-owen-checklist-tracker.md`  
Planning detail: `docs/curriculum-builder-production-registry-workflow-planning-brief.md`

---

## 6. Recommended Decision Categories

Use these categories when working through the table in § 7:

| Category | Meaning | Owen action |
| --- | --- | --- |
| **Approve now** | Safe governance affirmation or default that does not authorize writes or intake | Mark approved in tracker; no implementation mission yet |
| **Keep blocked** | Must remain off until a separate explicit mission | Affirm blocked; no change needed |
| **Needs more planning** | Architectural/product choice not ready to lock | Defer; optional follow-up planning doc |
| **Governance-first only** | Approving this item authorizes only a future docs/status/guardrails PR | Approve scope pattern; still no writes |
| **Metadata intake later** | Approving this item would eventually allow real metadata — not content — in a later mission | Approve boundary only; separate implementation prompt required |

---

## 7. Owen Decision Table (Work Through Directly)

| Checklist Item | Plain-English Decision | Recommended Default | Risk Level | What Approval Would Authorize | What Remains Blocked |
| --- | --- | --- | --- | --- | --- |
| 1. Production registry path | Choose where production records will live | **Needs more planning** — decide before any write mission | Medium | Future path decision doc + governance PR may reference chosen path | Writes, intake, integrations until path chosen and item 11 approved |
| 2. Write behavior allowed | Is governed production write ever allowed? | **Keep blocked** until items 1, 6, 7, 11 decided | High | Future manual-only write mission (smallest scope) after governance PR | Auto-write, batch import, hidden write paths |
| 3. Real curriculum metadata allowed | May Owen store real titles/labels in registry? | **Metadata intake later** — approve boundary only when ready | Medium | Later mission: Owen-entered metadata fields only | Curriculum content, student data, auto-ingest |
| 4. Real source references allowed | May Owen store manual path/URL labels? | **Metadata intake later** — manual labels only | Medium | Later mission: labeled references Owen types in | Auto-resolution, fetching, copying files |
| 5. Source systems permitted | Which systems are in v1 scope? | **Approve now:** manual entry only; **Keep blocked:** Drive/NAS/iCloud/Canvas/API | Low–Medium | Affirming manual-first does not authorize intake | Each integration needs its own approved mission |
| 6. Rollback requirements | Accept snapshot/diff/restore before writes? | **Approve now** (governance principle) | Low | Future governance PR includes rollback planning stub | Actual write code until item 2 + 11 approved |
| 7. Review states | Accept § D gate model? | **Approve now** or revise in writing | Low | Future workflow docs/tests reference chosen gates | Skipping review gates; auto-promotion |
| 8. Student-data prohibition | Student data absolutely prohibited? | **Approve now** (affirm absolute ban) | Critical if weakened | Stronger audit guardrails in future PRs | Any student names, rosters, grades, accommodations |
| 9. Canvas/Drive/NAS/iCloud/API/OAuth/network | Stay blocked in v1 production workflow? | **Approve now** (keep blocked) | High if opened early | Nothing until separate per-integration missions | All network/integration intake in v1 |
| 10. ID namespace | Choose real-record ID pattern | **Needs more planning** | Low–Medium | Future records use chosen namespace | Writes until namespace chosen |
| 11. First implementation PR scope | First PR is governance-only? | **Governance-first only** — approve § I pattern | Low | Docs/status/negative tests/audit planning stub only | `--write`, real intake, promotion, integrations in first PR |

### Suggested approve-now batch (low risk, no writes)

Owen may safely approve now without authorizing implementation:

1. Item 5 — manual entry only for v1; Drive/NAS/iCloud/Canvas remain blocked
2. Item 6 — rollback requirements accepted as planning requirement
3. Item 7 — review gate model accepted (or Owen supplies revisions)
4. Item 8 — student-data prohibition remains absolute
5. Item 9 — integrations remain blocked in v1 production workflow
6. Item 11 — governance-only first implementation PR scope accepted

Items 1, 2, 3, 4, and 10 still require explicit Owen choices before any write or real-metadata mission.

---

## 8. Approve-Now Candidates (Governance Affirmations Only)

| Item | Why safe to approve now | Does NOT authorize |
| --- | --- | --- |
| 5 — manual first | Matches existing repo posture and source-readiness plan | Drive/API intake |
| 6 — rollback | Planning requirement only | Registry mutation |
| 7 — review states | Workflow model only | Production writes |
| 8 — student-data ban | Absolute safety boundary | Nothing (affirmation) |
| 9 — integrations blocked | Matches engineering constitution | Network/OAuth |
| 11 — governance-first PR | Limits first code mission to guardrails | `--write`, intake |

---

## 9. Keep-Blocked Candidates

| Item / topic | Stay blocked until |
| --- | --- |
| Production writes (`--curriculum-registry-write`) | Items 1, 2, 6, 7, 11 approved + separate implementation mission |
| Real metadata in production registry | Item 3 approved + separate mission |
| Real source reference labels in production | Item 4 approved + separate mission |
| Drive / Canvas / NAS / iCloud / API / OAuth | Item 9 + per-integration Owen missions |
| Scanning / crawling / OCR / embeddings / RAG | Separate missions; not part of § J |
| Dry-run auto-promotion | Recommended permanent block |
| v0.2 fixtures as production | Explicit Owen reclassification only |

---

## 10. Needs-More-Planning Candidates

| Item | Open questions for Owen |
| --- | --- |
| 1 — Production registry path | Extend `registry/v0/registry.json` vs new `registry/v0-2/` vs directory of JSON files? |
| 10 — ID namespace | `owen-*`, `resource-*`, course-prefixed, or other? |
| 2 — Write behavior | If yes to writes: confirm manual-only, single-record, snapshot-first |

Reference: planning brief § B decision questions.

---

## 11. Governance-First-Only Candidates

If Owen approves item 11, the **first** implementation mission after checklist review should match planning brief § I:

**In scope for first PR:**

- Path decision doc (after item 1 decided)
- Read-only status proving `production_writes: blocked`
- Negative tests: no `--write`, no registry mutation
- Audit/rollback **planning** stub — no write code

**Explicitly out of scope for first PR:**

- Active `--write` or `--curriculum-registry-write` handler
- Real metadata intake
- Network, OAuth, scanning
- Dry-run → live promotion

**Second PR** (only after first merged + Owen re-approves): smallest possible single-record manual write with snapshot/rollback.

---

## 12. Metadata-Intake-Later Candidates

These items gate **real metadata** — not curriculum file content:

| Item | Future scope if approved | Still blocked |
| --- | --- | --- |
| 3 — Real curriculum metadata | Owen's own titles, subject, unit, lesson labels | Text excerpts, worksheets, answer keys |
| 4 — Real source references | Owen-typed path/URL label strings | Auto-fetch, file copy, indexing |

Cross-link: `docs/curriculum-source-readiness-and-intake-boundary-plan.md` (fake readiness complete; real intake blocked).

Approving items 3 or 4 does **not** authorize a mission by itself. A separate scoped implementation prompt is required.

---

## 13. Implementation Prompts That Must Wait

Do **not** issue these until relevant checklist items are approved:

| Prompt type | Wait for |
| --- | --- |
| Production registry governance PR | Items 6, 7, 8, 9, 11 (minimum); item 1 for path doc |
| Production registry write PR | Items 1, 2, 6, 7, 10, 11 + governance PR merged |
| Real metadata pilot | Items 3, 4, 5, 10 + write path exists |
| Source system integration | Item 9 opened per system + separate mission |
| Curriculum source real intake | Source readiness plan Owen tiny-pilot checklist + production registry decisions |

**ChatGPT review recommended** before any implementation prompt. See `docs/proposals/curriculum-builder-registry-lane-discovery-review.md`.

---

## 14. Safe Next Implementation Options (After Owen Decides)

| Owen completes | Safe next mission (still approval-gated) |
| --- | --- |
| Approve-now batch (§ 8) | Update tracker rows to `approved`; optional status doc refresh only |
| Item 1 (path) + Item 11 | Governance-first production registry PR (§ 11) |
| Items 1, 2, 6, 7, 10, 11 + governance PR merged | Smallest single-record manual write mission |
| Items 3, 4, 5 (manual only) | Real metadata pilot — metadata labels only, no content |
| Per-integration approval | Separate Drive/Canvas/NAS missions — not § J bulk approval |

---

## 15. How to Record Owen Decisions

1. Work through § 7 decision table.
2. For each approved item, update `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` — change `Owen status` from `pending` to `approved` with date/note.
3. For rejected or deferred items, use `rejected` or `deferred` with brief note.
4. Re-run `bin/chief-of-staff --curriculum-production-registry-owen-checklist-status` — WARN count decreases only as items leave `pending`.
5. Issue a **separate** scoped implementation prompt; do not infer approval from this packet.

---

## 16. Related Authority Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` | Checklist row tracker |
| `docs/curriculum-builder-production-registry-workflow-planning-brief.md` | Full planning brief § A–J |
| `docs/curriculum-builder-registry-authority-map.md` | v0 vs v0.2 vs production surfaces |
| `docs/curriculum-source-readiness-and-intake-boundary-plan.md` | Fake readiness vs real intake |
| `docs/curriculum-builder-registry-expected-warns.md` | Expected WARN registry |
| `docs/implementation-approval-gate.md` | Implementation gate |
| `docs/engineering-constitution.md` | Hard boundaries |

## Status Proof

```bash
bin/chief-of-staff --curriculum-production-registry-owen-checklist-status
bin/chief-of-staff --curriculum-production-registry-planning-status
bin/chief-of-staff --curriculum-registry-lane-status
```

## Non-Activation

This review packet does not activate production writes, `--write`, real intake, generation, APIs, network, scanning, or student-data workflows.
