# Chief of Staff Closeout Workflow

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Chief of Staff v1 Agent Core — Program B3
Read-only: yes
Automation: no
```

## Purpose

Define the **end-of-work closeout** workflow for Chief of Staff missions. Closeout is a proof and handoff discipline — not an automated git or GitHub workflow.

## Closeout Checklist

| Step | Proof | Command |
| --- | --- | --- |
| Final dashboard proof | Dashboard healthy | `bin/chief-of-staff --dashboard` |
| Status script proof | Phase + cursor workflow | `bash scripts/phase-1-status.sh` |
| Smoke test proof | CLI smoke | `bash tests/smoke-chief-of-staff-cli.sh` |
| Operating command proof | v1 operating tests | `bash tests/chief-of-staff-v1-operating-test.sh` |
| PR proof | PR reviewed/merged | `gh pr view` (manual) |
| Merge commit proof | On local main | `git log -1` |
| Local main proof | Clean tree | `git status` |
| Branch deletion proof | No feature branches | `git branch -a` |
| Non-activation proof | No forbidden runtime | mission report |
| Next mission recommendation | Roadmap/build queue | `docs/master-build-roadmap.md` |
| Remaining work logging | Deferred items | PR body or build queue |

## CLI Surface

`bin/chief-of-staff --closeout` prints the checklist and a local snapshot. It does **not**:

- merge PRs
- delete branches
- push to remote
- run network commands
- mutate repository state

## Branch deletion proof

After merge, verify branch deletion proof locally:

```bash
git checkout main
git pull
git branch -d feature/...
git push origin --delete feature/...
git fetch --prune
git branch -a
```

## Non-Activation Proof

Confirm the mission did not activate:

- APIs, OAuth, or network integrations
- lesson generation or student data workflows
- automation or background jobs
- Mac wallpaper/widget/shortcut installation
- Local LLM install or inference

## Related

- Proof workflow: `docs/chief-of-staff-proof-workflow.md`
- Program B closure: `docs/chief-of-staff-v1-program-b-closure.md`
