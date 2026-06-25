# Source Manifest Schema

The source manifest records local visual-mode image candidates and their review status.

Default path:

```text
~/Pictures/Teacher-AI-Workstation/source-manifest.json
```

The manifest is local workstation state, not repo state.

## Top-level fields

```json
{
  "version": 1,
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "policy": "docs/image-source-policy.md",
  "entries": []
}
```

## Entry fields

Each entry should include:

```json
{
  "local_path": "/local/path/to/file.jpg",
  "source_platform": "reddit",
  "source_url": "https://www.reddit.com/...",
  "source_title": "Post title or search query",
  "creator_or_author": "author when available",
  "downloaded_at": "ISO-8601 timestamp",
  "intended_use": "personal-reference-only",
  "license_status": "reference-only by default",
  "review_status": "reference-only",
  "notes": "Why this file was collected",
  "image_url": "direct image URL when available"
}
```

## Review status values

Supported values:

```text
reference-only
teacher-candidate
presentation-candidate
approved-for-personal-wallpaper
approved-for-teacher-use
approved-for-presentation-use
approved-for-product-use
rejected
unknown
```

## Defaults

Reddit/anime sources default to:

```text
intended_use: personal-reference-only
review_status: reference-only
license_status: reference-only by default
```

Unsplash sources default to:

```text
intended_use: teacher-candidate
review_status: teacher-candidate
license_status: requires review before publishing/distribution
```

## Duplicate prevention

Scripts should avoid adding duplicate entries by checking:

- source_url
- image_url when available
- local_path when available

## Future intake connection

A later script may generate review/intake stubs from manifest entries. That should not automatically approve any file. It only prepares items for human review.
