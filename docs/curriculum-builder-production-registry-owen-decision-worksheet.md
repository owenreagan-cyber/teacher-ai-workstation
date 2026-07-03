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
```

## How to Use This Worksheet

1. Read `docs/curriculum-builder-production-registry-owen-review-packet.md` § 7 decision table.
2. For each checklist item below, record your decision in `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` (change `Owen status` from `pending` to `approved`, `deferred`, or `rejected`).
3. Re-run `bin/chief-of-staff --curriculum-production-registry-owen-checklist-status` — the expected WARN remains while deferred items exist (3 deferred as of 2026-07-02).
4. Use the **Decision-to-Next-Prompt** table at the bottom before issuing any implementation mission.

## Checklist Worksheet

| # | Item | Your decision (pending/approved/deferred/rejected) | Date | Notes |
| ---: | --- | --- | --- | --- |
| 1 | Production registry path | approved | 2026-07-02 | Option B — `assistant/curriculum-builder/registry/v0-2/production-registry.json`; v0 remains read-only `sample-*` |
| 2 | Write behavior allowed | deferred | 2026-07-02 | No writes approved yet |
| 3 | Real curriculum metadata allowed | deferred | 2026-07-02 | Metadata pilot later; no real metadata intake approved |
| 4 | Real source references allowed | deferred | 2026-07-02 | Manual labels later; no real source references approved |
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
| Item 2 (writes allowed) | Future **separate** write mission prompt | Immediate `--write` |
| Item 3 + 4 (real metadata) | Future **separate** metadata pilot mission | File ingestion |

## Safe Tracker Update Examples

**Approve path decision (item 1):**

```markdown
| 1 | Production registry path | approved | Owen | 2026-07-02 | Option B — assistant/curriculum-builder/registry/v0-2/production-registry.json |
```

**Approve namespace (item 10):**

```markdown
| 10 | ID namespace | approved | Owen | 2026-07-02 | resource-* pattern; distinct from sample-* and example-* |
```

**Do not use `approved` on item 2 unless Owen explicitly authorizes future governed writes.**

## Decision-to-Next-Prompt Routing

| Owen state | Safe next mission |
| --- | --- |
| 3 items deferred (current) | **Item 2 write behavior decision session** — separate from path/namespace |
| Approved items 1, 5, 6, 7, 8, 9, 10, 11 (recorded 2026-07-02) | Tracker/status doc refresh only — **no writes** |
| Approved item 1 (path) + 10 (namespace) without item 2 | Path recorded; still no writes or file creation |
| Approved 1, 2, 6, 7, 10, 11 + governance merged | **Governed single-record write mission** — see `docs/proposals/backlog/production-registry-write-mission.md` |
| Approved 3, 4, 5 (manual only) without item 2 | **Metadata pilot planning mission** — docs/status only unless write also approved |
| Any integration need | **Separate per-system mission** — not bulk § J approval |

**ChatGPT review recommended** before any implementation prompt. See `docs/proposals/curriculum-builder-registry-lane-discovery-review.md`.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-review-packet.md` | Full decision table |
| `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` | Canonical tracker rows |
| `docs/curriculum-builder-production-registry-post-decision-implementation-map.md` | Post-decision routing detail |
| `docs/curriculum-builder-production-registry-governance-foundation.md` | CB-PROD-GOV closure |

## Non-Activation

This worksheet does not activate writes, intake, or integrations.
