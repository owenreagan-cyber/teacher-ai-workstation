# LLM Routing for CAD

## Routing

- Design brief interpretation: reasoning model.
- OpenSCAD/CadQuery code generation: coding-focused model.
- Image description/dimensional interpretation: vision-capable model only.
- SVG cleanup: deterministic tools first, AI second.
- Print failure diagnosis: use photos plus human notes when available.
- Sensitive/commercial files: prefer local/private processing where possible.

## Rules

- Never use a non-vision model to interpret image dimensions.
- Never trust any model to go directly from prompt to print without verification.
- Local models are useful for simple OpenSCAD/code generation, but all outputs still require verification.
- Cloud vision models may help with images, but they can still hallucinate geometry and dimensions.
- The model may recommend review, but it cannot block or stop a print.
