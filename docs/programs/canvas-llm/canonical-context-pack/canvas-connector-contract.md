# Canvas Connector Contract

## Purpose

The Canvas connector provides **read-only** access to normalized Canvas metadata in operational readiness builds.

It answers:

```text
Can the workstation read target Canvas context safely?
```

It does **not** write, publish, update, delete, or store credentials in the repo.

## Architecture

`CanvasConnector` with modes:

| Mode | Default | Writes | Network |
| --- | --- | --- | --- |
| `fake` | yes | disabled | none |
| `sandbox` | no | disabled | blocked until human-authorized credentials exist outside repo |

## Configuration

`CanvasConnectionConfig` fields:

- `mode`
- `enabled`
- `base_url`
- `credential_state`

Credential states:

- `missing`
- `configured`
- `disabled`

Tokens are **never** stored in repo files, logs, or status output.

## Normalized read models

- `CanvasCourseRecord`
- `CanvasPageRecord`
- `CanvasAssignmentRecord`
- `CanvasAnnouncementRecord`

## Read methods

- `read_course()`
- `read_page()`
- `read_assignment()`
- `read_announcement()`

All methods are read-only. Write paths are permanently disabled.

## Redaction

Logs and audit output must redact:

- tokens
- authorization headers
- private URLs

## Explicitly blocked

- Canvas POST/PUT/DELETE
- automatic publishing
- credential storage in repo
- student data ingestion

## Commands

```bash
bin/chief-of-staff --canvas-connector-status
python3 scripts/canvas_llm_phase22/canvas_connector.py self-test
bash tests/canvas-llm-canvas-connector-test.sh
bash scripts/canvas-llm-canvas-connector-status.sh
```

## Non-activation

This contract describes a local-first connector interface. Sandbox network reads remain blocked unless separately approved and credentialed outside the repo.
