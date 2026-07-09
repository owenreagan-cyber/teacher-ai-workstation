# Canonical Subject Prefix Rules

## Status

APPROVED_PATTERN

## Rule

Future Canvas LLM Center generation must use canonical subject prefixes.

AI does not choose prefixes.

Historical variations are aliases only.

## Canonical Prefix Table

| Subject | Canonical Prefix |
|---|---|
| Math | SM5 |
| Reading | RM4 |
| Spelling | RM4 |
| Language Arts / Shurley | ELA4 |
| History | HIST4 |
| Science | SCI4 |

## Required Examples

Math:

```text
SM5: Test 1
```

Reading:

```text
RM4: Mastery Test 1
```

Spelling:

```text
RM4: Spelling Test 5
```

Language Arts / Shurley:

```text
ELA4: Chapter 4 Test
```

History:

```text
HIST4: Chapter 5 Test
```

Science:

```text
SCI4: Chapter 1 Test
```

## Alias Policy

Historical prefixes and title variations may be preserved for search, migration, or legacy matching only.

They must not be used as future output formats unless Owen explicitly changes the canonical table.

## Validation Requirements

Future validators should fail or block when generated assignments/pages use non-canonical prefixes.

Spelling must use RM4 because it shares Reading course identity.
