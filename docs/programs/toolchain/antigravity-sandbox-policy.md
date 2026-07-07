# Antigravity Sandbox Policy

Status: documentation/status only.

## Classification

Antigravity 2.0 is [CANDIDATE], [SANDBOX-ONLY], [BLOCKED-IN-PRIMARY], and [MANUAL-COPY-ONLY].

Docs do not authorize install or execution. This policy is a safety gate, not a tool activation approval.

## Primary repo prohibitions

The primary repo must not contain or perform:

- Antigravity install.
- `agy`, `agy init`, or `agy migrate` execution.
- Active `.antigravity/` directory.
- `.antigravity.json`.
- agy config or migration files.
- Runtime agent execution or background processes.
- Mac system changes.
- Active settings that alter repo behavior.

## Sandbox-only requirements

Any future evaluation must occur in a disposable sandbox clone only. Before evaluation, the sandbox must remove `origin`, add `SANDBOX_ONLY_DO_NOT_MERGE.md`, and add `VALIDATION_JOURNAL.md`.

Direct sandbox-to-main merge is blocked. Useful results must be copied manually into a normal primary-repo branch after human review.

## Credential and integration blocks

The sandbox policy blocks credentials and secrets. It also blocks Canvas API/OAuth/live reads/writes, Canvas publishing, Drive/NAS/iCloud access, Supabase/Firebase, student data, real curriculum ingestion, network/API/OAuth/live integrations, production writes, and active `--write` behavior.

## Exit criteria

A future sandbox evaluation may be considered only if all evidence is documented in the validation journal and no blocked runtime behavior occurs. Passing documentation checks never promotes Antigravity out of candidate status.
