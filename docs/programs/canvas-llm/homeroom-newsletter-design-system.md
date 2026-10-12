# Homeroom Newsletter Design System

```text
Status: canonical design system (documentation)
Theme v1: CANONICAL / APPROVED
Theme v2: CANDIDATE (Fall / Level Up — awaiting Owen visual review)
```

## Purpose

The Homeroom family newsletter is a page-first, rolling Canvas artifact with a
polished visual identity. This document records that identity as a reusable
design system so future seasonal themes (Fall, Winter, Spring, Track-Out, …)
can be built without losing the approved original.

Reusable artifacts:

- Theme v1 record: `config/curriculum/canvas/themes/homeroom-newsletter-theme-v1.json`
- Theme v1 template: `config/curriculum/canvas/templates/homeroom/homeroom-newsletter-theme-v1.html`
- Theme v2 (candidate): `config/curriculum/canvas/themes/homeroom-newsletter-theme-v2-fall-level-up.json`
- Theme v2 template (candidate): `config/curriculum/canvas/templates/homeroom/homeroom-newsletter-theme-v2-fall-level-up.html`

## v1 — canonical visual rules

Extracted from the approved live Homeroom newsletter ("4th Grade Happenings").

| Rule | Value |
| --- | --- |
| Max width | ~900px, centered |
| Font | Arial, Helvetica, sans-serif |
| Text color | #1e293b (slate), line-height 1.55 |
| Hero | large rounded, gradient (indigo → blue → teal), centered, pill badges |
| Cards | rounded content cards (14–18px radius) |
| Callouts | left-border sections (6px solid) in indigo/blue/orange/red/green |
| Utility cards | three-column, 5px top accent border |
| Birthdays | one card per student, rotating soft tints, first name only |
| Quick links | dark block (#0f172a), white pill links |
| Staff favorites | light lavender container, per-staff cards |
| Spacing | 22px section margin, 22px card padding, 10px inner gap |
| Border radius | pill 999px, large 18px, card 14px, small 12px |
| Responsive | flex-wrap, min-width per card |

Canvas-safety: inline styles only, no external CSS dependency, no JavaScript,
no background images, no CSS animation. Gradient degrades to a solid color
gracefully.

## Dynamic content / privacy

The reusable template contains **no** student names, birthdays, live Canvas IDs,
or school URLs. Dynamic sections are `{{PLACEHOLDER}}` tokens replaced at build
time from persisted monthly state. Birthday tiles use first name only and are
omitted entirely when no birthdays are supplied.

## v2 — Fall / Level Up (candidate)

A warm, energetic fall-classroom candidate with subtle anime / slice-of-life
school-club energy. Palette and full spec live in the v2 theme record. v2 is a
**candidate** — it must not be promoted to canonical or applied to live Canvas
until Owen approves it visually.

## Theme lifecycle

```text
v1 CANONICAL (current)
v2 CANDIDATE (awaiting review)
```

Future themes follow the same pattern: preserve each approved theme as its own
versioned record + template under `config/curriculum/canvas/themes/` and
`config/curriculum/canvas/templates/homeroom/`.
