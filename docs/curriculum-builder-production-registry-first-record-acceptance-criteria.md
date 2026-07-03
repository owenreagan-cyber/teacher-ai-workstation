# First Production Record — Acceptance Criteria

Last updated: 2026-07-02

```text
Status: planning_only
Classification: acceptance and rejection criteria — no production records
Authority: future governed single-record write mission
```

## Purpose

Define **pass** and **fail** criteria for the first future `resource-*` production record. No record exists until a separate explicit write mission executes.

## Acceptance Criteria (All Required)

| # | Criterion | Verification |
| ---: | --- | --- |
| 1 | Exactly one `resource-*` ID in production registry | exactly one resource-* required |
| 2 | Records count changes from 0 to 1 only | Diff vs empty shell baseline |
| 3 | All populated fields conform to manual metadata contract | Metadata-boundary validator PASS |
| 4 | `source_reference` is non-resolving | No URLs, file IDs, Drive/Canvas/NAS paths as resolvable targets |
| 5 | `review_state` is valid per review-state model | Enum check; write only when `approved` |
| 6 | `audience` is valid | `teacher_facing` or `student_facing` |
| 7 | No copied curriculum content in any field | Length/heuristic guards; Owen review |
| 8 | No student data | Blocked-field guardrails PASS |
| 9 | No real file path, file ID, or URL in production fields | Guardrail scan |
| 10 | No integration activation fields | No API/OAuth/scan/embed fields |
| 11 | Sentinel handling explicit in write mission | Documented per mission — not removed by planning |
| 12 | Snapshot/diff/restore proof included in write mission | Per first-record snapshot plan |
| 13 | Validation PASS before mutation | Empty shell + contract validators |
| 14 | Validation PASS after mutation | Post-write validator |

## Rejection Criteria (Any Triggers FAIL)

| # | Rejection reason | Action |
| ---: | --- | --- |
| R1 | More than one record in first write | Reject; rollback to empty shell |
| R2 | ID not `resource-*` namespace | Reject write |
| R3 | `sample-*` or `example-*` ID in production path | Reject write |
| R4 | Curriculum excerpt or worksheet body in label fields | Reject write |
| R5 | Student name, roster, or individual grade data | Reject write |
| R6 | Resolvable path, URL, or file ID in any field | Reject write |
| R7 | `review_state` not `approved` at write time | Reject write |
| R8 | Post-write validator FAIL | Rollback per snapshot plan |
| R9 | Missing pre-write snapshot | Reject write (do not mutate) |
| R10 | Writer script or `--write` used without mission approval | Reject; escalate |

## Record Acceptance Summary

```text
ACCEPT: exactly one resource-* record, manual metadata only, validators PASS, audit proof complete
REJECT: any rejection criterion; restore empty shell if mutation occurred
```

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-metadata-pilot-execution-plan.md` | Pilot protocol |
| `docs/curriculum-builder-production-registry-first-record-owen-entry-worksheet.md` | Owen worksheet |
| `docs/curriculum-builder-production-registry-blocked-field-guardrails.md` | Blocked categories |

## Non-Activation

These criteria do not authorize registry mutation or metadata pilot execution.
