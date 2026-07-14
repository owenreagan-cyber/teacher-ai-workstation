# Phase 27B Security Review

Scope: every file added or modified by the Phase 27B recovery
(`scripts/canvas_llm_phase27/*`, the Phase 27 endpoints added to
`scripts/canvas_llm_phase26/phase26_workstation.py`, `fixtures/canvas-llm/phase-27/*`,
`apps/unified-weekly-production/{index.html,workstation.js}`, the rewritten status
script and test suite).

## Method

Grepped for each forbidden category, then manually classified every hit as one
of: **documentation/comment**, **negative test / rejection-list definition**
(defensive code that names the bad thing in order to reject it), or
**executable behavior** (would actually be a problem). Only the third category
would be a finding.

## Results by category

| Category | Hits | Classification |
|---|---|---|
| `authorization`, `bearer`, `password`, `secret`, `access_token`, `api_key` | `models.py`, `canvas_snapshot.py`, `canonicalize.py`, `pagination.py` | All are entries in rejection/exclusion lists (`_CREDENTIAL_MARKERS`, `FORBIDDEN_SNAPSHOT_KEYS`, `_VOLATILE_KEYS`, `_SENSITIVE_QUERY_KEYS`). None are actual credential values. |
| `studentId`, `grade`, `roster` | `canvas_snapshot.py`, `export_package.py` | All are forbidden-field-name entries used to **reject** input containing them, or a regex used to scan exported files for their presence. No actual student data anywhere. |
| `POST`/`PUT`/`PATCH`/`DELETE` | `transport.py`, `phase27_readiness.py` (serve handler), `phase26_workstation.py` (serve handler) | All are rejection points (`_MUTATING_HTTP_METHODS`, `do_POST`/`do_PUT`/etc. handlers that call `send_error(405, ...)`). Confirmed via test: no code path completes a POST/PUT/PATCH/DELETE request. |
| `create_page`/`create_assignment`/`publish_object`/etc. calls | `health_checks.py:184`, `phase27_readiness.py:29` | Both are calls made *specifically to prove they raise* `MutationNotAllowedError` (the mutation-disabled-state health check and the transport-readiness computation). Neither completes; both are wrapped in `try/except MutationNotAllowedError`. |
| Email / SMTP / OAuth | none | No hits anywhere in the added/modified files. |
| School Canvas URLs | none | Every URL in every fixture is `https://canvas.example.invalid/...`. Verified via `grep -rnoE 'https?://[a-zA-Z0-9.-]*canvas[a-zA-Z0-9.-]*'` across all fixtures. |
| Deploy / Publish / Upload buttons | none | Only hit for "publish"/"deploy"/"upload"/"email" as substrings anywhere in the UI is the pre-existing Phase 26 "Deployment Manifest" preview tab label, which is a read-only JSON viewer, not a control. No such button exists in the new Phase 27 panels; only `Import Snapshot`, `Refresh Comparison`, `Export Manifest`, `Approve Preview`, `Revoke Approval` buttons were added. |
| `.local` tracked files | none | `git ls-files '.local/*'` returns empty. |

## Notable fixes made *during* this recovery as a result of self-review

Two real bugs were found and fixed while building this (not pre-existing
Phase 27A issues, introduced and caught within this session):

1. `DEFAULT_LEDGER_PATH` and `DEFAULT_EXPORT_ROOT` were originally relative
   paths. Because Phase 26's `serve` command `os.chdir()`s into the app
   directory before Phase 27 code runs, this silently wrote the SQLite ledger
   and export package under `apps/unified-weekly-production/.local/...`
   instead of the repo-root-anchored `.local/canvas-llm/...` path. Both are now
   absolute, anchored via `Path(__file__).resolve().parents[2]`. Regression
   tests added.
2. The deployment manifest's `provenance` field stored the *absolute* local
   filesystem path to the Phase 26 packet and snapshot files, which the
   export package's own forbidden-content scanner correctly flagged as a
   `/Users/...` path leak. Fixed to store repo-relative paths; `validate`'s
   independent-recomputation path was updated to resolve those relative paths
   against the repo root rather than the process's current working directory
   (so it isn't itself broken by the same cwd-dependence class of bug).
   Regression test added asserting no provenance entry starts with `/`.

## Conclusion

No credentials, student data, real school URLs, or executable mutation path
exists in the Phase 27B recovery. The two cwd/path-leak bugs found during this
review were fixed and are now covered by regression tests in
`tests/canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh`.
