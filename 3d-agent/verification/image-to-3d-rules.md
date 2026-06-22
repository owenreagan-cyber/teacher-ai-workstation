# Image-to-3D Rules

The agent must ask what type of conversion is desired:

- Lithophane
- Traced outline extrusion
- Layered sign
- Relief
- Cookie-cutter style
- Full 3D reconstruction

## Rules

- Full 3D reconstruction from one image should be labeled experimental, not production-ready.
- For SVG/traced outlines, check for closed paths, self-intersections, missing holes, and scale.
- For lithophanes, ask for orientation, size, thickness range, and image contrast.
- For copyrighted/trademarked images or characters, route to `3d-agent/workflows/ip-safety-check.md` for advisory classification.
- The agent must not infer exact dimensions from an image unless a scale reference is provided.
