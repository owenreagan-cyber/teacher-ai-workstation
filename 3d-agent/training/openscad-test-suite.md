# OpenSCAD Test Suite

Use these as repeatable regression prompts for AI-generated OpenSCAD.

## 1. Exact outer dimension box

- Prompt: Create an OpenSCAD box with exact outer dimensions 50 x 30 x 20 mm and a 2 mm wall target.
- Expected properties: outer size matches target; walls are approximately 2 mm; units are mm.
- Check in OpenSCAD: renders cleanly; dimensions are parameterized.
- Check in Bambu Studio: scale and wall thickness appear correct.
- Pass/fail notes:
- Revision notes:

## 2. Cylinder or ring

- Prompt: Create a simple ring with known inner diameter and outer diameter.
- Expected properties: inner diameter is explicit; wall thickness is clear.
- Check in OpenSCAD: circular geometry is centered and parameterized.
- Check in Bambu Studio: hole size and wall count are plausible.
- Pass/fail notes:
- Revision notes:

## 3. Simple text extrusion

- Prompt: Create a flat nameplate with raised text.
- Expected properties: text is legible; base dimensions are explicit.
- Check in OpenSCAD: text renders and is positioned on the base.
- Check in Bambu Studio: letters are printable at chosen size.
- Pass/fail notes:
- Revision notes:

## 4. Two-body/multicolor example

- Prompt: Create a base and a separate raised icon body for multicolor printing.
- Expected properties: bodies can be assigned separate colors.
- Check in OpenSCAD: separate modules/bodies are clear.
- Check in Bambu Studio: color assignment can be verified.
- Pass/fail notes:
- Revision notes:

## 5. Simple token/fidget shape

- Prompt: Create a classroom token/fidget with rounded edges and no small detachable parts.
- Expected properties: classroom safety notes included; size is hand-friendly.
- Check in OpenSCAD: shape renders cleanly.
- Check in Bambu Studio: overhangs and edges are reasonable.
- Pass/fail notes:
- Revision notes:

## 6. 45-degree overhang case

- Prompt: Create a simple part with an intentional 45-degree overhang.
- Expected properties: overhang angle is documented.
- Check in OpenSCAD: overhang exists and is parameterized.
- Check in Bambu Studio: support preview reviewed.
- Pass/fail notes:
- Revision notes:

## 7. Press-fit/tolerance example

- Prompt: Create two simple press-fit parts with adjustable clearance.
- Expected properties: tolerance parameter is explicit.
- Check in OpenSCAD: mating dimensions are parameterized.
- Check in Bambu Studio: clearances are plausible for printer/material.
- Pass/fail notes:
- Revision notes:
