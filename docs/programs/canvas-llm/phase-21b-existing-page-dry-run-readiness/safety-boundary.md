# Phase 21B Safety Boundary

Phase 21B is dry-run only.

## Allowed

- Canvas read access using owner-supplied local token
- sandbox course inventory for `24399`
- reference-course inventory for `21919`, `21944`, `21957`
- dry-run planning
- local ignored artifacts under `.local/`
- documentation updates
- status validation

## Blocked

- Canvas writes
- `--allow-writes`
- `--mode experiment`
- page creation
- page updates
- page publish/schedule changes
- front-page mutation
- announcements or notification sends
- assignment mutation
- file mutation
- module mutation
- grades
- people/users
- settings
- submissions
- gradebook
- analytics
- student data

## Token Rule

`CANVAS_TOKEN` must never be printed, committed, or written into documentation.
