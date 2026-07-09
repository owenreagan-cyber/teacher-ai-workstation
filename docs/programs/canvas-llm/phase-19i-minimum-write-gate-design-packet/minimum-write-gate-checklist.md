# Minimum Canvas Write Gate Checklist

## Status

Preview-only checklist.

## Decision

```text
CANVAS_WRITES_REMAIN_BLOCKED
```

## Future Approval Phrase

A future phase may only proceed to a real Canvas write if Owen explicitly provides an approval phrase in that future phase.

Suggested phrase format:

```text
I APPROVE THIS ONE CANVAS WRITE FOR COURSE <course_id>: <exact operation>
```

## Minimum Required Packet

A future write packet must include:

```text
target_course_id
target_canvas_object_type
target_canvas_object_id_or_new_object_marker
operation_type
exact_before_state
exact_after_state
evidence_refs
rule_refs
medical_center_result
rollback_or_cleanup_plan
validation_plan
stop_conditions
human_approval_phrase
```

## Hard Stop Conditions

Stop if any of these are true:

- approval phrase is absent
- target course is not allowlisted
- object type is not explicitly allowed
- Medical Center result is FAIL
- Medical Center result is BLOCKED
- proposed mutation is broader than one object
- student data would be accessed
- raw `.local` metadata would be committed
- school Canvas URL would be committed
- token would be exposed
- rollback or cleanup plan is missing
- validation command is missing


## Explicit Blocked Actions

Phase 19I blocks:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- student data access
- raw `.local` metadata reads or commits
- school Canvas URL commits
- token exposure
- silent Canvas mutation
