# Canvas LLM Phase Memory Rule

## Purpose

Every Canvas LLM phase must leave behind durable repo-tracked memory before handoff.

This prevents future work from depending on archived chats, temporary Codex workspaces, assistant memory, copied terminal inventories, or unavailable sandbox paths.

## Rule

Every Canvas LLM phase must create or update a phase memory artifact before the phase is considered ready for handoff.

The memory artifact must summarize:

- current branch and commit state
- completed work
- validated evidence sources
- rejected, unavailable, or untrusted evidence sources
- owner decisions
- safety boundaries
- validation output
- next recommended phase or task
- handoff summary for the next chat or build session

## Authority

Archived chats, temporary Codex workspaces, pasted inventories, assistant memory, and old sandbox paths are not authoritative unless their contents are converted into a repo-tracked phase memory file or cited in a current handoff.

Future chats should begin from:

1. the latest repo-tracked handoff file
2. the latest phase memory file
3. current git status
4. current Chief of Staff status output

## Required Files

Each active Canvas LLM phase should maintain:

```text
docs/programs/canvas-llm/current-handoff.md
docs/programs/canvas-llm/memory/phase-XX-memory.md
```

## Safety Boundary

The phase memory system does not authorize:

- Canvas writes
- Canvas API calls
- live Canvas fetches
- assignment creation
- page creation
- file movement
- file upload
- publishing
- student data access
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure

It is documentation and continuity only.
