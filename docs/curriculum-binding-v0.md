# Curriculum Registry–Contract Binding v0

Last updated: 2026-07-01

## Purpose

Registry–Contract Binding v0 is the third approved Phase 2 implementation subsystem. It provides a **read-only local binding layer** that connects Curriculum Registry v0 and Output Contract v0 safely and deterministically.

Binding v0 supports lookup and consistency validation only. It does not generate lessons, render output, build Canvas packages, ingest files, or resolve external paths.

## Relationship to Other v0 Subsystems

| Subsystem | Role |
| --- | --- |
| [Curriculum Registry v0](curriculum-registry-v0.md) | Canonical manual metadata records (`registry_id`) |
| [Output Contract v0](curriculum-output-contract-v0.md) | Contract metadata with `registry_references` |
| **Binding v0** (this document) | Read-only cross-reference lookup and consistency checks |

Future renderers, Canvas packaging, retrieval indexes, and generation systems may consume binding results — but **none of those systems are activated in v0**.

## Functional Scope (v0)

Binding v0 supports:

1. **Read-only lookup**
   - list output contracts that reference a given `registry_id`
   - show which registry records each contract references
   - full binding report when no `registry_id` is supplied

2. **Deterministic consistency checks**
   - every contract `registry_reference` must exist in Registry v0
   - no missing registry IDs
   - no malformed references
   - no HTTP/network resolution
   - no live file checks, scanning, or crawling

3. **Optional alignment checks (WARN only)**
   - for canonical (`active_v0`) contracts, compare `subject`, `grade_band`, `unit`, and `lesson` between contract and referenced registry record
   - mismatches produce **WARN**, not FAIL, because fictional v0 samples may intentionally cross-reference mixed placeholders

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Binding README | `assistant/curriculum-builder/binding/v0/README.md` |
| Binding manifest | `assistant/curriculum-builder/binding/v0/binding-manifest.json` |
| Validator | `scripts/curriculum-binding-v0-validator.sh` |
| Lookup | `scripts/curriculum-binding-v0-lookup.sh` |
| Status proof | `scripts/curriculum-binding-v0-status.sh` |

## Binding Manifest

```json
{
  "binding_version": "0.1.0",
  "binding_status": "active_v0",
  "registry_source": "assistant/curriculum-builder/registry/v0/registry.json",
  "contract_root": "assistant/curriculum-builder/output-contract/v0",
  "contract_manifest": "assistant/curriculum-builder/output-contract/v0/placeholder-manifest.json"
}
```

## Commands

```bash
bash scripts/curriculum-binding-v0-validator.sh
bash scripts/curriculum-binding-v0-lookup.sh
bash scripts/curriculum-binding-v0-lookup.sh sample-sm5-textbook-001
bin/chief-of-staff --curriculum-binding-v0-validate
bin/chief-of-staff --curriculum-binding-v0-lookup sample-sm5-textbook-001
bin/chief-of-staff --curriculum-binding-v0-status
bash tests/curriculum-binding-v0-test.sh
```

## Read-Only Boundary

Binding scripts:

- read local Registry v0 and Output Contract v0 JSON only
- do not write registry or contract files
- do not resolve Drive, NAS, iCloud, or HTTP paths
- do not make network calls or call APIs
- report PASS/WARN/FAIL only

## Future Use (Not Activated)

Binding v0 is designed as a foundation for future:

- renderer input selection (which contracts reference which registry resources)
- Canvas packaging planning (contract-to-registry bundles)
- retrieval indexes (metadata joins without ingestion)
- generation pipelines (approval-gated; not active)

## Versioning

| Version | Status |
| --- | --- |
| v0.1.0 | Active — read-only lookup and consistency validation |
| v0.2+ | Not started — requires separate approved mission |

## Related Governance

- `docs/engineering-constitution.md`
- `docs/implementation-approval-gate.md`
- `docs/curriculum-builder-section-completion-audit.md`

## no lesson generation

Binding v0 does not generate lessons, drafts, or curriculum content.

## no renderers

Binding v0 does not render HTML, PDF, slides, or Canvas packages.

## no network calls

Binding v0 does not perform network calls, API access, OAuth, or external path resolution.

## no student data

Binding operates on fictional placeholder metadata only. No student-sensitive data belongs in binding lookups or validation.
