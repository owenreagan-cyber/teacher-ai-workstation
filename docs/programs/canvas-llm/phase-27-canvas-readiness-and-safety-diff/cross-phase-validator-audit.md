# Cross-Phase Validator Audit (Phase 22-26), for Phase 27B Recovery

Audit date: 2026-07-11. Per mission Part 6: this document classifies Phase 22-26 status scripts
and test harnesses for the same false-green patterns found in Phase 27, without broadly rewriting
older phases. No older-phase files were modified as a result of this audit.

## Classification

| Phase | Classification | Evidence |
|---|---|---|
| 22 — Predictive Weekly Planning Workstation | **Mostly trustworthy** | `scripts/canvas-llm-phase-22-...-status.sh` runs real `python3 -m py_compile`, a real `self-test` subcommand against a real SQLite path (`--db ... self-test`), and inline Python asserting instructional-calendar behavior. It also uses a `has()` helper (`grep -Fq -- "$2" "$1"`) for ~25 checks like `"module includes render_agenda_html"` — these are shallow string-presence checks (could in principle pass on a comment or dead code) but are only used for secondary UI/API surface confirmation, not for computing PASS/FAIL on core business logic, and they sit alongside the real `self-test` and calendar-assertion checks. `validate_canonical_knowledge.py` (51 checks) independently asserts real config values (lesson-to-Power-Up mappings, checkout fluency numbers, spelling word counts) — genuine data validation, not counter-trusting. |
| 23 — Weekly Content Production Engine | **Mostly trustworthy, one shallow spot** | `tests/canvas-llm-phase-23-...-test.sh:392-393` gates the real validator's exit code first (`python3 "$V" "$DEMO" ... || { ...; exit 1; }` — this correctly fails the suite), but the following line, `grep -q '^PASS: 1$' /tmp/p23-validate.txt \|\| true`, is toothless: the `\|\| true` means this specific assertion can never itself fail the build regardless of what the grep finds. Because the line above already exits on real validator failure, this is a **redundant, non-load-bearing** check today — but it is exactly the `\|\| true` masking pattern the mission asks to hunt for, and it should not be treated as a real assertion. **Not fixed in this recovery** (out of Phase 27's blast radius, does not undermine Phase 27 trust); recommend a follow-up phase-23 patch to drop the `\|\| true` or replace with a real nonzero-on-mismatch check. |
| 24 — Predictive Teacher Brain | **Trustworthy** | Real `py_compile`, real "predicted week builds"/"validates" invocations of production scripts, `[[ FAIL_COUNT -eq 0 ]]` real exit gate. |
| 25 — Curriculum Source Intelligence | **Trustworthy** | Same pattern as 24: real build/validate invocation of production scripts, real exit gate. |
| 26 — Unified Weekly Production Workstation | **Trustworthy** | `scripts/canvas-llm-phase-26-...-status.sh` builds a real demo packet via `python3 "$M" build-demo ...`, runs the real validator, `grep`s for exact validator output lines (anchored with `^...$`, i.e. matching real validator log format, not documentation text), then runs an inline Python block asserting concrete structural facts about the built packet (`schemaVersion == 1`, `len(weekSelection.weeks) == 37`, exception-inbox contents, deployment-manifest operation status). Ends with a real `[[ "${FAIL_COUNT}" -eq 0 ]]` gate. This is the strongest of the five status scripts and is a reasonable model for the Phase 27 rewrite. |

## Common weak pattern found across phases (not disqualifying)

Every phase's `has()`/`grep -Fq` style checks for "module includes `<name>`" or "UI includes
`<label>`" are string-presence checks, not behavioral checks — they would pass if the named
symbol appeared in a comment, a docstring, or dead code rather than working logic. This is a
**shallow but non-disqualifying** pattern: in each phase these checks are a minority of total
checks and are backed up by separate real build/validate/self-test invocations that do exercise
production code paths. This is different in kind from Phase 27, where the *primary* PASS lines
themselves were unconditional echoes with no backing check at all.

## What was explicitly checked and found absent in Phases 22-26

- No `expectedStatus`-style fixture-forced-classification fields were found in any Phase 22-26
  fixture (`grep -rl expectedStatus fixtures/canvas-llm/phase-2[2-6]*` returned nothing).
- No status script among 22-26 is fully hard-coded — each computes real `PASS_COUNT`/`FAIL_COUNT`
  from `pass`/`fail` function calls gated by actual checks, and each ends with a real
  `[[ FAIL_COUNT -eq 0 ]]` exit gate. Phase 27's status script has neither trait.
- `.local` hygiene checks (`git ls-files .local | grep -q .` → fail if tracked) are real and
  consistent across 22, 23, 26.

## Conclusion

Phases 22, 24, 25, and 26 do not require remediation as part of this recovery — their PASS counts
are backed by genuine behavior. Phase 23 has one non-load-bearing `|| true` worth a future,
separate small fix, noted above but intentionally not touched here to keep this recovery scoped to
Phase 27. Phase 27 is the outlier: its status script and several of its CLI paths are the first
occurrence in this codebase of unconditional-print "validation" and counter-trusting rather than
computed behavior.
