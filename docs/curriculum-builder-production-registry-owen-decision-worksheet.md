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
3. Re-run `bin/chief-of-staff --curriculum-production-registry-owen-checklist-status` — the expected WARN decreases only as items leave `pending`.
4. Use the **Decision-to-Next-Prompt** table at the bottom before issuing any implementation mission.

## Checklist Worksheet

| # | Item | Your decision (pending/approved/deferred/rejected) | Date | Notes |
| ---: | --- | --- | --- | --- |
| 1 | Production registry path | pending | | v0 extend vs v0.2 file vs directory — see path options doc |
| 2 | Write behavior allowed | pending | | manual-only if yes |
| 3 | Real curriculum metadata allowed | pending | | titles/labels only — not content |
| 4 | Real source references allowed | pending | | manual path/URL labels only |
| 5 | Source systems permitted | pending | | manual first; integrations separate |
| 6 | Rollback requirements | pending | | snapshot + diff + restore |
| 7 | Review states | pending | | accept or revise § D model |
| 8 | Student-data prohibition | pending | | recommend approve (absolute ban) |
| 9 | Integrations blocked in v1 | pending | | recommend approve (keep blocked) |
| 10 | ID namespace | pending | | choose pattern for real records |
| 11 | Governance-first first PR scope | pending | | CB-PROD-GOV complete; write mission separate |

## What Approval Does / Does Not Authorize

| If Owen approves… | Authorizes | Does NOT authorize |
| --- | --- | --- |
| Item 8 (student-data ban) | Affirmation in future PRs | Any data collection |
| Item 9 (integrations blocked) | v1 workflow stays local/manual | Drive/API intake |
| Item 11 (governance-first scope) | Acknowledges CB-PROD-GOV complete | Production writes |
| Item 6 + 7 (rollback + review gates) | Future write mission may reference model | Registry mutation |
| Item 1 + 10 (path + namespace) | Path decision doc update | Creating real records |
| Item 2 (writes allowed) | Future **separate** write mission prompt | Immediate `--write` |
| Item 3 + 4 (real metadata) | Future **separate** metadata pilot mission | File ingestion |

## Safe Tracker Update Examples

**Approve governance affirmation (item 8):**

```markdown
| 8 | Student-data prohibition | approved | Owen | 2026-07-02 | Absolute ban affirmed |
```

**Defer path decision (item 1):**

```markdown
| 1 | Production registry path | deferred | Owen | 2026-07-02 | Need more time on option B vs C |
```

**Do not use `approved` on item 2 unless Owen explicitly authorizes future governed writes.**

## Decision-to-Next-Prompt Routing

| Owen state | Safe next mission |
| --- | --- |
| No checklist changes | Continue Owen review; no implementation prompt |
| Approved items 5, 6, 7, 8, 9, 11 only | Optional tracker/status doc refresh only |
| Approved item 1 (path) + 11 | Update path-options doc with chosen path; still no writes |
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
