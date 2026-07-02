# Chief of Staff Proof Workflow

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Chief of Staff v1 Agent Core — Program B
Aligns with: .cursor/rules/teacher-ai-workstation-senior-engineer.mdc
```

## Purpose

Define the proof workflow Chief of Staff enforces for local-first, auditable workstation changes.

## Proof Stack

| Proof | Command / Script | When |
| --- | --- | --- |
| Dashboard | `bin/chief-of-staff --dashboard` | Pre-merge, post-merge on `main` |
| Phase status | `bash scripts/phase-1-status.sh` | Full repo health audit |
| Cursor workflow | `bash scripts/cursor-workflow-status.sh` | Governance and roadmap checks |
| Validation orchestration | `bin/chief-of-staff --validate-all` | Core subsystem validators |
| Smoke CLI | `bash tests/smoke-chief-of-staff-cli.sh` | CLI regression |
| Proof runner | `bin/chief-of-staff --proof-run` | Pre-merge bundle (`scripts/run-workstation-proof.sh`) |
| Operating commands | `bash tests/chief-of-staff-v1-operating-test.sh` | Program B commands + validate-all + proof-run |
| Daily operations | `bash tests/chief-of-staff-daily-operations-test.sh` | `--daily-status`, `--closeout`, queues, mode |
| Closeout checklist | `bin/chief-of-staff --closeout` | End-of-work template |
| PR proof | `gh pr view`, diff review | Before merge |
| Merge commit | `git log -1` on `main` | After merge |
| Branch deletion | `git branch -a`, `git fetch --prune` | After merge — branch deletion proof |
| Local main clean | `git status` | Final proof |
| Non-activation | Manual review + status docs | No APIs/automation activated |

## PASS/WARN/FAIL Semantics

- Status scripts report `PASS:`, `WARN:`, `FAIL:` counts in Summary sections.
- Dashboard aggregates section summaries; final health must remain green on `main`.
- Do not weaken or remove existing checks to force green.

## Senior Engineer Lifecycle

```text
pull main → branch → implement → validate → fix → PR → merge
  → pull main → delete branches → prune → validate on clean main → report proof
```

## Future Proof Surfaces (Planned)

- `bin/chief-of-staff --prove-main` — local main cleanliness bundle
- Branch cleanup proof command — feature branch inventory

## Non-Activation

Proof workflow is read-only orchestration. It does not mutate Mac settings, install packages, or call external services.
