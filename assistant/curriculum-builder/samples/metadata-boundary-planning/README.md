# Metadata Boundary Planning Samples

```text
Status: fake_fixture_only
Classification: planning-only — not production authority
ID namespace: example-* only (never resource-*)
```

Fake/local planning examples for production registry metadata-boundary refinement. These files are **not** production records and must not live at `assistant/curriculum-builder/registry/v0-2/production-registry.json`.

## Files

| File | Purpose |
| --- | --- |
| `example-metadata-boundary-record.json` | Canonical fake planning record shape |
| `negative/negative-resource-id.json` | Must fail — uses resource-* ID |
| `negative/negative-drive-url.json` | Must fail — resolvable URL in source_reference |

## Validation

```bash
bash scripts/curriculum-builder-production-registry-metadata-boundary-validate.sh \
  assistant/curriculum-builder/samples/metadata-boundary-planning/example-metadata-boundary-record.json
```

## Non-Activation

No production writes. No real curriculum. No student data.
