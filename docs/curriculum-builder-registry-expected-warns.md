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

## Registered WARNs

| WARN | Count (typical) | Reason | Follow-up |
| --- | ---: | --- | --- |
| `source_references[n] missing recommended A5 field: source_kind` | 2 | Fixture uses A5 core subset; optional planning fields from inactive sample not required for fake fixtures | Optional: add placeholder `source_kind` in fixture — Class B, low priority |
| `source_references[n] missing recommended A5 field: owner_context` | 2 | Same as above | Optional Class B |
| `source_references[n] missing recommended A5 field: access_notes` | 2 | Same as above | Optional Class B |
| `fixture embeds review_status on A4 records; standalone A6 envelope objects not required` | 1 | v0.2 fixture design embeds review on records; full A6 objects are future production concern | No action for fake fixtures |

**Typical total:** 7 WARN / 0 FAIL on canonical fixture.

## Owen Checklist Tracker WARNs

| WARN | Count (typical) | Reason | Follow-up |
| --- | ---: | --- | --- |
| `11 Owen checklist items pending approval — implementation blocked` | 1 | All § J checklist rows remain `pending` until Owen explicitly approves each item | Owen product decisions required before production registry implementation mission |

**Typical total on `--curriculum-production-registry-owen-checklist-status`:** 1 WARN / 0 FAIL while checklist incomplete.

**Typical total on `--curriculum-registry-lane-status` aggregate:** 8 WARN / 0 FAIL (7 A4–A7 + 1 Owen checklist) when canonical fixture unchanged.

## Rules

- WARNs listed here are **expected and non-blocking**.
- Do not downgrade WARNs to PASS without Owen-approved semantic change.
- Do not hide WARN output from status scripts.
- FAIL count must remain 0 for healthy lane.

## Related Commands

```bash
bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status
bin/chief-of-staff --curriculum-registry-lane-status
```
