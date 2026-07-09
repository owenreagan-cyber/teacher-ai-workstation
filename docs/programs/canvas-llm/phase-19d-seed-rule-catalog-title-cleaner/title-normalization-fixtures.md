# Phase 19D Title Normalization Fixtures

## Status

Preview-only fixtures.

## Purpose

These fixtures define expected title-cleaner behavior for close/mislabeled teacher inputs.

The cleaner must preview normalized output only.

It must not write to Canvas.

## Fixture Table

| Messy Input | Detected Type | Canonical Output | Confidence | Review Required |
|---|---|---|---|---|
| `SM5 Test 1` | math_test | `SM5: Test 1` | high | no |
| `SM 5: Test 1` | math_test | `SM5: Test 1` | high | no |
| `SM5 - Test 1` | math_test | `SM5: Test 1` | high | no |
| `SM5_Test_1` | math_test | `SM5: Test 1` | high | no |
| `Math Test 1` | math_test | `SM5: Test 1` | medium | yes |
| `SM5 Fact Test 2` | math_fact_test | `SM5: Fact Test 2` | high | no |
| `Fact Test 2` | math_fact_test | `SM5: Fact Test 2` | medium | yes |
| `SM5 Study Guide 3` | math_study_guide | `SM5: Study Guide 3` | high | no |
| `Study Guide 3` | math_study_guide | `SM5: Study Guide 3` | medium | yes |
| `ELA4 Test 4` | ela_test | `ELA4: Test 4` | high | no |
| `ELA 4: Test 4` | ela_test | `ELA4: Test 4` | high | no |
| `Shurley Test 4` | ela_test | `ELA4: Test 4` | medium | yes |
| `RM4 Test 5` | reading_test | `RM4: Test 5` | high | no |
| `RM 4: Test 5` | reading_test | `RM4: Test 5` | high | no |
| `Reading Test 5` | reading_test | `RM4: Test 5` | medium | yes |
| `Spelling Test 6` | spelling_test | `RM4: Spelling Test 6` | high | no |
| `RM4 Spelling Test 6` | spelling_test | `RM4: Spelling Test 6` | high | no |
| `RM 4: Spelling Test 6` | spelling_test | `RM4: Spelling Test 6` | high | no |
| `SP4 Spelling Test 6` | spelling_test | `RM4: Spelling Test 6` | high | no |
| `SPELL4 Spelling Test 6` | spelling_test | `RM4: Spelling Test 6` | high | no |
| `Spelling: Test 6` | spelling_test | `RM4: Spelling Test 6` | high | no |
| `Test 7` | ambiguous | needs review | needs_review | yes |
| `Chapter 4 Test` | ambiguous | needs review | needs_review | yes |

## Required Behavior

The title cleaner must:

- preserve the detected number
- normalize prefix spacing
- add the required colon after canonical prefix
- classify Spelling Tests as `RM4: Spelling Test {number}`
- require review for ambiguous subjectless tests
- never silently write corrected titles to Canvas

## Boundary

Fixtures are preview-only.

They do not authorize implementation, Canvas API calls, Canvas writes, or file mutation.
