# Phase 21D People Sandbox Verification

## Purpose

The People check is a read-only sandbox confidence gate.

It is not permission to use People data for student, grade, notification, or analytics logic.

## Allowed

The agent may read People/enrollments only for sandbox course `24399`.

The agent may write only a sanitized local summary under ignored `.local`.

Allowed summary fields:

```text
people_count
owner_user_present
unexpected_people_count
sandbox_people_gate_status
```

## Safe Condition

```text
People list is empty OR contains only Owen Reagan / owen.reagan@thalesacademy.com.
```

## Blocking Condition

If unexpected People are present, the write must stop with:

```text
BLOCKED_UNEXPECTED_PEOPLE_IN_SANDBOX_COURSE
```

## Blocked

- People writes
- People reads for production/reference courses
- raw People data in committed files
- raw People data in docs
- student/grade/analytics use
