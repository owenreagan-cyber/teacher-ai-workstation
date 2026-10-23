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

Run the live GET-only dry run. This reads Canvas to resolve existing pages,
assignment groups, assignments, and announcements, then prints every write the
Friday rollover would make or skip. It performs no POST, PUT, PATCH, or DELETE:

```bash
cd /Users/owen/Projects/teacher-ai-workstation
TAW_STATE_ROOT=/Users/owen/Projects/teacher-ai-workstation/.local bin/canvas-weekly-rollover --dry-run --live-readonly
```

The launcher always uses `/opt/homebrew/bin/python3.12`, independent of the
calling shell's `PATH`; dry-run output reports the executable and Python version.
To verify the deterministic no-Canvas dry run in a minimal environment:

```bash
env -i HOME="$HOME" PATH=/usr/bin:/bin bin/canvas-weekly-rollover --dry-run
```

The Friday screen also has **Publish now**. It accepts `ALL` or one course id
(`math`, `reading_spelling`, `language_arts`, `science`, or `homeroom`) and
requires the matching typed phrase `PUBLISH NOW Q2W3 ALL` or
`PUBLISH NOW Q2W3 MATH`. Before Friday 4:00 PM Eastern it publishes approved
page bodies, assignments, and reminders while holding front-page switches and
weekly updates for the normal Friday rollover. After 4:00 PM Friday through
Sunday it publishes the selected approved package immediately, including its
weekly update and front page for the coming Monday. From Monday onward, Publish
now remains available and displays a warning that the week has started.

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
