# Curriculum Builder Registry — Expected WARNs

Last updated: 2026-07-03

```text
Status: documentation/status only
Owner: Curriculum Builder Registry lane
Follow-up classification: A4–A7 optional fixture enrichment complete (2026-07-03)
```

## Purpose

Register **intentional non-blocking WARNs** from status commands so future agents do not treat them as failures or hidden regressions.

Per `docs/cursor-autonomous-build-engine.md` Expected WARN Policy.

## Global vs Component WARN Behavior

| Surface | Typical WARNs | Appears in dashboard? |
| --- | ---: | --- |
| `bin/chief-of-staff --dashboard` | 0 | Yes — aggregate health |
| `scripts/chief-of-staff-validate-all.sh` | 0 | Yes |
| `--curriculum-production-registry-owen-checklist-status` | 0 | No — targeted command only |
| `--curriculum-production-registry-metadata-boundary-status` | 0 | No — targeted command only |
| `--curriculum-production-registry-empty-file-status` | 0 | No — historical milestone; targeted command only |
| `--curriculum-production-registry-first-record-status` | 0 | No — targeted command only |
| `--curriculum-production-registry-next-gate-status` | 0 | No — targeted command only |
| `--curriculum-production-registry-metadata-pilot-plan-status` | 0 | No — targeted command only |
| `--presentation-engine-renderer-foundation-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m0-architecture-freeze-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m1-fake-catalog-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m2-local-discovery-approval-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m3-fake-duplicate-search-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m4-smart-rename-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m5-organization-rollback-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m6-extraction-ocr-approval-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7-connector-approval-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7b-manual-source-inventory-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7c-manual-inventory-import-preview-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7c-manual-inventory-fixture-validator` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7d-runtime-import-approval-gate-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7e-local-test-catalog-import` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7e-local-test-catalog-cleanup` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7e-local-test-catalog-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7g-persistent-working-catalog-import` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7g-persistent-working-catalog-backup` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m7g-persistent-working-catalog-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m2b-repo-staging-metadata-discovery` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m2b-repo-staging-metadata-import` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m2b-repo-staging-metadata-cleanup` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m2b-repo-staging-metadata-status` | 0 | No — targeted command only |
| `--teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status` | 0 | No — targeted command only |
| `--curriculum-registry-a4-a7-fixture-schema-status` | **0** (resolved 2026-07-03) | No — targeted command only |
| `--gemini-discovery-classification-intake-status` | 0 | No — targeted command only |
| `--markdown-frontmatter-planning-status` | 0 | No — targeted command only |
| `--whole-system-coherence-status` | 0 | No — targeted command only |
| `--agent-builder-compatibility-governance-status` | 0 | No — targeted command only |
| `--owen-architecture-decision-packets-status` | 0 | No — targeted command only |
| `--app-ecosystem-inventory-status` | 0 | No — targeted command only |
| `--classroom-timer-stopwatch-planning-status` | 0 | No — targeted command only |
| `--app-ecosystem-planning-lanes-status` | 0 | No — targeted command only |
| `--classroom-timer-stopwatch-runtime-status` | 0 | No — targeted command only |
| `--app-runtime-approval-gate-status` | 0 | No — targeted command only |
| `--vibe-wallpaper-widgets-planning-status` | 0 | No — targeted command only |
| `--curriculum-registry-lane-status` | 0 on aggregate script summary | Yes — component lines may show 0 WARN after enrichment |

The lane aggregate script reports **PASS on its own summary** while component scripts may emit documented WARNs. Do not hide component WARNs or weaken checks to make dashboard show them.

## Registered WARNs

No active unresolved WARNs on dashboard or validate-all surfaces as of 2026-07-03.

Resolved registry-lane WARN history is documented in the sections below. New WARNs must be registered here before agents treat them as expected.

## A4–A7 Fixture Schema (Resolved 2026-07-03)

Prior targeted WARNs (7 total) on `--curriculum-registry-a4-a7-fixture-schema-status` are **resolved** by fake/local optional-field enrichment:

| Former WARN | Resolution |
| --- | --- |
| `source_references[n] missing recommended A5 field: source_kind` (×2) | Added fake `source_kind` values in canonical fixture |
| `source_references[n] missing recommended A5 field: owner_context` (×2) | Added fake `owner_context` labels |
| `source_references[n] missing recommended A5 field: access_notes` (×2) | Added fake planning `access_notes` |
| `fixture embeds review_status on A4 records; standalone A6 envelope objects not required` | Documented embedded A6 design; status reports PASS with `a6_embedded_design: true` |

**Typical total now:** 0 WARN / 0 FAIL on `--curriculum-registry-a4-a7-fixture-schema-status`.

Evidence: `docs/curriculum-builder-registry-a4-a7-fixture-evidence.md`

**Intentionally not required in fake fixtures:** standalone A6 envelope objects (future production concern only).

## Owen Checklist Tracker (Resolved 2026-07-02)

Items 3 and 4 approved with strict manual-only boundaries. The prior deferred-metadata WARN on `--curriculum-production-registry-owen-checklist-status` is **resolved**.

**Typical total on `--curriculum-production-registry-owen-checklist-status`:** 0 WARN / 0 FAIL (all 11 items decided).

**Owen review packet:** `docs/curriculum-builder-production-registry-owen-review-packet.md` — boundary approval does not authorize registry mutation.

## Phase 2 Preflight (Resolved 2026-07-02)

The prior deferred-metadata WARN on `--curriculum-production-registry-phase-2-preflight-status` is **resolved** after items 3 and 4 approval.

**Typical total on `--curriculum-production-registry-phase-2-preflight-status`:** 0 WARN / 0 FAIL.

## Metadata Pilot Execution Planning (2026-07-02)

**Typical total on `--curriculum-production-registry-metadata-pilot-plan-status`:** 0 WARN / 0 FAIL when planning docs, first record, and pre-write snapshot are coherent.

Planning does not authorize write tooling or a second record.

## Empty-File Shell (Historical — 2026-07-02)

**Typical total on `--curriculum-production-registry-empty-file-status`:** 0 WARN / 0 FAIL when pre-write snapshot, sentinel, and historical docs are coherent.

Empty-file status is historical; live registry has one approved record.

## First Governed Record (2026-07-03)

**Typical total on `--curriculum-production-registry-first-record-status`:** 0 WARN / 0 FAIL when one approved record, sentinel semantics, negative validator tests, and audit diff proof are coherent.

First record does not authorize write tooling, second record, or source auto-resolution.

## Post–First-Record Hardening (2026-07-03)

Negative validator fixtures and sentinel semantics doc are expected. No new WARNs on dashboard or validate-all.

## Next-Gate Decision Packet (2026-07-03)

**Typical total on `--curriculum-production-registry-next-gate-status`:** 0 WARN / 0 FAIL when decision packet, boundary docs, and blocked-gate proofs are coherent.

Decision packet does not approve any implementation gate.

## Metadata Boundary Refinement (2026-07-02)

**Typical total on `--curriculum-production-registry-metadata-boundary-status`:** 0 WARN / 0 FAIL when refinement docs and planning validator are coherent.

**Typical total on `--curriculum-registry-lane-status` aggregate:** 0 WARN / 0 FAIL when A4–A7 fixture enrichment is current.

## Rules

- WARNs listed here are **expected and non-blocking** when marked unresolved.
- Resolved WARNs must remain documented with resolution rationale.
- Do not downgrade WARNs to PASS without repo-backed fake/local evidence or documented semantic change.
- Do not hide WARN output from status scripts.
- FAIL count must remain 0 for healthy lane.

## Related Commands

```bash
bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status
bin/chief-of-staff --curriculum-registry-lane-status
bin/chief-of-staff --curriculum-production-registry-owen-checklist-status
bin/chief-of-staff --curriculum-production-registry-phase-2-preflight-status
bin/chief-of-staff --curriculum-production-registry-empty-file-status
bin/chief-of-staff --curriculum-production-registry-metadata-pilot-plan-status
```
