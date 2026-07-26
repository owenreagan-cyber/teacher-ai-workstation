# Write Gate Contract

## Purpose

The write gate is a **design-only** safety boundary for future Canvas write operations.

It answers:

```text
Would this write be allowed if execution were enabled?
```

In the readiness build, **only `BLOCKED` is usable**. Execution remains disabled.

## Model

`WriteGateDecision` fields:

- `operation`
- `target_type`
- `target_id`
- `approved`
- `approved_by`
- `approved_at`
- `rollback_required`
- `validation_result`
- `gate_state`

## States

| State | Readiness build |
| --- | --- |
| `BLOCKED` | active default |
| `APPROVED` | design-only; does not execute |
| `EXECUTED` | not available |

## Rules

Writes are rejected when:

- write packet validation fails
- human approval is missing
- connector is disabled
- writes are not explicitly enabled (they remain disabled globally)

`attempt_write()` always returns `BLOCKED` in readiness builds.

## Explicitly blocked

- automatic deployment
- Canvas publishing
- email delivery
- background execution

## Commands

```bash
bin/chief-of-staff --canvas-write-gate-status
python3 scripts/canvas_llm_phase22/write_gate.py self-test
bash scripts/canvas-llm-write-gate-status.sh
```

## Non-activation

This contract documents a gate only. It does not perform Canvas writes or activate sandbox publishing.
