# Canvas LLM Phase 21D — Sandbox Week Render Write + Assignment Creation

## Purpose

Phase 21D prepares the first real sandbox Canvas write for a rendered weekly page and sandbox assignment creation.

## Target

```text
course_id: 24399
page title: Q1W1
page slug: q1w1
```

## Test Week Logic

```text
Monday: Lesson 1, odd homework
Tuesday: Lesson 2, even homework
Wednesday: Lesson 3, odd homework
Thursday: Lesson 4, even homework
Friday: Lesson 5, no homework
```

## Allowed Write Shape

Phase 21D may update only the existing sandbox page body for `q1w1`.

Phase 21D may create sandbox-only assignments in course `24399`.

Assignments must be idempotent. If an exact assignment name already exists, the agent must reuse it instead of creating a duplicate.

## Required Write Gates

```text
--allow-writes
--target-course-id 24399
--target-page-slug q1w1
--approval-phrase PHASE_21D_SANDBOX_WEEK_WRITE_APPROVED
```

## Additional Sandbox People Safety Gate

Before any write, the agent must perform a read-only People/enrollment verification for course `24399`.

Expected safe condition:

```text
People list is empty OR contains only Owen Reagan / owen.reagan@thalesacademy.com.
```

If unexpected People are found, the write must block with:

```text
BLOCKED_UNEXPECTED_PEOPLE_IN_SANDBOX_COURSE
```

People data must not be written, committed, or used for student/grade logic.

## Blocked

- production course writes
- reference course writes
- announcement send/notify
- module writes
- file writes
- deletion
- publish/unpublish changes
- grades
- people writes
- settings
- submissions
- gradebook
- analytics
- student data
