# Phase 27B Browser Proof

## Tooling limitation (reported before any install, per mission instructions)

Neither Playwright (Python or Node) nor the harness's `chromium-cli` headless
driver is installed in this environment, and this repository has no existing
project skill or script for automated browser driving. Per the mission's
instruction to report this limitation before installing anything, the
options were presented to the owner; the owner chose to verify visually
rather than have Playwright installed.

## What was verified by direct HTTP execution (real server, real endpoints, not mocked)

The real app server (`python3 scripts/canvas_llm_phase26/phase26_workstation.py serve`)
was started and driven with `curl` against the actual running process --
this exercises the same server, routes, and production code a browser would
hit; it just doesn't render the DOM or click buttons.

- `GET /` -> 200, serves the real `apps/unified-weekly-production/index.html`.
- `GET /api/phase27/packet` -> 200, returns a live packet built by real
  production code (`build_packet`) on every request. Confirmed the response
  contains all seven Safety Diff statuses
  (`CREATE, UPDATE, UNCHANGED, BLOCKED, CONFLICT, OMIT, DELETE_CANDIDATE`),
  20 health check results, and a `transportReadiness` block with
  `mutationRejectionVerified: true`.
- `GET /api/phase27/ledger-status` -> 200, reports real ledger integrity,
  schema version, and event count from the actual SQLite file.
- `POST /api/phase27/approve` on an eligible object -> `{"ok": true}`,
  persisted to the real ledger (confirmed via a subsequent `ledger-status`
  event-count increase).
- `POST /api/phase27/approve` on a CONFLICT object -> HTTP 409 with a
  rejection reason, proving the approval gate runs server-side, not only in
  client-side JS.
- `POST /api/phase27/revoke` immediately after an approve (same wall-clock
  second) -> 200, which is also the regression test for the ledger
  primary-key bug found and fixed during this recovery (see
  `security-review.md`).
- `POST /api/phase27/export` -> 200, writes all 11 required export files to
  the real, absolute, repo-anchored export path.
- `POST` / `PUT` / `PATCH` / `DELETE` against `/index.html` -> all return 405
  from the server's own mutation-rejecting handler, in addition to the
  transport-layer rejection already proven by the unit/negative tests.

## Owner's manual browser review (real, and the source of four fixes)

The owner opened the running app directly in a browser (not a substitute --
the actual DOM-rendering verification the section above could not provide)
and reviewed the rendered Phase 27 panels. This caught four real defects that
HTTP-level `curl` proof above did not surface, because they were about
*meaning* and *data completeness*, not endpoint status codes:

1. **CONFLICT/BLOCKED/OMIT/DELETE_CANDIDATE items had an enabled "Approve
   Preview" button.** DELETE_CANDIDATE in particular had no blockers and was
   not in `NON_APPROVABLE_STATUSES`, so it was genuinely approvable server-side
   too, not just a UI cosmetic issue. Fixed in `approval_gate.py`
   (`NON_APPROVABLE_STATUSES` now explicitly `{CONFLICT, BLOCKED, OMIT,
   DELETE_CANDIDATE}`) and mirrored in the UI's button-disabled logic.
   Regression test added covering all six named prohibited cases (CONFLICT,
   generic BLOCKED, archived-course BLOCKED, due-time BLOCKED, OMIT,
   DELETE_CANDIDATE), each asserting both rejection and that no ledger
   approval record was created.
2. **"Health: FAIL" next to the software status script's "FAIL: 0" read as
   contradictory.** They answer different questions: the status script
   validates the *software*; the manifest's prior single "Health" pill
   conflated that with *this specific demo week's content readiness* (which
   is expected to be blocked -- the fixture deliberately contains a
   CONFLICT and a due-time-blocked assignment to prove those states work).
   Fixed by adding `systemValidationStatus` to the manifest (PASS unless a
   real structural defect -- a dependency cycle or missing edge -- exists)
   and relabeling the UI to show both signals separately: "System
   validation: PASS" and "Demo manifest readiness: BLOCKED".
3. **Resource verification showed "resource verification subsystem not yet
   built."** Fixed by reusing the Phase 25/26 resolved-resource state that
   already exists in every Phase 26 packet (`resourceResolution.resolvedResources`,
   with real `verificationStatus`/`visibility`/`deploymentPolicy` fields) to
   classify each resource as verified / unverified / missing / teacher-only /
   assessment-secure / blocked. No new resource-verification subsystem was
   built -- this only reads what Phase 25/26 already computed.
4. **`la-worksheet-page` was BLOCKED (correctly, via dependency propagation)
   but absent from `manifest.dependencies.blocked`.** The manifest rebuilt its
   own dependency graph without seeding it with objects already
   BLOCKED/OMIT/CONFLICT for intrinsic reasons, so propagated blocks were
   invisible in that summary even though the underlying status was correct.
   Fixed by seeding `manifest.py`'s graph construction the same way
   `safety_diff.py` already does.

All four fixes are covered by new tests in
`tests/canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh` and were
re-verified against a live rebuild before this document was finalized.

## What still requires a final owner look

The owner has not yet re-opened the browser against the *updated* UI
(simplified Safety Diff cards with copy-ready content and Approve/Revoke/Copy
actions, collapsed Expert Details section, and the two separated status
pills). The server remains running at `http://127.0.0.1:18830/` for that
final pass. Everything above this section is either direct HTTP-level proof
against the real running server, or the owner's own prior browser
observations (which found real bugs, now fixed and tested) -- neither is a
substitute for looking at the final rendered page, which is why the app is
being left running rather than the browser-proof requirement being marked
fully closed here.
