# Runtime App Boundary Checklist

Last updated: 2026-07-04

Reusable checklist for any future **Level 3** runtime implementation mission. Complete one copy per mission; attach to PR body.

```text
Status: template — not runtime approval
Runtime approved: no (until Owen signs Level 3 mission)
```

## Identity

| Field | Value |
| --- | --- |
| App name | _fill in_ |
| Inventory ID | _fill in_ |
| Planning lane source doc | _path_ |
| Implementation packet | _path_ |
| Current readiness level | _0–2 before mission; 3 during approved mission_ |
| Owen approval status | **required — not implied by planning** |

## Runtime Surfaces

| Surface | Requested? | Denied by default? |
| --- | --- | --- |
| Static HTML page | | yes until approved |
| CSS styling | | yes until approved |
| JS timer/caller/layout logic | | yes until approved |
| React/Vue/Svelte components | | **denied** unless explicitly approved |
| Print/export | | denied unless approved |
| Audio playback | | **denied** |
| Animations | | **denied** |
| localStorage/sessionStorage | | **denied** |

## Files and Directories

| Allowed (after Level 3) | Forbidden |
| --- | --- |
| Approved app path under docs/classroom-utilities/ or mission-specified | assistant/classroom-utilities/runtime/ without approval |
| Fake/local fixture JSON | Real roster/curriculum files |
| Status script + test | writer scripts, --write handlers |

## Data Boundaries

| Type | Allowed | Forbidden |
| --- | --- | --- |
| Fake/local labels | yes | — |
| Student names/rosters | — | **absolute** |
| Grades/behavior/accommodations | — | **absolute** |
| Real curriculum content | — | **absolute** |
| Copied worksheets/tests | — | **absolute** |

## Integration and AI

| Check | Status |
| --- | --- |
| Drive/NAS/iCloud/Canvas | blocked |
| API/OAuth/network | blocked |
| Scanning/OCR/embeddings/RAG | blocked |
| AI generation | blocked |
| Local model/Ollama | blocked |

## Production Registry

| Check | Expected |
| --- | --- |
| Record count | exactly 1 |
| BLOCKED-NO-WRITES.sentinel | intact |
| --write active | no |
| Writer scripts | none |

## Validation Requirements

Before merge:

- [ ] `--app-runtime-approval-gate-status` PASS
- [ ] `--app-ecosystem-planning-lanes-status` PASS
- [ ] Dashboard / validate-all / phase-1 / smoke PASS
- [ ] App-specific status test (if added) PASS

## Rollback / Cleanup

- [ ] Revert plan documented
- [ ] Branch deletion after merge
- [ ] Final main dashboard proof

## Sign-Off

| Role | Status |
| --- | --- |
| Owen explicit runtime approval | **required** |
| Chief of Staff runtime execution | **never** |

## Cross-Links

- Approval gate: `docs/app-ecosystem/runtime-implementation-approval-gate.md`
- Readiness matrix: `docs/app-ecosystem/app-production-readiness-matrix.md`
