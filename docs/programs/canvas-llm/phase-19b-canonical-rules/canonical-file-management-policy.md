# Canonical File Management Policy

## Status

APPROVED_PATTERN for safety model.

## Vision

```text
AI File Assistant
```

## Near-Term Phase

```text
READ ONLY
```

Allowed:

- discover files
- classify files
- detect duplicates
- map relationships
- suggest organization
- create cleanup plans

## Future Phase

```text
WRITE-GATED FILE ORGANIZER
```

Before any operation:

1. show proposed changes
2. human approves
3. execute exact approved operation
4. verify result

## Never Allowed Without Explicit Gate

- automatic rename
- automatic move
- automatic delete
- automatic upload
- silent alteration of source materials

## Principle

```text
AI may organize information.
AI may not silently alter source materials.
```

## Future Safe Operation Model

Every future file operation must have:

- exact source path/reference
- exact destination path/reference
- operation type
- reason
- preview
- approval
- execution result
- verification result
- rollback/cleanup expectation

## Boundary

This policy does not authorize current file mutation.
