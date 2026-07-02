# Classroom App Lab — Fake Prototype Inventory Template

Last updated: 2026-07-02

```text
Status: planning_template_only
Program: Classroom App Lab — CAL1
Classification: metadata-only prototype inventory — no zip/parse/execute
```

## Purpose

Planning-only template for future **prototype rescue inventory** rows. All rows below are fake placeholders. No zip upload, extraction, code parsing, app execution, or LLM analysis.

## Inventory Template

| prototype_id | label | source_lane | rescue_stage | runtime_allowed | notes |
| --- | --- | --- | --- | --- | --- |
| fake-proto-001 | Sample Quiz Shell | external-lovable-adjacent | intake_blocked | false | Fake placeholder — no real app archive |
| fake-proto-002 | Sample Timer Utility | classroom-utility-adjacent | triage_blocked | false | Planning row only — CAL3+ blocked |
| fake-proto-003 | Sample Dashboard Widget | widget-shortcut-adjacent | catalog_only | false | Cross-lane reference — F1 metadata only |

## Rescue Stages (Planning Only)

1. **intake_blocked** — zip/upload not authorized
2. **triage_blocked** — manual review concept only
3. **catalog_only** — metadata indexed without execution
4. **rescue_blocked** — Cursor/automation execution not authorized

## Status Proof

```bash
bin/chief-of-staff --classroom-app-lab-status
bash scripts/classroom-app-lab-status.sh
```

## Related Documents

| Document | Role |
| --- | --- |
| `docs/classroom-app-lab-prototype-rescue-foundation.md` | CAL1 closure |
| `docs/classroom-app-lab-vs-lovable-lane-boundary.md` | CAL1 vs G1 boundary |
| `docs/classroom-app-lab-non-activation-boundaries.md` | Non-activation |

## Non-Activation

No zip upload, extraction, parsing, app execution, LLM/API analysis, automatic Cursor execution, student data, or network calls.
