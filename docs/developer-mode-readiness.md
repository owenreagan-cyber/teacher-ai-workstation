# Developer Mode Readiness

Last verified: 2026-06-26

## What Developer Mode Means For Owen

Developer Mode means a safe local workspace for building small teaching and classroom tools before anything becomes a deployed app or connected automation.

It can include:

- local lesson tools
- classroom helpers
- small apps and scripts
- teacher productivity workflows
- future web/app prototypes
- 3D printing workflow tools

Developer Mode should support practical teacher work first: planning, drafting, organizing, checking, and prototyping.

## What Developer Mode Does Not Mean Yet

Developer Mode does not yet mean:

- public deployment
- production database setup
- student data systems
- paid API secret handling
- Gmail automation
- Drive automation
- Calendar automation
- email sending
- background folder indexing
- autonomous publishing or deletion

## Current Repo Readiness

Ready now:

- Chief of Staff CLI foundation.
- Lesson support workflow.
- Lesson planning workspace scaffold.
- Developer Mode folder structure.
- Reusable local project templates.
- App development support workflow.
- Project memory structure.
- Intake review queue.
- Safety and permission docs.
- 3D Agent readiness docs and templates.
- Phase 1 readiness checklist.

Not ready yet:

- selected local indexing plan.
- external service connectors.
- secrets/capability broker.

## Safe Starter Project Types

- [small: 1-2 days] lesson plan generator scaffold
- [small: 1-2 days] rubric helper
- [small: 1-2 days] worksheet/checklist generator
- [small: 1-2 days] vocabulary/game activity builder
- [medium: about 1 week] parent email draft helper
- [medium: about 1 week] classroom materials organizer
- [medium: about 1 week] 3D print idea tracker
- [larger: multiple PRs] local lesson app prototype
- [larger: multiple PRs] product catalog / 3D print QA helper

## 3D Printing Readiness

The repo already contains a future 3D Design Agent lane:

- `docs/3d-printing-roadmap.md`
- `docs/3d-printing-day-1-setup.md`
- `3d-agent/README.md`
- `3d-agent/templates/`
- `3d-agent/verification/`
- `3d-agent/workflows/`

The 3D lane is advisory. The agent can warn, classify, and recommend review, but the human operator makes final print decisions. Slicer/printer automation remains a later optional phase after safety gates are proven.

## Required Safety Rules

- No student sensitive data by default.
- No secrets in the repo.
- Local prototypes first.
- Human review before sending, sharing, publishing, or printing.
- Explicit permission before connected services.
- Use approved source material for factual, standards-based, curriculum, history, science, and date-based content.
- Keep Gmail, Drive, Calendar, and email integrations out of early Developer Mode.
- Treat parent email tooling as draft-only until a later permissioned workflow exists.

## Recommended Developer Mode First Step

Recommended first step: local project template scaffold for lesson/app tools.

That scaffold should come after the Chief of Staff command launcher / status dashboard. The dashboard will make it easier to see whether memory, intake, safety, and Phase 0E transition checks are healthy before new lesson/app tools begin.
