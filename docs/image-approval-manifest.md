# Image Approval Manifest

The Image Approval Manifest is a local human review log for image candidates before they are used as wallpapers, Photos widgets, classroom presentation backgrounds, reference material, business assets, or 3D/product inspiration.

It exists so Owen can record where an image came from, what it is intended for, who reviewed it, and what approval status it has before the image moves into a final use folder.

This manifest does not approve images automatically. It does not replace licensing judgment. It should be used before moving images into final wallpaper, widget, or presentation folders.

## Setup

From the repo:

```bash
bash scripts/init-image-approval-manifest.sh
```

This creates the review folder if needed:

```text
~/Pictures/Teacher-AI-Workstation/Image-Review
```

It creates this file only if it does not already exist:

```text
~/Pictures/Teacher-AI-Workstation/Image-Review/approval-manifest.json
```

If the manifest already exists, the script leaves it unchanged.

## Validation

Run:

```bash
python3 -m json.tool ~/Pictures/Teacher-AI-Workstation/Image-Review/approval-manifest.json
```

## Recommended Workflow

1. Put candidate image into:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Incoming-Candidates
   ```

2. Review source and intended use.
3. Move image into the correct review folder.
4. Add or update an entry in:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Image-Review/approval-manifest.json
   ```

5. Only after approval, copy or move image into:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime
   ~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
   ~/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation
   ```

## Entry Fields

Each entry should record:

- `id`
- `filename`
- `local_path`
- `source_platform`
- `source_url`
- `creator`
- `license_or_usage_note`
- `intended_use`
- `review_status`
- `reviewer`
- `review_date`
- `notes`

## Example Entry

Use placeholder/example data only until a real image has been reviewed:

```json
{
  "id": "example-001",
  "filename": "example-image.jpg",
  "local_path": "~/Pictures/Teacher-AI-Workstation/Image-Review/Incoming-Candidates/example-image.jpg",
  "source_platform": "example-source",
  "source_url": "unknown",
  "creator": "unknown",
  "license_or_usage_note": "Placeholder only. Replace with source, license, attribution, or usage notes from human review.",
  "intended_use": "reference_only",
  "review_status": "reference_only",
  "reviewer": "Owen",
  "review_date": "YYYY-MM-DD",
  "notes": "Example entry only. Unknown source should default to reference_only or rejected_or_hold."
}
```

The repo also includes a template:

```text
configs/image-approval-manifest-template.json
```

## Review Rules

Unknown source should default to:

```text
reference_only
```

or:

```text
rejected_or_hold
```

Anime, Reddit, fan-art, and character images default to:

```text
reference_only
```

Unsplash candidates still require source metadata and human review.

Classroom presentation use requires:

```text
approved_presentation_safe
```

Business, commercial, public portfolio, or commercial 3D printing use requires explicit review/licensing outside this local scaffold.

## Testing

Run:

```bash
bash -n scripts/init-image-approval-manifest.sh
bash scripts/init-image-approval-manifest.sh
test -f "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/approval-manifest.json"
python3 -m json.tool "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/approval-manifest.json"
```

## Safety Boundaries

This scaffold does not:

- download images.
- call Reddit, Unsplash, Spotify, Photos, or any network API.
- modify Photos.
- scan or move existing user images.
- approve images automatically.
- change Display scaling.
- touch accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- change Raycast scripts.
- change Apple Shortcuts scripts.
- introduce dependencies.
