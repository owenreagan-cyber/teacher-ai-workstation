# Workstation Design Principles

These principles govern the Teacher AI Workstation as it grows from a setup repo into an assistant-powered work system.

## One next action

The system must avoid overwhelming Owen with giant checklists. When possible, tools and assistants must answer:

- What is the one highest-priority thing to do next?
- Is it required today?
- Where should it be done?
- What exact command, app, or page should be opened?

A full status report is useful, but it must not replace a clear next action.

## Capabilities, not credentials

Agents must receive capabilities, not passwords.

A safe capability might be:

- GitHub CLI is authenticated.
- Ollama is running locally.
- A named API key can be requested through an approved local broker.
- A local Markdown folder can be read.

An unsafe credential pattern is:

- Paste passwords into ChatGPT.
- Store API keys in Markdown.
- Export all secrets globally in every shell.
- Give raw credentials to an agent by default.

## Read-only before write

Every automation path must begin with read-only inspection before making changes.

Required order:

1. Inspect.
2. Report.
3. Recommend.
4. Ask for approval.
5. Apply.
6. Verify.

## Preview before apply

Scripts that change settings must support preview or dry-run mode whenever practical.

A script must explain:

- What it will do.
- What it will not do.
- Which files or settings it will change.
- Whether human approval is required.
- How to undo or repair the change.

## Backup before change

Before changing user-facing macOS or app configuration, scripts must preserve enough information to undo or explain the change.

Examples:

- Save current Dock settings before resetting the Dock.
- Save current screenshot location before changing it.
- Avoid destructive changes unless an undo path exists.

## Human approval for sensitive actions

Human approval is required before actions that touch:

- Secrets, passwords, passkeys, recovery codes, API keys, or tokens.
- External services or paid subscriptions.
- Account sign-in state.
- Privacy permissions.
- Destructive operations.
- School, student, parent, or confidential data.
- Commercial product decisions.

## No false confirmation

The system must not claim it verified something that cannot be reliably verified.

For example, macOS privacy permissions are often not reliably checkable from shell scripts. In those cases the script must say:

> Opened the correct settings page. Human verification is still required.

False confidence is worse than no check.

## No invisible work

Every action must be visible, approved, and reported.

The system must not silently:

- Create issues.
- Create branches.
- Edit files.
- Change settings.
- Access accounts.
- Retrieve secrets.

## Documentation before automation

When a workflow is confusing or risky, document the truth table first. Automation must be built on a shared understanding of what is installed, what needs an account, what needs human approval, and what agents can safely access.

## Optional stays optional

Optional tools must not appear as critical failures. They should be warnings, recommendations, or later-phase items unless Owen explicitly makes them required.