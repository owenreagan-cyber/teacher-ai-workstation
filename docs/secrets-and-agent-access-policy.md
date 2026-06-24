# Secrets and Agent Access Policy

This policy defines how the Teacher AI Workstation handles passwords, API keys, tokens, recovery codes, and future agent access.

## Core rule

1Password is the source of truth for secrets.

The repository is not a secret store. ChatGPT is not a secret store. Obsidian notes are not a secret store. Terminal history is not a secret store.

## Never store or paste raw secrets

Do not store, paste, log, screenshot, or commit:

- Passwords.
- API keys.
- Recovery codes.
- Passkeys.
- OAuth tokens.
- Personal access tokens.
- MFA codes.
- 1Password Secret Key.
- SSH private keys, unless intentionally stored inside 1Password.

These must never go into:

- GitHub repository files.
- Markdown documents.
- Obsidian notes.
- ChatGPT conversations.
- Terminal command history.
- Screenshots.
- Logs.
- Issue or pull request comments.

## Agents get capabilities, not credentials

Future assistants and scripts should use approved capabilities rather than raw credentials.

Safe examples:

- `gh` is authenticated and can create a pull request.
- Ollama is running and can serve a local model.
- A local Markdown vault path is approved for reading.
- A named capability can be requested through a future local broker.

Unsafe examples:

- Giving an agent a raw GitHub password.
- Exporting all API keys in every shell by default.
- Pasting an OpenAI API key into ChatGPT.
- Saving recovery codes in a repo document.

## 1Password usage

1Password should store:

- Account logins.
- Passkeys.
- Recovery codes.
- API keys.
- Software license keys.
- Secure setup notes.
- Device recovery information such as FileVault recovery key, if applicable.

Use separate vaults or clear item names for:

- Developer / Workstation.
- Personal accounts.
- 3D Printing Business.
- School-required tools, if needed.

Do not use 1Password as a database for student records, parent information, grades, medical details, or confidential school records.

## Phase 0E restriction

Phase 0E must not implement secret retrieval or API key injection.

Specifically disallowed in Phase 0E:

- Reading API keys through the 1Password CLI.
- Injecting API keys into `.zshrc`, `.zshenv`, or shell startup.
- Exporting secrets globally.
- Creating a password collection assistant.
- Giving raw credentials to agents.

## Future Phase 0F direction

Secret access belongs in a future Phase 0F: Secrets and Capability Broker.

The preferred future model is:

1. A command asks for a named capability.
2. 1Password approval happens locally.
3. The secret or token is passed only to the specific command that needs it.
4. The value is not printed.
5. The value is not saved in the repo.
6. The value is not exported globally to every shell.

## Recovery and incident rule

If a secret is accidentally pasted into ChatGPT, committed to GitHub, logged, or screenshotted, treat it as exposed.

Recommended response:

1. Revoke or rotate the credential.
2. Remove the exposed copy where possible.
3. Record the incident in a private secure note if needed.
4. Do not keep using the exposed credential.

## Practical rule for Owen

When in doubt:

- Put secrets in 1Password.
- Put setup knowledge in the repo.
- Put classroom/student confidential information in approved school systems.
- Do not mix these categories.