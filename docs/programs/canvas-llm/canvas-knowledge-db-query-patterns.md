# Canvas Knowledge DB Query Patterns

```text
Status: phase_5_fake_local_query_patterns
Classification: documentation/status only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

This document defines future source-backed query shapes using fake/local JSON fixtures only.

## Required Lookup Chain

Every future answer must be traceable:

```text
Question -> Answer -> Fact(s) -> Evidence -> Source Reference -> Source Class -> Evidence Level -> Approval Status
```

If any link is missing, stale, unverified, or blocked, the answer is not authoritative.

## Example Query Pattern

Question:

```text
What Canvas banner pattern should a page use?
```

Fake/local answer path:

```text
fake-qa.json
-> fake-facts.json
-> fake-evidence.json
-> fake-sources.json
-> fake-patterns.json
```

## Blocked Behavior

Phase 5 does not approve live Canvas lookup, RAG, embeddings, AI-generated answers, runtime query services, SQLite writes, production course data, student data, or real curriculum ingestion.
