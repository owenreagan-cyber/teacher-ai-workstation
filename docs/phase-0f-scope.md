# Phase 0F Scope: Secrets and Capability Broker

Phase 0F is a future phase. It is not implemented by Phase 0E-A.

This document freezes the advanced automation boundary so secret handling and capability automation do not leak into Phase 0E.

## Purpose

Phase 0F should design a safe way for local commands and future assistants to request approved capabilities without receiving raw credentials by default.

The guiding rule is:

> Agents get capabilities, not passwords.

## In scope for future Phase 0F

### 1Password CLI capability broker

A local broker may eventually allow commands to request named capabilities through 1Password with explicit local approval.

Example capability names might include:

- `openai-api-key-for-current-command`
- `anthropic-api-key-for-current-command`
- `github-token-for-approved-operation`

The broker should avoid printing, logging, or globally exporting secrets.

### Named capability request pattern

Future tooling should request capabilities by name, not ask Owen to paste secrets.

Preferred pattern:

1. Command asks for a named capability.
2. Owen approves locally if required.
3. 1Password provides the secret to that command only.
4. Secret is not printed.
5. Secret is not saved.
6. Secret is not exported globally.

### API keys through broker only

Phase 0F may support API keys through a broker pattern.

It should not use shell-startup injection as the default. Shell-startup injection can slow down terminals, fail silently when 1Password is locked, and expose keys to every child process.

### Model download automation

Phase 0F may add smarter Ollama or local-model setup, including:

- Model recommendations.
- Size warnings.
- Optional downloads.
- Progress reporting.
- Disk-space checks.

### Raycast assisted extension install

Phase 0F may add assisted Raycast extension setup.

This should be described as assisted, not fully automated, because Raycast extension installation may still require human clicks or approvals.

### Optional stateful setup orchestrator

Phase 0F may explore a stateful setup orchestrator that tracks completed steps in a local file such as:

```text
~/.teacher-ai-workstation/state.json
```

This should not replace `bootstrap.sh` until it has been tested separately.

### Git commit signing with SSH key

Phase 0F may evaluate SSH-based commit signing.

This should be opt-in and documented because it changes Git behavior.

### SSH key migration to 1Password

Phase 0F may evaluate moving SSH key management into 1Password.

This should be opt-in. The current working SSH setup should not be disrupted without approval.

## Out of scope for Phase 0F unless separately approved

- Browser automation that logs into websites with raw passwords.
- An autonomous agent with unrestricted Mac access.
- Storing credentials in the repository.
- Storing secrets in Markdown.
- Managing student data.
- Bypassing macOS privacy prompts.
- Bypassing paid subscription approval.

## Relationship to Phase 0E

Phase 0E-A documents the rules and boundaries.

Phase 0E-B may add read-only status tools.

Phase 0E-C may add interactive setup guidance.

Phase 0E-D may add reversible appearance automation.

Phase 0F is where secret-aware capability automation may begin, after Phase 0E is stable and reviewed.