# Medical Center / System Health Program

```text
Status: PARTIAL read-only status track
Classification: documentation/status only
Runtime monitoring: blocked unless approved
```

Medical Center is the planned health, readiness, and system-status surface for Teacher AI Workstation. The approved posture is observe/report planning and read-only status proof.

Reality audit: `docs/master-plan/build-state-checklist.md` classifies this track as **PARTIAL** because Health Monitor read-only foundations and `--system-health` exist, while runtime monitoring, background jobs, and repair behavior remain blocked.

Safe work:

- health/status docs.
- read-only checks.
- dashboard summaries.
- blocker categories.

Blocked unless separately approved:

- background monitoring.
- scheduler.
- Mac system changes.
- external service calls.
- automatic repair.
- secrets or credentials.

Key references:

- `docs/teacher-workstation-health-monitor.md`
- `docs/teacher-workstation-health-monitor-foundation.md`
