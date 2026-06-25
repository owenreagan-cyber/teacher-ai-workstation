# Phase 0E-D3 Reddit Anime Refresh

Phase 0E-D3 adds a safe refresh workflow for Casual Anime Mode images.

Owen wants Reddit anime/aesthetic images to support his custom local workstation profile, including wallpapers and Photos widget candidates. This content is for personal/local workstation use unless separately reviewed.

## Current finding

A dry-run test against Reddit's unauthenticated public JSON endpoint returned:

```text
HTTP Error 403: Blocked
```

That is useful signal. The dry-run passed, but the external unauthenticated fetch did not.

Therefore Phase 0E-D3 must pivot to authenticated Reddit API access before any real download workflow or weekly automation is approved.

## Intended use

Allowed by default:

- Personal Mac wallpaper candidates.
- Casual Anime Mode inspiration.
- Photos widget candidates.
- Local creative reference.

Not allowed by default:

- Public branding.
- Product images or product designs.
- Listing images.
- Public classroom slide decks.
- School websites or handouts.
- Public social posts.

Default decision rule:

```text
Reddit/anime content = Reference-Only until reviewed.
```

## Revised sub-phases

### 0E-D3-A: Documentation and local-state safety

Add:

- Reddit developer setup documentation.
- Reference-Only policy.
- Source manifest schema.
- Token/config path specification.
- `.gitignore` guards.

No downloads. No weekly automation.

### 0E-D3-B: Reddit auth setup

Add a dedicated auth setup script:

```text
scripts/reddit-auth-setup.py
```

It must:

- Use local credentials from an approved path or 1Password-backed workflow.
- Store tokens outside the repo at `~/.teacher-ai-workstation/reddit-token.json`.
- Refuse token paths inside the repo.
- Support `--test-auth`.
- Successfully fetch at least one image candidate through the authenticated API path before the phase is considered unblocked.

### 0E-D3-C: Manual refresh

Add a runtime refresh script:

```text
scripts/reddit-refresh.py
```

It must:

- Use a stored valid token.
- Check token validity before refresh.
- Print clear re-authorization instructions if auth is missing or invalid.
- Use a descriptive User-Agent.
- Use low limits and rate-limit-aware request behavior.
- Mark all Reddit/anime items as Reference-Only by default.
- Update `~/Pictures/Teacher-AI-Workstation/source-manifest.json`.

### 0E-D3-D: Weekly automation

Only after manual refresh succeeds end-to-end, add optional weekly automation.

Weekly automation must be explicit and reversible. It should not exist in the repo until the authenticated manual workflow works.

## Folder targets

Downloaded reference-only images go here:

```text
~/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration
```

Photos widget candidates may be copied here after download:

```text
~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
```

The Photos import folder is still not the same as an Apple Photos album. Owen may still need to import images into Photos and select the album/widget manually until Photos automation is proven reliable.

## Source manifest

All downloaded images must be recorded in:

```text
~/Pictures/Teacher-AI-Workstation/source-manifest.json
```

See:

```text
docs/source-manifest-schema.md
```

## Token and config paths

Approved local paths:

```text
~/.teacher-ai-workstation/reddit-config.json
~/.teacher-ai-workstation/reddit-token.json
```

Scripts must refuse to write token/config files inside the repository directory.

## 403 behavior

If Reddit blocks an unauthenticated request, scripts should print an actionable message such as:

```text
Reddit blocked unauthenticated access. Configure Reddit auth before downloading images. See docs/reddit-developer-setup.md.
```

Do not silently proceed as if zero candidates is a normal successful refresh.

## Future Photos widget path

Possible future improvement:

1. Refresh Reddit reference images through authenticated access.
2. Copy selected images to Photos import folder.
3. Import approved images into a Photos album named `Casual Anime Shuffle`.
4. Use the Photos widget to show that album.

Do not assume Photos/widget automation is reliable until tested manually on the M5.
