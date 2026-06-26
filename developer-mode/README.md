# Developer Mode

Developer Mode is a local workspace for safe teacher-created tools and prototypes.

Use it for local teacher tools, lesson helpers, workflow scripts, classroom productivity helpers, and future app prototypes. Start with small local templates and scripts before building real apps.

## What This Is

- Local project planning.
- Local starter templates.
- Manual project scaffolding.
- Small teacher workflow experiments.
- Future-safe structure for lesson tools and classroom helpers.

## What This Is Not

- Not a production deployment system.
- Not a public app hosting setup.
- Not a student data system.
- Not a database-backed app scaffold.
- Not an API integration layer.
- Not a place for secrets.

## Safety Rules

- Do not use student-sensitive data by default.
- Do not include real student names.
- Do not include grades, medical information, behavior notes, IEP/504 details, parent contact information, or private classroom incidents.
- Do not connect to Gmail, Drive, Calendar, APIs, school systems, OAuth, or paid services.
- Do not store secrets, API keys, tokens, or `.env` files.
- All classroom-facing output requires human review.

## Local Generated Projects

`developer-mode/projects/` is intentionally local/generated workspace output and should not be committed.

Create projects manually with:

```bash
bash scripts/create-developer-project.sh TEMPLATE_NAME PROJECT_SLUG
```

The dashboard and status scripts never create projects.
