# Decision Memory

## Purpose

Track meaningful project decisions so the Chief of Staff can explain why the repo is structured this way.

Decisions should record why something was decided, not just temporary timing status. Operational timing and current next steps belong in `active-priorities.md`.

## Decisions

### Use Markdown memory before databases

- Date: Initial planning phase
- Decision: Use explicit Markdown memory files before databases, vector indexes, embeddings, or background jobs.
- Reason: Keep memory inspectable, beginner-friendly, and easy to review before use.
- Applies to: Chief of Staff memory, project continuity, writing style memory.
- Review later: After Phase 1D and before any indexing phase.
- Source: Phase 1C planning.

### Build terminal CLI before app UI

- Date: Initial planning phase
- Decision: Build a terminal CLI before React or app UI.
- Reason: Prove the assistant loop safely with explicit Markdown context before building more surface area.
- Applies to: Chief of Staff implementation order.
- Review later: After Phase 1D.
- Source: Phase 1B planning.

### Keep Gmail/Drive/Canvas connectors for later

- Date: Initial planning phase
- Decision: Delay Gmail, Google Drive, and Canvas connectors.
- Reason: Avoid broad data access before permissions, memory, and intake review are proven.
- Applies to: future connectors and data access.
- Review later: Phase 1F and Phase 1G.
- Source: roadmap planning.

### Keep the 3D Design Agent separate from but coordinated by the Chief of Staff

- Date: Initial planning phase
- Decision: Treat 3D Design Agent as a future first-class specialist coordinated by the Chief of Staff.
- Reason: 3D work has separate verification, business, safety, and IP/reference concerns.
- Applies to: 3D printing roadmap and Chief of Staff coordination.
- Review later: Phase 3D-1.
- Source: Phase 0C planning.

### Delay opening the new MacBook Pro until installer readiness is proven

- Date: Initial planning phase
- Decision: Delay first boot and installer run until the repo has a verified installer, memory foundation, intake queue plan, and final Phase 0D audit, unless Owen intentionally decides to run the installer earlier.
- Reason: Avoid opening the new MacBook and running an incomplete setup, then needing to rework the machine or rerun major setup steps immediately.
- Applies to: MacBook Pro Day 1 setup, installer readiness, roadmap planning.
- Review later: After Phase 1D and Phase 0D Final Installer Audit.
- Source: roadmap planning.

### 3D verification is advisory and cannot block printing

- Date: Initial planning phase
- Decision: Keep 3D verification checklists advisory. The human operator makes the final print decision.
- Reason: The system can warn, classify, and recommend review, but should not claim printer-control authority.
- Applies to: 3D Design Agent readiness, verification docs, Bambu Studio workflow.
- Review later: Before any slicer/printer automation discussion.
- Source: Phase 0C planning.
