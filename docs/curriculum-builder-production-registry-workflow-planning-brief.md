# Curriculum Builder — Production Registry Workflow Planning Brief

Last updated: 2026-07-02

```text
Status: planning_only
Closure status: complete_production_registry_planning_brief
Production registry writes: blocked
Active user-facing --write: blocked
Real metadata intake: blocked
Student data: blocked
Real curriculum content: blocked
Implementation: blocked until explicit Owen Reagan approval
```

## A. Purpose

This document defines a **future** teacher-reviewed production registry workflow for the Curriculum Builder. It is **planning-only**. It does not authorize implementation, production writes, real metadata intake, or external integrations.

**Future goal (not active today):**

- A **manual-first**, **local-first**, **Owen-controlled** production registry workflow
- Metadata-only records describing where curriculum resources live — not copies of curriculum files
- Human review at every promotion step
- No automation without separate explicit approval
- No student data
- No uncontrolled curriculum ingestion

**Prerequisites complete:**

- CB-IMPL-1 dry-run validation (`--curriculum-registry-dry-run-status`)
- CB-IMPL-2–4 fake fixture foundations (`docs/curriculum-builder-registry-v0-2-lane-closure.md`)
- Level 2 lane discovery review (`docs/proposals/curriculum-builder-registry-lane-discovery-review.md`)

**Proof (read-only):**

```bash
bin/chief-of-staff --curriculum-production-registry-planning-status
```

---

## B. Target Registry Authority Decision

**Owen decision required.** Repo docs do not yet choose a single production authority path.

| Option | Path / surface | Current role | Production candidate? |
| --- | --- | --- | --- |
| **Registry v0 (live)** | `assistant/curriculum-builder/registry/v0/registry.json` | Active read-only v0 registry; `sample-*` fictional placeholders; validator only | **Open decision** — extend v0 vs replace |
| **Registry v0.2 fixtures** | `assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json` | Fake fixture envelope only; `example-*` IDs; `fake_fixture_only` | **Not production** — must remain fixture-only unless Owen explicitly reclassifies |
| **Future production path** | TBD — e.g. `assistant/curriculum-builder/registry/v0-2/` or governed v0 extension | Not implemented | **Open decision** |

### Decision questions for Owen

1. Should production registry **extend** existing v0 `registry.json`, or use a **new v0.2 production path**?
2. Should production be **one JSON file** or a **directory of record files** with an index manifest?
3. Should v0.2 sample fixtures **always remain** fake-only reference material?
4. Should dry-run candidates ever promote to production automatically? (**Recommended: no** — human mission per record.)
5. What ID namespace applies to real records (`owen-*`, `resource-*`, course-prefixed)? (**Open decision**)

### Interim authority rule (until Owen decides)

- **v0 `registry.json`** is the only committed non-sample registry surface today — still read-only.
- **v0.2 fixtures** are **not** production authority.
- **Dry-run success does not authorize writes.**

---

## C. Manual Entry Workflow (Future — Not Implemented)

Planned teacher/Owen workflow when implementation is separately approved:

```text
1. draft      → Owen creates candidate metadata (manual JSON or guided form — TBD)
2. validate   → dry-run validator passes (CB-IMPL-1 pattern)
3. review     → Owen reviews metadata fields, source labels, student-facing flags
4. approve    → explicit approval recorded (audit entry)
5. write      → single governed write to production registry (separate mission)
6. verify     → post-write validator + diff proof
7. rollback   → if error, restore prior registry state (see § E)
```

**Planning constraints:**

- Each step is human-gated; no batch auto-import
- No step may skip review for "convenience"
- Promotion from dry-run candidate to production requires **explicit mission authorization**
- Fixture records are never auto-promoted

---

## D. Review Gates (Future States — Planning Only)

These states are **not implemented in code** today. They describe a future governance model. Some overlap existing v0 `review_status` / `approval_status` enums in `registry-schema.json`; production workflow must reconcile with canonical schema before implementation.

| State | Meaning |
| --- | --- |
| `draft` | Work in progress; not validated |
| `candidate` | Submitted for validation |
| `validated` | Passed dry-run / schema checks |
| `teacher_reviewed` | Owen reviewed metadata; not yet approved for production |
| `approved` | Approved for production write |
| `rejected` | Rejected; must not write |
| `quarantined` | Held for policy/safety review |
| `archived` | Retired from active registry; retained for audit |

**Gate rule:** Only `approved` records may be written to production registry in a future implementation mission.

---

## E. Rollback / Audit Requirements (Future)

Every future production write (when separately approved) should require:

| Requirement | Description |
| --- | --- |
| Before/after diff | Machine-readable diff of registry file(s) before and after write |
| Timestamp | ISO-8601 write timestamp in audit log |
| Commit reference | Git commit or local audit file reference when applicable |
| Reviewer identity | Placeholder field only (e.g. `reviewer: owen`) — no student identifiers |
| Reason for change | Short human-entered reason string |
| Rollback procedure | Restore from backup copy or git revert; document steps before first write |
| Student data | **Prohibited** in audit entries |
| Curriculum content | **Prohibited** — metadata only; no copied text, excerpts, or answer keys |

**Rollback procedure (planning):**

1. Capture pre-write registry snapshot to local audit path (location TBD at implementation)
2. Perform governed write
3. Run post-write validator
4. On failure: restore snapshot; log rollback reason
5. Never silently overwrite without snapshot

---

## F. Explicit Non-Goals

A future production registry workflow **does not authorize** (unless Owen approves a **separate** mission for each):

- Scanning folders or home directories
- Crawling Google Drive, NAS, iCloud, or Canvas
- Canvas API or LTI integration
- OAuth or API credentials
- Network services or live URL resolution
- OCR or document parsing
- Embeddings, vector databases, or RAG
- Semantic search
- Lesson generation, worksheet generation, or presentation generation
- Review-note generation
- Automated imports from external tools
- Automated dry-run → live promotion
- Student-data handling or storage
- Real curriculum text storage in registry records
- Hidden write paths or background jobs

---

## G. Student Data and Curriculum Content Boundaries

**Absolute prohibitions for registry metadata (current and future):**

| Category | Blocked |
| --- | --- |
| Student data | Names, IDs, rosters, grades, accommodations, behavior notes, IEP details |
| Curriculum content | Copied text, textbook excerpts, worksheet body, slide content, answer keys, test/quiz items |
| School records | Private HR, discipline, or administrative records |
| Live identifiers | Real student emails, SIS IDs, Canvas enrollment IDs tied to students |

**Allowed (with Owen approval in future missions):**

- Teacher-authored **metadata labels** for Owen's own resources (title, subject, unit, lesson, resource type)
- **Placeholder or labeled** source references that Owen manually enters (not auto-resolved)
- Fictional examples in planning docs and fixtures only until explicit real-metadata approval

---

## H. Source-System Priority (Planning Questions)

**Recommended order (Owen to confirm):**

| Priority | Source | Status |
| --- | --- | --- |
| 1 | Manual metadata entry (CLI or form — TBD) | First when implementation approved |
| 2 | Local file path labels (metadata only; no scanning) | Later; separate approval |
| 3 | Google Drive (labeled references; no API) | Later; separate approval |
| 4 | NAS / iCloud (labeled references; no API) | Later; separate approval |
| 5 | Canvas (export references; no API) | Later; separate approval |
| 6 | External tools (Lovable, etc.) | Much later; separate approval |

**Rule:** Metadata references may describe *where* a resource lives; they must not auto-fetch, index, or copy content.

---

## I. Safe First Implementation PR (Future — Not This Mission)

If Owen later approves production registry **implementation**, the safest first PR is:

**PR scope: governance + blocked proof only**

1. Production registry path decision doc (if Owen chooses path in checklist)
2. Read-only status script proving `production_writes: blocked`
3. Negative tests: no `--write` flag, no registry mutation, `--curriculum-registry-write` remains blocked in manifest
4. Audit/rollback **planning** stub doc — no write code

**Explicitly excluded from first implementation PR:**

- Active `--write` or `--curriculum-registry-write` implementation
- Real metadata intake
- Any network, OAuth, or scanning code
- Promotion of dry-run candidates to live registry

**Second PR (only after first PR merged and Owen re-approves):**

- Governed single-record manual write with snapshot/rollback — smallest possible scope

---

## J. Owen Approval Checklist

Owen must explicitly approve each item before any production registry **implementation** mission:

- [ ] **Production registry path** — v0 extension vs new v0.2 production path vs directory model
- [ ] **Write behavior allowed** — yes/no; if yes, manual-only confirmed
- [ ] **Real curriculum metadata allowed** — Owen's own resource titles/labels only; no student data
- [ ] **Real source references allowed** — labeled paths/URLs Owen enters manually; no auto-resolution
- [ ] **Source systems permitted** — manual first; Drive/NAS/iCloud/Canvas remain blocked until separately listed
- [ ] **Rollback requirements** — snapshot + diff + restore procedure accepted
- [ ] **Review states** — gate model in § D accepted or revised
- [ ] **Student-data prohibition** — remains absolute
- [ ] **Canvas/Drive/NAS/iCloud/API/OAuth/network** — remain blocked in v1 production workflow unless each is separately approved
- [ ] **ID namespace** — chosen for real records
- [ ] **First implementation PR scope** — governance-only first PR accepted

**ChatGPT review recommended** before issuing implementation prompt. See `docs/proposals/curriculum-builder-registry-lane-discovery-review.md`.

---

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-registry-v0-2-lane-closure.md` | Completed fake/local foundation lane |
| `docs/curriculum-builder-registry-v0-2-record-boundaries.md` | Fixture vs live registry boundaries |
| `docs/curriculum-registry-v0.md` | Live v0 registry (read-only today) |
| `docs/implementation-approval-gate.md` | Implementation gate |
| `docs/proposals/curriculum-builder-registry-lane-discovery-review.md` | Level 2 review |

## Non-Activation

This planning brief does not activate production writes, `--write`, real intake, generation, APIs, network, scanning, or student-data workflows.
