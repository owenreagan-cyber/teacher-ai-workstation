# Locked Decisions

Owner-approved rules that must not be inferred, reinterpreted, or silently changed. If a rule here conflicts with a newer explicit Owen instruction, the newer instruction wins; otherwise these are binding.

```text
Status: owner-approved, locked
```

## Hard boundaries

- 4A - Reagan / Room 203
- authoritative pacing tab = 4A - Reagan
- blank pacing stays blank (do not infer or fill)
- never invent curriculum
- paper homework/classwork due same day at 11:59 PM America/New_York
- established paper assignments use `on_paper`
- Homeroom newsletter is family/Homeroom content, not a subject academic summary
- existing weekly pages update in place (never duplicated unnecessarily)
- Homeroom rolling newsletter updates in place
- grade-check safety rules remain unchanged
- grade-entry approval rules remain unchanged

## Operating contract rules (reference)

The full owner-approved operating contract is:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

Key locked items it covers:

- subject agenda pages contain only heading, date range, reminders, Mon-Fri, In Class, Homework
- reminders may list assessment names and dates only (no links, attachments, study guides, resources)
- assignment titles require the approved course-code prefix (`RM4:`, `SM5:`, `ELA4:`, `HIST4:`, `SCI4:`)
- all assignments worth 100 points, display as percentages, due same day at 11:59 PM
- inactive History/Science subject must remain untouched
- Homeroom newsletter cadence is monthly (rolling), school/event links permitted only there
- nothing authorizes automatic publication

## Rotating-subject quarter activation (2026-2027)

Authority: `config/curriculum/canvas/quarter-subject-activation-2026-2027.json`.

- Q1 / Q3: History is the active rotating content course; build/update History weekly pages and communications. Science receives no weekly instructional builds unless Owen explicitly overrides.
- Q2 / Q4: Science is the active rotating content course; build/update Science weekly pages and communications. Do not generate normal weekly History instructional content.
- Q2 / Q4 History redirect: maintain a simple History-course redirect message/announcement:
  > We are learning Science this track! Please check the Science Canvas page for this week's agenda, assignments, and updates.
  - Exact final wording remains teacher-editable.
- Never infer activity from the quarter number alone; the quarter-activation config is authority.

## Rule authority

These decisions are `OWNER_POLICY`. Anything observed from live Canvas is `LIVE_CANVAS_PRECEDENT` (precedent, not policy). Model inferences are `MODEL_INFERENCE` and must never silently become policy. See `config/fpk/rule-authority.json`.
