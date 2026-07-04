# ADR-0005: Resource → Representations → Sources Identity Model

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** Same homework may exist as PDF, Canvas file, answer key.  
**Decision:** Resource is canonical object; Representations link to Source Items at Sources.  
**Consequences:** Duplicate detection merges pending review; graph-based identity.  
**Blocked runtime:** Auto-merge; path-as-primary-key.  
**Validation hooks:** `docs/teacher-knowledge-vault/resource-identity-model.md`; M1 `fake-resources.json`
