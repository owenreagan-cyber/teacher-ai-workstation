# Chief of Staff Operating Model

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Chief of Staff v1 Agent Core — Program B1
```

## Purpose

Describe how Chief of Staff coordinates teacher workstation work **without** performing specialist execution.

## Operating Flow

```text
Teacher request
  → intake
  → safety and boundary check
  → approval gate check
  → capability selection
  → tool/subsystem routing
  → specialist execution (external or future)
  → validation
  → proof
  → next-action recommendation
  → closeout (planned B2+)
```

## Key Principle

**Chief of Staff coordinates and reports. Specialist systems perform specialized work. Approval gates decide what may activate.**

## Routing Examples (Planning)

| Need | Route to | CoS role |
| --- | --- | --- |
| Repo implementation | Cursor | Recommend mission; prove merge |
| Curriculum architecture | Gemini (manual) | Document routing; no API |
| Classroom app idea | Lovable (future G1) | Gate approval; track status |
| Local private task | Ollama (future D) | Policy only; no install |
| Classroom object idea | 3D Builder (future J) | Intake/safety gate concept |
| Curriculum status | Foundation status commands | Orchestrate PASS/WARN/FAIL |
| Pre-merge confidence | `--proof-run`, dashboard | Enforce proof workflow |

## Daily / Weekly Operating Assistant (Planned — Program B2+)

Future surfaces (not implemented in B1):

| Surface | Status |
| --- | --- |
| Daily briefing | planned |
| Next-action recommendation | **implemented** (`--next-action`) |
| Blocker review | planned |
| Approval queue review | planned |
| Validation summary | partial (`--validate-all`) |
| Closeout | planned |
| Weekly planning review | planned |
| Phase transition review | planned |

No scheduling, reminders, notifications, background jobs, Gmail, Calendar, or Slack integrations.

## Next-Action Architecture

Deterministic recommendations use repo-local sources only:

- `docs/master-build-roadmap.md`
- `docs/build-queue.md`
- `assistant/memory/active-priorities.md`
- dashboard health (when invoked in proof flows)
- validation results
- implementation approval gate status
- Canvas stop marker
- blocked capability manifests

Implementation: `scripts/chief-of-staff-next-action.sh` — no LLM inference.

## Non-Activation

Planning documentation only. No automation or live routing.
