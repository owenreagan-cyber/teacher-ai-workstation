# Cursor Mission — Full Product Feature Discovery and Prototype Strategy Review

**Classification:** proposal-only · Level 3 discovery · no implementation

---

## 1. Mission

Run a **Full-Product Discovery Strategy Review (Level 3)** for Teacher AI Workstation.

This is a **proposal-only strategic analysis** mission. Cursor must not implement features, prototypes, UI changes, runtime behavior, integrations, or automations.

Cursor is approved to inspect the full repo governance surface, proposal ledger, lane reviews, roadmap, and capability map; produce a ranked portfolio; update proposal docs if needed; validate; and complete the PR lifecycle for **documentation/proposal changes only**.

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
- `docs/implementation-approval-gate.md`
- `docs/engineering-constitution.md`
- Completed lane foundation/closure docs

---

## 3. Level 3 Readiness Checklist

- [ ] All program lanes marked `reviewed` in roadmap lane status, **or** Owen explicitly approved proceeding with open Level 2 items documented
- [ ] No required Level 2 lane reviews are blocking product strategy
- [ ] Owen explicitly approved this Level 3 mission
- [ ] Governance and proposal ledger are current

---

## 4. Scope

- Entire repository/product surface
- Roadmap and build queue
- Proposal ledger and lane-level reviews
- Completed foundations and governance docs
- Domain boundaries and approval gates

**Out of scope:** implementation, prototypes, runtime, APIs, network, student data, real curriculum content, scanning, generation, automation.

---

## 5. Analysis Goals

- Ranked portfolio of future capabilities (high → low priority)
- Cross-lane dependencies and sequencing implications
- Risk and approval-boundary classification for each recommendation
- Gaps between capability map and roadmap
- Consolidation of deferred/rejected proposals where appropriate
- No low-value proposal flooding

---

## 6. Proposal Rules

- Proposal-only — discovery is not implementation approval
- Check `docs/proposals/index.md` before creating entries
- No hard candidate cap, but prioritize quality over quantity
- All recommendations must state approval level required and blocked boundaries
- Use unified ledger schema in `docs/proposals/index.md`

---

## 7. Validation

```bash
git status --short
bash scripts/cursor-operating-modes-status.sh
bin/chief-of-staff --cursor-operating-modes-status
bash scripts/cursor-workflow-status.sh
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

---

## 8. PR / Merge / Branch Cleanup

If proposal or strategy docs change:

1. Feature branch → commit → push → PR → merge
2. Delete mission branch locally and remotely
3. Rerun validation on clean `main`

---

## 9. Final Report Format

## Program

`Full-Product Discovery Strategy Review (Level 3)`

## Completion Status

complete / partially complete / escalated

## Readiness

- Lanes reviewed: count / total
- Exceptions approved by Owen: yes/no

## Ranked Portfolio

| Rank | Candidate | Area | Value | Risk | Approval needed | Recommended next step |
| ---- | --------- | ---- | ----- | ---- | --------------- | --------------------- |

## Cross-Cutting Themes

Bullet list of themes across lanes.

## Proposal Ledger Updates

- Entries added/updated/deferred
- Migration or consolidation notes

## Safety Confirmation

Proposal-only. No implementation, runtime, APIs, or student data.

## Recommended Next Mission

Next build mission after strategy review.
