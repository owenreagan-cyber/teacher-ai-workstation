# Canvas Authority And Conflict Policy

```text
Status: PHASE_0_DOCS_ONLY
Classification: authority policy
```

## Authority Order

Use this order when Canvas planning notes conflict:

1. Hard safety boundaries and Owen approvals.
2. Repo authority docs in `docs/master-plan/` and `docs/programs/canvas-llm/`.
3. Existing Canvas LLM freeze/stop-marker docs.
4. Fake/local fixtures and report templates.
5. Planning inbox or external notes labeled as candidates.

## Conflict Handling

- If a note implies live Canvas access, mark it blocked.
- If a note implies student data, mark it blocked.
- If a note implies generation or publishing, mark it blocked.
- If a note references Supabase/Firebase as an active direction, mark it deprecated and convert useful ideas to local-first planning.
- If evidence is not repo-backed, mark it candidate or unknown.

## Human Decision Gate

Owen must explicitly approve any move from docs/status-only planning toward live Canvas access, data sweep, generation, validation runtime, export, publishing, or self-healing behavior.
