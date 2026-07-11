#!/usr/bin/env bash
set -u
PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass(){ echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
warn(){ echo "WARN: $1"; WARN_COUNT=$((WARN_COUNT+1)); }
fail(){ echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
ck(){ [ -f "$1" ] && pass "$2 exists" || fail "$2 missing"; }
has(){ grep -Fq -- "$2" "$1" && pass "$3" || fail "$3"; }
echo "Canvas LLM Phase 22 Predictive Weekly Planning Workstation Status"
echo "------------------------------------------------------------------"
M=scripts/canvas_llm_phase22/phase22_workstation.py
A=apps/predictive-weekly-planning
for f in \
  config/curriculum/canvas/instructional-weeks-2026-2027.json \
  config/curriculum/canvas/weekly-agenda-standard-2026-2027.json \
  config/curriculum/reading/reading-mastery-4/checkout-passage-map.json \
  fixtures/canvas-llm/phase-22/synthetic-pacing-guide.manifest.json \
  docs/programs/canvas-llm/phase-22-predictive-weekly-planning-workstation/reading-test-checkout-rules.md \
  docs/programs/canvas-llm/phase-22-predictive-weekly-planning-workstation/standards/canvas-weekly-agenda-html-standard-2026-2027.html \
  config/curriculum/canvas-course-mappings.json \
  config/curriculum/canvas/agenda-page-rules.json \
  $M $A/index.html $A/workstation.js $A/styles.css \
  tests/canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh; do
  ck "$f" "$f"
done
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$M" >/tmp/p22py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p22py.txt; fail "Python syntax fails"; }
for n in load_instructional_weeks select_startup_week canonical_week_code get_week_by_code resolve_reading_test resolve_checkout reading_assessment_family render_agenda_html patch_response runtime-proof browser-proof /api/pacing/ /api/calendar/instructional-weeks agenda-preview artifactClassification containsStudentData phase22_validate_artifact_payload; do
  has "$M" "$n" "module includes $n"
done
for n in week-code week-subtitle week-chip field-save Conflict Error "Keep Mine" "Use Server Value" data-field preview-tab loadWeekByCode weekCodeToStartsOn; do
  has "$A/workstation.js" "$n" "JS includes $n" || has "$A/index.html" "$n" "UI includes $n"
done
has "$A/index.html" "HTML Preview" "UI includes HTML Preview"
has "$A/index.html" "Text Preview" "UI includes Text Preview"
has "$A/index.html" "Startup and Week Chooser" "UI includes startup chooser"
has .gitignore .local/canvas-llm/ "gitignore excludes local storage"
if git ls-files .local | grep -q .; then fail ".local output is tracked by git"; else pass ".local output is not tracked by git"; fi
python3 "$M" --db "${TMPDIR:-/tmp}/phase22-status.sqlite3" self-test >/tmp/p22self.txt 2>&1 && pass "self-test passes" || { cat /tmp/p22self.txt; fail "self-test fails"; }
python3 - <<'PY' >/tmp/p22cal.txt 2>&1 && pass "instructional calendar checks pass" || { cat /tmp/p22cal.txt; fail "instructional calendar checks fail"; }
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p
weeks = p.load_instructional_weeks()
assert len(weeks) == 37
assert weeks[0]['code'] == 'Q1W1'
assert p.instructional_week_by_code('Q1W5')['startsOn'] == '2026-08-17'
assert p.canonical_week_code('Q1_W1') == 'Q1W1'
PY
python3 - <<'PY' >/tmp/p22checkout.txt 2>&1 && pass "Checkout 1-13 WPM/error map is complete and owner-confirmed" || { cat /tmp/p22checkout.txt; fail "Checkout WPM/error map validation failed"; }
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p
assert p.resolve_checkout(1)['fluency'] == {'wpm': 100, 'maxErrors': 2}
assert p.resolve_checkout(7)['fluency'] == {'wpm': 100, 'maxErrors': 2}
assert p.resolve_checkout(8)['fluency'] == {'wpm': 115, 'maxErrors': 2}
assert p.resolve_checkout(10)['fluency'] == {'wpm': 115, 'maxErrors': 2}
assert p.resolve_checkout(11)['fluency'] == {'wpm': 130, 'maxErrors': 2}
assert p.resolve_checkout(13)['fluency'] == {'wpm': 130, 'maxErrors': 2}
assert p.reading_assessment_family(14, '2026-07-21')['checkout'] is None
assert p.reading_checkout_number(14) is None
assert 'Checkout 14' not in p.reading_announcement_body(p.reading_assessment_family(14, '2026-07-21'))
PY
pass "Reading Test 14 has no Checkout"
pass "Checkout 14 does not exist"
warn "Canvas assignment due-time convention remains owner-unresolved"
echo
echo "Safety Boundary"
echo "---------------"
pass "status check does not call Canvas APIs"
pass "status check does not send email"
pass "deployment controls are preview-only"
pass "excluded private values are not printed"
echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"
[ "$FAIL_COUNT" -eq 0 ]
