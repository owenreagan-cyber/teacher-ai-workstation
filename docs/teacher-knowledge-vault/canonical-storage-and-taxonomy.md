# Teacher Knowledge Vault — Canonical Storage and Taxonomy

Last updated: 2026-07-04

```text
Status: planning-only — target taxonomy on paper only
Canonical storage: Google Drive and/or UGREEN NAS
Local MacBook: workshop/staging/cache only — not canonical
Real folder creation: blocked
```

## Canonical Storage Model

| Location | Role | Canonical? |
| --- | --- | --- |
| **Google Drive** | Primary canonical curriculum library | Yes |
| **UGREEN NAS** | Mirror, backup, fast local access | Yes |
| **MacBook Pro M5** | Dev workshop; optional staging/cache | No |
| **Canvas** | Publishing/deployment | No |

## Planned Target Root (Not Created)

```text
TeacherAI-Curriculum-Library/
```

## Top-Level Taxonomy (Frozen)

| Folder | Purpose |
| --- | --- |
| `00_INBOX_UNSORTED/` | Unsorted intake |
| `00_TEMPLATES/` | Templates |
| `01_MATH/` | Saxon IM5, etc. |
| `02_READING_MASTERY/` | Reading Mastery |
| `03_SPELLING/` | Spelling |
| `04_LANGUAGE_ARTS/` | Shurley |
| `05_WRITING/` | Writing |
| `06_HISTORY/` | CKHG |
| `07_SCIENCE/` | CKSci |
| `08_CLASSROOM_APPS/` | Classroom apps metadata |
| `09_PACING_GUIDES/` | Pacing guides |
| `10_TEACHER_ONLY/` | Restricted-indexable teacher materials |
| `11_STUDENT_FACING/` | Student-facing outputs |
| `12_AI_GENERATED/` | AI-generated (approval-gated) |
| `90_ARCHIVE/` | Archive |
| `99_DO_NOT_SCAN/` | Absolute exclusion |

Use `10_TEACHER_ONLY` — not 09_TEACHER_ONLY (stale taxonomy corrected).

Fixture: `assistant/teacher-knowledge-vault/samples/fake-taxonomy-target.json`

## Relationship to Curriculum Library

`docs/curriculum-library/folder-taxonomy.md` documents a related local planning view. Vault canonical taxonomy targets **Drive/NAS** authority.
