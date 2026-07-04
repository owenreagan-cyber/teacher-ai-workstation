# ADR-0007: Human-Approved Organization with Event Log and Rollback

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** File ops are destructive without audit trails.  
**Decision:** Approval required; dry-run (M5+); append-only event log; rollback records.  
**Consequences:** No silent mutations.  
**Blocked runtime:** Auto rename/move/copy/delete in M0–M4.  
**Validation hooks:** `docs/teacher-knowledge-vault/event-log-foundation.md`; M1 `fake-event-log.json`
