# Phase E Project Metadata Intelligence Pilot

## Scope

The only approved project is `/Users/owen/Projects/history`. The runner accepts
no source argument and performs no filesystem traversal. Output remains beneath
the ignored `.local/chief-of-staff/workspace/` root.

## Identity separation

| Identity | Meaning |
| --- | --- |
| `project:history` | Stable project concept |
| `observation:<run>:history-project` | One physical metadata observation |
| `representation:history:local-git` | Local Git representation |

None of these identities inherits authority from another.

## Git allowlist

Exactly five operations are available:

- Detect whether the approved root is a Git work tree.
- Verify that Git's repository root equals the approved root.
- Read the current branch only.
- Read the HEAD reference only.
- Produce a porcelain dirty-state summary.

The dirty summary stores counts, never paths. Git runs with optional locks and
the filesystem monitor disabled. Checkout, reset, pull, commit, stash, branch
creation, history, messages, branch enumeration, diff content, and every unknown
operation are rejected.

## Evidence

The snapshot records root existence, directory status, repository detection,
current branch, HEAD, count-only dirty state, trust, freshness, and review state.
The live state candidate defaults to `unknown`; Git recency or dirtiness cannot
decide activity, importance, production status, or abandonment.

One `related_to_resource_registry` candidate is prepared from the approved
project mapping. It is unreviewed, non-authoritative, and never linked
automatically.

## Exclusions

No README, source file, package manifest, dependency data, commit message,
commit history, issue data, secret, credential, or file content is opened or
stored. No project code is built or tested, and the project repository is never
modified.
