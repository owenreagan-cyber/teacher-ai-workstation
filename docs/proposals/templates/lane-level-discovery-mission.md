# Cursor Mission — Lane-Level Feature Discovery and Prototype Proposal Review

**Lane:** `[INSERT LANE NAME]`

**Classification:** proposal-only · Level 2 discovery · no implementation

---

## 1. Mission

Run an **End-of-Lane Discovery Review (Level 2)** for `[INSERT LANE NAME]`.

This is a **proposal-only** analysis mission. Cursor must not implement features, prototypes, UI changes, runtime behavior, integrations, or automations.

Cursor is approved to inspect lane docs/status/scripts/tests/commands, review prior Level 1 candidates, update proposal docs if needed, validate, and complete the PR lifecycle for **documentation/proposal changes only**.

---

## 2. Authority Documents

Inspect before work:

- `docs/cursor-operating-modes-and-approval-gates.md` — § Three-Level Discovery Governance
- `docs/teacher-workstation-domain-boundaries.md`
- `docs/proposals/index.md`
- `docs/master-build-roadmap.md` — Program Lane Status
- `docs/build-queue.md`
- `assistant/memory/active-priorities.md`
- `docs/teacher-workstation-capability-map.md`
- Lane-specific foundation/closure docs for `[INSERT LANE NAME]`

---

## 3. Preconditions

- Lane `[INSERT LANE NAME]` is marked `complete_pending_review` in roadmap lane status
- No Level 2 review has completed for this lane since its foundation closure
- Owen explicitly approved this Level 2 mission

---

## 4. Scope

- One completed lane: `[INSERT LANE NAME]`
- All docs, status scripts, tests, and commands belonging to that lane
- Level 1 discovery candidates connected to this lane since the last lane review
- Roadmap, build-queue, and capability-map context

**Out of scope:** implementation, prototypes, runtime, APIs, network, student data, real curriculum content, scanning, generation.

---

## 5. Proposal Rules

- Proposal-only — discovery is not implementation approval
- Review prior Level 1 candidates before creating new recommendations
- At most **five** full proposal ledger entries unless Owen approves a larger discovery sprint
- Check `docs/proposals/index.md` for duplicates before adding entries
- Classify each candidate: value, risk, technical complexity, student-data risk, curriculum-content risk, API/network requirement, recommended next step

---

## 6. Risk Classification

For each recommendation, classify:

| Dimension | Options |
| --- | --- |
| Risk | low / medium / high |
| Technical complexity | low / medium / high |
| Student-data risk | none / possible / blocked |
| Curriculum-content risk | none / possible / blocked |
| API/network requirement | none / future / blocked |

---

## 7. Validation

```bash
git status --short
bash scripts/cursor-operating-modes-status.sh
bin/chief-of-staff --cursor-operating-modes-status
bash scripts/cursor-workflow-status.sh
bin/chief-of-staff --dashboard
```

Add lane-specific status commands if the lane has them.

---

## 8. PR / Merge / Branch Cleanup

If proposal docs change:

1. Feature branch → commit → push → PR → merge
2. Delete mission branch locally and remotely
3. Rerun validation on clean `main`
4. Mark lane `reviewed` in `docs/master-build-roadmap.md` **only if** this Level 2 review completed or Owen explicitly approves the status

---

## 9. Final Report Format

## Program

`Lane-Level Discovery Review — [INSERT LANE NAME]`

## Completion Status

complete / partially complete / escalated

## Lane Reviewed

- Lane name
- Prior Level 1 candidates reviewed (count)
- New proposal entries created (count; max 5 unless approved)

## Proposal Recommendations

| Candidate | Area | Value | Risk | Recommended Next Step | Ledger entry? |
| --------- | ---- | ----- | ---- | --------------------- | ------------- |

## Lane Status Update

- Previous status
- New status (if changed)
- Evidence

## Safety Confirmation

Proposal-only. No implementation, runtime, APIs, or student data.

## Recommended Next Mission

Next build or discovery mission after lane review.
