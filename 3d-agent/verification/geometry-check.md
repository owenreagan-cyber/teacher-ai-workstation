# Geometry Check

## Checks

- Manifold geometry
- No holes
- No inverted normals
- No non-manifold edges
- No floating islands unless intentional
- Bottom face sits on the build plate or orientation is explained
- Minimum wall thickness is compatible with nozzle/material
- Overhangs are identified
- Moving parts/press fits have tolerances
- Generated file is not called print-ready

If geometry cannot be verified from text alone, the agent must say so and require slicer/OpenSCAD/Bambu Studio inspection.

## Output notes

- Geometry status:
- Items requiring Bambu Studio inspection:
- Slicer-ready pending human verification: yes/no
