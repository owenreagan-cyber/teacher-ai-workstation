# Rule Source Linking Schema

## Status

Preview-only schema specification.

## Purpose

Rule Source Linking ensures every canonical rule can be traced back to evidence.

## Link Types

```text
supports
conflicts_with
supersedes
derived_from
aliases
requires_review
blocks
```

## Link Record Schema

| Field | Required | Description |
|---|---:|---|
| link_id | yes | Stable ID, for example `LINK-CANVAS-0001` |
| from_type | yes | evidence, rule, question, diagnostic |
| from_id | yes | Source ID |
| link_type | yes | supports, conflicts_with, supersedes, derived_from, aliases, requires_review, blocks |
| to_type | yes | evidence, rule, question, diagnostic |
| to_id | yes | Target ID |
| reason | yes | Human-readable reason for the link |
| created_in_phase | yes | Phase ID |
| review_status | yes | proposed, reviewed, approved, rejected |

## Example

```text
EV-CANVAS-0003 supports RULE-CANVAS-0007
```

## Conflict Example

```text
EV-CANVAS-0012 conflicts_with EV-CANVAS-0021
```

## Future Use

Future diagnostics should use links to explain:

- why a rule exists
- what evidence supports it
- what conflicts remain
- whether a preview is safe
- whether a write gate remains blocked

## Boundary

Links are explanatory and diagnostic.

They do not authorize Canvas writes.
