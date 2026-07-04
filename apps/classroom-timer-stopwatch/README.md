# Classroom Timer & Stopwatch — Local Runtime Prototype

Owen-approved **Level 3** local-only prototype. **No other app** is runtime-approved.

## Usage

Open `index.html` locally in a browser (file:// or local static server). No network required.

## Features

- Countdown and stopwatch modes
- Start, pause, reset
- Static preset buttons (1m, 3m, 5m, 10m, Warmup, Transition, Exit ticket)
- Large classroom-readable display
- Keyboard: Space = start/pause, R = reset

## Blocked (not in this prototype)

- Audio, animations, localStorage/sessionStorage, cookies
- Network, CDN, external scripts/fonts
- Student data, curriculum data, persistence
- Widgets, shortcuts, Mac wrappers

## Authority

- Planning: `docs/classroom-utilities/classroom-timer-stopwatch-planning.md`
- Runtime packet: `docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md`
- Status: `bin/chief-of-staff --classroom-timer-stopwatch-runtime-status`

## Proof

```bash
bin/chief-of-staff --classroom-timer-stopwatch-runtime-status
bash tests/classroom-timer-stopwatch-runtime-static-safety-test.sh
```
