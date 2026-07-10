# Phase 21D Assignment Creation Rules

## Scope

Assignments may only be created in sandbox course `24399`.

## Idempotency

Before creating an assignment, the agent must search existing sandbox assignments by exact name.

If an exact assignment already exists, the agent must record:

```text
reused_existing_assignment
```

and not create a duplicate.

## Naming

Examples:

```text
Phase 21D Sandbox Math Lesson 1
Phase 21D Sandbox Math Lesson 1 Practice
Phase 21D Sandbox Math Lesson 1 Homework Odd
Phase 21D Sandbox Math Lesson 2 Homework Even
```

## Defaults

Sandbox assignments should use conservative defaults:

```text
points_possible: 0
published: false when supported
```

No due dates are required in Phase 21D.

## Friday Rule

Friday uses Lesson 5 but has no homework assignment.
