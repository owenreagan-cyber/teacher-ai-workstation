# Phase 22 Curriculum Map Archaeology

Status: focused read-only archaeology pass, prepared for Phase 22 configuration review.

Date: 2026-07-10

## 1. Executive Summary

This pass inspected the highest-value local legacy sources for deterministic curriculum rules needed by the Phase 22 predictive weekly planning workstation.

Recovered exact deterministic evidence includes:

- A Supabase-seeded Saxon Math 5 lesson-to-Power-Up map for lessons 1-120.
- A newer Thales server/client Math test-to-Fact-Test map for tests 1-23.
- Math test-family generation rules: written test, fact test, and study guide.
- Friday/pre-test homework suppression behavior.
- Reading + Spelling Together Logic, including Reading/Spelling course routing.
- Reading fluency benchmark bands, Reading lesson-to-test map, and confirmed no-checkout behavior for Reading Test 14.
- Spelling test maps and focus-word generation rules.
- Assignment title/group rules and subject/course prefix history.
- Pre-deploy validators for duplicates, Friday violations, missing files, title conventions, and missing Math Study Guides.

No tracked source recovered a complete, conflict-free Saxon Math 5 test-to-Study-Guide resource map, blank/completed Study Guide resource selector, Reading Mastery 4 homework-question map, or full Reading lesson-to-reader/resource map. Those remain owner-confirmation or source-material extraction candidates.

Do not promote conflicting Power-Up maps automatically. The strongest exact map by coverage is the Supabase `power_up_map` seed, but `Thalescanvasgemini` contains a shorter, different map in server/client deterministic code.

## 2. Repositories Inspected

| Source | Local Path | Git Evidence | Notes |
|---|---|---:|---|
| `oreagan81-arch/pacing-sync-pilot-8c50be47` candidate | `/Users/owen/Projects/pacing-sync-pilot-8c50be47` | `main` at `ea6ecbc` | Supabase-backed Lovable app with migrations, edge functions, announcement docs, tests, and validators. |
| duplicate local checkout | `/Users/owen/pacing-sync-pilot-8c50be47` | `main` at `ea6ecbc` | Duplicate clean checkout; not separately mined after confirming same branch/head. |
| `oreagan81-arch/Thalescanvasgemini` candidate | `/Users/owen/Projects/Thalescanvasgemini` | `main` at `b75ce84` | Firebase/functions-backed Thales Academic OS with server-core mappings and assignment engine. |
| local Lovable export evidence | `/Users/owen/Projects/pacing-sync-pilot-8c50be47/.lovable` | source-controlled file history found `.lovable/memory/db/content-map-registry.md` | No canonical deterministic map was promoted from Lovable memory in this pass. |
| iCloud export candidates | `~/Library/Mobile Documents/.../pacing-sync-pilot-main*` and ZIPs | not opened | Deferred by timebox because local git checkouts already contained high-value source-controlled evidence. |

Remote cloning/fetching was not performed because local source-controlled copies were present for the high-value repositories.

## 3. Exact Maps Recovered

### Saxon Math 5 Lesson-To-Power-Up

Classification: `exact-database-seed`, `conflicting`

Primary coverage source:

- Repository: `pacing-sync-pilot-8c50be47`
- Commit: `ea6ecbc`
- Path: `supabase/migrations/20260410192446_6430ce02-5c4b-41a7-b033-ec1ef8dca072.sql`
- Lines: 1-12
- Evidence: `system_config.power_up_map` default maps lessons 1-120 to letters A-K.

Recovered map:

```json
{"1":"A","2":"A","3":"A","4":"A","5":"A","6":"A","7":"A","8":"A","9":"B","10":"B","11":"B","12":"B","13":"B","14":"B","15":"B","16":"C","17":"C","18":"C","19":"C","20":"D","21":"D","22":"F","23":"E","24":"F","25":"D","26":"F","27":"F","28":"E","29":"F","30":"D","31":"F","32":"E","33":"F","34":"D","35":"F","36":"E","37":"F","38":"D","39":"F","40":"E","41":"F","42":"D","43":"E","44":"F","45":"D","46":"F","47":"F","48":"G","49":"G","50":"F","51":"G","52":"F","53":"F","54":"G","55":"F","56":"G","57":"F","58":"G","59":"F","60":"G","61":"F","62":"G","63":"F","64":"F","65":"C","66":"F","67":"G","68":"E","69":"F","70":"G","71":"C","72":"D","73":"F","74":"G","75":"C","76":"H","77":"H","78":"H","79":"H","80":"H","81":"H","82":"H","83":"H","84":"H","85":"H","86":"H","87":"H","88":"H","89":"F","90":"F","91":"I","92":"I","93":"I","94":"I","95":"I","96":"I","97":"I","98":"I","99":"I","100":"I","101":"J","102":"J","103":"J","104":"J","105":"J","106":"J","107":"J","108":"J","109":"J","110":"J","111":"K","112":"K","113":"K","114":"K","115":"K","116":"K","117":"K","118":"K","119":"K","120":"K"}
```

Conflict:

- Repository: `Thalescanvasgemini`
- Commit: `b75ce84`
- Paths: `functions/src/core/mappings.ts` lines 32-36, `src/lib/thales/mappings.ts` lines 36-40, `functions/src/core/assignmentEngine.ts` lines 56-65
- Evidence: shorter map for tests 1-23: `1:A, 2:A, 3:B, 4:C, 5:A, 6:B, 7:B, 8:C, 9:D, 10:C, 11:D, 12:E, 13:E, 14:F, 15:F, 16:F, 17:H, 18:G, 19:H, 20:I, 21:H, 22:J, 23:I`.

Confidence:

- High that both maps are exact legacy values.
- Low that either should become canonical without Owen confirmation because early values differ and one is lesson-based while the other is test-number-based.

### Saxon Math 5 Test-To-Fact-Test Practice

Classification: `exact-code-map`

Source:

- Repository: `Thalescanvasgemini`
- Commit: `b75ce84`
- Paths: `functions/src/core/mappings.ts` lines 6-30, `src/lib/thales/mappings.ts` lines 10-34
- Rule: tests 1-23 map to named fact-skill practice strings.

Recovered values:

| Test | Fact-Test Practice |
|---:|---|
| 1 | Addition facts starting with 5+5, 2+9 |
| 2 | Addition facts starting with 5+5, 2+9 |
| 3 | Subtraction facts starting with 9-8, 8-5 |
| 4 | Multiplication facts starting with 9x6, 7x1 |
| 5 | Addition facts starting with 5+5, 2+9 |
| 6 | Subtraction facts starting with 9-8, 8-5 |
| 7 | Subtraction facts starting with 9-8, 8-5 |
| 8 | Multiplication facts starting with 9x6, 7x1 |
| 9 | Division facts starting with 49/7, 25/5 |
| 10 | Multiplication facts starting with 9x6, 7x1 |
| 11 | Division facts starting with 49/7, 25/5 |
| 12 | Division facts starting with 81/9, 48/8 |
| 13 | Division facts starting with 81/9, 48/8 |
| 14 | Multiplication facts starting with 7x9, 4x4 |
| 15 | Multiplication facts starting with 7x9, 4x4 |
| 16 | Multiplication facts starting with 7x9, 4x4 |
| 17 | Improper fractions starting with 8/3, 12/4 |
| 18 | Division with remainders starting with 7/2, 16/3 |
| 19 | Improper fractions starting with 8/3, 12/4 |
| 20 | Reducing fractions to lowest terms starting with 2/10, 3/9 |
| 21 | Improper fractions starting with 8/3, 12/4 |
| 22 | Simplifying fractions starting with 6/4, 10/8 |
| 23 | Reducing fractions to lowest terms starting with 2/10, 3/9 |

Tests support it: no direct unit tests found.

Owner confirmation needed: yes, before canonical promotion, because no independent resource/source-material evidence was found.

### Reading Test Map And Checkout/Fluency

Classification: `exact-code-map`

Source:

- Repository: `Thalescanvasgemini`
- Commit: `b75ce84`
- Path: `functions/src/core/mappings.ts` lines 62-87
- Rule: Reading lessons 80, 90, 100, 110, 120, 130 map to Reading tests 8, 9, 10, 11, 12, 13.

Recovered map:

```json
{"80":8,"90":9,"100":10,"110":11,"120":12,"130":13}
```

Fluency bands:

- Tests 1-7: 100 WPM, 2 or fewer errors.
- Tests 8-10: 115 WPM, 2 or fewer errors.
- Tests 11-13: 130 WPM, 2 or fewer errors.
Reading Test 14 has no Checkout.

Supporting sources:

- `pacing-sync-pilot-8c50be47/supabase/migrations/20260420000000_update_fluency_benchmarks.sql` lines 1-12 seeds the same bands into `system_config.auto_logic.readingFluencyBenchmarks`.
- `pacing-sync-pilot-8c50be47/src/lib/reading-fluency.ts` lines 12-52 resolves configured bands.
- `config/curriculum/reading/reading-mastery-4/checkout-passage-map.json` contains only Checkouts 1-13.

### Spelling Test And Focus-Word Rules

Classification: `exact-code-map`, `inferred-from-implementation`

Sources:

- Repository: `Thalescanvasgemini`
- Commit: `b75ce84`
- Path: `functions/src/core/mappings.ts` lines 109-140 and 142-152
- Repository: `pacing-sync-pilot-8c50be47`
- Commit: `ea6ecbc`
- Paths: `src/lib/together-logic.ts` lines 57-104, `src/lib/announcement-templates.ts` lines 52-70

Rules:

- Static spelling test word lists exist for tests 1-24, each with `lessonsCovered` from 1-5 through 1-120.
- `pacing-sync-pilot-8c50be47` derives a spelling test dynamically: Test N covers lessons `1..N*5` from `system_config.spelling_word_bank`.
- Focus words in the newer announcement path are positions 21-25 of the cumulative word list, 1-indexed.
- Older server-core helper `getSpellingWords` returns first five words, while `getChallengeWords` returns indexes 5, 10, 15, 20, 25. Treat this as conflicting for announcement focus words.

Tests support it: no direct unit tests found.

Owner confirmation needed: yes for which focus-word selector is canonical.

## 4. Partial Maps Recovered

| Target | Classification | Evidence | Status |
|---|---|---|---|
| Saxon Math 5 test-to-Study-Guide mapping | `inferred-from-implementation` | Math test triple creates `Study Guide` sibling with same lesson/test number. | Exact resource values not recovered. |
| Saxon Math 5 Study Guide blank/completed resource mapping | `missing` | No tracked blank/completed selector map found. | Needs owner/source extraction. |
| Reading Mastery 4 homework-question mapping | `missing` | No deterministic homework-question map found. | Needs source extraction. |
| Reading lesson-to-reader/resource mapping | `partial`, `documentation-only` | `CHECKOUT_PAGE_MAP` has only lessons/tests 10 and 11 in `src/lib/thales/mappings.ts` lines 121-124. | Too partial to canonicalize. |
| Reading checkout/test logic | `exact-code-map` | Reading tests 1-13 create Reading Test + Checkout; Reading Test 14 has no Checkout. | Owner-confirmed. |
| Resource filename aliases | `inferred-from-implementation` | `resourceResolver.ts` keyword matching and `pre-deploy-validator.ts` lesson-ref regex. | Not exact enough for canonical aliases. |

## 5. Supabase/Firebase Evidence

### Supabase

Repository: `pacing-sync-pilot-8c50be47`

Evidence:

- `system_config` table includes `course_ids`, `assignment_prefixes`, `power_up_map`, `spelling_word_bank`, `auto_logic`, and `canvas_base_url`.
- Initial migration seeds course IDs: Math 21957, Reading 21919, Language Arts 21944, History 21934, Science 21970, Homeroom 22254.
- Initial migration seeds assignment prefixes: Math `SM5:`, Reading `RM4:`, Spelling `RM4:`, Language Arts `ELA4:`.
- Migration `20260417212846_37c0a03f-8008-465b-a2ff-f093e6c8356a.sql` changes Language Arts prefix to `ELA4A`.
- Migration `20260420000000_update_fluency_benchmarks.sql` adds Reading fluency bands and removes `100 words per minute` from generic reading phrases, leaving `tracking and tapping`.
- Trigger `enforce_friday_rules()` sets Friday non-test `create_assign=false` and `at_home=NULL`, and blocks non-CP/non-test Language Arts assignment creation.

### Firebase

Repository: `Thalescanvasgemini`

Evidence:

- Firestore-backed services and functions are present, including `functions/src/core/assignmentEngine.ts`, `functions/src/core/mappings.ts`, and `functions/src/canvas/deployAssignments.ts`.
- `assignmentEngine.ts` stores duplicate guard evidence through `idempotencyKey` and `shouldCreateAssignment()` against the `assignments` collection.
- `firestore.rules`, `firebase-blueprint.json`, and `firebase-applet-config.json` exist, but no richer deterministic curriculum seed was recovered there during this pass.

No live Supabase or Firebase connection was used.

## 6. Conflicting Implementations

| Rule Area | Conflict |
|---|---|
| Power-Up mapping | Supabase seed maps lessons 1-120 and has lessons 3-8 as A/A/A/A/A/A; Thales server/client maps tests 1-23 and has 3:B, 4:C, 6:B, 7:B, 8:C. |
| Study Guide grading | Phase 19B owner-approved docs say Study Guide should be 0 points and excluded from final grade; older client assignment logic returns 100 points and `omitFromFinal=true`; newer server engine returns 0 points, pass/fail, omitted. |
| Reading lesson-to-test | Server mappings hard-lock 80/90/100/110/120/130 -> 8-13; assignment engine only hard-locks 80 -> 8 and falls back by tens. |
| Reading Test 14 / checkout absence | One implementation included a Test 14 checkout path; owner rules confirm Reading Test 14 has no Checkout. |
| Spelling focus words | Announcement path uses cumulative positions 21-25; server helper has first-five and challenge-word selector. |
| Reading/Spelling course ID | Main Together Logic routes Reading/Spelling to 21919; `AnnouncementRM.tsx` has a local `TOGETHER_LOGIC_COURSE_ID = 22254`, likely wrong because 22254 is Homeroom in seeded config. |
| Language Arts prefix | Initial seed uses `ELA4:`, later migration changes to `ELA4A`, while Phase 19 owner-approved docs prefer `ELA4`. |

## 7. Known Legacy Bugs

Evidence recovered:

- Duplicate assignments: pre-deploy validator detects duplicate `subject|day|title`; Firebase engine uses `idempotencyKey`; `Thalescanvasgemini` services include multiple cleanup/dedup paths.
- Incorrect Reading checkout calculation: conflicting `READING_TEST_MAP` vs fallback `Math.ceil(lessonNum / 10)` is a plausible source.
- Historical Test 14 checkout bug is superseded by the owner-confirmed no-checkout rule for Reading Test 14.
- Math Study Guide plus normal homework duplication: Math test triple creates a Study Guide sibling; pre-deploy validator requires paired Study Guide, but normal homework suppression on test/pre-test days is not fully evidenced as a separate rule.
- Incorrect Power Up selection: conflicting Power-Up maps.
- Wrong blank/completed resource selection: no deterministic selector found.
- Missing resource URLs: pre-deploy validator detects lesson references without `canvas_url`.
- Friday homework behavior: three layers recovered: UI default, save mutation, DB trigger, and pre-deploy validator.

## 8. Missing Mappings

These should not be canonicalized from this pass:

- Saxon Math 5 Study Guide blank/completed resource map.
- Saxon Math 5 test-to-Study-Guide exact resource/file map.
- Reading Mastery 4 homework-question map.
- Full Reading lesson-to-reader/resource map.
- Complete resource filename alias registry.
- Owner-confirmed Power-Up authority between Supabase seed and Thales deterministic server map.

## 9. Recommended Canonical Source

Recommended near-term canonicalization strategy:

1. Use Phase 19B owner-approved docs for subject prefixes, Study Guide grading, assignment existence policy, and Friday rules where they exist.
2. Use Supabase `system_config.power_up_map` only as a reviewed candidate, not canonical, until Owen confirms whether it is lesson-based or test-based.
3. Use `Thalescanvasgemini/functions/src/core/mappings.ts` as a reviewed candidate for Fact-Test practice, Reading test map, spelling lists, and fluency bands.
4. Use `pacing-sync-pilot-8c50be47/src/lib/together-logic.ts` and `announcement-templates.ts` as candidates for Reading/Spelling Together Logic and announcement focus words.
5. Do not import any private URLs, live database IDs beyond course mapping history, or raw legacy files.

## 10. Owner-Confirmation Questions

1. Which Power-Up map is authoritative for Phase 22: Supabase lesson 1-120 map, Thales test 1-23 map, or a third source?
2. Should Math Study Guides always be generated for every Math Test, and should they always be due the day before when the test is Tuesday-Friday?
3. Should Math Study Guides suppress normal Math homework on the pre-test day?
4. What is the authoritative blank/completed Study Guide resource naming and selection rule?
5. Should spelling focus words be cumulative positions 21-25, first five, or selected challenge words?
6. Is Reading + Spelling Together Logic course ID 21919 for all future output?
7. Should the Language Arts prefix be `ELA4`, `ELA4A`, or treated as historical alias only?

## 11. Proposed Phase 22 Config Files

Create these only after owner review:

- `fixtures/canvas-llm/phase-22/config-candidates/math-power-up-map.candidate.json`
- `fixtures/canvas-llm/phase-22/config-candidates/math-fact-test-map.candidate.json`
- `fixtures/canvas-llm/phase-22/config-candidates/reading-test-map.candidate.json`
- `fixtures/canvas-llm/phase-22/config-candidates/reading-fluency-bands.candidate.json`
- `fixtures/canvas-llm/phase-22/config-candidates/spelling-test-map.candidate.json`
- `fixtures/canvas-llm/phase-22/config-candidates/assignment-generation-rules.candidate.json`
- `fixtures/canvas-llm/phase-22/config-candidates/resource-aliases.candidate.json`

No tracked Phase 22 configuration was extracted in this pass because the highest-value maps contain unresolved conflicts or missing owner confirmation.
