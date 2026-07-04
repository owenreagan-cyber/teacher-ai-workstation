# Teacher Knowledge Vault — Canonical Naming Convention

Last updated: 2026-07-04

```text
Status: naming recommendations — not automatic rewrites
Human-editable final name required before any future execution (M5+)
```

## Pattern Structure

`{subject}_{grade}_{curriculum}_{unit_or_lesson}_{artifact_type}_{variant}_v{n}.{ext}`

## Example Canonical Names (Fake)

| Example filename | Notes |
| --- | --- |
| `math_g5_saxon_lesson_021_homework_odds_v1.pdf` | Student homework |
| `math_g5_saxon_lesson_021_teacher_guide_v1.pdf` | Teacher-only guide |
| `math_g5_saxon_power_up_h_v1.pdf` | Power Up letter H |
| `reading_g4_rm_lesson_042_reader_section_v1.pdf` | Reading Mastery |
| `history_g5_ckhg_american_revolution_ch03_study_guide_blank_v1.pdf` | CKHG study guide |
| `science_g5_cksci_energy_transfer_unit01_assessment_teacher_key_v1.pdf` | Teacher key — restricted |
| `ai_generated_math_g5_lesson_021_review_game_v1.html` | AI-generated under `12_AI_GENERATED` |

## Rules

- Naming rules are recommendations, not automatic rewrites
- Version suffixes must not overwrite prior versions
- Teacher-only markers preserved for answer keys, tests, manuals (`teacher_key`, `teacher_guide`)
- AI-generated resources use `ai_generated_` prefix or `12_AI_GENERATED` destination policy
- Generated student-facing files must pass leakage checks

Fixture: `assistant/teacher-knowledge-vault/m4/fake-canonical-name-examples.json`

Cross-reference: `docs/teacher-knowledge-vault/classification-rule-dsl.md`
