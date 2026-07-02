# Level 2 Lane Discovery Review — Curriculum Builder Registry Hardening

Last updated: 2026-07-02

```text
Review level: 2 (End-of-Lane Discovery Review)
Lane: Curriculum Builder Registry Hardening (CB-REG-HARDEN)
Prior lane_status: complete_pending_review
New lane_status: reviewed
Implementation: none authorized by this review
```

## Scope Reviewed

| Deliverable | Evidence |
| --- | --- |
| Registry Authority Map | `docs/curriculum-builder-registry-authority-map.md` |
| Aggregate lane status | `bin/chief-of-staff --curriculum-registry-lane-status` |
| A4–A7 fixture cross-validation | `bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status` |
| Expected WARN registry | `docs/curriculum-builder-registry-expected-warns.md` |
| Status scripts | `scripts/curriculum-builder-registry-*-status.sh` |

**Level 1 candidates reviewed:** 3 implemented from prior registry Level 2 (authority map, aggregate status, A4–A7 cross-validation); 1 proposed (dry-run promotion spec).

---

## Required Review Questions

### 1. Is CB-REG-HARDEN coherent?

**Yes.** Hardening bundle addresses three confusion vectors from registry Level 2 review: authority map, single aggregate lane proof command, and schema cross-validation on fake fixtures. Expected WARNs are documented and not hidden (7 WARNs intentional).

### 2. Discoverability?

**Improved.** `--curriculum-registry-lane-status` orchestrates subtrack proof. Authority map is linked from closure doc, production planning brief, and registry review.

### 3. Fake-only boundaries?

**Stronger than pre-hardening.** Authority map table explicitly states writable?=No for all current surfaces. A4–A7 cross-validation runs on fixture envelope only.

**Remaining gap:** Dry-run → fixture promotion seam documented in planning spec (implemented this sprint).

### 4. Confusion vectors?

| Surface | Risk after hardening |
| --- | --- |
| v0 vs v0.2 fixture | Reduced — authority map is canonical |
| Dry-run PASS → write | Still policy-only; planning spec adds explicit gates |
| A4–A7 WARNs | Documented; agents must not "fix" optional field WARNs as failures |

### 5. Hidden risks?

**None activated.** Cross-validation is read-only Python in bash. No production write paths added.

### 6. PASS/WARN/FAIL meaningful?

**Improved.** Aggregate lane status surfaces subtrack health. A4–A7 cross-validation produces real schema signal (with expected optional-field WARNs).

### 7–8. Missing negatives?

| Item | Severity |
| --- | --- |
| Renderer disk-write negative test | medium — proposed backlog |
| Explicit "do not promote on PASS" in dry-run status output | low — proposed |

---

## Proposal Recommendations

| Candidate | Value | Risk | Status |
| --- | --- | --- | --- |
| Dry-run to fixture promotion planning spec | medium | low | **implemented** |
| Dry-run status banner: PASS ≠ promotion | low | low | **implemented** — dry-run status output |
| Renderer no-disk-write negative test | medium | low | **implemented** — `tests/backlog-non-mutation-guardrails-test.sh` |
| Authority map link in dry-run status script header | low | low | **proposed** |
| CB-REG-HARDEN closure one-pager | low | low | **deferred** |

---

## Expected WARNs (Preserved)

Source: `--curriculum-registry-a4-a7-fixture-schema-status` — **17 PASS / 7 WARN / 0 FAIL**

Documented in `docs/curriculum-builder-registry-expected-warns.md`. Do not convert to PASS without schema/fixture change.

---

## Lane Status Update

| Previous | `complete_pending_review` |
| New | `reviewed` |
| Evidence | This document |

---

## Recommended Next Mission

Production registry implementation remains **blocked** until Owen completes planning brief § J checklist. Safe work: negative tests and status clarity only.

---

## Safety Confirmation

Proposal-only. No production writes, no fixture promotion automation.
