# Local Script Tool Template

## Purpose

This template starts a tiny local Bash script tool.

It is for safe local experiments only. It does not install dependencies, call APIs, use secrets, or write files by default.

## Copy Manually

Use the helper:

```bash
bash scripts/create-developer-project.sh local-script-tool my-local-tool
```

Or copy this folder manually into a local working folder under `developer-mode/projects/`.

## Run

```bash
bash tool.sh
bash test-tool.sh
```

## Safety Boundaries

- No secrets.
- No external services.
- No dependency installation.
- No student-sensitive data.
- No file writes by default.
- Human review before classroom use.
