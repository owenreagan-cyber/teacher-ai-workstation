# Image Source Review Queue

The Image Source Review Queue is a local safety layer before using images as wallpapers, Photos widgets, classroom backgrounds, or 3D/product inspiration.

It exists because image candidates can come from very different sources: Unsplash, personal photos, Reddit, anime/fan-art posts, screenshots, and unknown references. Those sources should not all flow directly into wallpaper, widget, classroom, or product folders.

This workflow is local and manual. It does not download images. It does not approve licenses automatically. It does not replace human review.

## Prepare The Queue

From the repo:

```bash
bash scripts/prepare-image-review-queue.sh
```

This creates:

```text
~/Pictures/Teacher-AI-Workstation/Image-Review
~/Pictures/Teacher-AI-Workstation/Image-Review/Incoming-Candidates
~/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Personal-Wallpaper
~/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Photos-Widget
~/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Presentation-Safe
~/Pictures/Teacher-AI-Workstation/Image-Review/Rejected-or-Hold
~/Pictures/Teacher-AI-Workstation/Image-Review/Reference-Only
```

It also writes:

```text
~/Pictures/Teacher-AI-Workstation/Image-Review/README.txt
```

## Folder Workflow

1. Place candidate images in:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Incoming-Candidates
   ```

2. Review the image and source.

3. Move it manually to one of:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Reference-Only
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Personal-Wallpaper
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Photos-Widget
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Presentation-Safe
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Rejected-or-Hold
   ```

4. Only after approval, copy or move images into:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime
   ~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
   ~/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation
   ```

## Review Checklist

Before approving an image, ask:

- Do I know where this image came from?
- Is it personal/reference-only?
- Is it fan art, anime, Reddit, or character-based?
- Is it safe for public classroom presentation?
- Is it only for private wallpaper/widget use?
- Would I be comfortable using it in front of students/parents/admin?
- Is there any licensing or creator attribution concern?
- Should it stay Reference-Only?

## Source Category Rules

### Reddit, Anime, Fan-Art, Or Character Images

Default:

```text
Reference-Only
```

Possible after human review:

```text
Approved-Personal-Wallpaper
Approved-Photos-Widget
```

Not for public classroom, business, commercial, public portfolio, or commercial 3D sale use by default.

### Unsplash

Unsplash images may be candidates for presentation-safe or wallpaper use.

They still require source metadata and human review. Preserve source and creator info when possible.

### Unknown Source

Default to:

```text
Rejected-or-Hold
```

or:

```text
Reference-Only
```

## Review Status Config

The queue statuses and intended uses are documented in:

```text
configs/image-review-queue.json
```

This config is a plan for humans and future scripts. It does not move files or approve anything automatically.

## Testing

Run:

```bash
bash -n scripts/prepare-image-review-queue.sh
bash scripts/prepare-image-review-queue.sh
test -d "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/Incoming-Candidates"
test -f "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/README.txt"
cat "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/README.txt"
```

## Safety Boundaries

This scaffold does not:

- download images.
- call Reddit, Unsplash, Spotify, Photos, or any network API.
- modify Photos.
- change Display scaling.
- touch accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- move existing user images automatically.
- alter existing source manifests.
- change Raycast scripts.
- change Apple Shortcuts scripts.
- introduce dependencies.
