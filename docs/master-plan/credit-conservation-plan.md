# Credit Conservation Plan

```text
Status: active validation guidance
Classification: documentation/status only
```

Use targeted repo inspection and validation first.

Preferred order:

1. Inspect only files relevant to the mission.
2. Run the new or changed status command.
3. Run directly related script tests if present.
4. Run dashboard/status checks only when needed for repo convention or handoff proof.
5. Run smoke or validate-all only when required for PR readiness or existing repo convention.

If a command runs much longer than expected, stop and report the command, elapsed time, last output, suspected cause, blocking status, and recommended fix.
