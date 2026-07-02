# Curriculum Builder Registry v0.2 — Manual Entry Dry-Run

Last updated: 2026-07-02

```text
Status: dry-run validation only
Program: Curriculum Builder — CB-IMPL-1
Closure status: complete_cb_impl_1_dry_run
Registry writes: blocked
Active --write: blocked
```

## Purpose

First safe implementation step after metadata contract schemas A4–A7. Provides a **fake-data-only dry-run path** for validating candidate manual registry entries against repo-local contract expectations **without** writing to `assistant/curriculum-builder/registry/v0/registry.json`.

## Implemented Now

| Component | Path |
| --- | --- |
| Dry-run boundaries | `docs/curriculum-builder-registry-v0-2-dry-run-boundaries.md` |
| Validation rules | `docs/curriculum-builder-registry-v0-2-validation-rules.md` |
| Fake samples | `assistant/curriculum-builder/samples/registry-v0-2-dry-run/` |
| Dry-run validator | `scripts/curriculum-builder-registry-v0-2-dry-run.sh` |
| Status script | `scripts/curriculum-builder-registry-v0-2-status.sh` |
| CLI | `bin/chief-of-staff --curriculum-registry-dry-run-status` |
| Tests | `tests/curriculum-builder-registry-v0-2-dry-run-test.sh`, `tests/curriculum-builder-registry-v0-2-status-test.sh` |

## Future / Blocked

| Capability | Status |
| --- | --- |
| Persistent registry writes | blocked — separate approval mission |
| Active `--write` flag | blocked — separate approval mission |
| Real registry records / production intake | blocked — separate approval mission |
| File ingestion / scanning / crawling | blocked |
| Lesson generation | blocked |
| Canvas / Drive / NAS / iCloud APIs | blocked |
| Student data / real curriculum content | blocked |

## Dry-Run Semantics

- Validates candidate JSON files only
- Prints PASS/WARN/FAIL and a dry-run summary (`would_write: false`)
- Does **not** mutate registry, samples, git, or docs
- Does **not** resolve placeholder URIs

## Orchestrated Proof

```bash
bash scripts/curriculum-builder-registry-v0-2-dry-run.sh
bash scripts/curriculum-builder-registry-v0-2-status.sh
bin/chief-of-staff --curriculum-registry-dry-run-status
bash tests/curriculum-builder-registry-v0-2-dry-run-test.sh
bin/chief-of-staff --dashboard
```

## Recommended Next Mission

**Production Registry Workflow** (approval-gated; requires explicit intake). Local foundation lane CB-IMPL-2–4 complete — see `docs/curriculum-builder-registry-v0-2-lane-closure.md`.

## Non-Activation

No registry mutation, no network, no ingestion, no generation.
