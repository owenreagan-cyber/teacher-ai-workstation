# Chief of Staff Mode Status — Operating Context

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Chief of Staff v1 Agent Core — Program B5
Mode switching: conceptual only
Mac changes: no
Automation: no
```

## Purpose

Define **operating context modes** for Chief of Staff planning. Modes are descriptive labels that help Owen and Cursor align on focus. They do **not** change Mac settings, install widgets, or trigger automation.

## Operating Modes

| Mode | Focus | System impact |
| --- | --- | --- |
| Planning Mode | Lesson/weekly planning review | none |
| Development Mode | Repo/engineering missions (Cursor) | none |
| Curriculum Mode | Curriculum Builder foundations | none |
| Lesson Planning Mode | Lesson planning scaffold review | none |
| Teaching Mode | Classroom delivery focus | none |
| Canvas Prep Mode | Frozen Canvas export planning | none |
| Review Mode | Grading/review workflows | none |
| Closeout Mode | End-of-day proof and handoff | none |

## What Modes Do Not Do

Modes do **not**:

- change Mac wallpaper or appearance
- install widgets or shortcuts
- open apps automatically
- modify local system state
- switch AI models or routing at runtime
- activate integrations

## CLI Surface

`bin/chief-of-staff --mode-status` prints the mode table and planning hints. It does not switch modes.

## Related Programs

Future Mac Workstation Experience (Program E) may extend mode documentation. Program E does not activate from this command.
