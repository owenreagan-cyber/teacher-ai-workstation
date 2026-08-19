const $ = (id) => document.getElementById(id);

const esc = (value) =>
  String(value ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

const STATUS_LABELS = {
  create: 'Create',
  exists: 'Already exists',
  'no-assignment': 'No assignment',
  manual: 'Manual',
  'needs-owen': 'Needs Owen',
};

const PREFIXES = ['SM5:', 'RM4:', 'ELA4:', 'HIST4:', 'SCI4:', 'ELA4A:', 'ELA4B:'];

function shortTitle(value) {
  let s = String(value || '').trim();
  for (const prefix of PREFIXES) {
    if (s.startsWith(prefix)) { s = s.slice(prefix.length).trim(); break; }
  }
  return s || '—';
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  let data = {};
  try { data = await response.json(); } catch (e) { /* non-JSON */ }
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status} ${response.statusText}`);
  }
  return data;
}

const state = { week: 'Q1W5', workspace: null, pacingDetail: false };

/* ---------- Chat ---------- */

function addMessage(role, text, meta) {
  const log = $('chat-log');
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  el.innerHTML = esc(text) + (meta ? `<span class="meta">${esc(meta)}</span>` : '');
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

function pushAssistant(text, meta) { addMessage('assistant', text, meta); }

function focusReview() {
  $('review-btn').scrollIntoView({ behavior: 'smooth', block: 'center' });
  if ($('review-details').hidden) toggleReview(true);
}

async function handleChat(message) {
  addMessage('user', message);
  const result = await api('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, week: state.week, dryRun: true }),
  });
  pushAssistant(result.reply);

  if (result.week && result.week !== state.week) {
    state.week = result.week;
    await loadWorkspace();
  }
  if (result.launch) renderLaunch(result.launch);
  if (result.action === 'focus-assignments') {
    $('assignments-list').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  if (result.action === 'focus-review' || result.action === 'refresh') focusReview();
  if (result.action === 'focus-week') {
    $('week-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/* ---------- Week panel ---------- */

function renderWeekPanel(week) {
  $('week-code').textContent = week.weekCode;
  $('week-dates').textContent = `${week.dateRange} · Quarter ${week.quarter}`;

  const grid = $('pacing-grid');
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const dayShort = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

  const head = document.createElement('div');
  head.className = 'pacing-head';
  head.innerHTML = '<span></span>' + dayShort.map((d) => `<span>${d}</span>`).join('');

  grid.innerHTML = '';
  grid.appendChild(head);

  for (const subject of week.subjects) {
    const row = document.createElement('div');
    row.className = 'pacing-row';
    const prefix = subject.prefix ? `<small>${esc(subject.prefix)} · ${esc(subject.courseId ?? '')}</small>` : `<small>${esc(subject.courseId ?? '')}</small>`;
    let cells = `<div class="subj-label">${esc(subject.label)}${prefix}</div>`;
    for (const day of days) {
      const entries = (week.pacing[subject.id] || {})[day] || [];
      if (!entries.length) {
        cells += '<div class="cell empty"></div>';
        continue;
      }
      const inner = entries
        .map((e) => `<span class="day-text" title="${esc(e.title)}">${esc(shortTitle(e.title))}</span>`)
        .join('');
      cells += `<div class="cell${subject.active ? '' : ' inactive'}">${inner}</div>`;
    }
    row.innerHTML = cells;
    grid.appendChild(row);
  }

  if (state.pacingDetail) renderPacingDetail(week);
}

function renderPacingDetail(week) {
  const box = $('pacing-detail');
  box.innerHTML = '';
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  for (const subject of week.subjects) {
    const rows = [];
    for (const day of days) {
      const entries = (week.pacing[subject.id] || {})[day] || [];
      for (const e of entries) {
        const parts = [];
        if (e.inClass) parts.push(`In class: ${e.inClass}`);
        if (e.atHome) parts.push(`Homework: ${e.atHome}`);
        rows.push(
          `<div class="detail-row"><strong>${esc(day)}</strong> — ${esc(shortTitle(e.title))}` +
          (parts.length ? `<p>${esc(parts.join(' · '))}</p>` : '') +
          '</div>'
        );
      }
    }
    box.innerHTML += `<h4>${esc(subject.label)}${subject.active ? '' : ' (inactive quarter)'}</h4>${rows.join('') || '<p>No entries this week.</p>'}`;
  }
  box.hidden = false;
}

/* ---------- Suggested assignments ---------- */

function renderAssignments(items) {
  const list = $('assignments-list');
  $('assignments-count').textContent = `${items.length} items`;
  list.innerHTML = items
    .map((item) => {
      const question = item.question && item.status === 'needs-owen'
        ? `<div class="decision-row"><button data-decision="${esc(item.id)}" data-answer="yes">Yes</button><button data-decision="${esc(item.id)}" data-answer="no">No</button></div>`
        : '';
      return (
        `<li><span class="pill ${esc(item.status)}">${esc(STATUS_LABELS[item.status] || item.status)}</span>` +
        `<span class="title"><span class="day">${esc(item.day)}</span>${esc(item.title)}</span>` +
        `${question ? `<span class="decision-row-inline">${question}</span>` : ''}</li>`
      );
    })
    .join('');
}

function renderWeekStatus(status) {
  $('status-pacing').textContent = status.pacing;
  $('status-decisions').textContent = `${status.decisionsNeeded} decision${status.decisionsNeeded === 1 ? '' : 's'} needed`;
  $('status-assessments').textContent = `${status.assessments} assessment${status.assessments === 1 ? '' : 's'}`;
  $('status-state').textContent = status.state;
}

/* ---------- Review ---------- */

function toggleReview(force) {
  const box = $('review-details');
  box.hidden = force !== undefined ? !force : !box.hidden;
}

function renderReview(review) {
  const summary = $('review-summary');
  if (!review.available) {
    summary.innerHTML = '<span class="muted">No launch manifest yet.</span>';
    return;
  }
  summary.innerHTML =
    `<span class="chunk create">Create ${review.create}</span>` +
    `<span class="chunk update">Update ${review.update}</span>` +
    `<span class="chunk remove">Remove ${review.remove}</span>` +
    `<span class="chunk leave">Leave ${review.leave}</span>` +
    (review.reminders ? `<span class="chunk reminders">${review.reminders} reminders</span>` : '');

  const box = $('review-details');
  box.innerHTML = review.details
    .map(
      (d) =>
        `<div class="detail-row"><span class="act ${esc(d.action.toLowerCase())}">${esc(d.action)}</span>` +
        `<span class="what">${esc(d.course)} · ${esc(d.type)} — ${esc(d.title)}</span></div>`
    )
    .join('');
}

/* ---------- Launch ---------- */

function renderLaunch(launch) {
  const box = $('launch-state');
  const stateName = launch.state || 'Ready';
  box.innerHTML = `<span class="pill ${esc(stateName)}">${esc(stateName)}</span>`;
  $('launch-reason').textContent = launch.reason || '';
}

async function handleLaunch() {
  const button = $('launch-btn');
  button.disabled = true;
  $('launch-state').innerHTML = '<span class="pill Launching"><span class="spin"></span>Launching</span>';
  $('launch-reason').textContent = '';
  try {
    const result = await api('/api/launch', {
      method: 'POST',
      body: JSON.stringify({ week: state.week, dryRun: true }),
    });
    renderLaunch(result);
  } catch (error) {
    renderLaunch({ state: 'Blocked', reason: `Canvas could not be reached. Nothing was changed. (${error.message})` });
  } finally {
    button.disabled = false;
  }
}

/* ---------- Load ---------- */

async function loadWorkspace() {
  const workspace = await api(`/api/workspace?week=${encodeURIComponent(state.week)}`);
  state.workspace = workspace;
  $('week-select').value = state.week;
  renderWeekPanel(workspace.week);
  renderAssignments(workspace.suggestedAssignments);
  renderWeekStatus(workspace.weekStatus);
  renderReview(workspace.review);
  renderLaunch(workspace.launch);
}

async function loadWeeks() {
  const data = await api('/api/weeks');
  const select = $('week-select');
  select.innerHTML = data.weeks.map((w) => `<option value="${esc(w.code)}">${esc(w.label)}</option>`).join('');
  select.value = state.week;
}

/* ---------- Wiring ---------- */

$('chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = $('chat-text');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  try {
    await handleChat(text);
  } catch (error) {
    pushAssistant(`Something went wrong: ${error.message}`);
  }
});

$('chat-chips').addEventListener('click', (event) => {
  const chip = event.target.closest('.chip');
  if (!chip) return;
  handleChat(chip.dataset.msg).catch((error) => pushAssistant(`Something went wrong: ${error.message}`));
});

$('week-select').addEventListener('change', async (event) => {
  state.week = event.target.value;
  await loadWorkspace();
});

$('review-btn').addEventListener('click', () => toggleReview());

$('launch-btn').addEventListener('click', handleLaunch);

$('pacing-guide-btn').addEventListener('click', () => {
  state.pacingDetail = !state.pacingDetail;
  const box = $('pacing-detail');
  if (!state.pacingDetail) {
    box.hidden = true;
  } else if (state.workspace) {
    renderPacingDetail(state.workspace.week);
  }
  $('pacing-guide-btn').textContent = state.pacingDetail ? 'Hide pacing guide' : 'Open live pacing guide';
});

document.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-decision]');
  if (!button) return;
  const id = button.dataset.decision;
  const answer = button.dataset.answer;
  api('/api/decision', {
    method: 'POST',
    body: JSON.stringify({ week: state.week, id, answer }),
  })
    .then((result) => {
      renderAssignments(result.suggestedAssignments);
      renderWeekStatus(result.weekStatus);
    })
    .catch((error) => pushAssistant(`Something went wrong: ${error.message}`));
});

/* ---------- Boot ---------- */

(async function boot() {
  pushAssistant(
    'Hi Owen. I can help with your week: type “Update Q1W6”, “Refresh pacing”, “Show assignments”, “Looks good”, or “Launch”.'
  );
  try {
    await loadWeeks();
    await loadWorkspace();
  } catch (error) {
    $('chat-log').innerHTML = '';
    addMessage('assistant', `Could not load the workspace: ${error.message}`);
  }
})();
