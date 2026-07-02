# Chief of Staff Approval and Blocker Queues

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Chief of Staff v1 Agent Core — Program B4
Read-only: yes
Task creation: no
Gate bypass: no
```

## Purpose

Define how Chief of Staff **reports** approval and blocker queues without bypassing the Implementation Approval Gate or Engineering Constitution.

## Queue Concepts

| Queue | Meaning | Chief of Staff role |
| --- | --- | --- |
| Approval queue | Work requiring Owen approval or intake | Report categories; do not auto-approve |
| Blocker queue | Active stop markers and blocked capabilities | Report blockers; do not clear |
| Escalation queue | Constitution-level conflicts | Point to `docs/engineering-constitution.md` |

## approval queue categories

Items that require explicit mission authorization:

- New implementation tracks (`docs/implementation-approval-gate.md`)
- Real registry records (Curriculum Builder; no student data)
- Renderers and generation surfaces
- Canvas LLM stop marker supersession
- Drive/Gmail/Canvas API/OAuth connectors
- Mac wallpaper/widget/shortcut install missions
- Local LLM install and model downloads
- Lovable / cloud API connection
- 3D Builder CAD/slicing/printing activation
- Health Monitor repair or System Updater apply
- Automation and background jobs

## Blocked Capability Categories

| Category | Blocker |
| --- | --- |
| Canvas LLM runtime | Stop marker active |
| Implementation default | Not approved by default |
| Lovable integration | Program G1 planning only |
| Cloud AI APIs | No routing active |
| Local LLM | Program D approval-gated |
| Mac system/widgets/shortcuts | Approval-gated |
| 3D CAD/slicing/printing | Program J approval-gated |
| Drive/Gmail/Canvas API | Last-stage integrations |

## CLI Surfaces

```bash
bin/chief-of-staff --approval-queue
bin/chief-of-staff --blocker-queue
```

Both commands are deterministic, local-only, and read-only.

## Boundaries

Chief of Staff must not:

- create tasks in external systems
- schedule work
- call APIs
- process student or curriculum content
- bypass Owen approval or the Implementation Approval Gate
