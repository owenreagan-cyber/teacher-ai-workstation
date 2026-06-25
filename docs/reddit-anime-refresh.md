# Phase 0E-D3 Reddit Anime Refresh

Phase 0E-D3 adds a safe refresh workflow for Casual Anime Mode images.

Owen wants Reddit anime/aesthetic images to support his custom local workstation profile, including wallpapers and Photos widget candidates. This content is for personal/local workstation use unless separately reviewed.

## Intended use

Allowed by default:

- Personal Mac wallpaper candidates.
- Casual Anime Mode inspiration.
- Photos widget candidates.
- Local creative reference.

Not allowed by default:

- Business branding.
- Commercial 3D products.
- Product listings.
- Customer/client assets.
- Public classroom slide decks.

Default decision rule:

```text
Reddit/anime content = Reference-Only until reviewed.
```

## Refresh modes

### Manual trigger

Run:

```bash
scripts/refresh-anime-inspiration.sh
```

This should refresh the local candidate folders and update the source manifest.

### Dry run

Run:

```bash
python3 scripts/refresh-anime-inspiration.py --dry-run --limit 10
```

This previews candidates without downloading.

### Weekly automatic refresh

A future/optional LaunchAgent can run once per week.

The first version should install only after Owen explicitly runs an installer script. It should not silently enable weekly background downloads.

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

Each image entry should include:

- local_path
- source_platform
- source_url
- source_title
- creator_or_author
- downloaded_at
- intended_use
- license_status
- review_status
- notes

## Refresh behavior

The script should:

- Use configured subreddit presets.
- Respect a low default limit.
- Avoid duplicate URLs already present in the manifest.
- Save only image-like URLs.
- Use a descriptive user-agent.
- Avoid storing secrets.
- Default all Reddit/anime items to `reference-only`.

## Weekly scheduling boundary

Weekly refresh should be implemented with a user LaunchAgent under:

```text
~/Library/LaunchAgents/
```

The LaunchAgent should run as Owen, not root.

Logs should go to:

```text
~/Library/Logs/teacher-ai-workstation/
```

The weekly job should be removable with an uninstall script.

## Future Photos widget path

Possible future improvement:

1. Refresh Reddit reference images.
2. Copy selected images to Photos import folder.
3. Import approved images into a Photos album named `Casual Anime Shuffle`.
4. Use the Photos widget to show that album.

Do not assume Photos/widget automation is reliable until tested manually on the M5.
