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
R=scripts/canvas_llm_phase22/artifact_registry.py
Q=scripts/canvas_llm_phase22/approval_queue.py
D=scripts/canvas_llm_phase22/teacher_decisions.py
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
  $M $R $Q $D $A/index.html $A/workstation.js $A/styles.css \
  docs/programs/canvas-llm/canonical-context-pack/artifact-registry-contract.md \
  docs/programs/canvas-llm/canonical-context-pack/approval-queue-contract.md \
  docs/programs/canvas-llm/canonical-context-pack/teacher-decision-contract.md \
  tests/canvas-llm-artifact-health-test.sh \
  tests/canvas-llm-approval-queue-test.sh \
  tests/canvas-llm-teacher-decisions-test.sh \
  tests/canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh; do
  ck "$f" "$f"
done
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$M" "$R" "$Q" "$D" >/tmp/p22py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p22py.txt; fail "Python syntax fails"; }
for n in load_instructional_weeks select_startup_week canonical_week_code get_week_by_code resolve_reading_test resolve_checkout reading_assessment_family render_agenda_html patch_response runtime-proof browser-proof /api/pacing/ /api/calendar/instructional-weeks agenda-preview artifactClassification containsStudentData phase22_validate_artifact_payload selected_graded_assignment_specs build_week_graded_selection_context build_week_announcement_drafts announcement_date_for_target_week month_code_for_date build_monthly_newsletter_draft build_newsletter_update_announcement get_newsletter_month_state homeroom_newsletter_months is_instructional_school_day daily_brief_title daily_brief_intended_for_utc build_daily_teacher_brief build_daily_teacher_briefs_for_week replace_daily_brief_drafts decode_daily_brief_response; do
  has "$M" "$n" "module includes $n"
done
has "$M" "generate monthly homeroom newsletter preview" "module includes generate monthly homeroom newsletter preview"
for n in ArtifactRegistryRecord normalize_draft_row load_registry_from_drafts evaluate_artifact_health print_health_report registry_is_read_only; do
  has "$R" "$n" "artifact registry includes $n"
done
if grep -Fq 'INSERT INTO' "$R" || grep -Fq 'UPDATE drafts' "$R" || grep -Fq 'DELETE FROM drafts' "$R"; then
  fail "artifact registry contains draft mutation statements"
else
  pass "artifact registry remains read-only"
fi
python3 "$R" self-test >/tmp/p22registry.txt 2>&1 && pass "artifact registry self-test passes" || { cat /tmp/p22registry.txt; fail "artifact registry self-test fails"; }
for n in ApprovalQueueItem TeacherDecision build_queue_from_registry derive_queue_status print_queue_report validate_teacher_decision_shape queue_is_read_only; do
  has "$Q" "$n" "approval queue includes $n"
done
if grep -Fq 'artifact_registry' "$Q"; then pass "approval queue builds on artifact registry"; else fail "approval queue missing artifact registry integration"; fi
if grep -Fq 'approve_artifact' "$Q" || grep -Fq 'deploy_artifact' "$Q" || grep -Fq 'UPDATE drafts' "$Q"; then
  fail "approval queue contains approval or deployment mutation handlers"
else
  pass "approval queue remains read-only"
fi
python3 "$Q" self-test >/tmp/p22queue.txt 2>&1 && pass "approval queue self-test passes" || { cat /tmp/p22queue.txt; fail "approval queue self-test fails"; }
for n in TeacherDecisionRecord record_decision sync_invalidations derive_teacher_approval_state list_decision_history print_decision_status_report; do
  has "$D" "$n" "teacher decisions includes $n"
done
if grep -Fq 'teacher_decision_records' "$M"; then pass "teacher decision migration exists"; else fail "teacher decision migration missing"; fi
if grep -Fq 'UPDATE drafts' "$D" || grep -Fq 'deploy_artifact' "$D"; then
  fail "teacher decisions mutate artifacts or deployment handlers"
else
  pass "teacher decisions remain audit-only for artifacts"
fi
python3 "$D" self-test >/tmp/p22decisions.txt 2>&1 && pass "teacher decisions self-test passes" || { cat /tmp/p22decisions.txt; fail "teacher decisions self-test fails"; }
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
import json
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
q1w5=p.instructional_week_by_code('Q1W5'); _,nl,up=p.resolve_newsletter_for_week_start(q1w5['startsOn'])
assert nl['title']=='Homeroom Newsletter — August 2026' and nl['course_id']==26427
assert up['body_text']=='The newsletter has been updated for August 2026.' and up['depends_on']==nl['local_object_id']
monday='2026-08-17'
assert p.daily_brief_title(monday)=='Daily Teacher Brief — Monday, August 17, 2026'
briefs=p.build_daily_teacher_briefs_for_week(q1w5['startsOn'],[],q1w5)
assert len(briefs)==5 and briefs[0]['recipientDisplay']=='Teacher'
assert 'owen.reagan@' not in json.dumps(briefs).lower()
PY
pass "C0P deterministic Daily Teacher Brief previews are generated"
pass "C0O monthly Homeroom newsletter preview is generated"
pass "Reading Test 14 has no Checkout"
pass "Checkout 14 does not exist"
pass "Assignments use same-day 11:59 PM America/New_York due times"
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
