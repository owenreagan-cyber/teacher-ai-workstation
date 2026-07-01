# Curriculum Registry–Contract Binding v0

Read-only binding layer connecting Curriculum Registry v0 and Output Contract v0.

## Purpose

- list output contracts that reference a given `registry_id`
- show registry records referenced by each contract
- validate reference consistency deterministically

## Inputs

| Source | Path |
| --- | --- |
| Binding manifest | `binding-manifest.json` |
| Registry v0 | `../registry/v0/registry.json` |
| Output Contract v0 | `../output-contract/v0/` |

## Boundaries

- read-only lookup and validation only
- no lesson generation, renderers, ingestion, or external resolution
- no registry or contract writes from CLI

## Commands

```bash
bash scripts/curriculum-binding-v0-validator.sh
bash scripts/curriculum-binding-v0-lookup.sh
bash scripts/curriculum-binding-v0-lookup.sh sample-sm5-textbook-001
bin/chief-of-staff --curriculum-binding-v0-status
bin/chief-of-staff --curriculum-binding-v0-lookup sample-sm5-textbook-001
```
