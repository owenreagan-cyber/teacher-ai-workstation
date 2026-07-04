#!/usr/bin/env bash
# One-time generator for app planning lane docs and fixtures. Not invoked by status/dashboard.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

slug_to_closure() { echo "complete_$(echo "$1" | tr '-' '_')_planning_lane"; }

write_planning_doc() {
  local slug="$1" name="$2" tier="$3" inv_row="$4" category="$5" purpose="$6" modes="$7" fixture_hint="$8"
  local closure extra_banner
  closure="$(slug_to_closure "${slug}")"
  extra_banner=""
  [[ "${tier}" == "3" ]] && extra_banner=$'\n**Tier 3 — Owen decision required before implementation mission.**\n'
  local doc="docs/classroom-utilities/${slug}-planning.md"
  cat >"${doc}" <<EOF
# ${name} — Planning Lane

Last updated: 2026-07-04

\`\`\`text
Status: planning-only — not implementation approval
Closure: ${closure}
Classification: Tier ${tier} app planning lane
Inventory row: ${inv_row}
Category: ${category}
Runtime classroom app: blocked
Student data: blocked — absolute
Database/API/integration: blocked
AI generation / local models: blocked
\`\`\`

## Purpose

${purpose}

**Planning lane only. Runtime implementation is not approved.**${extra_banner}

## Teacher Workflow (Planned)

1. Owen opens future utility on classroom display or teacher device (**not built**).
2. Select mode or preset from fake/local labels only.
3. Run activity using display labels — no student roster binding.
4. End session; **no log retained** by default.

## Classroom Use Cases

- Smartboard or projector display for whole-class activities.
- Teacher-only control; aggregate or generic labels only.
- Offline/local future posture — no network required.

## Display / Interaction Modes (Non-Runtime)

${modes}

## Fake / Local Examples

See \`assistant/classroom-utilities/samples/${slug}-planning/\`. Fixtures are \`fake_local_planning_only\`.

Primary fixture label: \`${fixture_hint}\`

## Text-Only Wireframe (Concept)

\`\`\`text
+------------------------------------------+
|  ${name}          [ mode selector ]       |
|                                          |
|         ( main display label area )      |
|                                          |
|  [ teacher control — start / reset ]     |
+------------------------------------------+
No student names. No persistence.
\`\`\`

## Blocked Capabilities

\`\`\`text
runtime app / HTML / JS / React
student data / rosters / grades / behavior logs
database / API / OAuth / network
Drive / NAS / iCloud / Canvas
real curriculum content / AI generation / Ollama
audio / animation runtime / widgets / shortcuts
\`\`\`

## Future Implementation Approval Path

Separate explicit Owen runtime mission required. Cite this doc and \`bin/chief-of-staff --app-ecosystem-planning-lanes-status\` PASS.

## Non-Activation

\`${closure}\` is documentation only. No runtime authorized.

EOF
}

write_fixture() {
  local slug="$1" name="$2" fixture_hint="$3"
  local dir="assistant/classroom-utilities/samples/${slug}-planning"
  mkdir -p "${dir}"
  cat >"${dir}/example-settings-001.json" <<EOF
{
  "fixture_classification": "fake_local_planning_only",
  "app_candidate": "${slug}",
  "display_label": "${fixture_hint}",
  "runtime_app": "blocked",
  "student_data": "none",
  "persistence": "blocked",
  "integrations": "blocked"
}
EOF
  cat >"${dir}/README.md" <<EOF
# ${name} Planning Samples

Fake/local planning fixtures only. Not consumed by any runtime app.
EOF
}

# slug | name | tier | row | category | purpose | modes | fixture_hint
while IFS='|' read -r slug name tier row category purpose modes hint; do
  [[ -z "${slug}" ]] && continue
  write_planning_doc "${slug}" "${name}" "${tier}" "${row}" "${category}" "${purpose}" "${modes}" "${hint}"
  write_fixture "${slug}" "${name}" "${hint}"
done <<'LANES'
interactive-bingo-caller|Interactive Bingo Caller|1|18|arcade / game module|Plan a bingo number caller and randomizer for classroom games using generic number/card labels only.|• Number draw display labels\n• Card grid placeholder labels\n• Teacher-only "next" control concept|example-bingo-number-42
desk-layout-design-architect|Desk Layout Design Architect|1|19|3D / spatial / layout|Plan classroom desk grid layouts with generic seat labels — no real student names.|• Grid row/column labels\n• Table group placeholders\n• Layout preset names|example-seat-grid-a1
daily-schedule-card-designer|Daily Schedule Card Designer|1|22|design / print utility|Plan printable daily schedule cards with subject/time labels only.|• Period block labels\n• Subject placeholder text\n• Print layout wireframe|example-period-morning-math
pyramid-game|Pyramid Game|1|38|arcade / game module|Plan a word-association pyramid game shell with category labels.|• Category tier labels\n• Clue placeholder text\n• Team score placeholders (no names)|example-category-animals
word-scramble|Word Scramble|1|39|arcade / game module|Plan an anagram display game with fake scrambled word labels.|• Scrambled letter labels\n• Hint placeholder\n• Reveal control concept|example-scrambled-word-label
code-cracker|Code Cracker|1|35|arcade / game module|Plan a vault/code puzzle game shell with fake code labels.|• Code digit placeholders\n• Hint label slots\n• Success state text only|example-vault-code-label
lets-make-a-deal-curtain-game|Let's Make a Deal Curtain Game|1|24|arcade / game module|Plan a game-show curtain picker with generic prize labels.|• Curtain A/B/C labels\n• Prize placeholder text\n• Teacher pick control|example-curtain-choice-b
classroom-arcade|Classroom Arcade|1|7|arcade / game module|Plan an arcade hub shell listing game mode labels without executable games.|• Mode menu labels\n• Hub navigation placeholders\n• No student binding|example-arcade-mode-review
note-taking-prompt-engine|Note-Taking Prompt Engine|1|47|personal utility|Plan a prompt library for note-taking app ideas — docs only.|• Prompt template labels\n• Section outline placeholders\n• No app runtime|example-prompt-outline-label
ipad-optimizer-prompt-engine|iPad Optimizer Prompt Generator|1|44|design / print utility|Plan iPad layout optimization prompt templates for teacher reference.|• Layout constraint labels\n• Prompt snippet placeholders\n• No device probing|example-ipad-layout-prompt
noise-meter|Noise Meter|2|5|classroom management|Plan noise threshold display labels — aggregate only, no live microphone.|• Threshold band labels\n• Aggregate level placeholders\n• No individual student attribution|example-noise-level-calm
time-bomb-vocabulary-game|Time Bomb Vocabulary Game|2|29|arcade / game module|Plan a timed vocabulary game shell with fake word list labels.|• Countdown display concept\n• Fake vocab word labels\n• No real curriculum text|example-vocab-word-label
charades-game|Charades Game|2|30|arcade / game module|Plan charades prompt cards with generic action labels.|• Prompt card labels\n• Category placeholders\n• Timer display concept (labels only)|example-charades-prompt-label
trivia-showdown|Trivia Showdown|2|42|arcade / game module|Plan a trivia game shell with fake question labels.|• Question placeholder text\n• Answer reveal labels\n• Team placeholder names (generic)|example-trivia-question-label
thales-os-morning-preview-banner|Thales OS Morning Preview Banner|2|40|presentation / display|Plan a morning announcement banner wireframe — Thales family, no runtime.|• Banner headline placeholders\n• Date/period labels\n• No live feed|example-morning-headline-label
live-session-auto-burst-presentation|Live Session Auto-Burst Presentation Engine|2|36|presentation / display|Plan static slide-burst labels tied to Presentation Engine — no auto-generation.|• Slide burst sequence labels\n• Session placeholder IDs\n• Generation runtime blocked|example-burst-sequence-label
design-architect-interview-system|Design Architect Interview System|2|52|design / print utility|Plan interview question wireframes for design discovery — docs only.|• Question category labels\n• Response outline placeholders\n• No runtime app|example-interview-question-label
daily-agenda-announcement-engine|Daily Agenda and Announcement Engine|2|26|presentation / display|Plan daily agenda display labels for classroom screen.|• Agenda item labels\n• Announcement placeholders\n• Time block text|example-agenda-item-label
spelling-studio|Spelling Studio|3|6|curriculum prep|Plan literacy practice shell labels — fake word lists only; curriculum gate applies.|• Fake word-list labels\n• Practice mode placeholders\n• Real curriculum ingestion blocked|example-spelling-word-label
shurley-chapter-parser|Shurley English Chapter Parser|3|25|curriculum prep|Plan chapter outline labels — no parser, no real Shurley content.|• Chapter section labels\n• Outline placeholder text\n• Parser/OCR blocked|example-chapter-outline-label
shurley-sentence-diagrammer|Shurley Sentence Diagrammer|3|33|curriculum prep|Plan sentence diagram wireframe labels — fake sentences only.|• Sentence placeholder labels\n• Diagram node text\n• No real curriculum sentences|example-sentence-diagram-label
power-up-packet-maker|Power Up Packet Maker|3|43|curriculum prep|Plan packet outline wireframes — no real worksheet content.|• Section header labels\n• Activity placeholder text\n• Generation blocked|example-packet-section-label
constitution-prompts-architect|Constitution Prompts Architect|3|49|curriculum prep|Plan civics prompt template labels — fake topic names only.|• Topic placeholder labels\n• Prompt structure outline\n• No real civics authority claims|example-civics-topic-label
science-worksheet-portal|Science Worksheet Portal|3|51|curriculum prep|Plan science worksheet portal wireframe — fake topic labels only.|• Unit topic placeholders\n• Worksheet shell labels\n• No real science content|example-science-topic-label
ultimate-design-architect|Ultimate Design Architect|3|31|design / print utility|Plan omni-prompt portal outline — prompt templates only.|• Prompt category labels\n• Template placeholder text\n• No runtime portal|example-design-prompt-label
valentine-holiday-pass-generator|Valentine Holiday Pass Generator|3|34|design / print utility|Plan generic holiday pass art labels — no student names on passes.|• Pass template labels\n• Holiday art placeholders\n• Generic text only|example-holiday-pass-label
LANES

echo "Generated planning docs and fixtures."
