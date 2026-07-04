# ADR-0010: Canvas as Future Publishing Target, Not Storage

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** Canvas holds deployed content but should not be canonical library.  
**Decision:** Canvas is publishing target; Drive/NAS canonical; Canvas connector read-only first (M7).  
**Consequences:** Reconciliation tracks Canvas-only vs Drive-only drift.  
**Blocked runtime:** Canvas API, publishing in M0/M1.  
**Validation hooks:** `docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md`
