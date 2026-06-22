# Backup Exclusions

Time Machine and cloud backup are important for the Teacher AI Workstation. Back up curriculum source files, lesson plans, final PDFs, final worksheets, final presentations, and final Teacher OS artifacts.

Backup exclusions should be applied carefully after Phase 1 starts. Do not create broad exclusions on Day 1.

## What may be safe to exclude later

Later React apps will create `node_modules` folders. Later builds may create `dist`, `.next`, `coverage`, `.turbo`, `.vite`, and cache folders.

Future media and 3D-printing exports can also become large. Review those folders before backing them up everywhere.

## What not to exclude

Do not exclude curriculum source files, lesson plans, final PDFs, final worksheets, final presentations, or final Teacher OS artifacts.

## Advanced manual examples

Use exclusions only after you understand the folder and know it can be rebuilt.

```bash
tmutil addexclusion /path/to/folder
```

For example, after Phase 1 starts, a rebuildable dependency folder might be excluded manually:

```bash
tmutil addexclusion ~/Projects/teacher-ai-workstation/node_modules
```

Do not use a script that crawls the whole home folder. Keep exclusions specific and intentional.
