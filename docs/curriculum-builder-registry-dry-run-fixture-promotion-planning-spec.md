# Curriculum Builder — Dry-Run to Fixture Promotion Planning Spec

Last updated: 2026-07-02

```text
Status: planning_only
Closure status: complete_dry_run_fixture_promotion_planning_spec
Production registry writes: blocked
Fixture promotion: blocked
Automatic promotion: blocked
Implementation: blocked until explicit Owen Reagan approval
```

## Purpose

Document the **intentionally blocked** workflow seam between:

1. **CB-IMPL-1** — dry-run validation of single candidate JSON (`would_write=false`)
2. **CB-IMPL-2** — committed multi-record fake fixture envelope

This spec closes the gap identified in `docs/proposals/curriculum-builder-registry-lane-discovery-review.md` § Q1. It does **not** authorize promotion, file mutation, or production registry writes.

**Proof surfaces (read-only):**

```bash
bin/chief-of-staff --curriculum-registry-dry-run-status
bin/chief-of-staff --curriculum-registry-records-status
bin/chief-of-staff --curriculum-registry-lane-status
```

---

## Current State (Blocked)

| Step | Today | Writable? |
| --- | --- | --- |
| Author candidate JSON | `samples/registry-v0-2-dry-run/` | No |
| Validate candidate | `--curriculum-registry-dry-run-status` | No — reports only |
| Promote to fixture envelope | **Not implemented** | **Blocked** |
| Promote to production registry | **Not implemented** | **Blocked** |

Dry-run success means: *schema/shape looks valid for a fake candidate*. It does **not** mean write authorization.

---

## Authority Rules (Non-Negotiable)

From `docs/curriculum-builder-registry-authority-map.md`:

| Surface | ID pattern | Promotion target? |
| --- | --- | --- |
| Dry-run candidates | `example-*` | **Never auto** |
| Local fixtures | `example-*` | **Human mission only**; remain `fake_fixture_only` |
| Registry v0 live | `sample-*` | **Blocked** without production mission |
| Production (future) | TBD | **Owen decision** — see production planning brief |

---

## Future Human-Gated Promotion Workflow (Planning Only)

If Owen approves a **fixture promotion mission** (not production):

```text
1. Owen or mission author selects ONE dry-run candidate file
2. Mission prompt explicitly authorizes fixture envelope edit
3. Human reviews candidate fields against A4–A7 contracts
4. Human adds/updates record in local-registry.json envelope
5. Run --curriculum-registry-records-status (must PASS)
6. Run --curriculum-registry-a4-a7-fixture-schema-status (WARNs allowed if documented)
7. Run --curriculum-registry-lane-status aggregate proof
8. Commit fixture change with mission reference in commit message
9. No automatic step from dry-run PASS → git commit
```

**Production promotion** requires a separate mission per `docs/curriculum-builder-production-registry-workflow-planning-brief.md`.

---

## Explicitly Forbidden (Until Separate Approval)

- CLI `--write` or hidden write flags
- Script that copies dry-run candidate → fixture without human review
- Script that copies fixture → `registry/v0/registry.json`
- Batch promotion of all passing dry-run files
- Promotion based on CI PASS alone
- Changing `fake_fixture_only` flags during promotion
- Real curriculum URIs, student data, or external URLs in promoted records

---

## Status / Test Hardening Candidates (Proposal-Only)

| Candidate | Class | Notes |
| --- | --- | --- |
| Negative test: dry-run script does not modify fixture JSON | B | Safe fake-fixture hardening |
| Status note in dry-run output: "PASS does not authorize promotion" | A | Clarity |
| Planning spec cross-link in authority map | C | Coherence — this doc |

---

## Owen Decisions Required Before Any Implementation

1. Should fixture promotion ever be a **single CLI command**, or remain **manual JSON edit + validation**?
2. Should promoted fixture records require a new field (e.g. `promoted_from_dry_run: <filename>`)?
3. Should dry-run and fixture directories remain separate on disk forever?

**Default recommendation:** remain manual JSON edit + validation; no promotion CLI until production registry path is decided.

---

## References

| Doc | Role |
| --- | --- |
| `docs/curriculum-builder-registry-authority-map.md` | Authority surfaces |
| `docs/curriculum-builder-registry-expected-warns.md` | Expected WARN registry |
| `docs/curriculum-builder-production-registry-workflow-planning-brief.md` | Production workflow (separate) |
| `docs/proposals/curriculum-builder-registry-lane-discovery-review.md` | Level 2 gap source |
