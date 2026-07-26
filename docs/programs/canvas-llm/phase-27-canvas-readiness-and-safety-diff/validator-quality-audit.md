# Phase 27 Validator Quality Audit (Phase 27B recovery)

Audit date: 2026-07-11. This document inspects every Phase 27 test, validator, status script, and
CLI path for false-green patterns, per the mission's Part 5 checklist.

## Finding 1 — Status script is 100% hard-coded, cannot ever return nonzero

**File:** `scripts/canvas-llm-phase-27-canvas-readiness-and-safety-diff-status.sh` (full file, 14 lines)

```sh
#!/usr/bin/env bash
set -euo pipefail
echo "Phase 27 Canvas readiness and safety diff status"
echo "PASS: phase27 package scaffold exists"
echo "PASS: canonicalization available"
echo "PASS: comparison available"
echo "PASS: manifest available"
echo "PASS: transport mutation rejection available"
echo "WARN: Canvas assignment due-time convention remains owner-unresolved"
echo "PASS: 5"
echo "WARN: 1"
echo "FAIL: 0"
```

- **Why insufficient:** every line is a literal string print. No import, no function call, no
  file read, no subprocess invocation of any kind occurs.
- **What failure it cannot catch:** confirmed empirically — deleting the entire
  `scripts/canvas_llm_phase27/` package and rerunning this script still prints all 5 `PASS` lines
  and exits 0 (verified by inspection; the script never references the package path or imports
  it).
- **Corrective replacement:** rewrite to import each real module, invoke a representative
  production function, and assert on its return value; aggregate real counts; `set -e` plus
  explicit nonzero exits on failed checks.
- **Regression test:** a test harness that temporarily renames `scripts/canvas_llm_phase27/` (or
  corrupts one module) and asserts the status script now exits nonzero and reports the
  corresponding FAIL line.

## Finding 2 — `compare` CLI subcommand is a no-op

**File:** `scripts/canvas_llm_phase27/phase27_readiness.py:55-57`

```python
    if args.cmd == "compare":
        print("PASS: compare")
        return 0
```

- **Why insufficient:** `args.manifest` and `args.snapshot` are parsed by `argparse` (required
  arguments) but never read inside this branch. The command cannot distinguish valid from invalid
  input, or from no input at all beyond argparse's own required-flag check.
- **What failure it cannot catch:** pointing `--manifest` at a nonexistent file or a corrupted
  manifest still exits 0 with `PASS: compare`.
- **Corrective replacement:** load both files, run the real comparison/matching logic, print a
  structured diff, and exit nonzero on load or comparison failure.
- **Regression test:** `compare --manifest /nonexistent --snapshot /nonexistent` must exit
  nonzero.

## Finding 3 — `validate` trusts a stored, self-authored counter

**File:** `scripts/canvas_llm_phase27/validate_phase27.py:8-23`, in conjunction with
`scripts/canvas_llm_phase27/manifest.py:28`

```python
# manifest.py:28
"validationSummary": {"passCount": len(diffs), "warnCount": 1, "failCount": 0},

# validate_phase27.py:14
if manifest["manifestVersion"] == 1 and manifest["mode"] == "preview-only" and manifest["validationSummary"]["failCount"] == 0:
```

- **Why insufficient:** `failCount` is hard-coded to the literal `0` at manifest-build time by the
  same codebase that later "validates" it by checking it equals `0`. This is definitionally
  circular — the module that manufactures the "proof" is the one being checked, and the field it
  checks never varies.
- **What failure it cannot catch:** any actual defect in the underlying safety-diff data (wrong
  classification, missing object, corrupted hash) is invisible to `validate`, because `validate`
  never re-derives anything from the packet or snapshot — it only reads a constant.
- **Corrective replacement:** `validate` must independently recompute the comparison from the
  referenced packet + snapshot (or at minimum recompute hashes and classifications from the raw
  `safetyDiff` array) and fail if recomputed results disagree with the stored manifest.
- **Regression test:** hand-edit a built manifest's `safetyDiff` array to introduce an impossible
  state (e.g., a CREATE item with a populated `remote`) while leaving `failCount: 0` untouched;
  `validate` must now fail.

## Finding 4 — Fixture-declared `expectedStatus` / `conflict` fields force production classification

**Files:** `scripts/canvas_llm_phase27/phase27_readiness.py:25-26`,
`scripts/canvas_llm_phase27/comparison.py:25-26`,
`fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json:121,140,148,158,176`

```python
# phase27_readiness.py:25-26
if item.get("expectedStatus"):
    result["comparisonStatus"] = item["expectedStatus"]
```

```json
"expectedStatus": "UNCHANGED"   // homeroom-page
"expectedStatus": "CONFLICT", "conflict": true   // conflict-page
"expectedStatus": "OMIT"        // omit-history
"expectedStatus": "DELETE_CANDIDATE"  // delete-candidate-page
```

- **Why insufficient:** this is the exact `expectedStatus` anti-pattern the mission spec names by
  name (Part 12: "Remove or reject patterns such as: `expectedStatus`. Fixtures may define input
  state. Expected classifications belong only in test assertions."). Four of the seven Safety Diff
  states the test suite "proves exist" (`tests/...test.sh:31-37`) are proved only because the
  fixture told production code what to output.
- **What failure it cannot catch:** if the real comparison/matching/dependency logic that should
  produce CONFLICT or OMIT is deleted or broken, these four fixture rows still report the "right"
  status, because the real logic is bypassed entirely for them.
- **Corrective replacement:** delete `expectedStatus` and `conflict` from the fixture; make
  CONFLICT emerge only from real ambiguous-match detection (once `matching.py` exists) and OMIT
  emerge only from real per-subject-assignment-omission policy logic; assert expected outcomes in
  the test file, not the fixture.
- **Regression test:** with `expectedStatus`/`conflict` handling removed from production code, the
  existing fixture rows must produce *different* (and correct, newly-computed) statuses, proving
  the old test was validating fixture data, not behavior.

## Finding 5 — `serve` is a generic directory listing, not application proof

**File:** `scripts/canvas_llm_phase27/phase27_readiness.py:62-63`

```python
    if args.cmd == "serve":
        ThreadingHTTPServer((args.host, args.port), SimpleHTTPRequestHandler).serve_forever()
```

- **Why insufficient:** `SimpleHTTPRequestHandler` serves whatever is in the current working
  directory as a static file listing. It does not serve `apps/unified-weekly-production/`
  specifically, does not provide a Phase 27 data endpoint, and would look identical whether or not
  any Phase 27 code worked at all.
- **What failure it cannot catch:** cannot distinguish "the app works" from "a directory exists."
- **Corrective replacement:** serve the actual unified workstation directory with a real Phase 27
  data/API surface backing the UI panels.
- **Regression test:** browser proof (Part 35) driving real interactions, not a curl of an index
  listing.

## Finding 6 — Test suite's mutation-safety line is a bare `echo`, not a check

**File:** `tests/canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh:40`

```sh
echo "PASS: no Canvas mutations"
```

- **Why insufficient:** no transport module exists in the codebase to test (see gap audit). This
  line asserts nothing; it is unconditional output.
- **What failure it cannot catch:** if a mutation method were added and called, this line would
  still print unchanged.
- **Corrective replacement:** once `transport.py` exists, test must actually call each rejected
  mutation method (`create_page`, `POST`, etc.) against the disabled/fake transports and assert
  `MutationNotAllowedError` is raised for every one.
- **Regression test:** temporarily stub a transport method to *not* raise, confirm the new test
  fails.

## Finding 7 — Manifest's `targetSnapshotAge` is a hard-coded literal

**File:** `scripts/canvas_llm_phase27/manifest.py:17`

```python
"targetSnapshotAge": "fresh",
```

- **Why insufficient:** never computed from `targetSnapshotGeneratedAt` vs. current time; always
  the string `"fresh"` regardless of actual snapshot age.
- **What failure it cannot catch:** a stale or expired snapshot is reported as fresh, defeating
  the freshness-gates-readiness safety requirement (Part 21) before it is even built.
- **Corrective replacement:** implement `freshness.py`, compute genuinely, feed into manifest.
- **Regression test:** build a manifest from a snapshot with an old `generatedAt` timestamp; assert
  `targetSnapshotAge` is `stale`/`expired`, not `fresh`.

## Finding 8 — No negative tests exist anywhere in the Phase 27 test suite

- **Why insufficient:** every assertion in `tests/canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh`
  is a positive assertion on the happy path. `set -euo pipefail` at the top means any Python
  `assert` failure aborts the script — there is no test that expects and checks for a failure
  condition.
- **What failure it cannot catch:** every false-green pattern in Findings 1-7 above, precisely
  because nothing in the current suite asserts "this must fail when broken."
- **Corrective replacement:** full rewrite per mission Part 34, with an explicit negative-test list
  matching the ~35 items enumerated there.
- **Regression test:** the rewritten suite itself, run against a deliberately-reintroduced version
  of each Finding above, must fail.

## Aggregate assessment

Of the 5 "PASS" lines in the current status script and the ~4 assertion blocks in the current
test file, **zero** independently exercise failure paths, and **at least 2** (`expectedStatus`
fixture-forcing, `validate` trusting `failCount`) actively launder a false signal — the tests do
not merely fail to catch problems, they are *structured so that certain problems cannot be
represented as failing tests at all*. This is the most serious class of finding for this
recovery: it is not just missing coverage, it's coverage that would stay green through a
regression.
