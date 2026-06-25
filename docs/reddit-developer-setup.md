# Reddit Developer Setup for Anime Refresh

This document defines the approved Reddit access path for Phase 0E-D3.

The goal is to refresh personal anime/aesthetic image candidates for Owen's local Mac profile without relying on fragile unauthenticated Reddit scraping and without putting Reddit passwords or secrets in the repository.

## Current status

The first dry-run proved that unauthenticated Reddit JSON may return:

```text
HTTP Error 403: Blocked
```

That means the refresh workflow should pivot to authenticated Reddit API access before any real downloads or weekly automation are used.

## Approved credential boundary

Do not put any of these in the repo:

- Reddit password.
- Reddit client secret.
- Reddit access token.
- Reddit refresh token.
- `.env` files containing Reddit credentials.
- JSON files containing Reddit credentials.

Do not paste Reddit secrets into ChatGPT.

Use 1Password for credential storage before the first authenticated request.

## Local state paths

Reddit local state must live outside the repo:

```text
~/.teacher-ai-workstation/reddit-config.json
~/.teacher-ai-workstation/reddit-token.json
```

The scripts must refuse to write token or config files inside the repository directory.

The repo `.gitignore` includes a defensive guard for local token/config filenames, but the primary safety rule is still: store local state outside the repo.

## Reddit app type

Use a personal Reddit app created from Reddit's developer preferences.

Recommended starting approach:

```text
App type: script
Purpose: personal local automation on Owen's own Mac
```

However, the workstation scripts should avoid collecting or storing Owen's Reddit account password.

For public subreddit reading, prefer an OAuth approach that does not require the Reddit account password in a local script. If app-only OAuth is sufficient for the needed public read endpoints, use that first. If not, add a browser authorization flow with explicit human approval.

Do not implement a password-based flow unless Owen separately approves it after reviewing the tradeoffs.

## User-Agent requirement

Every Reddit API request must use a descriptive User-Agent, for example:

```text
TeacherAIWorkstation/1.0 by owenreagan-cyber
```

Do not use a generic Python or browser User-Agent.

## Rate limit behavior

The refresh script should be rate-limit-aware:

- Use low default limits.
- Pause between subreddit requests.
- Respect HTTP 429 responses.
- Print clear warnings instead of retrying aggressively.
- Avoid running more often than weekly unless Owen manually triggers it.

## Required test gate

0E-D3-B is not complete until an authenticated test can:

1. Load credentials from the approved local/1Password-backed path.
2. Obtain or validate a token.
3. Fetch at least one subreddit listing through the authenticated Reddit API path.
4. Identify one image candidate.
5. Print the candidate without downloading unless `--download` is explicitly passed.

No manual refresh wrapper or weekly automation should be treated as unblocked until this test succeeds.

## Failure behavior

If a token is missing, expired, invalid, or blocked, the script should print clear next steps, such as:

```text
Reddit auth is not configured or is invalid.
Run scripts/reddit-auth-setup.py and confirm the 1Password/local credential setup.
```

It should not silently download nothing.

## Future weekly automation

Weekly LaunchAgent automation belongs in a later sub-phase after:

- Auth setup works.
- Manual refresh works.
- One real download test succeeds.
- Manifest entries are correct.
- Owen explicitly approves background refresh.
