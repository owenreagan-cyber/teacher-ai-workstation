# Curriculum Library Planning Samples

Read-only **fake/local planning fixtures** for Setup and Manual Registry Foundation.

| File | Purpose |
| --- | --- |
| `fake-folder-tree.json` | Fictional planned folder taxonomy (not created on disk) |
| `fake-manual-registry.csv` | Fictional manual registry rows |
| `fake-classification-suggestion.json` | Fictional classification suggestion under approval gate |

All fixtures: `fake_local_planning_only`. No real curriculum content. No student data.

Validate:

```bash
bin/chief-of-staff --curriculum-library-foundation-status
bash tests/curriculum-library-foundation-status-test.sh
```

Future mission (not approved here): Owen-approved script may create `~/TeacherAI-Curriculum-Library/` skeleton.
