# Owen § J Production Registry — Decision Worksheet

Last updated: 2026-07-02

```text
Status: owen_decision_worksheet
Audience: Owen Reagan
Classification: decision support only — not implementation authority
```

## Non-Approval Statement

```text
Documenting an option does not approve it.
Updating this worksheet does not authorize implementation.
Only explicit tracker row updates by Owen authorize checklist progress.
PASS on any status command does not authorize writes.
Item 2 approval in principle does not authorize registry mutation.
```

## How to Use This Worksheet

1. Read `docs/curriculum-builder-production-registry-owen-review-packet.md` § 7 decision table.
2. For each checklist item below, record your decision in `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` (change `Owen status` from `pending` to `approved`, `deferred`, or `rejected`).
3. Re-run `bin/chief-of-staff --curriculum-production-registry-owen-checklist-status` — all 11 items decided as of 2026-07-02 (0 expected WARN).
4. Use the **Decision-to-Next-Prompt** table at the bottom before issuing any implementation mission.

## Checklist Worksheet

| # | Item | Your decision (pending/approved/deferred/rejected) | Date | Notes |
| ---: | --- | --- | --- | --- |
| 1 | Production registry path | approved | 2026-07-02 | Option B — `assistant/curriculum-builder/registry/v0-2/production-registry.json`; v0 remains read-only `sample-*` |
| 2 | Write behavior allowed | approved | 2026-07-02 | Manual-only in principle; Phase 2 preflight only next; no file, no records, no --write |
| 3 | Real curriculum metadata allowed | approved | 2026-07-02 | Manual Owen-entered descriptive metadata only (title, subject, grade band, unit, lesson, resource type, teacher/student-facing flag, review state, manual tags, notes); no copied curriculum content, no student data, no file parsing, no OCR, no AI summaries, no embeddings/RAG, no auto-ingest |
| 4 | Real source references allowed | approved | 2026-07-02 | Manual non-resolving source-reference labels typed by Owen only (display label, source_type enum, citation/note string); no API/OAuth, no live Drive/Canvas/NAS/iCloud access, no auto-resolution, no crawling/scanning, no real file reads, no resolvable file IDs or paths |
| 5 | Source systems permitted | approved | 2026-07-02 | Manual entry only; integrations blocked |
| 6 | Rollback requirements | approved | 2026-07-02 | Snapshot + diff + restore required before any write mission |
| 7 | Review states | approved | 2026-07-02 | § D review-state gate model accepted |
| 8 | Student-data prohibition | approved | 2026-07-02 | Absolute ban affirmed |
| 9 | Integrations blocked in v1 | approved | 2026-07-02 | Canvas/Drive/NAS/iCloud/API/OAuth/network remain blocked unless separate missions |
| 10 | ID namespace | approved | 2026-07-02 | `resource-*` pattern (e.g. `resource-sm5-textbook-001`); distinct from `sample-*` and `example-*` |
| 11 | Governance-first first PR scope | approved | 2026-07-02 | CB-PROD-GOV merged; governed write mission remains separate and unapproved |

## What Approval Does / Does Not Authorize

| If Owen approves… | Authorizes | Does NOT authorize |
| --- | --- | --- |
| Item 8 (student-data ban) | Affirmation in future PRs | Any data collection |
| Item 9 (integrations blocked) | v1 workflow stays local/manual | Drive/API intake |
| Item 11 (governance-first scope) | Acknowledges CB-PROD-GOV complete | Production writes |
| Item 6 + 7 (rollback + review gates) | Future write mission may reference model | Registry mutation |
| Item 1 + 10 (path + namespace) | Path decision doc update; namespace recorded | Creating real records or production-registry.json |
| Item 2 (writes in principle) | Phase 2 preflight eligible via **separate** mission prompt | Immediate `--write`, file creation, records |
| Item 3 + 4 (real metadata) | Future **separate** metadata pilot mission | File ingestion |

## Safe Tracker Update Examples

**Approve write behavior in principle (item 2):**

```markdown
| 2 | Write behavior allowed | approved | Owen | 2026-07-02 | Manual-only governed writes permitted in principle; Phase 2 preflight only next |
```

**Do not interpret item 2 approval as authorization to create production-registry.json or records without a separate explicit mission.**

## Decision-to-Next-Prompt Routing

| Owen state | Safe next mission |
| --- | --- |
| 2 items deferred (current) | **Superseded** — items 3 and 4 approved 2026-07-02 |
| All 11 items decided + Phase 2 complete | **Metadata-boundary refinement** docs/status/tests — separate explicit prompt |
| Metadata boundaries approved | Future empty-file or single-record missions — separate prompts each |
| Approved 1, 2, 6, 7, 10, 11 + Phase 2 complete | **Governed single-record write mission** — see write-mission backlog; still requires items 3/4 for real metadata |
| Approved 3, 4, 5 (manual only) without registry file | **Metadata pilot planning mission** — docs/status only |
| Any integration need | **Separate per-system mission** — not bulk § J approval |

**ChatGPT review recommended** before Phase 2 preflight or any write implementation prompt.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-review-packet.md` | Full decision table |
| `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` | Canonical tracker rows |
| `docs/curriculum-builder-production-registry-post-decision-implementation-map.md` | Post-decision routing detail |
| `docs/curriculum-builder-production-registry-governance-foundation.md` | CB-PROD-GOV closure |

## Non-Activation

This worksheet does not activate writes, intake, or integrations.
