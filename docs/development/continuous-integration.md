# Continuous integration

CI validates pull requests and `main`. It does not deploy, publish, or call Canvas or Google.

The Saxon lesson-page deployment stays in `.github/workflows/deploy-saxon-lesson-1-pages.yml`. That workflow runs only when its own paths change on `main`, or when someone starts it by hand. Pull-request validation does not start it.

## When it runs

`.github/workflows/ci.yml` runs on:

- pull requests targeting `main`
- pushes to `main`
- pushes to `feat/automated-ci-validation` and `fix/canvas-quarter-week-live-authorization`, so those branches can start jobs before their workflow edits are only on `main`
- manual `workflow_dispatch`

The job permission is `contents: read`. It has no secrets.

## What it runs

One `Validate` job on `ubuntu-latest` with Python 3.12. `TAW_STATE_ROOT` is `/tmp/taw-ci-state/.local` on the hosted runner. `runner.temp` cannot be used in the job environment, and this path is still empty there. A missed redirect cannot see a developer machine's `.local`. The path contains `.local`, which the intake manifest self-test checks.

| Step | Command |
| --- | --- |
| Shell syntax | `bash -n` on the intake and deployment shell tests |
| Whitespace | `git diff --check` from the merge base with `origin/main` |
| Q2W5 lifecycle and integration | the `tests/q2w5-*.py` files, including approval propagation, and `python3 -m scripts.canvas_llm_intake.manifest` |
| Canvas rollover | every `tests/canvas_rollover/test_*.py`, with the repository root on `PYTHONPATH` |
| Canvas planner | `python3 -m unittest discover -s tests/canvas_planner` |
| Canvas intake and deployment | `tests/canvas-llm-intake-test.sh`, `tests/canvas-llm-deploy-test.sh`, and `tests/canvas-llm-phase-3-announcement-test.py` |
| Live authorization | `python3 tests/canvas-live-authorization-test.py` |

The rollover step fails if it executes no files. The live-authorization step always runs that test. A missing file or a failed test fails the job.

A failing step fails the job. Output is not converted into a warning.

These suites use temporary directories and fake Canvas clients. They do not need credentials. The birthday-roster check only asks `git check-ignore` about a gitignored path. It does not read a roster.

## Reproduce locally

From the repository root:

```bash
export PYTHONPATH="$PWD"
bash -n tests/canvas-llm-intake-test.sh
bash -n tests/canvas-llm-deploy-test.sh
python3 tests/q2w5-lifecycle-integrity-test.py
python3 tests/q2w5-lifecycle-correction-test.py
python3 tests/q2w5-execution-gate-test.py
python3 tests/q2w5-canonical-assessment-integration-test.py
python3 tests/q2w5-approval-propagation-test.py
python3 -m scripts.canvas_llm_intake.manifest
for test in tests/canvas_rollover/test_*.py; do python3 "$test" || exit 1; done
python3 -m unittest discover -s tests/canvas_planner
bash tests/canvas-llm-intake-test.sh
bash tests/canvas-llm-deploy-test.sh
python3 tests/canvas-llm-phase-3-announcement-test.py
python3 tests/canvas-live-authorization-test.py
```

## Diagnose a failure

Open the failed step in the Actions log. The step name is the suite. Fix the test or the code, and do not mark a failure as success. New tests that read or write `.local`, call Canvas, or need a secret do not belong in this workflow until they use a temporary root and a fake client.

## Adding a suite

Add a named step to `.github/workflows/ci.yml`. Keep the step's command identical to the local command. Document it in the table above. Do not attach the new step to the Saxon deployment workflow.

## Before merge

The `Validate` job should be green on the pull request. GitHub will not require that job until branch protection lists it. Until then, reviewers still need to look at the check instead of treating a missing required check as approval.
