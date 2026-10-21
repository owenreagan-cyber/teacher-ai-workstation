# Canvas Planner 1 — owner steps

Status: implementation runbook. These commands are for Owen to run after the
feature is reviewed and merged into the installed main checkout. This mission
does not install or load the LaunchAgent.

## Try the planner

```bash
cd /Users/owen/Projects/teacher-ai-workstation
TAW_STATE_ROOT=/Users/owen/Projects/teacher-ai-workstation/.local bin/teacher-workstation --open '#week/q2w3'
```

Read the same cached projection Chief of Staff uses:

```bash
cd /Users/owen/Projects/teacher-ai-workstation
TAW_STATE_ROOT=/Users/owen/Projects/teacher-ai-workstation/.local bin/canvas-weekly-status --json
```

Run a local-only package preview (zero Canvas calls):

```bash
cd /Users/owen/Projects/teacher-ai-workstation
TAW_STATE_ROOT=/Users/owen/Projects/teacher-ai-workstation/.local bin/canvas-weekly-rollover --week q2w3 --dry-run
```

## Install the one Friday LaunchAgent

The single job runs the same `bin/canvas-weekly-rollover --scheduled` entrypoint
at 1:00 PM and 4:00 PM every Friday. At 1:00 PM it exposes the local Chief
decision item when approvals remain. At 4:00 PM it uses the canonical rollover
engine, and it publishes nothing unless all five exact packages are approved
and Automatic rollover is enabled.

```bash
cd /Users/owen/Projects/teacher-ai-workstation
mkdir -p /Users/owen/Projects/teacher-ai-workstation/.local/canvas-planner/logs "$HOME/Library/LaunchAgents"
plutil -lint launchd/com.teacher-ai-workstation.canvas-friday.plist
cp launchd/com.teacher-ai-workstation.canvas-friday.plist "$HOME/Library/LaunchAgents/com.teacher-ai-workstation.canvas-friday.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.teacher-ai-workstation.canvas-friday.plist"
launchctl print "gui/$(id -u)/com.teacher-ai-workstation.canvas-friday"
```

Do not alter, unload, copy, or reuse `com.teacher-ai-workstation.grade-check`.
The Canvas Friday job has its own label, entrypoint, state, and log.

## Uninstall the Friday LaunchAgent

```bash
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.teacher-ai-workstation.canvas-friday.plist"
rm "$HOME/Library/LaunchAgents/com.teacher-ai-workstation.canvas-friday.plist"
```

Uninstalling the job does not remove planner packets, approvals, or rollover
ledgers. It only stops the two Friday invocations.
