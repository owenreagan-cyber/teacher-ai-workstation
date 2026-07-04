# Classroom Timer & Stopwatch — Local Runtime Prototype

Owen-approved **Level 3** local-only prototype. **No other app** is runtime-approved.

## Usage

Open `index.html` locally in a browser (file:// or local static server). No network required.

## Features

- Countdown and stopwatch modes
- Start, pause, reset
- Static preset buttons (1m, 3m, 5m, 10m, Warmup, Transition, Exit ticket)
- Large classroom-readable display (high contrast, tabular numerals)
- Screen-reader status region and preset announcements (text only — no audio)
- Visible focus rings on all controls

## Keyboard

| Key | Action |
| --- | --- |
| Space | Start or pause (when focus is not on a button) |
| R | Reset (when focus is not on a button) |
| 1–7 | Apply preset by position (when focus is not on a button) |
| Tab | Move between mode, controls, and preset buttons |

Buttons activate with Enter/Space when focused. A skip link jumps to the main timer panel.

## Level 3 Hardening (not Level 4)

This prototype includes accessibility polish only: focus visibility, keyboard presets, aria-live announcements, duplicate-interval guards, and expanded static safety tests. It does **not** add audio, persistence, widgets, shortcuts, or Mac wrappers.

## Blocked (not in this prototype)

- Audio, animations, localStorage/sessionStorage, cookies
- Network, CDN, external scripts/fonts
- Student data, curriculum data, persistence
- Widgets, shortcuts, Mac wrappers

## Authority

- Planning: `docs/classroom-utilities/classroom-timer-stopwatch-planning.md`
- Runtime packet: `docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-implementation-packet.md`
- Status: `bin/chief-of-staff --classroom-timer-stopwatch-runtime-status`

## Proof

```bash
bin/chief-of-staff --classroom-timer-stopwatch-runtime-status
bash tests/classroom-timer-stopwatch-runtime-static-safety-test.sh
```
