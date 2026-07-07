# Agent Tool Permission Matrix

Status: documentation/status only.

| Tool / behavior | Primary repo | Disposable sandbox | Notes |
| --- | --- | --- | --- |
| Antigravity 2.0 | [BLOCKED-IN-PRIMARY] | [CANDIDATE], [SANDBOX-ONLY] | Manual review required. |
| Antigravity output migration | [MANUAL-COPY-ONLY] | [MANUAL-COPY-ONLY] | Direct sandbox-to-main merge blocked. |
| `agy` execution | Blocked | Blocked until explicit future sandbox approval | This plan does not approve execution. |
| `agy init` / `agy migrate` | Blocked | Blocked until explicit future sandbox approval | No active config or migration in primary repo. |
| `.antigravity/` or `.antigravity.json` | Blocked | Documentation-only sentinel review if ever created in sandbox | Must not appear in primary repo. |
| Credentials/secrets | Blocked | Blocked | No credential entry or storage. |
| Canvas API/OAuth/live reads/writes | Blocked | Blocked | Includes publishing and live reads. |
| Drive/NAS/iCloud | Blocked | Blocked | No connector access. |
| Supabase/Firebase | Blocked | Blocked | Deprecated and blocked. |
| Student data / real curriculum ingestion | Blocked | Blocked | Fake/local/manual evidence only. |
| Runtime agent behavior/background processes | Blocked | Blocked | No activation from docs. |
| Docs/status edits | Allowed | Allowed | Must preserve safety labels. |
