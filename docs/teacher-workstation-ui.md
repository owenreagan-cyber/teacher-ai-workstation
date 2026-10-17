# Teacher Workstation UI

```text
Status: read-only local UI (foundation)
Command: bin/teacher-workstation
Module: Canvas Weekly Planner
```

## Architecture

The UI is a **cockpit** over the existing intake engine. It reads the local
staging/deployment packets under `.local/canvas-llm/` and renders a
teacher-facing view. It duplicates no curriculum, Canvas, pacing, approval, or
lifecycle logic.

```text
UI (apps/teacher-workstation, vanilla JS)
  └─ read-only JSON API (scripts/teacher_workstation/server.py, stdlib http.server)
       └─ adapter (scripts/teacher_workstation/adapter.py)
            └─ existing intake modules (canvas_llm_intake) + .local packets
```

## Stack

Python stdlib `http.server` (no new dependencies) + vanilla HTML/CSS/JS (no
framework). This matches the repo's existing plain-JS apps and avoids adding a
web framework solely for a local read-only dashboard.

## Local-only boundary

- Binds to `127.0.0.1` only (never `0.0.0.0`).
- Default port `4310`.
- No external hosting, cloud deployment, tunnel, or remote access.

## Launcher

```bash
bin/teacher-workstation            # start (prints URL; does NOT open browser)
bin/teacher-workstation --no-open  # same; browser opening is not implemented
bin/teacher-workstation --help
```

Startup banner:

```text
Teacher Workstation
Local URL: http://127.0.0.1:4310
Mode: READ ONLY
Canvas writes: DISABLED
```

## Read-only API

```text
GET /api/status
GET /api/home
GET /api/weeks
GET /api/week/{quarter}/{week}
GET /api/week/{quarter}/{week}/questions
GET /api/completed
```

Write verbs (`POST`/`PUT`/`PATCH`/`DELETE`) return `405`. There is no write
path and no hidden write endpoint.

## Safety constraints

- Canvas writes: `POST=0 PUT=0 PATCH=0 DELETE=0`.
- The Canvas token, Authorization headers, verifier-bearing URLs, and secrets
  are **never** emitted to the browser, API JSON, HTML, JS, or logs.
- No student names, grades, submissions, parent emails, health info, or PII.
- No browser localStorage/sessionStorage for sensitive state (browser is
  display-only; backend/local files are the state source).

## Screens

Home · Weekly Planning (Monday–Friday subject grid) · Subject detail · Day detail
(Phase 2) · Assignments · Announcements · Questions · Review & Publish (read-only)
· Completed Weeks · System Status.

## Future phases (documented only — not implemented)

- **Phase 2** — edit day/subject, owner overrides, answer questions,
  partial-week intake, impact preview.
- **Phase 3** — approvals in the UI.
- **Phase 4** — guarded deployment (separate workflow).
- **Phase 5** — Homeroom/newsletter module.
- **Phase 6** — broader Teacher Workstation modules.
