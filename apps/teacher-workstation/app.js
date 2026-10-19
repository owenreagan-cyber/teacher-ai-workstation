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
  { id: 'review', label: 'Review & Approve' },
  { id: 'deploy', label: 'Deploy' },
  { id: 'completed', label: 'Completed Weeks' },
  { id: 'system', label: 'System Status' },
];

const STATE = { detail: null, dirty: false };

// Per-server-start request token, injected into index.html by the server.
// Mutating requests must send it (with JSON content type, same origin).
const REQUEST_TOKEN = document.querySelector('meta[name="teacher-workstation-token"]')?.content || '';

async function api(path, opts) {
  const o = opts || {};
  const method = o.method || 'GET';
  const headers = {};
  if (method !== 'GET') {
    headers['Content-Type'] = 'application/json';
    headers['X-Teacher-Workstation-Token'] = REQUEST_TOKEN;
  }
  const r = await fetch(path, {
    method,
    headers,
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
    'STALE': 'fail', 'NOT_REQUIRED': 'neutral',
    // Friday rollover lifecycle.
    'READY': 'pass', 'HELD_UNTIL_4PM': 'pass', 'EXECUTING': 'pending',
    'NEEDS_OWEN': 'warn', 'PREPARING': 'pending', 'NOT_DUE': 'neutral',
  };
  const label = { 'PENDING': 'PENDING', 'STALE': 'APPROVAL STALE', 'NOT_REQUIRED': 'NOT REQUIRED', 'BLOCKED': 'BLOCKED' };
  return `<span class="pill ${map[state] || 'neutral'}">${esc(label[state] || state)}</span>`;
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
  const rollover = await api('/api/friday-rollover').catch(() => null);
  let needs = [];
  let approval = null;
  if (next) {
    const detail = await api(`/api/week/${next.quarter}/${next.week}`);
    needs = detail.open_questions || [];
    approval = approvalProgress(detail);
    // Also surface pending days for actionable "what needs Owen".
    const pending = [];
    for (const subj of SUBJECTS) {
      for (const wd of WEEKDAYS) {
        const st = (detail.day_states[subj.key] || {})[wd];
        if (st === 'PENDING_SOURCE' || st === 'NEEDS_INPUT') pending.push({ subject: subj.label, day: wd });
      }
    }
    // Approval tasks needing Owen.
    const approvalNeeds = approval ? approval.pendingApprovals.map(a => ({ subject: a.subject, artifact: a.artifact })) : [];
    return renderHome(h, s, completed, next, needs, pending, approval, approvalNeeds, rollover);
  }
  return renderHome(h, s, completed, next, needs, [], approval, [], rollover);
}

function approvalProgress(d) {
  const records = d.approval_records || {};
  const subjects = d.active_subjects || [];
  let approved = 0, required = 0;
  const pendingApprovals = [];
  for (const s of subjects) {
    const hasAssignments = (d.assignments || []).some(a => a.course === s);
    const hasReminder = (d.assessment_reminders || []).some(r => r.course === subjectLabel(s));
    const requiredArtifacts = ['page', 'announcement'];
    if (hasAssignments) requiredArtifacts.push('assignments');
    if (hasReminder) requiredArtifacts.push('assessment_reminder');
    for (const g of requiredArtifacts) {
      required++;
      const rec = (records[s] || {})[g] || {};
      const st = rec.state || 'PENDING';
      if (st === 'APPROVED') approved++;
      else if (st === 'NOT_REQUIRED') { /* satisfied; still count as required, not pending */ }
      else pendingApprovals.push({ subject: s, artifact: g });
    }
  }
  return { approved, required, ready: d.ready_to_publish, pendingApprovals };
}

function renderHome(h, s, completed, next, needs, pending, approval, approvalNeeds, rollover) {
  const approvalLine = approval && next
    ? `<div class="kv"><span class="k">Approval</span><span class="v">${approval.approved} of ${approval.required} required artifacts approved</span></div>
       <div class="kv"><span class="k">Publish readiness</span><span class="v">${approval.ready ? statePill('READY_TO_PUBLISH') : '<span class="pill warn">NOT READY</span>'}</span></div>`
    : '';
  const rolloverLine = rollover
    ? `<div class="section">
        <h2>Friday Rollover</h2>
        <div class="kv"><span class="k">Transition</span><span class="v">${esc(rollover.from_week)} → ${esc(rollover.to_week)}</span></div>
        <div class="kv"><span class="k">Scheduled</span><span class="v">${esc(rollover.scheduled_at || '—')}</span></div>
        <div class="kv"><span class="k">Status</span><span class="v">${statePill(rollover.status)}</span></div>
        ${(rollover.blockers || []).length ? `<ul class="needs-list">${rollover.blockers.map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
      </div>`
    : '';
  const needsList = [
    ...pending.map(p => `<li><a href="#subject/${next.quarter}/${next.week}/${SUBJECTS.find(x=>x.label===p.subject).key}"><span class="q-subject">${esc(p.subject)}</span> — ${esc(p.day)} plan pending</a></li>`),
    ...approvalNeeds.map(a => `<li><a href="#review"><span class="q-subject">${esc(subjectLabel(a.subject))}</span> — ${esc(a.artifact.replace('_', ' '))} needs approval</a></li>`),
    ...needs.map(q => `<li><a href="#questions"><span class="q-subject">${esc(subjectLabel(q.subject))}</span> — ${esc(q.reason)}</a></li>`),
  ];
  const needsHtml = needsList.length
    ? `<ul class="needs-list">${needsList.join('')}</ul>`
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
        <div class="kv"><span class="k">Dates</span><span class="v">${esc(fmtRange(next.date_range))}</span></div>
        ${approvalLine}` : '<div class="empty">No next week prepared.</div>'}
    </div>
    <div class="section"><h2>What needs Owen?</h2>${needsHtml}</div>
    ${rolloverLine}
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
    <div class="section"><h2>Approvals</h2>${renderApprovals(approves)}
      <p class="muted" style="margin-top:8px;">Approve or revoke in <a href="#review">Review &amp; Approve</a>.</p>
    </div>
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
  if (!d) return '<h1>Review &amp; Approve</h1><div class="empty">No prepared week.</div>';
  STATE.detail = d;
  return renderReviewApprove(d);
}

function artifactBlocked(d, subject) {
  // A subject is blocked for approval if it has pending-source days or open questions.
  const states = (d.day_states || {})[subject] || {};
  const pendingDays = WEEKDAYS.filter(w => (states[w] === 'PENDING_SOURCE' || states[w] === 'NEEDS_INPUT'));
  const openQ = (d.open_questions || []).filter(q => q.subject === subject);
  const blockers = [];
  if (pendingDays.length) blockers.push(`${pendingDays.join(', ')} source pending`);
  if (openQ.length) blockers.push(`${openQ.length} open question${openQ.length > 1 ? 's' : ''}`);
  return blockers;
}

function renderReviewApprove(d) {
  const ready = d.ready_to_publish;
  const subjects = d.active_subjects || [];
  const approvals = d.approval_records || {};
  const hashes = d.draft_hashes || {};

  const artifactsFor = (s) => {
    const list = ['page', 'assignments', 'announcement', 'assessment_reminder'];
    // Only show artifacts that actually exist/apply.
    const hasAssignments = (d.assignments || []).some(a => a.course === s);
    const hasReminder = (d.assessment_reminders || []).some(r => r.course === subjectLabel(s));
    return list.filter(g => {
      if (g === 'assignments') return hasAssignments;
      if (g === 'assessment_reminder') return hasReminder;
      return true; // page + announcement always
    });
  };

  const subjectCards = subjects.map(s => {
    const blockers = artifactBlocked(d, s);
    const sHashes = hashes[s] || {};
    const sAppr = approvals[s] || {};
    const artRows = artifactsFor(s).map(g => {
      const rec = sAppr[g] || {};
      const state = rec.state || 'PENDING';
      const blocked = blockers.length > 0 && state !== 'APPROVED' && state !== 'NOT_REQUIRED';
      const hash = sHashes[g] || '';
      const shortHash = hash ? hash.slice(0, 10) : '—';
      const stale = state === 'APPROVED' && rec.draft_hash && rec.draft_hash !== hash;
      const effectiveState = stale ? 'STALE' : (blocked ? 'BLOCKED' : state);
      const label = effectiveState === 'PENDING' ? 'PENDING APPROVAL' : effectiveState;
      const approveBtn = (state === 'APPROVED' || stale)
        ? `<button class="btn neutral small" data-revoke="${s}" data-artifact="${g}">Revoke</button>`
        : (blocked
          ? `<span class="muted" style="font-size:12px;">blocked</span>`
          : `<button class="btn small" data-approve="${s}" data-artifact="${g}" data-hash="${esc(hash)}">Approve</button>`);
      return `<tr>
        <td>${g.replace('_', ' ')}</td>
        <td>${statePill(effectiveState === 'PENDING APPROVAL' ? 'PENDING' : effectiveState)}</td>
        <td class="mono" style="font-size:11px;">${esc(shortHash)}</td>
        <td>${approveBtn}</td>
      </tr>`;
    }).join('');

    const blockerTxt = blockers.length ? `<div class="muted" style="margin-top:6px;">⚠ ${esc(blockers.join('; '))}</div>` : '';
    return `<div class="section">
      <h2>${subjectLabel(s)}</h2>
      ${blockerTxt}
      <table><thead><tr><th>Artifact</th><th>Approval</th><th>Hash</th><th></th></tr></thead><tbody>${artRows}</tbody></table>
    </div>`;
  }).join('');

  // What prevents publishing panel.
  const blockerLines = [];
  if (d.publish_blockers && d.publish_blockers.length) {
    blockerLines.push(...d.publish_blockers.map(b => `<li class="muted">· ${esc(b)}</li>`));
  } else if (ready) {
    blockerLines.push('<li class="muted">Nothing — ready to publish.</li>');
  } else {
    blockerLines.push('<li class="muted">Review subject approvals below.</li>');
  }

  // Live Canvas context (GET-only page lookup, if the packet carried one).
  const liveLookup = d.page_lookup || {};
  const liveSubjects = subjects.filter(s => liveLookup[s] && liveLookup[s].status);
  const liveBlock = liveSubjects.length
    ? `<table><thead><tr><th>Subject</th><th>Live page</th></tr></thead><tbody>
        ${liveSubjects.map(s => {
          const pl = liveLookup[s];
          const st = pl.status === 'FOUND' ? `FOUND (page ${esc(pl.page_id || '')})` : esc(pl.status);
          return `<tr><td>${subjectLabel(s)}</td><td>${st}</td></tr>`;
        }).join('')}</tbody></table>`
    : '<div class="muted">LIVE CANVAS CONTEXT UNAVAILABLE — approval is local only; no Canvas GET was performed.</div>';

  return `
    ${banner()}
    <h1>Review &amp; Approve</h1>
    <p class="page-sub">${esc(d.week_code)} · ${statePill(d.status)}</p>

    <div class="section">
      <h2>What still prevents READY_TO_PUBLISH?</h2>
      ${ready
        ? '<div class="pill pass">READY TO PUBLISH</div><p class="muted" style="margin-top:8px;">All required artifacts are approved. Nothing has been written to Canvas.</p>'
        : `<div class="pill warn">NOT READY</div><ul class="needs-list" style="margin-top:8px;">${blockerLines.join('')}</ul>`}
    </div>

    ${subjectCards}

    <div class="section">
      <h2>Current live Canvas vs proposed</h2>
      ${liveBlock}
    </div>

    <div class="section">
      <h2>Approval history</h2>
      ${renderApprovalHistory(d.approval_history || [])}
    </div>

    <div class="banner readonly">Approval is a <strong>local</strong> workflow. Nothing here writes to Canvas. Deployment is a separate Phase 4.</div>
  `;
}

function renderApprovalHistory(events) {
  if (!events || !events.length) return '<div class="empty">No approval events yet.</div>';
  const label = { set_approved: 'Approved', revoke: 'Revoked', invalidated: 'Invalidated', set_pending: 'Reset to pending', set_blocked: 'Blocked', set_not_required: 'Not required' };
  return `<table><thead><tr><th>Time</th><th>Subject</th><th>Artifact</th><th>Action</th><th>Reason</th></tr></thead><tbody>
    ${events.slice(0, 40).map(e => `<tr>
      <td class="mono" style="font-size:11px;">${esc((e.at || '').slice(0, 19).replace('T', ' '))}</td>
      <td>${subjectLabel(e.subject)}</td>
      <td>${esc((e.granularity || '').replace('_', ' '))}</td>
      <td>${esc(label[e.action] || e.action)}</td>
      <td class="muted">${esc(e.reason || '')}</td>
    </tr>`).join('')}</tbody></table>`;
}

async function viewDeploy() {
  const d = await currentWeek();
  if (!d) return '<h1>Deploy</h1><div class="empty">No prepared week.</div>';
  STATE.detail = d;
  return renderDeploy(d, null);
}

function renderDeploy(d, preflight) {
  const ready = d.ready_to_publish;
  const pf = preflight;
  const counts = (pf && pf.plan && pf.plan.counts) || null;
  const plan = (pf && pf.plan) || null;

  const gateLine = ready
    ? '<div class="pill pass">READY TO PUBLISH</div>'
    : `<div class="pill warn">NOT READY</div><ul class="needs-list" style="margin-top:8px;">${(d.publish_blockers || []).map(b => `<li class="muted">· ${esc(b)}</li>`).join('')}</ul>`;

  const preflightState = pf
    ? (pf.ready ? '<div class="pill pass">PREFLIGHT PASSED</div>'
        : '<div class="pill fail">PREFLIGHT BLOCKED</div>')
    : '<div class="pill neutral">PREFLIGHT NOT RUN</div>';

  const blockersHtml = pf && pf.blockers && pf.blockers.length
    ? `<ul class="needs-list">${pf.blockers.map(b => `<li class="muted">· ${esc(b)}</li>`).join('')}</ul>`
    : '';

  const planHtml = plan ? `
    <table><thead><tr><th>Action</th><th>Target</th><th>Course</th></tr></thead><tbody>
      ${(plan.pages || []).map(p => `<tr><td>UPDATE</td><td>${esc(subjectLabel(p.subject))} page</td><td>${esc(p.course_id)}</td></tr>`).join('')}
      ${(plan.assignments || []).map(a => `<tr><td>CREATE</td><td>${esc(a.title)}</td><td>${esc(a.course_id)}</td></tr>`).join('')}
      ${(plan.weekly_announcements || []).map(a => `<tr><td>CREATE</td><td>${esc(a.title)} (scheduled)</td><td>${esc(a.course_id)}</td></tr>`).join('')}
      ${(plan.assessment_reminders || []).map(a => `<tr><td>CREATE</td><td>${esc(a.title)}</td><td>${esc(a.course_id)}</td></tr>`).join('')}
    </tbody></table>
    <div class="kv"><span class="k">Pages update</span><span class="v">${counts.pages_update}</span></div>
    <div class="kv"><span class="k">Assignments create</span><span class="v">${counts.assignments_create}</span></div>
    <div class="kv"><span class="k">Announcements create</span><span class="v">${counts.announcements_create}</span></div>
    <div class="kv"><span class="k">Deletions</span><span class="v">${counts.deletes}</span></div>`
    : '<div class="empty">Run preflight to generate the exact write plan.</div>';

  // Deploy control: disabled unless a ready preflight exists + production + confirmation.
  const canDeploy = pf && pf.ready;
  return `
    ${banner()}
    <h1>Deploy to Canvas</h1>
    <p class="page-sub">${esc(d.week_code)} · ${statePill(d.status)}</p>

    <div class="section">
      <h2>Week status</h2>
      <div class="kv"><span class="k">Lifecycle</span><span class="v">${statePill(d.status)}</span></div>
      <div class="kv"><span class="k">Source hash</span><span class="v mono" style="font-size:11px;">${esc((d.source_hash || '').slice(0, 12))}</span></div>
      <div class="kv"><span class="k">Publish readiness</span><span class="v">${gateLine}</span></div>
    </div>

    <div class="section">
      <h2>Live preflight</h2>
      <div class="kv"><span class="k">State</span><span class="v">${preflightState}</span></div>
      ${blockersHtml}
      <div class="btn-row" style="margin-top:8px;">
        <button class="btn" id="btn-preflight" data-q="${d.quarter}" data-w="${d.week}">Run Preflight (dry-run)</button>
      </div>
    </div>

    <div class="section">
      <h2>Write plan</h2>
      ${planHtml}
    </div>

    <div class="section">
      <h2>Deploy</h2>
      <div class="banner readonly">Production deployment is a guarded, explicit-consent action. It writes to live Canvas.</div>
      <label class="field-label"><input type="checkbox" id="deploy-production"> Production mode (real Canvas writes)</label>
      <label class="field-label">Confirmation (type <code>DEPLOY ${esc(d.week_code)}</code>)</label>
      <input type="text" id="deploy-confirm" placeholder="DEPLOY ${esc(d.week_code)}" style="width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;">
      <div class="btn-row" style="margin-top:8px;">
        <button class="btn" id="btn-deploy" data-q="${d.quarter}" data-w="${d.week}"
          ${canDeploy ? '' : 'disabled'} style="${canDeploy ? '' : 'opacity:.4;cursor:not-allowed;'}">Confirm Deployment</button>
      </div>
      <div id="deploy-status" class="muted" style="margin-top:8px;"></div>
    </div>
  `;
}

async function runPreflight(q, w) {
  try {
    const pf = await api(`/api/weeks/${q}/${w}/preflight`, { method: 'POST', body: { production: false } });
    STATE.prefight = pf;
    const d = STATE.detail;
    const main = $('main');
    main.innerHTML = renderDeploy(d, pf);
    bindInteractions();
  } catch (e) {
    alert(`Preflight failed: ${e.message}`);
  }
}

async function runDeploy(q, w, production, confirmation) {
  const pf = STATE.prefight;
  if (!pf) { alert('Run preflight first.'); return; }
  if (!production) { alert('Production mode must be enabled to deploy.'); return; }
  const d = STATE.detail;
  if ((confirmation || '').trim().toUpperCase() !== `DEPLOY ${d.week_code}`.toUpperCase()) {
    alert(`Confirmation must be exactly "DEPLOY ${d.week_code}".`);
    return;
  }
  if (!confirm('This will WRITE to live Canvas. Confirm? There is no automatic rollback.')) return;
  try {
    const rep = await api(`/api/weeks/${q}/${w}/deploy`, {
      method: 'POST',
      body: {
        preflight_id: pf.preflight_id,
        expected_source_hash: pf.source_hash,
        expected_approval_snapshot_hash: pf.approval_snapshot_hash,
        owner_confirmation: confirmation,
        production: true,
      },
    });
    const status = $('deploy-status');
    if (status) status.innerHTML = rep.deployment_state === 'PUBLISHED_VERIFIED'
      ? '<span class="pill pass">PUBLISHED &amp; VERIFIED</span>'
      : '<span class="pill fail">PARTIAL DEPLOYMENT — ATTENTION REQUIRED</span>';
  } catch (e) {
    alert(`Deployment blocked: ${e.message}`);
  }
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
      case 'deploy': html = await viewDeploy(); break;
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
  document.querySelectorAll('button[data-approve]').forEach(btn => {
    btn.addEventListener('click', () => {
      approveArtifact(btn.dataset.approve, btn.dataset.artifact, btn.dataset.hash);
    });
  });
  document.querySelectorAll('button[data-revoke]').forEach(btn => {
    btn.addEventListener('click', () => {
      revokeArtifact(btn.dataset.revoke, btn.dataset.artifact);
    });
  });
  const btnPreflight = $('btn-preflight');
  if (btnPreflight) {
    btnPreflight.addEventListener('click', () => runPreflight(btnPreflight.dataset.q, btnPreflight.dataset.w));
  }
  const btnDeploy = $('btn-deploy');
  if (btnDeploy) {
    btnDeploy.addEventListener('click', () => {
      const production = $('deploy-production') ? $('deploy-production').checked : false;
      const confirmation = $('deploy-confirm') ? $('deploy-confirm').value : '';
      runDeploy(btnDeploy.dataset.q, btnDeploy.dataset.w, production, confirmation);
    });
  }
}

async function approveArtifact(subject, artifactType, expectedHash) {
  const d = STATE.detail;
  if (!d) return;
  const label = `${subjectLabel(subject)} ${artifactType.replace('_', ' ')}`;
  if (!confirm(`You are approving this exact staged artifact: ${label}.\n\nIf it changes later, this approval will automatically become stale.\n\nConfirm approval?`)) return;
  try {
    await api(`/api/weeks/${d.quarter}/${d.week}/approve`, {
      method: 'POST',
      body: { source_hash: d.source_hash, subject, artifact_type: artifactType, expected_artifact_hash: expectedHash },
    });
    STATE.detail = await api(`/api/week/${d.quarter}/${d.week}`);
    render();
  } catch (e) {
    alert(`Could not approve: ${e.message}`);
  }
}

async function revokeArtifact(subject, artifactType) {
  const d = STATE.detail;
  if (!d) return;
  if (!confirm(`Revoke approval for ${subjectLabel(subject)} ${artifactType.replace('_', ' ')}?`)) return;
  try {
    await api(`/api/weeks/${d.quarter}/${d.week}/revoke-approval`, {
      method: 'POST',
      body: { source_hash: d.source_hash, subject, artifact_type: artifactType },
    });
    STATE.detail = await api(`/api/week/${d.quarter}/${d.week}`);
    render();
  } catch (e) {
    alert(`Could not revoke: ${e.message}`);
  }
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
