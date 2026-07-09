# Canonical Friday Rules

## Status

APPROVED_PATTERN

## Rule

Friday is protected from normal homework by default.

## Canonical Friday Behavior

On Friday:

- no normal homework assignments
- non-test assignments are blocked by default
- At Home section is omitted unless explicitly required
- tests are allowed
- reminder communication is allowed
- celebratory copy remains optional and teacher-controlled

## At Home Rule

Default Friday page behavior:

```text
omit At Home
```

Do not add Friday homework text unless the pacing data explicitly requires it and the exception is teacher-approved.

## Assignment Rule

Default Friday assignment behavior:

```text
create_assign = false
```

Exception:

```text
Test
```

## Unknown / Not Canonical Yet

The legacy idea of replacing Friday In Class with a completion checklist is not canonical.

It remains:

```text
UNKNOWN_NEEDS_REVIEW
```

## Validation Requirements

Future validators should check:

- no non-test homework assignments on Friday
- no Friday At Home section unless explicit exception exists
- Friday reminders do not create assignment mutations
- celebratory copy is optional and teacher-controlled
