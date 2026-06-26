# Phase 1 Readiness Checklist

This is a planning document only. Do not build Phase 1 in this PR.

The next major build direction is:

- Teacher Chief of Staff.
- Developer Mode for lesson tools/apps.
- lesson planning assistant workflows.
- safe classroom productivity automation.

## A. Repo / Developer Readiness

- [ ] `main` branch is clean.
- [ ] final setup verifier passes.
- [ ] Phase 0E verifier passes:

  ```bash
  bash scripts/verify-phase-0e.sh
  ```

- [ ] GitHub auth works.
- [ ] Codex workflow works.
- [ ] Raycast status tools are optional but useful.
- [ ] Apple Shortcuts status tools are optional but useful.

## B. Teacher Chief Of Staff Readiness

- [ ] local memory docs are available.
- [ ] intake queue docs/scripts are available.
- [ ] Chief of Staff memory files are current.
- [ ] `assistant/memory/active-priorities.md` reflects Phase 0E completion before serious Phase 1 work.
- [ ] `assistant/memory/projects.md` reflects Phase 0E completion before serious Phase 1 work.
- [ ] no email, Drive, or Gmail automation happens without explicit permission.
- [ ] drafts and classroom artifacts require human review.
- [ ] future student data handling is careful, minimal, and explicit.

## C. Developer Mode Readiness

- [ ] app/tool ideas start with small local scripts or docs.
- [ ] no public deployment yet.
- [ ] no production database yet.
- [ ] no paid API keys in repo.
- [ ] no secrets in code.
- [ ] local prototypes come first.
- [ ] classroom tools stay human-reviewed.

## D. Lesson / App Build Queue Ideas

These are unordered ideas. A follow-up PR should prioritize them before implementation.

- lesson plan generator scaffold.
- rubric helper.
- worksheet/checklist generator.
- parent email draft helper.
- student grouping/planning helper with no sensitive data by default.
- 3D print classroom object idea tracker.
- vocabulary/game activity builder.
- standards-aligned planning docs, if standards are manually provided or approved.

## E. Next Recommended PRs

1. Phase 1A/B/C recap and current Chief of Staff status audit.
2. Chief of Staff command launcher / status dashboard.
3. Lesson planning workspace scaffold.
4. Developer Mode project templates.
5. Safe local document indexing plan.
6. Later: permissioned Gmail/Drive integrations.
7. Later: secrets/capability broker.

Do not build these in this PR.
