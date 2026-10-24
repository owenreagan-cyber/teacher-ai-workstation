// Canvas Weekly Planner — every screen consumes the canonical planner service.
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));
const REQUEST_TOKEN = document.querySelector('meta[name="teacher-workstation-token"]')?.content || '';
const APP = { data: null, route: null, phone: false, saveTimer: null, dailyChecks: new Set() };

async function api(path, options = {}) {
  const method = options.method || 'GET';
  const headers = {};
  if (method !== 'GET') {
    headers['Content-Type'] = 'application/json';
    headers['X-Teacher-Workstation-Token'] = REQUEST_TOKEN;
  }
  const response = await fetch(path, {method, headers, body: options.body ? JSON.stringify(options.body) : undefined});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || body.error || `Request failed (${response.status})`);
  return body;
}

function parseRoute() {
  const raw = location.hash.replace(/^#\/?/, '');
  if (raw === 'completed' || raw === 'settings' || raw === 'agent') return { special: raw };
  const match = raw.match(/^week\/q([1-4])w(\d+)(?:\/(source|friday|([a-z_]+)\/(plan|ai|preview)))?$/i);
  if (!match) return null;
  return {quarter: Number(match[1]), week: Number(match[2]), code: `Q${match[1]}W${match[2]}`,
    stage: match[3] || 'week', course: match[4] || null, courseStage: match[5] || null};
}

function routeFor(code, ...parts) {
  return `#week/${code.toLowerCase()}${parts.length ? `/${parts.join('/')}` : ''}`;
}

function teacherState(value) {
  return ({done:'Ready', missing:'Not connected', to_review:'Review', stale:'Review again', approved:'Approved',
    not_required:'Not needed', passed:'Passed', needs_you:'Needs you', unavailable:'Unavailable', not_run:'Waiting',
    pending:'Checking', blocked:'Blocked', planned:'Planned', not_started:'Not started', SOURCE_SYNCED:'Source synced',
    PLANNED:'Planned', AI_REVIEWED:'AI reviewed', NEEDS_OWEN:'Needs you', READY_TO_PUBLISH:'Ready for Friday',
    HELD_UNTIL_4PM:'Ready for Friday 4 PM', EXECUTING:'Publishing', PUBLISHED_VERIFIED:'Published and checked',
    BLOCKED:'Blocked'})[value] || String(value || 'Waiting').replaceAll('_', ' ').toLowerCase();
}

function pill(value) {
  const positive = ['done','approved','passed','planned','PUBLISHED_VERIFIED','READY_TO_PUBLISH','HELD_UNTIL_4PM'];
  const negative = ['blocked','BLOCKED'];
  const attention = ['to_review','stale','needs_you','NEEDS_OWEN'];
  const kind = positive.includes(value) ? 'pass' : negative.includes(value) ? 'fail' : attention.includes(value) ? 'warn' : 'neutral';
  return `<span class="pill ${kind}">${esc(teacherState(value))}</span>`;
}

function activeCourse(data, requested) {
  return data.courses.find((course) => course.id === requested)
    || data.courses.find((course) => course.id !== 'homeroom') || data.courses[0];
}

function stageLink(data, stage, course) {
  if (stage === 'week') return routeFor(data.week.code);
  if (stage === 'source' || stage === 'friday') return routeFor(data.week.code, stage);
  return routeFor(data.week.code, course || activeCourse(data).id, stage);
}

function navigation(data, route) {
  const openAi = data.status.action_items.filter((item) => item.deep_link.includes('/ai')).length;
  const approvals = data.courses.filter((course) => !['approved','not_required'].includes(course.stages.preview)).length;
  const selected = route.courseStage || route.stage;
  const items = [['week','Week',null],['source','1 · Source',null],['plan','2 · Plan',null],
    ['ai','3 · AI review',openAi],['preview','4 · Preview & approve',approvals],['friday','5 · Friday',null]];
  return items.map(([id,label,badge]) => `<a class="${selected === id ? 'active' : ''}" href="${stageLink(data,id,route.course)}">
    <span>${label}</span>${badge ? `<span class="nav-badge">${badge}</span>` : ''}</a>`).join('')
    + `<div class="nav-separator"></div><a class="${route.special === 'agent' ? 'active' : ''}" href="#agent">Weekly Planner Agent</a>
       <div class="nav-separator"></div><a class="${route.special === 'completed' ? 'active' : ''}" href="#completed">Completed weeks</a>
       <a class="${route.special === 'settings' ? 'active' : ''}" href="#settings">Settings</a>`;
}

function header(data, title, subtitle = '') {
  const prev = data.week.previous;
  const next = data.week.next;
  return `<header class="page-header"><div><h1>${esc(title)}</h1><p class="page-sub">${esc(subtitle || `${data.week.code} · ${data.week.label}`)}</p></div>
    <div class="week-switcher">${prev ? `<a class="btn neutral small" href="${routeFor(prev.code)}">← ${esc(prev.code)}</a>` : ''}
    ${next ? `<a class="btn neutral small" href="${routeFor(next.code)}">${esc(next.code)} →</a>` : ''}</div></header>`;
}

function courseTabs(data, stage, current) {
  return `<div class="course-tabs">${data.courses.map((course) => {
    const needs = stage === 'ai' ? (course.ai_review.findings || []).filter((f) => ['NEEDS_OWEN','FAIL'].includes(f.status)).length
      : course.stages.preview === 'approved' ? 0 : 1;
    return `<a class="${course.id === current ? 'active' : ''}" href="${routeFor(data.week.code,course.id,stage)}">
      ${esc(course.name)}${needs ? `<span>${needs}</span>` : ''}</a>`;
  }).join('')}</div>`;
}

function summaryText(data) {
  const approvals = data.courses.filter((course) => course.stages.preview !== 'approved').length;
  const ai = data.status.action_items.filter((item) => item.deep_link.includes('/ai')).length;
  if (!approvals && !ai) return 'Everything is approved and ready for Friday.';
  const pieces = [];
  if (approvals) pieces.push(`${approvals} ${approvals === 1 ? 'course needs' : 'courses need'} your review`);
  if (ai) pieces.push(`AI flagged ${ai} ${ai === 1 ? 'thing' : 'things'}`);
  return `Almost ready for Friday. ${pieces.join(', and ')}.`;
}

function nextCourseLink(data, course) {
  if (course.stages.plan !== 'done') return routeFor(data.week.code,course.id,'plan');
  if (course.stages.ai_review === 'needs_you') return routeFor(data.week.code,course.id,'ai');
  return routeFor(data.week.code,course.id,'preview');
}

function viewWeek(data) {
  const next = data.status.next_action;
  const rows = data.courses.map((course) => `<tr><td><strong>${esc(course.name)}</strong></td>
    <td>${pill(course.stages.source)}</td><td>${pill(course.stages.plan)}</td><td>${pill(course.stages.assignments)}</td>
    <td>${pill(course.stages.preview)}</td><td><a class="btn neutral small" href="${nextCourseLink(data,course)}">${course.stages.preview === 'approved' ? 'Review' : 'Fix or review'}</a></td></tr>`).join('');
  const findings = data.status.action_items.filter((item) => item.deep_link.includes('/ai')).slice(0,4);
  return `${header(data,`${data.week.code} · ${data.week.label}`,`Goes live ${formatDate(data.week.rollover_at)}, once all ${data.courses.length} are approved.`)}
    <a class="primary-next" href="${esc(new URL(next.deep_link).hash)}">Next: ${esc(next.title.replace(/^Next:\s*/,''))} →</a>
    <div class="summary-banner">${esc(summaryText(data))}</div>
    <section class="section"><h2>Courses and stages</h2><div class="table-wrap"><table><thead><tr><th>Course</th><th>Source</th><th>Plan</th><th>Assignments</th><th>Page + announcement</th><th></th></tr></thead><tbody>${rows}</tbody></table></div></section>
    <div class="panel-grid"><section class="section"><h2>Pacing source</h2>
      <div class="kv"><span class="k">Sheet</span><span class="v">${esc(data.source.name)}</span></div>
      <div class="kv"><span class="k">Tab</span><span class="v">${esc(data.source.tab)}</span></div>
      <div class="kv"><span class="k">Last synced</span><span class="v">${esc(formatDate(data.source.synced_at))}</span></div>
      <a class="btn neutral" href="${routeFor(data.week.code,'source')}">Review source</a></section>
      <section class="section"><h2>AI check</h2>${findings.length ? findings.map((item) => `<div class="finding-mini"><strong>${esc(item.title)}</strong><br>${esc(item.reason)}</div>`).join('') : '<p class="empty">No open AI findings.</p>'}</section></div>`;
}

function viewSource(data) {
  const proposal = data.source.proposal || {};
  const sheetPreview = data.source.sheet_preview || {};
  const changes = proposal.changed_cells || [];
  const proposalCard = proposal.status === 'PENDING_DECISION' ? `<section class="section change-card"><h2>The sheet changed</h2>
    <p>Nothing has been applied. Review each source change first.</p>
    ${changes.map((change) => `<article class="change-row"><strong>${esc(change.subject)} · ${esc(change.weekday)}</strong>
      <div><del>${esc(change.before || 'blank')}</del> → <ins>${esc(change.after || 'blank')}</ins></div>
      <p>Affects: ${esc((change.affects || []).join(', '))}</p></article>`).join('')}
    <p><strong>Owen's edits kept:</strong> ${(proposal.kept_overrides || []).length}. <strong>Unchanged subjects:</strong> ${esc((proposal.unchanged_subjects || []).join(', ') || 'none')}.</p>
    <div class="btn-row"><button class="btn" data-action="apply-source">Apply change</button>
    <button class="btn neutral" data-action="keep-source">Keep my current plan</button></div></section>` : '';
  const rows = data.courses.filter((course) => course.id !== 'homeroom').map((course) => `<tr><td><strong>${esc(course.name)}</strong></td>
    ${course.days.map((day) => `<td>${esc(day.sheet_says || '—')}${day.edited ? '<span class="edited-badge">Edited</span>' : ''}</td>`).join('')}</tr>`).join('');
  const sheetUrl = data.source.spreadsheet_id ? `https://docs.google.com/spreadsheets/d/${encodeURIComponent(data.source.spreadsheet_id)}` : null;
  const sheetPreviewCard = sheetPreview.status === 'PREVIEWED' ? `<section class="section change-card"><h2>Preview this source</h2>
    <div class="kv"><span class="k">Spreadsheet</span><span class="v">${esc(sheetPreview.name)}</span></div>
    <div class="kv"><span class="k">Tab</span><span class="v">${esc(sheetPreview.tab)}</span></div>
    <p><strong>Detected week columns:</strong> ${esc((sheetPreview.week_columns || []).join(', '))}</p>
    <p><strong>Subjects:</strong> ${esc((sheetPreview.subjects || []).join(', '))}</p>
    <div class="sample-grid">${(sheetPreview.sample_values || []).map((sample) => `<div><strong>${esc(sample.day)} · ${esc(sample.subject)}</strong><br>${esc(sample.value)}</div>`).join('')}</div>
    <p>Saving changes the configured source and stages a review card; it does not apply any pacing change.</p>
    <button class="btn" data-action="save-sheet" data-preview-hash="${esc(sheetPreview.preview_hash)}">Save this source</button></section>` : '';
  return `${header(data,'1 · Source','Review the pacing sheet before anything changes in your plan.')}
    <section class="section source-panel"><div><h2>${esc(data.source.name)}</h2><p>${esc(data.source.tab)} · ${data.source.connected ? 'Connected' : 'Not connected'} · Last synced ${esc(formatDate(data.source.synced_at))}</p></div>
    <div class="btn-row"><button class="btn" data-action="resync-source">Resync</button><button class="btn neutral" data-action="change-sheet">Change sheet</button>
    ${sheetUrl ? `<a class="btn neutral" target="_blank" rel="noreferrer" href="${sheetUrl}">Open in Google Sheets</a>` : ''}</div></section>
    ${sheetPreviewCard}${proposalCard}<section class="section"><h2>Pacing grid</h2><div class="table-wrap"><table><thead><tr><th>Subject</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th></tr></thead><tbody>${rows}</tbody></table></div></section>
    <div class="sticky-actions"><a class="btn neutral" href="${routeFor(data.week.code,activeCourse(data).id,'plan')}">Edit this week</a>
    <a class="btn" href="${routeFor(data.week.code,activeCourse(data).id,'plan')}">Looks right · Continue to Plan</a></div>`;
}

function viewPlan(data, requested) {
  const course = activeCourse(data,requested);
  const questions = (data.questions || []).filter((question) => question.subject === course.id && question.status !== 'ANSWERED');
  const rows = course.days.map((day) => `<tr data-plan-row data-course="${course.id}" data-day="${day.day}">
    <td><strong>${esc(day.day)}</strong><br><span class="muted">${esc(day.date || '')}</span></td><td>${esc(day.sheet_says || '—')}</td>
    <td><label>In Class<textarea data-field="in_class" rows="2">${esc((day.in_class || []).join('\n'))}</textarea></label>
    <label>At Home<input data-field="at_home" value="${esc(day.at_home || '')}"></label>${day.edited ? '<span class="edited-badge">Edited</span>' : ''}
    <div class="btn-row"><button class="btn neutral small" data-action="restore-source" data-course="${course.id}" data-day="${day.day}">Restore source</button>
    <button class="btn neutral small" data-action="mark-pending" data-course="${course.id}" data-day="${day.day}" data-source="${esc(day.sheet_says || '')}">Mark pending</button>
    <button class="btn neutral small" data-action="mark-blank" data-course="${course.id}" data-day="${day.day}" data-source="${esc(day.sheet_says || '')}">Intentionally blank</button></div>
    <div class="autosave-status" aria-live="polite">${esc(teacherState(day.status))}</div></td>
    <td>${day.assignments.length ? day.assignments.map((a) => `<div class="assignment-chip"><strong>${esc(a.title)}</strong><br>${esc(a.assignment_group || 'Assignment')} · due ${esc(a.due_date || '')}
    <button class="btn reject small" data-action="reject-assignment" data-course="${course.id}" data-title="${esc(a.title)}">Reject proposal</button></div>`).join('') : '<span class="empty">None proposed</span>'}
    ${day.reminders.map((r) => `<div class="reminder-chip">${esc(r.title)}</div>`).join('')}</td></tr>`).join('');
  return `${header(data,'2 · Plan','Edit lesson plans and see the assignments they will create.')}${courseTabs(data,'plan',course.id)}
    <section class="section"><div class="table-wrap"><table class="plan-table"><thead><tr><th>Day</th><th>Sheet says</th><th>Your lesson plan</th><th>Assignments it will create</th></tr></thead><tbody>${rows}</tbody></table></div></section>
    <section class="section"><h2>Questions for ${esc(course.name)}</h2>${questions.length ? questions.map((question) => `<article class="finding needs"><h3>${esc(question.reason)}</h3>
    <p>${esc(question.evidence || '')}</p><label>Your answer<input data-question-input="${esc(question.question_id)}" value="${esc(question.answer || '')}"></label>
    <div class="btn-row"><button class="btn small" data-action="answer-question" data-id="${esc(question.question_id)}">Answer</button>
    ${question.recommended_default ? `<button class="btn neutral small" data-action="answer-question" data-id="${esc(question.question_id)}" data-answer="${esc(question.recommended_default)}">Use recommended</button>` : ''}</div></article>`).join('') : '<p class="empty">No open questions.</p>'}</section>
    <div class="sticky-actions"><button class="btn neutral" data-action="add-assignment">Add an assignment</button><button class="btn neutral" data-action="undo-plan">Undo last edit</button>
    <a class="btn" href="${routeFor(data.week.code,course.id,'ai')}">${esc(course.name)} is planned · See AI review</a></div>`;
}

function viewAi(data, requested) {
  const course = activeCourse(data,requested);
  const globalUnavailable = data.ai_review.state === 'UNAVAILABLE';
  const findings = course.ai_review.findings || [];
  const checks = data.ai_review.checks || [];
  return `${header(data,'3 · AI review','AI reviews with evidence. It never edits, approves, or publishes.')}${courseTabs(data,'ai',course.id)}
    ${globalUnavailable ? `<div class="banner fail"><strong>AI review unavailable.</strong> ${esc(data.ai_review.reason)} You may still approve after confirming.</div>` : ''}
    <section class="section"><h2>${esc(course.name)} · ${esc(teacherState(course.stages.ai_review))}</h2>
    ${findings.length ? findings.map((finding) => `<article class="finding ${finding.status === 'NEEDS_OWEN' ? 'needs' : ''}"><h3>${esc(finding.title)}</h3><p>${esc(finding.reason)}</p><pre>${esc(finding.evidence)}</pre>
      ${['NEEDS_OWEN','FAIL'].includes(finding.status) ? `<div class="btn-row"><button class="btn small" data-action="answer-ai" data-id="${esc(finding.id)}" data-answer="ACCEPT">Add it</button>
      <button class="btn neutral small" data-action="answer-ai" data-id="${esc(finding.id)}" data-answer="DECLINE">No, leave it</button></div>` : ''}</article>`).join('') : '<p class="empty">No findings need you.</p>'}</section>
    <section class="section"><h2>What it checked</h2><div class="check-grid">${checks.length ? checks.map((check) => `<div>${pill(String(check.state || '').toLowerCase())} ${esc(String(check.id || '').replaceAll('_',' '))}</div>`).join('') : '<p class="empty">Review has not run yet.</p>'}</div>
    <p class="muted">Model: ${esc(data.ai_review.model || 'No eligible model recorded')}</p></section>
    <div class="sticky-actions"><a class="btn" href="${routeFor(data.week.code,course.id,'preview')}">See exact preview</a></div>`;
}

function viewPreview(data, requested) {
  const course = activeCourse(data,requested);
  const diff = course.reapproval || {};
  const aiUnavailable = data.ai_review.state === 'UNAVAILABLE';
  return `${header(data,'4 · Preview & approve','These are the exact bytes the Friday publisher will use.')}${courseTabs(data,'preview',course.id)}
    ${diff.required && diff.changes?.length ? `<div class="banner warn"><strong>Review again.</strong> ${esc(diff.reason)}
    ${diff.changes.map((change) => `<details><summary>${esc(change.summary)}</summary><pre class="diff">${esc(change.diff)}</pre></details>`).join('')}</div>` : ''}
    <div class="preview-toolbar"><strong>${esc(course.name)}</strong><div><button class="btn neutral small" data-action="preview-width" data-width="desktop">Desktop</button>
    <button class="btn neutral small" data-action="preview-width" data-width="phone">Phone</button></div></div>
    <div class="preview-grid ${APP.phone ? 'phone' : ''}"><section><h2>Page preview</h2><iframe class="preview-frame" data-preview="page" sandbox title="Exact page preview"></iframe></section>
    <section><h2>Announcement preview</h2><p class="muted">${esc(course.name)} · posts ${esc(formatDate(course.announcement.posting_time))}</p>
    ${course.id === 'homeroom' ? '<p class="empty">Homeroom is carried forward as its page; no separate announcement.</p>' : '<iframe class="preview-frame" data-preview="announcement" sandbox title="Exact announcement preview"></iframe>'}</section></div>
    <section class="section"><h2>Assignments and reminders</h2>${course.assignments.length ? course.assignments.map((a) => `<div class="artifact-row"><strong>${esc(a.title)}</strong><span>${esc(a.assignment_group)} · due ${esc(a.due_date)}</span></div>`).join('') : '<p class="empty">No assignments for this course.</p>'}
    ${course.reminders.map((r) => `<div class="artifact-row"><strong>${esc(r.title)}</strong><span>Reminder · ${esc(r.assessment_date)}</span></div>`).join('')}</section>
    <section class="section"><p><strong>AI check:</strong> ${esc(teacherState(course.stages.ai_review))}</p>
    ${aiUnavailable ? '<label class="confirm-line"><input type="checkbox" id="confirm-without-ai"> I reviewed this without AI because the model is unavailable.</label>' : ''}
    <div class="btn-row"><button class="btn" data-action="approve-course" data-course="${course.id}">${course.stages.preview === 'approved' ? 'Approved' : `Approve ${esc(course.name)}`}</button>
    <button class="btn neutral" data-action="individual-items">Review individual items</button>${course.id !== 'homeroom' ? `<button class="btn neutral" data-action="edit-announcement" data-course="${course.id}">Edit announcement</button>` : ''}</div></section>`;
}

function viewFriday(data) {
  const blocked = data.week.rollover_state === 'BLOCKED';
  const rows = data.courses.map((course) => `<li><strong>${esc(course.name)}</strong><span>${course.stages.preview === 'approved' ? 'Approved and ready' : 'Still needs your approval'}</span></li>`).join('');
  return `${header(data,'5 · Friday',`${formatDate(data.week.rollover_at)} · ${relativeDays(data.week.rollover_at)}`)}
    <section class="section friday-head"><label class="switch-line"><span><strong>Automatic rollover</strong><small>Publishes the full week only when every course is approved.</small></span><input type="checkbox" ${data.settings.automatic_rollover ? 'checked' : ''} data-action="automatic-toggle"></label></section>
    ${blocked ? '<div class="banner fail"><strong>Friday rollover is blocked.</strong> The full week needs approval before it can publish.</div>' : '<div class="banner pass"><strong>Ready.</strong> The full package will publish Friday at 4:00 PM.</div>'}
    <section class="section"><h2>Readiness</h2><ul class="readiness-list">${rows}</ul></section>
    <section class="section"><h2>At 4:00 PM, the planner will</h2><ol><li>Make each course's page its home page.</li><li>Post the weekly updates.</li>
    <li>Create the approved assignments and reminders.</li><li>Carry the Homeroom newsletter forward.</li><li>Read everything back from Canvas and confirm it matches what was approved.</li></ol>
    <div class="btn-row"><button class="btn neutral" data-action="dry-run">Dry run now</button>
    <button class="btn" data-action="publish-now">Publish now…</button>
    <button class="btn reject" data-action="partial-publish">Publish approved courses only…</button></div></section>
    <section class="section"><h2>Last week</h2>${data.status.completed.length ? `<p>${esc(data.status.completed[0].week)} · ${esc(data.status.completed[0].result)} · ${esc(formatDate(data.status.completed[0].verified_at))}</p>` : '<p class="empty">No verified prior week found.</p>'}</section>`;
}

function viewCompleted(data) {
  return `${header(data,'Completed weeks','Verified Friday rollover history.')}<section class="section">${data.status.completed.length ? data.status.completed.map((item) => `<div class="artifact-row"><strong>${esc(item.week)}</strong><span>${esc(item.result)} · ${esc(formatDate(item.verified_at))}</span></div>`).join('') : '<p class="empty">No completed weeks yet.</p>'}</section>`;
}

function viewSettings(data) {
  return `${header(data,'Settings','Planner mode and technical details.')}<section class="section"><h2>Planner mode</h2><p>Planning. Nothing goes to Canvas until Friday 4 PM, or until you choose Publish now.</p></section>
    <section class="section"><h2>Technical details</h2><div class="kv"><span class="k">State root</span><span class="v mono">${esc(data.settings.state_root)}</span></div>
    <div class="kv"><span class="k">Source fingerprint</span><span class="v mono">${esc(data.settings.source_hash || '—')}</span></div>
    <div class="kv"><span class="k">Approval store updated</span><span class="v">${esc(formatDate(data.settings.approval_updated_at))}</span></div>
    <details><summary>Page identifiers</summary><pre>${esc(JSON.stringify(data.settings.page_lookup,null,2))}</pre></details></section>
    <section class="section"><h2>System status</h2><pre class="mono">${esc(JSON.stringify(data.settings.system_status,null,2))}</pre></section>
    <section class="section"><h2>Recent history</h2>${data.history.length ? data.history.map((event) => `<div class="history-row"><strong>${esc(event.action.replaceAll('_',' '))}</strong><span>${esc(event.reason)} · ${esc(formatDate(event.at))}</span></div>`).join('') : '<p class="empty">No planner history yet.</p>'}</section>`;
}

function formatDate(value) {
  if (!value) return 'not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([],{weekday:'long',month:'long',day:'numeric',hour:'numeric',minute:'2-digit'});
}
function relativeDays(value) { const days = Math.max(0,Math.ceil((new Date(value).getTime()-Date.now())/86400000)); return days === 0 ? 'today' : `in ${days} day${days === 1 ? '' : 's'}`; }

function renderPreviewFrames(data, route) {
  if (route.courseStage !== 'preview') return;
  const course = activeCourse(data,route.course);
  const page = document.querySelector('[data-preview="page"]');
  const announcement = document.querySelector('[data-preview="announcement"]');
  if (page) page.srcdoc = course.page_html || '<p>Preview unavailable.</p>';
  if (announcement) announcement.srcdoc = course.announcement.exact_html || '<p>Preview unavailable.</p>';
}

async function loadWeek(quarter, week) { return api(`/api/planner-week/${quarter}/${week}`); }
async function chooseDefaultWeek() {
  const home = await api('/api/home');
  const target = home.next_prepared || home.weeks?.[0];
  if (!target) throw new Error('No prepared Canvas week is available.');
  location.hash = `week/q${target.quarter}w${target.week}`;
}

async function render() {
  const route = parseRoute();
  if (!route) return chooseDefaultWeek();
  let data = APP.data;
  if (!data || (!route.special && (data.week.quarter !== route.quarter || data.week.number !== route.week))) {
    if (route.special && !data) {
      const home = await api('/api/home');
      const target = home.next_prepared || home.weeks?.[0];
      data = await loadWeek(target.quarter,target.week);
    } else if (!route.special) data = await loadWeek(route.quarter,route.week);
    APP.data = data;
  }
  APP.route = route;
  if (route.stage === 'source' && !APP.dailyChecks.has(data.week.code)) {
    APP.dailyChecks.add(data.week.code);
    api(`/api/weeks/${data.week.quarter}/${data.week.number}/daily-source-check`,{method:'POST',body:requestBody()})
      .then((result) => { if (result.checked) { APP.data = null; render().catch(showError); } })
      .catch(() => {});
  }
  $('nav').innerHTML = navigation(data,route);
  let html;
  if (route.special === 'completed') html = viewCompleted(data);
  else if (route.special === 'settings') html = viewSettings(data);
  else if (route.special === 'agent') html = viewAgent(data);
  else if (route.stage === 'week') html = viewWeek(data);
  else if (route.stage === 'source') html = viewSource(data);
  else if (route.stage === 'friday') html = viewFriday(data);
  else if (route.courseStage === 'plan') html = viewPlan(data,route.course);
  else if (route.courseStage === 'ai') html = viewAi(data,route.course);
  else html = viewPreview(data,route.course);
  $('main').innerHTML = html;
  renderPreviewFrames(data,route);
  if (route.special === 'agent') renderAgentTab('today');
}

async function refresh() { APP.data = null; await render(); }
function requestBody(extra = {}) { return {source_hash:APP.data.settings.source_hash,...extra}; }

async function act(button) {
  const action = button.dataset.action;
  const {quarter,number:week} = APP.data.week;
  if (action === 'resync-source') await api(`/api/weeks/${quarter}/${week}/resync-source`,{method:'POST',body:requestBody()});
  else if (action === 'apply-source' || action === 'keep-source') await api(`/api/weeks/${quarter}/${week}/${action}`,{method:'POST',body:requestBody()});
  else if (action === 'undo-plan') await api(`/api/weeks/${quarter}/${week}/undo-plan`,{method:'POST',body:requestBody()});
  else if (['restore-source','mark-pending','mark-blank'].includes(action)) {
    await api(`/api/weeks/${quarter}/${week}/${action}`,{method:'POST',body:requestBody({subject:button.dataset.course,day:button.dataset.day,source_value:button.dataset.source || ''})});
  } else if (action === 'answer-question') {
    const answer = button.dataset.answer ?? document.querySelector(`[data-question-input="${CSS.escape(button.dataset.id)}"]`)?.value ?? '';
    await api(`/api/weeks/${quarter}/${week}/questions/${encodeURIComponent(button.dataset.id)}/answer`,{method:'POST',body:requestBody({answer})});
  } else if (action === 'reject-assignment') {
    await api(`/api/weeks/${quarter}/${week}/assignments/disposition`,{method:'POST',body:requestBody({subject:button.dataset.course,title:button.dataset.title,action:'REJECT'})});
  }
  else if (action === 'answer-ai') await api(`/api/weeks/${quarter}/${week}/ai-findings/${encodeURIComponent(button.dataset.id)}`,{method:'POST',body:requestBody({answer:button.dataset.answer})});
  else if (action === 'approve-course') {
    const course = activeCourse(APP.data,button.dataset.course);
    const confirmWithoutAi = Boolean(document.getElementById('confirm-without-ai')?.checked);
    await api(`/api/weeks/${quarter}/${week}/approve-course`,{method:'POST',body:requestBody({course:course.id,expected_hashes:course.hashes,confirm_without_ai:confirmWithoutAi})});
  } else if (action === 'preview-width') { APP.phone = button.dataset.width === 'phone'; return render(); }
  else if (action === 'edit-announcement') {
    const course = activeCourse(APP.data,button.dataset.course);
    const transition = window.prompt('Announcement transition',course.announcement.transition || '');
    if (transition !== null) await api(`/api/weeks/${quarter}/${week}/announcements/edit`,{method:'POST',body:requestBody({subject:course.id,transition})});
  } else if (action === 'change-sheet') {
    const name = window.prompt('Spreadsheet name',APP.data.source.name || ''); if (name === null) return;
    const tab = window.prompt('Tab name',APP.data.source.tab || ''); if (tab === null) return;
    const spreadsheetId = window.prompt('Google Sheets spreadsheet ID',APP.data.source.spreadsheet_id || ''); if (spreadsheetId === null) return;
    await api(`/api/weeks/${quarter}/${week}/change-sheet-preview`,{method:'POST',body:requestBody({name,tab,spreadsheet_id:spreadsheetId})});
  } else if (action === 'save-sheet') {
    await api(`/api/weeks/${quarter}/${week}/change-sheet-save`,{method:'POST',body:requestBody({expected_preview_hash:button.dataset.previewHash})});
  }
  else if (action === 'add-assignment' || action === 'individual-items') { window.alert('Use the course plan and artifact list to review the individual item.'); return; }
  else if (action === 'dry-run') {
    const result = await api(`/api/weeks/${quarter}/${week}/rollover-dry-run`,{method:'POST',body:requestBody({production:true})});
    window.alert(result.summary || 'Dry run finished. Nothing was changed.');
  } else if (action === 'publish-now') {
    const choices = APP.data.courses.map((course) => `${course.id} (${course.name})`).join(', ');
    const courseChoice = window.prompt(`Publish which approved package now? Enter ALL or one course id: ${choices}`, 'ALL');
    if (courseChoice === null) return;
    const selected = courseChoice.trim().toLowerCase() === 'all' ? ['all'] : [courseChoice.trim().toLowerCase()];
    const courseText = selected[0] === 'all' ? 'ALL' : selected[0].toUpperCase();
    const phrase = `PUBLISH NOW ${APP.data.week.code} ${courseText}`;
    const confirmation = window.prompt(`Type exactly: ${phrase}`, '');
    if (confirmation !== phrase) return;
    const result = await api(`/api/weeks/${quarter}/${week}/publish-now`,{method:'POST',body:requestBody({
      courses:selected,owner_confirmation:confirmation,production:true,
    })});
    window.alert(`${result.publish_now_mode || 'Publish now'} completed.${result.warning ? `\n${result.warning}` : ''}`);
  } else if (action === 'partial-publish') {
    const phrase = window.prompt('Families may see mixed weeks. Type PUBLISH APPROVED COURSES to continue.');
    if (phrase !== 'PUBLISH APPROVED COURSES') return;
    await api(`/api/weeks/${quarter}/${week}/rollover-partial`,{method:'POST',body:requestBody({owner_confirmation:phrase,production:true})});
  } else if (action === 'automatic-toggle') {
    await api(`/api/weeks/${quarter}/${week}/automatic-rollover`,{method:'POST',body:requestBody({enabled:Boolean(button.checked)})});
  }
  await refresh();
}

async function savePlanRow(row) {
  const {quarter,number:week} = APP.data.week;
  const inClass = row.querySelector('[data-field="in_class"]').value.split('\n').map((s) => s.trim()).filter(Boolean);
  const atHome = row.querySelector('[data-field="at_home"]').value.trim();
  const status = row.querySelector('.autosave-status');
  status.textContent = 'Saving…';
  try {
    await api(`/api/weeks/${quarter}/${week}/overrides`,{method:'POST',body:requestBody({subject:row.dataset.course,day:row.dataset.day,
      in_class:inClass,at_home:atHome,clear_at_home:!atHome,status:'PLANNED',note:'Edited in Canvas Planner'})});
    status.textContent = 'Saved'; APP.data = null;
  } catch (error) { status.textContent = error.message; }
}

// ---------------------------------------------------------------------------
// Weekly Planner Agent — teacher-facing conversational surface
// ---------------------------------------------------------------------------
function agentWeek() {
  return {quarter: APP.data.week.quarter, week: APP.data.week.number};
}

function viewAgent(data) {
  return `${header(data, 'Weekly Planner Agent', 'Plain language → proposed plan → review → approve')}
  <div class="agent-tabs" id="agent-tabs">
    <button class="agent-tab active" data-agent-tab="today">Today</button>
    <button class="agent-tab" data-agent-tab="week-plan">Week plan</button>
    <button class="agent-tab" data-agent-tab="friday-review">Friday review</button>
    <button class="agent-tab" data-agent-tab="agent">Agent</button>
  </div>
  <div id="agent-body" class="agent-body"><div class="loading">Loading…</div></div>`;
}

function agentTabLabel(tab) {
  return {today:'Today', 'week-plan':'Week plan', 'friday-review':'Friday review', agent:'Agent'}[tab] || 'Today';
}

async function renderAgentTab(tab) {
  const {quarter, week} = agentWeek();
  document.querySelectorAll('.agent-tab').forEach((el) => el.classList.toggle('active', el.dataset.agentTab === tab));
  const body = document.getElementById('agent-body');
  if (!body) return;
  body.innerHTML = '<div class="loading">Loading…</div>';
  try {
    if (tab === 'agent') return renderAgentChat(body, quarter, week);
    const view = {today:'today', 'week-plan':'week-plan', 'friday-review':'friday-review'}[tab];
    const payload = await api(`/api/agent/${view}/${quarter}/${week}`);
    if (tab === 'today') body.innerHTML = renderAgentToday(payload);
    else if (tab === 'week-plan') body.innerHTML = renderAgentWeekPlan(payload);
    else body.innerHTML = renderAgentFridayReview(payload);
  } catch (error) {
    body.innerHTML = `<div class="banner fail">Agent view unavailable: ${esc(error.message)}</div>`;
  }
}

function renderAgentToday(p) {
  const attention = (p.needs_attention || []).map((s) => `<span class="pill warn">${esc(s)}</span>`).join(' ') || '<span class="empty">Nothing needs attention.</span>';
  const freshness = [
    `<div class="kv"><span class="k">Pacing</span><span class="v">${esc(freshnessLabel(p.source_freshness?.pacing))}</span></div>`,
    `<div class="kv"><span class="k">Canvas</span><span class="v">${esc(freshnessLabel(p.source_freshness?.canvas))}</span></div>`,
  ].join('');
  return `<section class="section"><h2>Today</h2>
    <div class="summary-banner">${esc(p.message || 'No changes detected.')}</div>
    <div class="kv"><span class="k">Changes detected</span><span class="v">${p.changes_detected ?? 0}</span></div>
    <div class="kv"><span class="k">Friday review</span><span class="v">${pill(p.friday_review_state)}</span></div>
    <div class="kv"><span class="k">Needs attention</span><span class="v">${attention}</span></div>
    <h3>Source freshness</h3>${freshness}</section>`;
}

function renderAgentWeekPlan(p) {
  const subjects = Object.keys(p.subjects || {});
  if (!subjects.length) return '<section class="section"><h2>Week plan</h2><p class="empty">No plan is available yet.</p></section>';
  const cards = subjects.map((subject) => {
    const days = (p.subjects[subject] || []).map(renderAgentDay).join('');
    return `<div class="agent-subject-card"><h3>${esc(subject)}</h3><div class="agent-days">${days}</div></div>`;
  }).join('');
  return `<section class="section"><h2>Week plan — ${esc(p.week_id || '')}</h2><div class="agent-subject-grid">${cards}</div></section>`;
}

function renderAgentDay(d) {
  const assessment = d.assessment ? `<div class="agent-assessment">${esc(d.assessment.name || 'Assessment')}${d.assessment.day ? ` · ${esc(d.assessment.day)}` : ''}</div>` : '';
  const homework = (d.homework || []).filter(Boolean).map((h) => `<div class="agent-homework">At home: ${esc(h)}</div>`).join('');
  const confidence = d.confidence === 'predicted' ? '<span class="pill warn">Suggested — not confirmed</span>' : '';
  return `<div class="agent-day">
    <div class="agent-day-head"><strong>${esc(d.day)}</strong>${confidence}</div>
    <div>${esc(d.lesson || '')}</div>${assessment}${homework}</div>`;
}

function renderAgentFridayReview(r) {
  const changes = (r.changes_since_last_review || []).map((c) =>
    `<div class="change-card-item">${esc(c.subject)} · ${esc(c.day)} · ${esc(c.type)}</div>`).join('') || '<span class="empty">No changes since last review.</span>';
  const changed = (r.changed_subjects || []).map((s) => `<span class="pill warn">${esc(s)}</span>`).join(' ') || '<span class="empty">All subjects unchanged.</span>';
  return `<section class="section"><h2>Friday review — ${esc(r.week_id || '')}</h2>
    <div class="summary-banner">${pill(r.state)}</div>
    <div class="agent-counts">
      <div class="kv"><span class="k">Pages</span><span class="v">${r.pages_count}</span></div>
      <div class="kv"><span class="k">Assignments</span><span class="v">${r.assignments_count}</span></div>
      <div class="kv"><span class="k">Announcements</span><span class="v">${r.announcements_count}</span></div>
      <div class="kv"><span class="k">Reminders</span><span class="v">${r.reminders_count}</span></div>
    </div>
    <h3>Changed subjects</h3><div>${changed}</div>
    <h3>Changes since last review</h3><div>${changes}</div>
    <p class="empty">Approval and publishing stay in the existing Planner &amp; Friday flow.</p></section>`;
}

function freshnessLabel(value) {
  if (!value) return 'not checked yet';
  try {
    const then = new Date(value).getTime();
    const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
    if (mins < 60) return `Checked ${mins} minute${mins === 1 ? '' : 's'} ago`;
    const hours = Math.round(mins / 60);
    return `Checked ${hours} hour${hours === 1 ? '' : 's'} ago`;
  } catch (_) { return 'stale'; }
}

async function renderAgentChat(body, quarter, week) {
  const view = await api(`/api/agent/view/${quarter}/${week}`);
  const conversation = (view.conversation || []).map((entry) => {
    if (entry.role === 'teacher') return `<div class="chat-line teacher"><strong>You</strong><div>${esc(entry.text)}</div></div>`;
    const reply = entry.result?.reply || '';
    return `<div class="chat-line agent"><strong>Agent</strong><div>${esc(reply)}</div></div>`;
  }).join('') || '<p class="empty">Ask me something, e.g. “Move the Math test to Thursday.”</p>';
  body.innerHTML = `<section class="section agent-chat">
    <h2>Agent</h2>
    <p class="page-sub">Tell me what to change in plain language. No JSON, no hashes, no page IDs.</p>
    <div class="agent-conversation" id="agent-conversation">${conversation}</div>
    <form id="agent-form" class="agent-form">
      <input id="agent-input" class="agent-input" type="text" autocomplete="off" placeholder="What do you want to change?" />
      <button class="btn primary" type="submit">Send</button>
    </form>
    <details class="agent-advanced"><summary>Advanced (debug)</summary>
      <pre>${esc(JSON.stringify(view.plan, null, 2))}</pre></details>
  </section>`;
}

async function submitAgentInstruction(form) {
  const input = document.getElementById('agent-input');
  const text = (input?.value || '').trim();
  if (!text) return;
  const {quarter, week} = agentWeek();
  input.value = '';
  const result = await api(`/api/agent/instruct/${quarter}/${week}`, {method: 'POST', body: {text}});
  await renderAgentTab('agent');
  const convo = document.getElementById('agent-conversation');
  if (convo && result.reply) {
    convo.insertAdjacentHTML('beforeend', `<div class="chat-line teacher"><strong>You</strong><div>${esc(text)}</div></div><div class="chat-line agent"><strong>Agent</strong><div>${esc(result.reply)}</div></div>`);
  }
}

document.addEventListener('click',(event) => { const button = event.target.closest('[data-action]'); if (!button) return; event.preventDefault(); act(button).catch((error) => window.alert(error.message)); });
document.addEventListener('input',(event) => { const row = event.target.closest('[data-plan-row]'); if (!row) return; clearTimeout(APP.saveTimer); APP.saveTimer = setTimeout(() => savePlanRow(row),700); });
document.addEventListener('click',(event) => { const tab = event.target.closest('[data-agent-tab]'); if (!tab) return; event.preventDefault(); renderAgentTab(tab.dataset.agentTab).catch(showError); });
document.addEventListener('submit',(event) => { if (event.target.id !== 'agent-form') return; event.preventDefault(); submitAgentInstruction(event.target).catch((error) => window.alert(error.message)); });
window.addEventListener('hashchange',() => render().catch(showError));
function showError(error) { $('main').innerHTML = `<div class="banner fail"><strong>Planner could not load.</strong> ${esc(error.message)}</div>`; }
render().catch(showError);
