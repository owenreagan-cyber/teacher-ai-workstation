# Resource Resolution Hierarchy

Phase 25 resolves approved resources using a deterministic precedence order:

1. exact verified lesson or assessment match
2. owner-approved correction
3. approved reusable resource
4. approved lesson-range match
5. approved parity or assessment-family match
6. verified source alias
7. historical approved pattern
8. unverified candidate
9. unresolved

Teacher-only, answer-key, and assessment-secure resources never become student-facing HTML links. When a blocked resource is the best available candidate, the resolver records a block reason and keeps the item in the review queue.
