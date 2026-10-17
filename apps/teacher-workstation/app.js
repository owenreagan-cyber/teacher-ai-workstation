// Teacher Workstation — read-only frontend (vanilla JS, no framework).
// Displays local staged intake/deployment data. No write controls, no secrets.

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

let CACHE = { home: null, week: null, completed: null, status: null };
let selectedWeek = { quarter: null, week: null, code: null };

async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function statePill(state) {
  const map = {
    'PUBLISHED_VERIFIED': 'pass',
    'READY_TO_PUBLISH': 'pass',
    'READY_FOR_REVIEW': 'warn',
    'NEEDS_INPUT': 'warn',
    'DRAFTED': 'pending',
    'NORMALIZED': 'pending',
    'SOURCE_FETCHED': 'pending',
    'APPROVED': 'pass',
    'PENDING': 'pending',
    'NEEDS_CHANGES': 'warn',
    'BLOCKED': 'fail',
  };
  return `<span class="pill ${map[state] || 'neutral'}">${esc(state)}</span>`;
}

function dayStatePill(state) {
  const map = {
    'PLANNED': 'neutral',
    'PENDING_SOURCE': 'pending',
    'OWNER_CONFIRMED_BLANK': 'neutral',
    'NOT_APPLICABLE': 'pending',
    'NEEDS_INPUT': 'warn',
    'READY': 'pass',
    'ASSESSMENT': 'warn',
    'REVIEW': 'neutral',
    'BLOCKED': 'fail',
  };
  const label = { 'PENDING_SOURCE': 'PENDING', 'OWNER_CONFIRMED_BLANK': 'BLANK', 'NOT_APPLICABLE': 'N/A' };
  return `<span class="pill ${map[state] || 'neutral'}">${esc(label[state] || state)}</span>`;
}

function nav() {
  return NAV.map(n => `<a href="#${n.id}" data-nav="${n.id}">${n.label}</a>`).join('');
}

function banner() {
  return `<div class="banner readonly"><strong>Read-only mode.</strong> Canvas writes are disabled. This is a planning view only.</div>`;
}

// ============ Views ============

async function viewHome() {
  const h = await api('/api/home');
  const s = await api('/api/status');
  const today = h.today;
  const cur = h.current_week || '—';
  const completed = h.latest_completed;
  const next = h.next_prepared;

  let needs = [];
  if (next) {
    const detail = await api(`/api/week/${next.quarter}/${next.week}`);
    needs = detail.open_questions || [];
  }

  const needsHtml = needs.length
    ? `<ul class="needs-list">${needs.map(q => `<li><span class="q-subject">${esc(subjectLabel(q.subject))}</span> — ${esc(q.reason)}</li>`).join('')}</ul>`
    : '<div class="empty">Nothing pending.</div>';

  return `
    ${banner()}
    <h1>Teacher Workstation</h1>
    <p class="page-sub">${esc(today)} · Current week: ${esc(cur)}</p>

    <div class="panel-grid">
      <div class="section">
        <h2>Today</h2>
        <div class="kv"><span class="k">Date</span><span class="v">${esc(today)}</span></div>
        <div class="kv"><span class="k">Current week</span><span class="v">${esc(cur)}</span></div>
      </div>

      <div class="section">
        <h2>Latest completed</h2>
        ${completed
          ? `<div class="kv"><span class="k">Week</span><span class="v">${esc(completed.week_code)}</span></div>
             <div class="kv"><span class="k">Status</span><span class="v">${statePill(completed.status)}</span></div>
             <div class="kv"><span class="k">Dates</span><span class="v">${esc(fmtRange(completed.date_range))}</span></div>`
          : '<div class="empty">None yet.</div>'}
      </div>
    </div>

    <div class="section">
      <h2>Next prepared</h2>
      ${next
        ? `<div class="kv"><span class="k">Week</span><span class="v">${esc(next.week_code)}</span></div>
           <div class="kv"><span class="k">Status</span><span class="v">${statePill(next.status)}</span></div>
           <div class="kv"><span class="k">Dates</span><span class="v">${esc(fmtRange(next.date_range))}</span></div>`
        : '<div class="empty">No next week prepared. Run <span class="mono">bin/canvas-intake prepare-next</span>.</div>'}
    </div>

    <div class="section">
      <h2>What needs Owen?</h2>
      ${needsHtml}
    </div>

    <div class="section">
      <h2>System status</h2>
      <pre class="mono" style="white-space: pre-wrap; font-size: 12.5px;">${esc(s.text)}</pre>
    </div>
  `;
}

async function viewWeekly() {
  const h = await api('/api/home');
  const weeks = h.weeks || [];
  const prepared = weeks.filter(w => w.status !== 'PUBLISHED_VERIFIED');
  const target = prepared[0];
  if (!target) {
    return `<h1>Weekly Planning</h1><div class="empty">No prepared week. Run <span class="mono">prepare-next</span>.</div>`;
  }
  selectedWeek = { quarter: target.quarter, week: target.week, code: target.week_code };
  const d = await api(`/api/week/${target.quarter}/${target.week}`);
  return renderWeekDetail(d, true);
}

function renderWeekDetail(d, withHeader) {
  const states = d.day_states || {};
  let head = '';
  if (withHeader) {
    head = `
      <h1>${esc(d.week_code)} — Weekly Planning</h1>
      <p class="page-sub">${esc(fmtRange(d.date_range))} · ${statePill(d.status)}</p>
      <div class="banner readonly"><strong>Read-only.</strong> No Canvas writes.</div>`;
  }
  const rows = SUBJECTS.map(s => {
    const cells = WEEKDAYS.map(wd => `<td>${dayStatePill((states[s.key] || {})[wd] || 'PENDING_SOURCE')}</td>`).join('');
    return `<tr><td><a href="#subject/${d.quarter}/${d.week}/${s.key}">${s.label}</a></td>${cells}</tr>`;
  }).join('');

  return `
    ${head}
    <div class="section">
      <h2>Subject grid</h2>
      <table class="grid-table">
        <thead><tr><th>Subject</th>${WEEKDAYS.map(w => `<th>${w.slice(0,3)}</th>`).join('')}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p class="muted" style="margin-top:10px;">Click a subject for detail. Tap a day cell is coming in Phase 2.</p>
    </div>

    <div class="section">
      <h2>Open questions (${(d.open_questions || []).length})</h2>
      ${renderQuestions(d.open_questions || [])}
    </div>
  `;
}

function subjectLabel(key) {
  const s = SUBJECTS.find(x => x.key === key);
  return s ? s.label : key;
}

async function viewSubject(quarter, week, subject) {
  const d = await api(`/api/week/${quarter}/${week}`);
  selectedWeek = { quarter, week, code: d.week_code };
  const norm = (d.week_norm || {}).subjects || {};
  const states = d.day_states || {};
  const subjNorm = norm[subject] || {};

  const dayRows = WEEKDAYS.map(wd => {
    const cell = subjNorm[wd] || { raw: '', blank: true };
    const st = (states[subject] || {})[wd] || 'PENDING_SOURCE';
    return `<tr>
      <td>${wd}</td>
      <td class="mono">${esc(cell.raw || '') || '<span class="muted">blank</span>'}</td>
      <td>${dayStatePill(st)}</td>
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
      <table>
        <thead><tr><th>Day</th><th>Source</th><th>State</th></tr></thead>
        <tbody>${dayRows}</tbody>
      </table>
    </div>

    <div class="section">
      <h2>Assignments (${assigns.length})</h2>
      ${assigns.length ? `<table>
        <thead><tr><th>Title</th><th>Group</th><th>Due</th><th>Duplicate</th></tr></thead>
        <tbody>${assigns.map(a => `<tr><td>${esc(a.title)}</td><td>${esc(a.assignment_group)}</td><td>${esc(a.due_date)}</td><td>${esc(a.duplicate_classification || '—')}</td></tr>`).join('')}</tbody>
      </table>` : '<div class="empty">No assignment proposals.</div>'}
    </div>

    <div class="section">
      <h2>Assessment reminders (${rems.length})</h2>
      ${rems.length ? rems.map(r => `<div class="card">
        <div class="card-title">${esc(r.title)}</div>
        <div class="card-meta">${esc(r.assessment_date || '')}${r.power_up ? ` · Power Up ${esc(r.power_up)}` : ''}</div>
      </div>`).join('') : '<div class="empty">None.</div>'}
    </div>

    <div class="section">
      <h2>Approvals</h2>
      ${renderApprovals(approves)}
    </div>
  `;
}

async function viewAssignments() {
  const d = await ensureWeek();
  if (!d) return '<h1>Assignments</h1><div class="empty">No prepared week.</div>';
  const rows = (d.assignments || []).map(a => `<tr>
    <td>${subjectLabel(a.course)}</td>
    <td>${esc(a.title)}</td>
    <td>${esc(a.assignment_group)}</td>
    <td>${esc(a.due_date)}</td>
    <td>${esc(a.duplicate_classification || 'NEW_PROPOSAL')}</td>
    <td>${statePill('PENDING')}</td>
  </tr>`).join('');
  return `
    ${banner()}
    <h1>Assignments</h1>
    <p class="page-sub">${esc(d.week_code)} — proposed only, not created.</p>
    <div class="section"><table>
      <thead><tr><th>Subject</th><th>Title</th><th>Group</th><th>Due</th><th>Duplicate</th><th>Approval</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="6" class="muted">None.</td></tr>'}</tbody>
    </table></div>
  `;
}

async function viewAnnouncements() {
  const d = await ensureWeek();
  if (!d) return '<h1>Announcements</h1><div class="empty">No prepared week.</div>';
  const weekly = d.weekly_announcements || [];
  const rems = d.assessment_reminders || [];
  return `
    ${banner()}
    <h1>Announcements</h1>
    <p class="page-sub">${esc(d.week_code)} — drafts only, not posted.</p>
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
  const d = await ensureWeek();
  if (!d) return '<h1>Questions</h1><div class="empty">No prepared week.</div>';
  const open = d.open_questions || [];
  const answered = (d.questions || []).filter(q => q.status === 'ANSWERED');
  return `
    ${banner()}
    <h1>Questions</h1>
    <p class="page-sub">${esc(d.week_code)}</p>
    <div class="section">
      <h2>Open (${open.length})</h2>
      ${renderQuestions(open)}
    </div>
    <div class="section">
      <h2>Answered (${answered.length})</h2>
      ${answered.length ? answered.map(q => `<div class="card"><div class="card-title">${subjectLabel(q.subject)}</div><div class="card-meta">${esc(q.answer || '')}</div></div>`).join('') : '<div class="empty">None.</div>'}
    </div>
  `;
}

function renderQuestions(qs) {
  if (!qs || !qs.length) return '<div class="empty">None.</div>';
  return qs.map(q => `<div class="card">
    <div class="card-title">${subjectLabel(q.subject)}${q.date ? ` · ${esc(q.date)}` : ''}</div>
    <div>${esc(q.reason)}</div>
    <div class="card-meta" style="margin-top:6px;">Recommended: ${esc(q.recommended_default || '—')}</div>
    ${q.risk_if_guessed ? `<div class="card-meta">Risk if guessed: ${esc(q.risk_if_guessed)}</div>` : ''}
  </div>`).join('');
}

async function viewReview() {
  const d = await ensureWeek();
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
      <div class="kv"><span class="k">State</span><span class="v">${ready ? statePill('READY_TO_PUBLISH') : `<span class="pill warn">NOT READY</span>`}</span></div>
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
  if (!latest) return `<h1>Completed Weeks</h1><div class="empty">None.</div>`;
  const ledger = latest.ledger || {};
  return `
    ${banner()}
    <h1>Completed Weeks</h1>
    <p class="page-sub">Latest completed deployment.</p>
    <div class="section">
      <h2>${esc(latest.week_code)} — ${statePill('PUBLISHED_VERIFIED')}</h2>
      <div class="kv"><span class="k">Dates</span><span class="v">${esc(fmtRange(latest.date_range))}</span></div>
      <div class="kv"><span class="k">Verified at</span><span class="v">${esc((ledger.verified_at || '').slice(0, 19))}</span></div>
      <div class="kv"><span class="k">Pages</span><span class="v">${(ledger.pages || []).length}</span></div>
      <div class="kv"><span class="k">Assignments</span><span class="v">${ledger.assignment_count || 0}</span></div>
      <div class="kv"><span class="k">Assessment reminders</span><span class="v">${(ledger.assessment_reminders || []).length}</span></div>
      <div class="kv"><span class="k">Email / Inbox sends</span><span class="v">${(ledger.communication || {}).email_sends ?? 0} / ${(ledger.communication || {}).canvas_inbox_sends ?? 0}</span></div>
    </div>
    <div class="section">
      <h2>Weekly announcements</h2>
      ${(ledger.weekly_announcements || []).map(a => `<div class="card"><div class="card-title">${subjectLabel(a.subject)}</div><div class="card-meta">id ${esc(a.announcement_id)}${a.note ? ` · ${esc(a.note)}` : ''}</div></div>`).join('') || '<div class="empty">None.</div>'}
    </div>
  `;
}

async function viewSystem() {
  const s = await api('/api/status');
  return `
    ${banner()}
    <h1>System Status</h1>
    <p class="page-sub">Chief of Staff · Canvas Weekly Intake health.</p>
    <div class="section">
      <pre class="mono" style="white-space: pre-wrap; font-size: 13px;">${esc(s.text)}</pre>
    </div>
  `;
}

function renderApprovals(approves) {
  if (!approves || !Object.keys(approves).length) return '<div class="empty">None.</div>';
  const order = ['page', 'assignments', 'announcement', 'assessment_reminder'];
  return `<table><thead><tr><th>Artifact</th><th>State</th></tr></thead><tbody>
    ${order.map(g => `<tr><td>${g.replace('_', ' ')}</td><td>${statePill((approves[g] || 'PENDING'))}</td></tr>`).join('')}
  </tbody></table>`;
}

async function ensureWeek() {
  const h = await api('/api/home');
  const weeks = h.weeks || [];
  const prepared = weeks.filter(w => w.status !== 'PUBLISHED_VERIFIED');
  if (!prepared.length) return null;
  const t = prepared[0];
  selectedWeek = { quarter: t.quarter, week: t.week, code: t.week_code };
  return api(`/api/week/${t.quarter}/${t.week}`);
}

function fmtRange(range) {
  if (!range) return '—';
  return `${range.start || ''} → ${range.end || ''}`;
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
  } catch (e) {
    main.innerHTML = `<h1>Error</h1><p class="muted">${esc(e.message)}</p>`;
  }
}

window.addEventListener('hashchange', render);
$('nav').innerHTML = nav();
render();
