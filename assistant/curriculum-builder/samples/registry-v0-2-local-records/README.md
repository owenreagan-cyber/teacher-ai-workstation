# Registry v0.2 Local Fake Records (CB-IMPL-2)

Committed fixture registry for local fake-record validation only.

- **Not** the live registry at `assistant/curriculum-builder/registry/v0/registry.json`
- **Not** the production registry at `assistant/curriculum-builder/registry/v0-2/production-registry.json`
- **Not** real curriculum content or student data
- Validated by `scripts/curriculum-builder-registry-v0-2-local-records-validate.sh`
- A4–A7 cross-validation: `bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status`

## Fixtures

| Path | Purpose |
| --- | --- |
| `local-registry.json` | Canonical fake/local A4–A7 enriched fixture |
| `negative/` | Invalid examples that must fail validation |

Evidence doc: `docs/curriculum-builder-registry-a4-a7-fixture-evidence.md`
