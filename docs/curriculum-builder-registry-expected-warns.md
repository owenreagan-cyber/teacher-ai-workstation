# Curriculum Builder Registry — Expected WARNs

Last updated: 2026-07-02

```text
Status: documentation/status only
Owner: Curriculum Builder Registry lane
Follow-up classification: optional fixture enrichment (Class B) — not required for lane health
```

## Purpose

Register **intentional non-blocking WARNs** from `--curriculum-registry-a4-a7-fixture-schema-status` so future agents do not treat them as failures or hidden regressions.

Per `docs/cursor-autonomous-build-engine.md` Expected WARN Policy.

## Global vs Component WARN Behavior

| Surface | Typical WARNs | Appears in dashboard? |
| --- | ---: | --- |
| `bin/chief-of-staff --dashboard` | 0 | Yes — aggregate health |
| `scripts/chief-of-staff-validate-all.sh` | 0 | Yes |
| `--curriculum-production-registry-owen-checklist-status` | 0 | No — targeted command only |
| `--curriculum-production-registry-metadata-boundary-status` | 0 | No — targeted command only |
| `--curriculum-registry-a4-a7-fixture-schema-status` | 7 (fixture optional fields) | No — targeted command only |
| `--curriculum-registry-lane-status` | 0 on aggregate script summary | Yes — component WARNs roll up in component lines, not aggregate FAIL |

The lane aggregate script reports **PASS on its own summary** while component scripts may emit documented WARNs. Do not hide component WARNs or weaken checks to make dashboard show them.

## Registered WARNs

| WARN | Count (typical) | Reason | Follow-up |
| --- | ---: | --- | --- |
| `source_references[n] missing recommended A5 field: source_kind` | 2 | Fixture uses A5 core subset; optional planning fields from inactive sample not required for fake fixtures | Optional: add placeholder `source_kind` in fixture — Class B, low priority |
| `source_references[n] missing recommended A5 field: owner_context` | 2 | Same as above | Optional Class B |
| `source_references[n] missing recommended A5 field: access_notes` | 2 | Same as above | Optional Class B |
| `fixture embeds review_status on A4 records; standalone A6 envelope objects not required` | 1 | v0.2 fixture design embeds review on records; full A6 objects are future production concern | No action for fake fixtures |

**Typical total:** 7 WARN / 0 FAIL on canonical fixture.

## Owen Checklist Tracker (Resolved 2026-07-02)

Items 3 and 4 approved with strict manual-only boundaries. The prior deferred-metadata WARN on `--curriculum-production-registry-owen-checklist-status` is **resolved**.

**Typical total on `--curriculum-production-registry-owen-checklist-status`:** 0 WARN / 0 FAIL (all 11 items decided).

**Owen review packet:** `docs/curriculum-builder-production-registry-owen-review-packet.md` — boundary approval does not authorize registry mutation.

## Phase 2 Preflight (Resolved 2026-07-02)

The prior deferred-metadata WARN on `--curriculum-production-registry-phase-2-preflight-status` is **resolved** after items 3 and 4 approval.

**Typical total on `--curriculum-production-registry-phase-2-preflight-status`:** 0 WARN / 0 FAIL.

## Metadata Boundary Refinement (2026-07-02)

**Typical total on `--curriculum-production-registry-metadata-boundary-status`:** 0 WARN / 0 FAIL when refinement docs and planning validator are coherent.

**Typical total on `--curriculum-registry-lane-status` aggregate:** 7 WARN / 0 FAIL (A4–A7 fixture optional fields only) when canonical fixture unchanged.

## Rules

- WARNs listed here are **expected and non-blocking**.
- Do not downgrade WARNs to PASS without Owen-approved semantic change.
- Do not hide WARN output from status scripts.
- FAIL count must remain 0 for healthy lane.

## Related Commands

```bash
bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status
bin/chief-of-staff --curriculum-registry-lane-status
bin/chief-of-staff --curriculum-production-registry-owen-checklist-status
bin/chief-of-staff --curriculum-production-registry-phase-2-preflight-status
```
