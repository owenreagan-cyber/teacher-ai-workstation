# First-Record Planning Negative Fixtures

```text
Status: planning_only
Classification: validator negative tests — not production
fake_fixture_only: yes
```

## Purpose

Negative production-registry shapes for `scripts/curriculum-builder-production-registry-first-record-validate.sh` tests. These files are **not** production authority and must never be copied into `production-registry.json`.

## Fixtures

| File | Expected validator result |
| --- | --- |
| `negative/negative-two-records.json` | FAIL — records count not 1 |
| `negative/negative-wrong-record-id.json` | FAIL — wrong approved ID |
| `negative/negative-url-in-notes.json` | FAIL — URL pattern in notes |

## Non-Activation

Does not authorize writes or record promotion.
