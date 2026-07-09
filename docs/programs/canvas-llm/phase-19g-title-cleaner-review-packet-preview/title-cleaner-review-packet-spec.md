# Title Cleaner Review Packet Spec

## Status

Preview-only spec.

## Required Fields

Each title-cleaner review row must include:

```text
input_title
proposed_title
decision
confidence
needs_review
rule_ref
evidence_ref
blocked_reason
```

## Required Review Behavior

The review packet must make safe decisions visible.

Approved examples may show a proposed canonical title.

Ambiguous examples must show:

```text
decision: needs_review
proposed_title: blank
blocked_reason: ambiguous_input_requires_review
```

## Canonical Examples

```text
SM5 Test 1 -> SM5: Test 1
SM 5: Test 1 -> SM5: Test 1
SM5 Fact Test 2 -> SM5: Fact Test 2
SM5 Study Guide 3 -> SM5: Study Guide 3
ELA4 Test 4 -> ELA4: Test 4
RM4 Test 5 -> RM4: Test 5
Spelling Test 6 -> RM4: Spelling Test 6
SP4 Spelling Test 6 -> RM4: Spelling Test 6
Test 7 -> needs_review
Chapter 4 Test -> needs_review
```

## Non-Goals

The review packet does not write to Canvas and does not approve Canvas mutation.
