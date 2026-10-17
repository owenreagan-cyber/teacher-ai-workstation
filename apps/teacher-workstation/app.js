// Teacher Workstation — interactive planning (local-state only, no Canvas).
// Edits mutate .local planning state via POST/DELETE; never Canvas.

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const SUBJECTS = [
  { key: 'math', label: 'Math' },
  { key: 'reading_spelling', label: 'Reading/Spelling' },
  { key: 'language_arts', label: 'Language Arts' },
  { key: 'science', label: 'Science' },
  { key: 'history', label: 'History' },
];

const NAV = [
  { id: 'home', label: 'Home' },
  { id: 'weekly', label: 'Weekly Planning' },
  { id: 'assignments', label: 'Assignments' },
  { id: 'announcements', label: 'Announcements' },
  { id: 'questions', label: 'Questions' },
  { id: 'review', label: 'Review & Publish' },
  { id: 'completed', label: 'Completed Weeks' },
  { id: 'system', label: 'System Status' },
];

const STATE = { detail: null, dirty: false };

async function api(path, opts) {
  const o = opts || {};
  const r = await fetch(path, {
    method: o.method || 'GET',
    headers: o.body ? { 'Content-Type': 'application/json' } : {},
    body: o.body ? JSON.stringify(o.body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const err = new Error(data.detail || data.error || `HTTP ${r.status}`);
    err.status = r.status;
    err.data = data;
    throw err;
  }
  return data;
}

function statePill(state) {
  const map = {
    'PUBLISHED_VERIFIED': 'pass', 'READY_TO_PUBLISH': 'pass', 'READY_FOR_REVIEW': 'warn',
    'NEEDS_INPUT': 'warn', 'DRAFTED': 'pending', 'NORMALIZED': 'pending', 'SOURCE_FETCHED': 'pending',
    'APPROVED': 'pass', 'PENDING': 'pending', 'NEEDS_CHANGES': 'warn', 'BLOCKED': 'fail',
  };
  return `<span class="pill ${map[state] || 'neutral'}">${esc(state)}</span>`;
}

function dayStatePill(state) {
  const map = {
    'PLANNED': 'neutral', 'PENDING_SOURCE': 'pending', 'OWNER_CONFIRMED_BLANK': 'neutral',
    'NOT_APPLICABLE': 'pending', 'NEEDS_INPUT': 'warn', 'READY': 'pass',
    'ASSESSMENT': 'warn', 'REVIEW': 'neutral', 'BLOCKED': 'fail',
  };
  const label = { 'PENDING_SOURCE': 'PENDING', 'OWNER_CONFIRMED_BLANK': 'BLANK', 'NOT_APPLICABLE': 'N/A' };
  return `<span class="pill ${map[state] || 'neutral'}">${esc(label[state] || state)}</span>`;
}

function nav() {
  return NAV.map(n => `<a href="#${n.id}" data-nav="${n.id}">${n.label}</a>`).join('');
}

function banner() {
  return `<div class="banner readonly"><strong>Local planning mode.</strong> Edits save to local intake state only. Canvas writes stay disabled.</div>`;
}

function subjectLabel(key) {
  const s = SUBJECTS.find(x => x.key === key);
  return s ? s.label : key;
}

function fmtRange(range) {
  if (!range) return '—';
  return `${range.start || ''} → ${range.end || ''}`;
}

// ============ helpers ============

async function currentWeek() {
  const h = await api('/api/home');
  const weeks = h.weeks || [];
  const prepared = weeks.filter(w => w.status !== 'PUBLISHED_VERIFIED');
  if (!prepared.length) return null;
  const t = prepared[0];
  return api(`/api/week/${t.quarter}/${t.week}`);
}

function overrideFor(detail, subject, day) {
  return (detail.owner_overrides || []).find(o => o.subject === subject && o.day === day) || null;
}

// ============ Views ============

async function viewHome() {
  const h = await api('/api/home');
  const s = await api('/api/status');
  const completed = h.latest_completed;
  const next = h.next_prepared;
  let needs = [];
  if (next) {
    const detail = await api(`/api/week/${next.quarter}/${next.week}`);
    needs = detail.open_questions || [];
    // Also surface pending days for actionable "what needs Owen".
    const pending = [];
    for (const subj of SUBJECTS) {
      for (const wd of WEEKDAYS) {
        const st = (detail.day_states[subj.key] || {})[wd];
        if (st === 'PENDING_SOURCE' || st === 'NEEDS_INPUT') pending.push({ subject: subj.label, day: wd });
      }
    }
    return renderHome(h, s, completed, next, needs, pending);
  }
  return renderHome(h, s, completed, next, needs, []);
}

function renderHome(h, s, completed, next, needs, pending) {
  const needsHtml = (needs.length || pending.length)
    ? `<ul class="needs-list">`
      + pending.map(p => `<li><a href="#subject/${next.quarter}/${next.week}/${SUBJECTS.find(x=>x.label===p.subject).key}"><span class="q-subject">${esc(p.subject)}</span> — ${esc(p.day)} plan pending</a></li>`).join('')
      + needs.map(q => `<li><a href="#questions"><span class="q-subject">${esc(subjectLabel(q.subject))}</span> — ${esc(q.reason)}</a></li>`).join('')
      + `</ul>`
    : '<div class="empty">Nothing pending.</div>';

  return `
    ${banner()}
    <h1>Teacher Workstation</h1>
    <p class="page-sub">${esc(h.today)} · Current week: ${esc(h.current_week || '—')}</p>
    <div class="panel-grid">
      <div class="section">
        <h2>Today</h2>
        <div class="kv"><span class="k">Date</span><span class="v">${esc(h.today)}</span></div>
        <div class="kv"><span class="k">Current week</span><span class="v">${esc(h.current_week || '—')}</span></div>
      </div>
      <div class="section">
        <h2>Latest completed</h2>
        ${completed ? `<div class="kv"><span class="k">Week</span><span class="v">${esc(completed.week_code)}</span></div>
          <div class="kv"><span class="k">Status</span><span class="v">${statePill(completed.status)}</span></div>` : '<div class="empty">None yet.</div>'}
      </div>
    </div>
    <div class="section">
      <h2>Next prepared</h2>
      ${next ? `<div class="kv"><span class="k">Week</span><span class="v">${esc(next.week_code)}</span></div>
        <div class="kv"><span class="k">Status</span><span class="v">${statePill(next.status)}</span></div>
        <div class="kv"><span class="k">Dates</span><span class="v">${esc(fmtRange(next.date_range))}</span></div>` : '<div class="empty">No next week prepared.</div>'}
    </div>
    <div class="section"><h2>What needs Owen?</h2>${needsHtml}</div>
    <div class="section"><h2>System status</h2><pre class="mono" style="white-space:pre-wrap;font-size:12.5px;">${esc(s.text)}</pre></div>
  `;
}

async function viewWeekly() {
  const d = await currentWeek();
  if (!d) return '<h1>Weekly Planning</h1><div class="empty">No prepared week.</div>';
  STATE.detail = d;
  return renderWeekly(d);
}

function renderWeekly(d) {
  const states = d.day_states || {};
  const rows = SUBJECTS.map(s => {
    const cells = WEEKDAYS.map(wd => {
      const st = (states[s.key] || {})[wd] || 'PENDING_SOURCE';
      const ov = overrideFor(d, s.key, wd);
      const mark = ov ? ' · override' : '';
      return `<td><button class="cell ${st.toLowerCase()}" data-subject="${s.key}" data-day="${wd}" title="${esc(subjectLabel(s.key))} ${wd}${mark}">${dayStatePill(st)}</button></td>`;
    }).join('');
    return `<tr><td><a href="#subject/${d.quarter}/${d.week}/${s.key}">${s.label}</a></td>${cells}</tr>`;
  }).join('');
  return `
    ${banner()}
    <h1>${esc(d.week_code)} — Weekly Planning</h1>
    <p class="page-sub">${esc(fmtRange(d.date_range))} · ${statePill(d.status)}</p>
    <div class="section">
      <h2>Subject grid</h2>
      <p class="muted" style="margin-bottom:8px;">Click a cell to edit that day. Save applies a local owner override (never Canvas).</p>
      <table class="grid-table">
        <thead><tr><th>Subject</th>${WEEKDAYS.map(w => `<th>${w.slice(0,3)}</th>`).join('')}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="section" id="editor-slot"></div>
    <div class="section"><h2>Open questions (${(d.open_questions || []).length})</h2>${renderQuestions(d.open_questions || [], d)}</div>
  `;
}

async function viewSubject(quarter, week, subject) {
  const d = await api(`/api/week/${quarter}/${week}`);
  STATE.detail = d;
  const norm = (d.week_norm || {}).subjects || {};
  const states = d.day_states || {};
  const subjNorm = norm[subject] || {};

  const dayRows = WEEKDAYS.map(wd => {
    const cell = subjNorm[wd] || { raw: '', blank: true };
    const st = (states[subject] || {})[wd] || 'PENDING_SOURCE';
    const ov = overrideFor(d, subject, wd);
    return `<tr>
      <td>${wd}</td>
      <td class="mono">${esc(cell.raw || '') || '<span class="muted">blank</span>'}</td>
      <td>${ov && ov.at_home ? `<div class="override" style="padding:4px 8px;font-size:12px;">Owner: ${esc(ov.at_home)}</div>` : ''}</td>
      <td>${dayStatePill(st)}</td>
      <td><button class="btn small" data-edit="${subject}" data-day="${wd}">Edit</button></td>
    </tr>`;
  }).join('');

  const assigns = (d.assignments || []).filter(a => a.course === subject);
  const rems = (d.assessment_reminders || []).filter(r => r.course === subjectLabel(subject));
  const approves = (d.approval_summary || {})[subject] || {};

  return `
    ${banner()}
    <h1>${subjectLabel(subject)}</h1>
    <p class="page-sub">${esc(d.week_code)} · ${esc(fmtRange(d.date_range))}</p>
    <div class="section">
      <h2>Pacing by day</h2>
      <table><thead><tr><th>Day</th><th>Source</th><th>Owner override</th><th>State</th><th></th></tr></thead><tbody>${dayRows}</tbody></table>
    </div>
    <div class="section"><h2>Assignments (${assigns.length})</h2>${renderAssignments(assigns)}</div>
    <div class="section"><h2>Assessment reminders (${rems.length})</h2>
      ${rems.length ? rems.map(r => `<div class="card"><div class="card-title">${esc(r.title)}</div><div class="card-meta">${esc(r.assessment_date || '')}${r.power_up ? ` · Power Up ${esc(r.power_up)}` : ''}</div></div>`).join('') : '<div class="empty">None.</div>'}
    </div>
    <div class="section"><h2>Approvals</h2>${renderApprovals(approves)}</div>
    <div class="section" id="editor-slot"></div>
  `;
}

async function viewAssignments() {
  const d = await currentWeek();
  if (!d) return '<h1>Assignments</h1><div class="empty">No prepared week.</div>';
  STATE.detail = d;
  return `${banner()}<h1>Assignments</h1><p class="page-sub">${esc(d.week_code)} — proposals only.</p>
    <div class="section">${renderAssignments(d.assignments || [])}</div>`;
}

function renderAssignments(assigns) {
  if (!assigns.length) return '<div class="empty">None.</div>';
  return `<table><thead><tr><th>Subject</th><th>Title</th><th>Group</th><th>Due</th><th>Duplicate</th><th>Action</th></tr></thead><tbody>
    ${assigns.map(a => `<tr>
      <td>${subjectLabel(a.course)}</td>
      <td>${esc(a.title)}</td>
      <td>${esc(a.assignment_group)}</td>
      <td>${esc(a.due_date)}</td>
      <td>${esc(a.duplicate_classification || 'NEW_PROPOSAL')}</td>
      <td><button class="btn small reject" data-reject="${esc(a.title)}" data-subject="${esc(a.course)}">Reject</button></td>
    </tr>`).join('')}</tbody></table>`;
}

async function viewAnnouncements() {
  const d = await currentWeek();
  if (!d) return '<h1>Announcements</h1><div class="empty">No prepared week.</div>';
  STATE.detail = d;
  const weekly = d.weekly_announcements || [];
  const rems = d.assessment_reminders || [];
  return `
    ${banner()}
    <h1>Announcements</h1>
    <p class="page-sub">${esc(d.week_code)} — drafts only.</p>
    <div class="section">
      <h2>Weekly updates (${weekly.length})</h2>
      ${weekly.map(a => `<div class="card"><div class="card-title">${esc(a.title)}</div>
        <div class="card-meta">${esc(a.transition || '')}</div></div>`).join('') || '<div class="empty">None.</div>'}
    </div>
    <div class="section">
      <h2>Assessment reminders (${rems.length})</h2>
      ${rems.map(r => `<div class="card"><div class="card-title">${esc(r.title)}</div>
        <div class="card-meta">${esc(r.course)} · ${esc(r.assessment_date || '')}${r.power_up ? ` · <strong>Power Up ${esc(r.power_up)}</strong>` : ''}</div></div>`).join('') || '<div class="empty">None.</div>'}
    </div>
  `;
}

async function viewQuestions() {
  const d = await currentWeek();
  if (!d) return '<h1>Questions</h1><div class="empty">No prepared week.</div>';
  STATE.detail = d;
  const open = d.open_questions || [];
  const answered = (d.questions || []).filter(q => q.status === 'ANSWERED');
  return `
    ${banner()}
    <h1>Questions</h1>
    <p class="page-sub">${esc(d.week_code)}</p>
    <div class="section"><h2>Open (${open.length})</h2>${renderQuestions(open, d)}</div>
    <div class="section"><h2>Answered (${answered.length})</h2>
      ${answered.length ? answered.map(q => `<div class="card"><div class="card-title">${subjectLabel(q.subject)}</div><div class="card-meta">${esc(q.answer || '')}</div></div>`).join('') : '<div class="empty">None.</div>'}
    </div>
  `;
}

function renderQuestions(qs, d) {
  if (!qs || !qs.length) return '<div class="empty">None.</div>';
  return qs.map(q => `<div class="card">
    <div class="card-title">${subjectLabel(q.subject)}${q.date ? ` · ${esc(q.date)}` : ''}</div>
    <div>${esc(q.reason)}</div>
    <div class="card-meta" style="margin-top:6px;">Recommended: ${esc(q.recommended_default || '—')}</div>
    <div class="answer-row" style="margin-top:8px;">
      <input type="text" class="q-answer" placeholder="Answer…" data-qid="${esc(q.question_id)}" data-recommended="${esc(q.recommended_default || '')}">
      <button class="btn small" data-answer="${esc(q.question_id)}">Answer</button>
      <button class="btn small" data-recommended-btn="${esc(q.question_id)}">Use recommended</button>
    </div>
  </div>`).join('');
}

async function viewReview() {
  const d = await currentWeek();
  if (!d) return '<h1>Review &amp; Publish</h1><div class="empty">No prepared week.</div>';
  const ready = d.ready_to_publish;
  const touched = d.active_subjects || [];
  const untouched = SUBJECTS.map(s => s.label).filter(l => !touched.map(subjectLabel).includes(l));
  return `
    ${banner()}
    <h1>Review &amp; Publish</h1>
    <p class="page-sub">${esc(d.week_code)} — read-only preview.</p>
    <div class="section">
      <h2>Ready to publish</h2>
      <div class="kv"><span class="k">State</span><span class="v">${ready ? statePill('READY_TO_PUBLISH') : '<span class="pill warn">NOT READY</span>'}</span></div>
      ${(d.publish_blockers || []).length ? `<div style="margin-top:8px;">${d.publish_blockers.map(b => `<div class="muted">· ${esc(b)}</div>`).join('')}</div>` : ''}
    </div>
    <div class="section">
      <h2>What would happen (if approved)</h2>
      <div class="kv"><span class="k">WILL UPDATE pages</span><span class="v">${(d.page_files ? Object.values(d.page_files).filter(p => p.exists).length : 0)}</span></div>
      <div class="kv"><span class="k">WILL CREATE assignments</span><span class="v">${(d.assignments || []).length}</span></div>
      <div class="kv"><span class="k">WILL POST announcements</span><span class="v">${(d.weekly_announcements || []).length}</span></div>
      <div class="kv"><span class="k">Assessment reminders</span><span class="v">${(d.assessment_reminders || []).length}</span></div>
    </div>
    <div class="section">
      <h2>Courses</h2>
      <div class="kv"><span class="k">Touched</span><span class="v">${touched.map(subjectLabel).join(', ') || '—'}</span></div>
      <div class="kv"><span class="k">Untouched</span><span class="v">${untouched.join(', ') || '—'}</span></div>
    </div>
    <div class="banner readonly">Deployment is a separate, guarded workflow. No deploy button here.</div>
  `;
}

async function viewCompleted() {
  const c = await api('/api/completed');
  const latest = c.latest;
  if (!latest) return '<h1>Completed Weeks</h1><div class="empty">None.</div>';
  const ledger = latest.ledger || {};
  return `
    ${banner()}
    <h1>Completed Weeks</h1>
    <p class="page-sub">Latest completed deployment.</p>
    <div class="section">
      <h2>${esc(latest.week_code)} — ${statePill('PUBLISHED_VERIFIED')}</h2>
      <div class="kv"><span class="k">Dates</span><span class="v">${esc(fmtRange(latest.date_range))}</span></div>
      <div class="kv"><span class="k">Pages</span><span class="v">${(ledger.pages || []).length}</span></div>
      <div class="kv"><span class="k">Assignments</span><span class="v">${ledger.assignment_count || 0}</span></div>
      <div class="kv"><span class="k">Assessment reminders</span><span class="v">${(ledger.assessment_reminders || []).length}</span></div>
      <div class="kv"><span class="k">Email / Inbox sends</span><span class="v">${(ledger.communication || {}).email_sends ?? 0} / ${(ledger.communication || {}).canvas_inbox_sends ?? 0}</span></div>
    </div>
  `;
}

async function viewSystem() {
  const s = await api('/api/status');
  return `${banner()}<h1>System Status</h1><p class="page-sub">Chief of Staff · Canvas Weekly Intake health.</p>
    <div class="section"><pre class="mono" style="white-space:pre-wrap;font-size:13px;">${esc(s.text)}</pre></div>`;
}

function renderApprovals(approves) {
  if (!approves || !Object.keys(approves).length) return '<div class="empty">None.</div>';
  const order = ['page', 'assignments', 'announcement', 'assessment_reminder'];
  return `<table><thead><tr><th>Artifact</th><th>State</th></tr></thead><tbody>
    ${order.map(g => `<tr><td>${g.replace('_', ' ')}</td><td>${statePill(approves[g] || 'PENDING')}</td></tr>`).join('')}
  </tbody></table>`;
}

// ============ Day editor (impact-preview + save) ============

function renderEditor(d, subject, day) {
  const norm = (d.week_norm || {}).subjects || {};
  const cell = (norm[subject] || {})[day] || { raw: '', blank: true };
  const ov = overrideFor(d, subject, day) || {};
  const inClass = (ov.in_class || []).join('\n');
  const atHome = ov.at_home || '';
  const status = ov.status || 'PLANNED';

  const affected = [
    `${subjectLabel(subject)} weekly page`,
    `${subjectLabel(subject)} weekly announcement`,
    `${subjectLabel(subject)} approvals become stale`,
  ];

  return `
    <h2>Edit — ${subjectLabel(subject)} · ${day}</h2>
    <div class="kv"><span class="k">Source</span><span class="v mono">${esc(cell.raw || '') || '<span class="muted">blank</span>'}</span></div>
    <div class="kv"><span class="k">Owner override</span><span class="v">${ov.active === undefined ? 'none' : ov.at_home ? 'present' : 'status: ' + esc(status)}</span></div>

    <label class="field-label">In Class (one line per item)</label>
    <textarea id="edit-inclass" rows="2">${esc(inClass)}</textarea>

    <label class="field-label">At Home (leave blank to clear)</label>
    <textarea id="edit-athome" rows="2">${esc(atHome)}</textarea>

    <label class="field-label">Status</label>
    <select id="edit-status">
      <option value="PLANNED" ${status === 'PLANNED' ? 'selected' : ''}>Planned</option>
      <option value="PENDING_SOURCE" ${status === 'PENDING_SOURCE' ? 'selected' : ''}>Pending (source not finalized)</option>
      <option value="OWNER_CONFIRMED_BLANK" ${status === 'OWNER_CONFIRMED_BLANK' ? 'selected' : ''}>Intentionally blank</option>
    </select>

    <div class="impact">
      <div class="impact-title">This change will affect</div>
      <ul>${affected.map(a => `<li>${esc(a)}</li>`).join('')}</ul>
      <div class="muted">Unaffected: other subjects.</div>
    </div>

    <div class="btn-row">
      <button class="btn" id="btn-save" data-subject="${subject}" data-day="${day}" data-source="${esc(cell.raw || '')}">Save Local Change</button>
      <button class="btn neutral" id="btn-restore" data-subject="${subject}" data-day="${day}">Restore Source</button>
      <button class="btn neutral" id="btn-pending" data-subject="${subject}" data-day="${day}">Mark Pending</button>
      <button class="btn neutral" id="btn-blank" data-subject="${subject}" data-day="${day}">Mark Intentionally Blank</button>
    </div>
    <div id="save-status" class="muted"></div>
  `;
}

async function saveDayEdit(subject, day, sourceValue, action) {
  const d = STATE.detail;
  if (!d) return;
  const body = { source_hash: d.source_hash, subject, day, source_value: sourceValue };
  let endpoint;
  if (action === 'save') {
    endpoint = '/overrides';
    body.in_class = ($('edit-inclass').value || '').split('\n').map(s => s.trim()).filter(Boolean);
    const atHome = ($('edit-athome').value || '').trim();
    body.at_home = atHome || null;
    body.clear_at_home = !atHome;
    body.status = $('edit-status').value;
  } else if (action === 'restore') {
    endpoint = '/restore-source';
  } else if (action === 'pending') {
    endpoint = '/mark-pending';
  } else if (action === 'blank') {
    endpoint = '/mark-blank';
  }
  const st = $('save-status');
  try {
    await api(`/api/weeks/${d.quarter}/${d.week}${endpoint}`, { method: 'POST', body });
    st.textContent = 'Saved.';
    // Refresh detail + weekly view.
    STATE.detail = await api(`/api/week/${d.quarter}/${d.week}`);
    render();
  } catch (e) {
    st.textContent = e.status === 409 ? `Could not save: ${e.message}. Refresh and review.` : `Could not save: ${e.message}`;
  }
}

async function answerQuestion(qid, answer) {
  const d = STATE.detail;
  if (!d) return;
  try {
    await api(`/api/weeks/${d.quarter}/${d.week}/questions/${encodeURIComponent(qid)}/answer`, {
      method: 'POST', body: { source_hash: d.source_hash, answer },
    });
    STATE.detail = await api(`/api/week/${d.quarter}/${d.week}`);
    render();
  } catch (e) {
    alert(`Could not answer: ${e.message}`);
  }
}

async function rejectAssignment(subject, title) {
  const d = STATE.detail;
  if (!d) return;
  try {
    await api(`/api/weeks/${d.quarter}/${d.week}/assignments`, {
      method: 'POST', body: { source_hash: d.source_hash, subject, title, action: 'REJECT' },
    });
    STATE.detail = await api(`/api/week/${d.quarter}/${d.week}`);
    render();
  } catch (e) {
    alert(`Could not reject: ${e.message}`);
  }
}

// ============ Router ============

async function render() {
  const hash = location.hash || '#home';
  const parts = hash.slice(1).split('/');
  const page = parts[0] || 'home';
  const main = $('main');
  document.querySelectorAll('.nav a').forEach(a => a.classList.toggle('active', a.dataset.nav === page));
  main.innerHTML = '<div class="loading">Loading…</div>';
  try {
    let html;
    switch (page) {
      case 'home': html = await viewHome(); break;
      case 'weekly': html = await viewWeekly(); break;
      case 'subject': html = await viewSubject(parseInt(parts[1]), parseInt(parts[2]), parts[3]); break;
      case 'assignments': html = await viewAssignments(); break;
      case 'announcements': html = await viewAnnouncements(); break;
      case 'questions': html = await viewQuestions(); break;
      case 'review': html = await viewReview(); break;
      case 'completed': html = await viewCompleted(); break;
      case 'system': html = await viewSystem(); break;
      default: html = await viewHome();
    }
    main.innerHTML = html;
    bindInteractions();
  } catch (e) {
    main.innerHTML = `<h1>Error</h1><p class="muted">${esc(e.message)}</p>`;
  }
}

function bindInteractions() {
  // Day cell click -> open editor in subject view context.
  document.querySelectorAll('.cell[data-subject]').forEach(btn => {
    btn.addEventListener('click', () => {
      const subject = btn.dataset.subject;
      const day = btn.dataset.day;
      const d = STATE.detail;
      const slot = $('editor-slot');
      if (slot) {
        slot.innerHTML = renderEditor(d, subject, day);
        bindEditorButtons(subject, day);
        slot.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  });
  document.querySelectorAll('button[data-edit]').forEach(btn => {
    btn.addEventListener('click', () => {
      const subject = btn.dataset.edit;
      const day = btn.dataset.day;
      const d = STATE.detail;
      const slot = $('editor-slot');
      if (slot) {
        slot.innerHTML = renderEditor(d, subject, day);
        bindEditorButtons(subject, day);
      }
    });
  });
  document.querySelectorAll('button[data-answer]').forEach(btn => {
    btn.addEventListener('click', () => {
      const qid = btn.dataset.answer;
      const input = document.querySelector(`.q-answer[data-qid="${qid}"]`);
      answerQuestion(qid, (input && input.value) || '');
    });
  });
  document.querySelectorAll('button[data-recommended-btn]').forEach(btn => {
    btn.addEventListener('click', () => {
      const qid = btn.dataset.recommendedBtn;
      const input = document.querySelector(`.q-answer[data-qid="${qid}"]`);
      const rec = input ? input.dataset.recommended : '';
      answerQuestion(qid, rec);
    });
  });
  document.querySelectorAll('button[data-reject]').forEach(btn => {
    btn.addEventListener('click', () => {
      rejectAssignment(btn.dataset.subject, btn.dataset.reject);
    });
  });
}

function bindEditorButtons(subject, day) {
  const d = STATE.detail;
  $('btn-save').addEventListener('click', () => saveDayEdit(subject, day, $('btn-save').dataset.source, 'save'));
  $('btn-restore').addEventListener('click', () => saveDayEdit(subject, day, '', 'restore'));
  $('btn-pending').addEventListener('click', () => saveDayEdit(subject, day, $('btn-save').dataset.source, 'pending'));
  $('btn-blank').addEventListener('click', () => saveDayEdit(subject, day, $('btn-save').dataset.source, 'blank'));
}

window.addEventListener('hashchange', render);
$('nav').innerHTML = nav();
render();
