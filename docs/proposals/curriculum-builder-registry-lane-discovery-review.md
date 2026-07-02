# Level 2 Lane Discovery Review — Curriculum Builder Registry Local Foundation Lane

Last updated: 2026-07-02

```text
Review level: 2 (End-of-Lane Discovery Review)
Lane: Curriculum Builder Registry Local Foundation (CB-IMPL-1 through CB-IMPL-4)
Prior lane_status: complete_pending_review (implicit; lane not yet in Program Lane Status table)
New lane_status: reviewed
Implementation: none authorized by this review
```

## Scope Reviewed

| Subtrack | Status | Primary CLI |
| --- | --- | --- |
| CB-IMPL-1 Manual Entry Dry-Run | complete | `--curriculum-registry-dry-run-status` |
| CB-IMPL-2 Local Fake Registry Records | complete | `--curriculum-registry-records-status` |
| CB-IMPL-3 Fake-Record Renderer | complete | `--curriculum-registry-renderer-status` |
| CB-IMPL-4 Fake-Record Retrieval Hooks | complete | `--curriculum-registry-retrieval-status` |

**Evidence:** PR #207 (CB-IMPL-1), PR #208 (CB-IMPL-2–4), lane closure `docs/curriculum-builder-registry-v0-2-lane-closure.md`.

**Level 1 candidates reviewed:** 0 formal ledger entries existed before this review. Prior mission final reports recommended approval-gated production workflow only.

---

## Required Review Questions

### 1. Is CB-IMPL-1 through CB-IMPL-4 coherent as a completed fake/local foundation lane?

**Yes.** The lane forms a logical pipeline:

1. **Dry-run (CB-IMPL-1)** — validate single candidate JSON files (`example-*` IDs, placeholder URIs, `would_write=false`).
2. **Local fixtures (CB-IMPL-2)** — committed multi-record envelope with `source_references` and `lesson_links`, explicit `fake_fixture_only` flags.
3. **Renderer (CB-IMPL-3)** — deterministic markdown/text metadata preview from the fixture envelope.
4. **Retrieval (CB-IMPL-4)** — deterministic field filters over fixture records.

Each subtrack has boundaries doc, status script, CLI flag, dashboard section, and tests. Coherence is strong for a read-only fake-data foundation.

**Gap:** No documented bridge from a dry-run-validated candidate to a fixture record (intentionally blocked, but the workflow seam is implicit).

### 2. Are commands, scripts, docs, fixtures, and tests discoverable and understandable?

**Mostly yes, with friction.**

**Strengths:**

- Four parallel `--curriculum-registry-*-status` flags in CLI, manifest, command index, capability map, dashboard, and `validate-all`.
- Lane closure doc provides orchestrated proof commands.
- Fixture READMEs exist under `assistant/curriculum-builder/samples/registry-v0-2-*/`.

**Friction:**

- Four separate status commands; no single aggregate lane summary command.
- Two registry surfaces coexist: live v0 (`registry/v0/registry.json`, `sample-*` IDs) and v0.2 fixtures (`example-*` IDs). Boundaries doc explains this, but discovery requires reading multiple docs.
- Roadmap Program Lane Status table did not list this lane independently; `Curriculum Builder v1` row still said "CB-IMPL subtracks remain" despite completion (stale note).

### 3. Are fake-only boundaries strong enough?

**Yes for current scope.** Multiple layers enforce fake-only:

- Envelope flags: `local_registry_mode: fake_fixture_only`, `no_production_write`, `fixture_only`, `generation_blocked`.
- Validators reject non-`example-*` IDs, `https?://` URLs, and weak student-data patterns.
- Tests verify live `registry.json` is not mutated.
- Status scripts grep for `curl`, `find`, `ollama` shell invocation.
- Negative assertions in status output.

**Weakness:** Boundaries rely on convention (path under `samples/`, ID prefix) rather than a single machine-readable authority manifest that future agents must consult first.

### 4. Places future agents might mistake fake fixtures for real registry authority?

**Yes — three confusion vectors:**

| Surface | Path | ID pattern | Risk |
| --- | --- | --- | --- |
| Live Registry v0 | `assistant/curriculum-builder/registry/v0/registry.json` | `sample-*` | Agents may treat as writable production registry |
| v0.2 local fixture | `assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json` | `example-*` | Agents may copy fixture into live registry after validation |
| Dry-run candidates | `assistant/curriculum-builder/samples/registry-v0-2-dry-run/` | `example-*` | Agents may assume dry-run success implies write authorization |

Mitigation exists in docs but is not enforced by a single authority map or aggregate guard command.

### 5. Hidden write, scan, crawl, generation, or integration risks?

**No active risks found in reviewed scripts.** All validators and retrieval are read-only Python embedded in bash. No `--write` flags, no file mutation, no network calls.

**Latent risks (design-level, not activated):**

- Duplicated inline Python validation in dry-run and local-records validators could drift from A4–A7 canonical JSON schemas.
- Renderer outputs markdown to stdout only (safe); no file write today, but a future "export preview" mission could accidentally add writes without governance.
- Retrieval filters are naive string equality; a future "semantic search" mission could introduce embeddings/RAG if boundaries are not re-read.

### 6. Are PASS/WARN/FAIL checks sufficiently meaningful?

**Adequate for foundation proof; some checks are shallow.**

**Meaningful:**

- Validator functional tests with negative fixtures (bad IDs, real URLs).
- Live registry non-mutation tests.
- CLI smoke tests for all four flags.

**Shallow / brittle:**

- Status scripts heavily use `check_file` and `grep -Fq` for doc string presence — can PASS while behavior regresses if docs stay stale.
- `curl`/`find`/`ollama` grep checks miss Python `urllib`, `subprocess`, or `requests` (not present today).
- Only two fixture records — limited field-combination coverage.
- Retrieval WARN on zero matches does not fail; intentional but could hide broken filters in CI if misconfigured.

### 7. Missing negative assertions?

| Missing assertion | Severity |
| --- | --- |
| Render preview does not write files to disk | medium |
| Retrieval does not modify fixture JSON | medium |
| Explicit "fixture path must stay under samples/" guard in status scripts | low |
| Cross-check that v0.2 validators never open `registry/v0/registry.json` for write | low (covered by mutation test only) |
| Dry-run candidate cannot be auto-promoted to fixture without human mission | low (policy only) |

### 8. Brittle checks that may create false confidence?

- **Doc-contains PASS checks** — high false-confidence risk if implementation breaks but docs remain.
- **Duplicate validation logic** — dry-run and local-records validators maintain parallel Python field lists; schema drift would not fail until someone updates one side.
- **Small fixture set** — PASS with 2 records does not prove envelope scale or edge cases.
- **Roadmap stale note** — "CB-IMPL subtracks remain" implied incomplete work when lane was done.

### 9. Safest next technical step?

**Docs/status only:** Registry Authority Map documenting v0 live vs v0.2 fixture vs future production write path, plus optional aggregate `--curriculum-registry-lane-status` command. No writes, no new fixtures resembling real curriculum.

### 10. Highest-value next teacher workflow step?

**Planning brief for teacher-reviewed manual metadata intake** — Owen defines which fictional-safe fields he would actually fill when cataloging his own resources, before any production write or Drive/NAS reference. Connects registry metadata to lesson-planning queue concepts without generation.

### 11. What requires explicit Owen approval before implementation?

- Production registry writes or `--write`
- Real metadata intake from Owen's files or cloud storage
- Copying validated candidates into `registry/v0/registry.json`
- Teacher-reviewed renderers with exported artifacts
- Retrieval over real registry or filesystem
- Any API/OAuth/network/Canvas/Drive/NAS/iCloud integration
- Lesson/worksheet/presentation generation from registry links

### 12. What should remain blocked until much later?

- Scanning, crawling, OCR, folder indexing
- Embeddings, vector DB, RAG, semantic search
- Live Canvas/Drive/NAS/iCloud resolution
- Student-data workflows
- Automated promotion from dry-run to live registry
- LLM/local inference for metadata or rendering

### 13. Real-metadata intake workflow vs more fake/local foundations?

**Plan real-metadata intake workflow first (planning-only); build minimal additional fake foundations only if planning reveals schema gaps.**

Rationale: CB-IMPL-1–4 prove the validation/render/retrieve pattern. Further fake fixtures have diminishing returns. The blocker is product/policy (what Owen will manually enter, review cadence, write boundaries), not missing fake infrastructure.

Optional small fake foundation: A4–A7 JSON schema cross-validation on fixtures (integrity, not new behavior).

### 14. Safest first PR if Owen later approves production registry workflow?

**Planning + read-only governance PR only:**

1. `docs/curriculum-builder-production-registry-workflow-plan.md` — explicit write boundaries, human review steps, rollback, no `--write` flag yet.
2. Status script proving plan exists and still says `production_writes: blocked`.
3. Negative test that no write path exists.

No actual write implementation in first PR.

### 15. What should ChatGPT review with Owen before any implementation prompt?

- Whether production registry targets v0 `registry.json` or a new v0.2 production path
- Manual entry UX: CLI-only vs future UI (planning)
- Which source systems Owen will actually use first (Drive vs NAS vs local folder)
- Review/approval states for teacher-only vs student-facing resources
- Whether lesson-planning queue should reference registry IDs yet
- Student-data and real-curriculum-content confirmation for any real titles/paths
- Explicit non-goals: no scanning, no generation, no Canvas API in v1 production workflow

---

## Top Gaps and Opportunities

| Gap | Opportunity | Blocked? |
| --- | --- | --- |
| Dual registry surfaces (v0 vs v0.2 fixture) | Registry Authority Map doc + aggregate status | No |
| Dry-run → fixture promotion unclear | Planning spec for blocked promotion path | Planning only |
| Validators not tied to A4–A7 JSON schemas | Schema cross-validation on fake fixtures | No |
| Four separate status commands | Single lane summary CLI | No |
| Lesson-planning integration | Planning doc for metadata-only handoff | Planning only |
| Production workflow undefined | Production registry workflow planning brief | Approval-gated |

---

## Safety Confirmation

This review is **proposal-only**. No implementation, runtime behavior, APIs, network calls, student data, or real curriculum content was introduced.

---

## Lane Status Update

| Field | Value |
| --- | --- |
| Lane | Curriculum Builder Registry v0.2 Local Foundation |
| Previous | Not listed in Program Lane Status; functionally `complete_pending_review` |
| New | `reviewed` |
| Evidence | This document + ledger entries + `docs/master-build-roadmap.md` § Program Lane Status |

`Curriculum Builder v1 (registry/contracts)` remains `in_progress` — renderers, generation, and integrations are not reviewed by this lane review.

---

## Recommended Next Mission

**ChatGPT planning prompt:** "Curriculum Builder Production Registry Workflow — Planning Brief (approval-gated, no writes)" for Owen review before any implementation mission.
