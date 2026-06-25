# Image Source Policy

This policy controls how images are used by Visual Modes and future Vibe Engine scripts.

The goal is to make the workstation personal, beautiful, and practical without mixing personal inspiration, teacher materials, and business/product assets.

## Use categories

### Personal / Reference-Only

Examples:

- Anime character art.
- Fan art.
- Reddit images.
- Pinterest-style inspiration.
- Screenshots.
- Reference images for personal study.

Allowed uses:

- Personal wallpaper.
- Personal Photos widget.
- Personal inspiration board.
- Local reference folder.

Not approved for:

- Business product design.
- Commercial 3D printing.
- Public listing images.
- Customer/client work.
- Public classroom presentation materials.

### Teacher / Presentation Candidate

Examples:

- Unsplash backgrounds.
- Original photos.
- Licensed classroom-safe images.
- Abstract patterns.
- Nature/desk/library/classroom photos.

Allowed uses after review:

- Teacher wallpaper.
- Slide background.
- Classroom presentation.
- Documentation visuals.

Still verify licensing and attribution requirements before publishing or distributing.

### Business / Commercial Candidate

Examples:

- Original product photos.
- Original renderings.
- Licensed stock art with commercial terms.
- Brand assets Owen owns or has permission to use.

Allowed uses only after commercial/IP review:

- Product listings.
- Business branding.
- Customer/client assets.
- Commercial 3D printing support materials.

## Source rules

### Reddit

Reddit may be useful for personal anime and lofi inspiration, but Reddit content is not automatically copyright-free.

Future Reddit scripts must save images only to a personal/reference-only location unless a separate license review confirms broader use.

Default folder:

```text
~/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration
```

### Unsplash

Unsplash may be useful for teacher/coding wallpapers, presentation backgrounds, and calm slide visuals.

Future Unsplash scripts should:

- Use the official Unsplash API where possible.
- Save source metadata.
- Save author and source URL information.
- Keep an attribution/source manifest.
- Avoid claiming images are automatically business-safe.

Default folders:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding
~/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation
```

### User-provided images

Images Owen manually adds should stay in the folder matching their intended use.

When unsure, put images in Reference-Only first.

## Manifest requirement

Future image provisioning scripts should create a source manifest such as:

```text
source-manifest.json
```

The manifest should record:

- Local filename.
- Source URL.
- Source platform.
- Author/creator when available.
- Download date.
- Intended use mode.
- License/status note.
- Review status.

## 3D printing boundary

Personal/reference anime images must not be used as the basis for commercial 3D products unless IP/license permission is confirmed.

If an image is based on an existing product, character, logo, brand, franchise, marketplace listing, downloaded model, or customer-provided file, route it through the 3D Agent IP/safety workflow before any commercial use.

## Default decision rule

When license or source status is unclear:

```text
Reference-Only. Not approved for sale. Human review required.
```
