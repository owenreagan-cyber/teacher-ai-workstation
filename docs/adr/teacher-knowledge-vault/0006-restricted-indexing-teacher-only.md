# ADR-0006: Restricted-Indexing — `10_TEACHER_ONLY` vs `99_DO_NOT_SCAN`

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** Teacher materials need grounding but must not reach students.  
**Decision:** `10_TEACHER_ONLY` restricted-indexable; `99_DO_NOT_SCAN` absolutely excluded. Use `10_` not `09_TEACHER_ONLY`.  
**Consequences:** Folder-class indexing policies differ.  
**Blocked runtime:** Indexing `99_DO_NOT_SCAN`; student exposure of teacher-only.  
**Validation hooks:** `docs/teacher-knowledge-vault/restricted-indexing-and-pacing-guardrails.md`
