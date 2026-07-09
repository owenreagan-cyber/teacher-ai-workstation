# Canvas LLM Handoff Breadcrumb Guardrail

## Problem

Older Canvas LLM status scripts check `current-handoff.md` for exact historical strings.

When a new phase rewrites the current handoff, those exact strings can be accidentally removed.

This causes repeated breadcrumb failures even when the actual phase work is correct.

## Required Preflight

Before major phase validation, run:

```bash
python3 scripts/canvas-llm-handoff-breadcrumb-repair.py --repair
python3 scripts/canvas-llm-handoff-breadcrumb-repair.py --check
```

## Safety Boundary

The repair script:

- does not call Canvas APIs
- does not fetch live Canvas data
- does not write to Canvas
- does not read `.local` metadata
- does not access `CANVAS_TOKEN`
- only repairs `docs/programs/canvas-llm/current-handoff.md`

## Future Direction

Eventually, old status scripts should read from a canonical breadcrumb manifest instead of each script hardcoding separate historical strings.

Until then, this guardrail prevents repeated handoff breadcrumb regressions.
