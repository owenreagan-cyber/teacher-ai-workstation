const state = {
  pending: new Map(),
  timers: new Map(),
  records: new Map(),
  conflicts: new Map(),
  boot: null,
  week: null,
  selectedWeekCode: null,
  subjectId: 'math',
  previewTab: 'text',
  startupNote: '',
};

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const SELECTED_WEEK_STORAGE_KEY = 'phase22.selectedWeekCode';

function canonicalWeekCode(code) {
  return String(code ?? '').trim().toUpperCase().replace(/[\s_-]+/g, '').replace(/^Q([1-4])W0*(\d{1,2})$/, (_, q, w) => `Q${q}W${Number(w)}`);
}

function weekCodeToStartsOn(code) {
  const normalized = canonicalWeekCode(code);
  return (state.boot?.instructionalWeeks || []).find((week) => canonicalWeekCode(week.code) === normalized)?.startsOn || null;
}

function getSavedSelectedWeekCode() {
  try {
    return canonicalWeekCode(localStorage.getItem(SELECTED_WEEK_STORAGE_KEY));
  } catch {
    return '';
  }
}

function persistSelectedWeekCode(code) {
  state.selectedWeekCode = canonicalWeekCode(code);
  try {
    localStorage.setItem(SELECTED_WEEK_STORAGE_KEY, state.selectedWeekCode);
  } catch {
    // ignore storage failures; the live session still has the selected week
  }
}

async function api(path, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timeout = timeoutMs ? setTimeout(() => controller.abort('timeout'), timeoutMs) : null;
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  try {
    const response = await fetch(path, { ...options, headers, signal: controller.signal });
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.error || response.statusText);
      error.status = response.status;
      error.data = data;
      throw error;
    }
    return data;
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

function recordKey(table, id, field) {
  return `${table}:${id}:${field}`;
}

function setFieldSaveState(key, value) {
  const el = document.querySelector(`[data-save-key="${key}"]`);
  if (el) {
    el.textContent = value;
    el.className = `field-save ${value.toLowerCase()}`;
  }
  $('save-state').textContent = value;
  $('save-state').className = value.toLowerCase();
}

function storeRecord(table, payload) {
  const rec = payload.record || payload;
  state.records.set(`${table}:${rec.id}`, rec);
  return rec;
}

function autosave(key, table, path, payload, fieldName, currentValue) {
  setFieldSaveState(key, 'Unsaved');
  clearTimeout(state.timers.get(key));
  state.pending.set(key, { table, path, payload, fieldName, currentValue, attempts: 0 });
  state.timers.set(key, setTimeout(() => flush(key), state.boot?.settings?.autosaveDebounceMs || 700));
}

async function flush(key) {
  const item = state.pending.get(key);
  if (!item) return;
  setFieldSaveState(key, item.attempts ? 'Retrying' : 'Saving');
  try {
    const result = await api(item.path, { method: 'PATCH', body: JSON.stringify(item.payload) });
    const savedValue = item.fieldName ? result[item.fieldName] : null;
    const editorValue = item.currentValue;
    if (item.fieldName && String(savedValue ?? '') !== String(editorValue ?? '')) {
      state.pending.delete(key);
      setFieldSaveState(key, 'Error');
      return;
    }
    storeRecord(item.table, result);
    document.querySelectorAll(`[data-record-id="${result.record.id}"][data-version-field]`).forEach((node) => {
      node.dataset.version = String(result.version);
    });
    state.pending.delete(key);
    state.conflicts.delete(key);
    clearConflictUi(key);
    setFieldSaveState(key, 'Saved');
  } catch (error) {
    if (error.status === 409) {
      const server = error.data?.serverRecord;
      state.conflicts.set(key, { localValue: item.currentValue, serverRecord: server });
      setFieldSaveState(key, 'Conflict');
      showConflictUi(key, server);
      return;
    }
    item.attempts += 1;
    setFieldSaveState(key, error?.name === 'AbortError' ? 'Error' : 'Error');
    if (item.attempts < 3) setTimeout(() => flush(key), 1000);
  }
}

async function flushAll() {
  await Promise.all([...state.pending.keys()].map((key) => flush(key)));
}

function showConflictUi(key, serverRecord) {
  const host = document.querySelector(`[data-conflict-host="${key}"]`);
  if (!host || !serverRecord) return;
  const field = key.split(':').pop();
  const serverValue = serverRecord[field] ?? '';
  host.innerHTML = `<div class="conflict-panel" role="alert">
    <p><strong>Conflict</strong> — server has: <code>${esc(serverValue)}</code></p>
    <button type="button" data-conflict-action="keep" data-save-key-ref="${key}">Keep Mine / Retry</button>
    <button type="button" data-conflict-action="server" data-save-key-ref="${key}">Use Server Value</button>
  </div>`;
  host.querySelector('[data-conflict-action="keep"]').onclick = async () => {
    const item = state.pending.get(key);
    if (!item) return;
    item.payload.version = serverRecord.version;
    item.attempts = 0;
    await flush(key);
  };
  host.querySelector('[data-conflict-action="server"]').onclick = () => {
    const input = document.querySelector(`[data-save-key-input="${key}"]`);
    if (input) input.value = serverValue;
    storeRecord(key.split(':')[0], { record: serverRecord, version: serverRecord.version });
    document.querySelectorAll(`[data-record-id="${serverRecord.id}"][data-version-field]`).forEach((node) => {
      node.dataset.version = String(serverRecord.version);
    });
    state.pending.delete(key);
    state.conflicts.delete(key);
    host.innerHTML = '';
    setFieldSaveState(key, 'Unsaved');
  };
}

function clearConflictUi(key) {
  const host = document.querySelector(`[data-conflict-host="${key}"]`);
  if (host) host.innerHTML = '';
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') flushAll();
});
window.addEventListener('blur', () => flushAll());
window.addEventListener('beforeunload', () => {
  flushAll();
});

document.querySelectorAll('.rail-button').forEach((button) => {
  button.onclick = async () => {
    await flushAll();
    document.querySelectorAll('.rail-button').forEach((x) => x.classList.toggle('active', x === button));
    document.querySelectorAll('.view').forEach((view) => view.classList.toggle('active', view.id === `view-${button.dataset.view}`));
  };
});

function renderWeekHeader() {
  const iw = state.week?.payload?.instructionalWeek || {};
  const code = state.selectedWeekCode || iw.code || state.week?.starts_on;
  $('metric-week').textContent = code || 'Week';
  $('week-code').textContent = code || 'Week';
  $('week-subtitle').textContent = iw.displaySubtitle || state.week?.starts_on || '';
  $('metric-state').textContent = state.week?.state || '-';
  $('metric-subject').textContent = SUBJECT_LABEL(state.subjectId);
  $('startup-message').textContent = state.startupNote || state.boot?.currentWeek?.startupPrompt || 'Current instructional week opened from SQLite.';
  const warning = state.boot?.currentWeek?.warning;
  const startCopy = `${warning ? `<p class="warn-banner">${esc(warning)}</p>` : ''}<p>${esc(state.startupNote || 'Selected week is restored locally before any fallback runs. SQLite is canonical. Autosave persists before navigation, blur, tab changes, and page unload when timing allows.')}</p>`;
  let extra = '';
  if (!state.week) {
    const startsOn = weekCodeToStartsOn(state.selectedWeekCode);
    if (startsOn) {
      extra = `<div id="create-week-panel"><button type="button" id="create-week-btn" class="primary-button">Create Week ${esc(code)}</button></div>`;
    }
  }
  $('startup-panel').innerHTML = `${startCopy}${extra}<div id="week-chooser" class="week-chooser"></div>`;
  renderWeekChooser();
  const createBtn = document.getElementById('create-week-btn');
  if (createBtn) createBtn.onclick = createSelectedWeek;
}

function renderWeekChooser() {
  const activeCode = canonicalWeekCode(state.selectedWeekCode || state.week?.payload?.instructionalWeek?.code || state.week?.starts_on);
  $('week-chooser').innerHTML = (state.boot?.instructionalWeeks || []).map((w) => {
    const active = canonicalWeekCode(w.code) === activeCode;
    return `<button type="button" class="week-chip${active ? ' active' : ''}" data-week-code="${esc(canonicalWeekCode(w.code))}" aria-pressed="${active ? 'true' : 'false'}" aria-label="Open ${esc(canonicalWeekCode(w.code))}">${esc(canonicalWeekCode(w.code))}</button>`;
  }).join('');
  document.querySelectorAll('[data-week-code]').forEach((btn) => {
    btn.onclick = async () => {
      await flushAll();
      await loadWeekByCode(btn.dataset.weekCode, { persist: true, source: 'button' });
    };
  });
}

const SUBJECT_LABEL = (id) => (state.boot?.subjects || []).find((s) => s.id === id)?.name || id;

async function loadWeekByCode(code, { persist = true, source = 'bootstrap' } = {}) {
  const canonical = canonicalWeekCode(code);
  const startsOn = weekCodeToStartsOn(canonical);
  if (!startsOn) {
    throw new Error(`Unknown instructional week: ${canonical}`);
  }
  if (persist) persistSelectedWeekCode(canonical);
  state.selectedWeekCode = canonical;
  try {
    const week = await api(`/api/weeks/by-code/${encodeURIComponent(canonical)}`);
    state.week = week;
    state.startupNote = source === 'button'
      ? `Selected week ${canonical}.`
      : source === 'explicit'
        ? `Opened requested week ${canonical}.`
        : `Restored saved week ${canonical}.`;
    renderWeekHeader();
    renderWeekGrid();
    $('metric-validation').textContent = `${state.week.validation.length} items`;
    $('validation-list').innerHTML = state.week.validation.map((v) => `<li class="${v.severity}">${v.severity.toUpperCase()}: ${esc(v.message)}</li>`).join('');
    $('deployment-list').innerHTML = (state.week.deploymentPreview?.items || []).map((item) => `<li>${esc(item.target)} — ${esc(item.status)}</li>`).join('');
    renderDrafts(state.week.drafts || []);
    await loadAgendaPreview();
    return week;
  } catch (error) {
    if (error.status === 404) {
      state.week = null;
      state.startupNote = `Week ${canonical} does not exist yet. Choose a week and click "Create Week" to get started.`;
      renderWeekHeader();
      renderWeekGrid();
      $('metric-validation').textContent = '0 items';
      $('validation-list').innerHTML = '';
      $('deployment-list').innerHTML = '';
      $('draft-list').innerHTML = '';
      $('html-preview').textContent = '';
      $('page-preview').innerHTML = '';
      return null;
    }
    throw error;
  }
}

function bindEditable(input, table, field) {
  const key = recordKey(table, input.dataset.recordId, field);
  input.dataset.saveKeyInput = key;
  const status = document.createElement('span');
  status.className = 'field-save saved';
  status.dataset.saveKey = key;
  status.textContent = 'Saved';
  input.insertAdjacentElement('afterend', status);
  const conflictHost = document.createElement('div');
  conflictHost.dataset.conflictHost = key;
  status.insertAdjacentElement('afterend', conflictHost);
  const schedule = () => {
    autosave(key, table, input.dataset.patchPath, {
      version: Number(input.dataset.version),
      fields: { [field]: input.value },
    }, field, input.value);
  };
  input.addEventListener('input', schedule);
  input.addEventListener('change', schedule);
  input.addEventListener('blur', () => {
    if (state.pending.has(key)) flush(key);
  });
}

function renderWeekGrid() {
  if (!state.week || !state.week.subjects) {
    $('week-grid').innerHTML = '<p class="empty-state">No week loaded. Select a week and click Create Week.</p>';
    return;
  }
  const subject = state.week.subjects.find((s) => s.subject === state.subjectId) || state.week.subjects[0];
  state.subjectId = subject.subject;
  $('metric-subject').textContent = SUBJECT_LABEL(subject.subject);
  $('week-grid').innerHTML = `<div class="subject-tabs">${state.week.subjects.map((s) =>
    `<button type="button" class="subject-tab${s.subject === subject.subject ? ' active' : ''}" data-subject="${s.subject}" aria-label="Show ${esc(SUBJECT_LABEL(s.subject))}">${esc(SUBJECT_LABEL(s.subject))}</button>`
  ).join('')}</div><div class="daily-grid">${subject.days.map((day) => `
    <article class="day-card">
      <h3>${esc(day.weekday)} <span class="muted">${esc(day.entry_date)}</span></h3>
      <label>Lesson <input data-field="lesson" data-record-id="${day.id}" data-version-field data-version="${day.version}" data-patch-path="/api/daily-entries/${day.id}" value="${esc(day.lesson)}"></label>
      <label>Title <input data-field="title" data-record-id="${day.id}" data-version-field data-version="${day.version}" data-patch-path="/api/daily-entries/${day.id}" value="${esc(day.title)}"></label>
      <label>In Class <textarea data-field="in_class" rows="3" data-record-id="${day.id}" data-version-field data-version="${day.version}" data-patch-path="/api/daily-entries/${day.id}">${esc(day.in_class)}</textarea></label>
      <label>At Home <textarea data-field="at_home" rows="3" data-record-id="${day.id}" data-version-field data-version="${day.version}" data-patch-path="/api/daily-entries/${day.id}">${esc(day.at_home)}</textarea></label>
      <label>Tests <input data-field="tests" data-record-id="${day.id}" data-version-field data-version="${day.version}" data-patch-path="/api/daily-entries/${day.id}" value="${esc(day.tests)}"></label>
      <details><summary>Resolver</summary><pre>${esc(JSON.stringify(day.resolver_output, null, 2))}</pre></details>
    </article>`).join('')}</div>`;
  document.querySelectorAll('.subject-tab').forEach((tab) => {
    tab.onclick = async () => {
      await flushAll();
      state.subjectId = tab.dataset.subject;
      renderWeekGrid();
    };
  });
  document.querySelectorAll('#week-grid [data-field]').forEach((node) => {
    const field = node.dataset.field;
    storeRecord('daily_subject_entries', { record: subject.days.find((d) => d.id === node.dataset.recordId) });
    bindEditable(node, 'daily_subject_entries', field);
  });
}

function renderPacing(entries) {
  $('pacing-body').innerHTML = entries.slice(0, 100).map((entry) =>
    `<tr><td>${esc(entry.entry_date)}</td><td>${esc(entry.subject)}</td><td>${esc(entry.entry_type)}</td><td><input data-field="normalized_title" data-record-id="${entry.id}" data-version-field data-version="${entry.version}" data-patch-path="/api/pacing/${entry.id}" value="${esc(entry.normalized_title)}"></td></tr>`
  ).join('');
  document.querySelectorAll('#pacing-body input[data-field]').forEach((input) => {
    storeRecord('pacing_entries', { record: entries.find((e) => e.id === input.dataset.recordId) });
    bindEditable(input, 'pacing_entries', input.dataset.field);
  });
}

function renderDrafts(drafts) {
  $('draft-list').innerHTML = drafts.map((draft) =>
    `<li><button type="button" data-draft="${draft.id}" aria-label="Preview ${esc(draft.title)}">${esc(draft.kind)}: ${esc(draft.title)}</button></li>`
  ).join('');
  document.querySelectorAll('[data-draft]').forEach((button) => {
    button.onclick = () => {
      const draft = drafts.find((d) => d.id === button.dataset.draft);
      $('draft-text').value = draft.body_text;
      $('page-preview').innerHTML = draft.body_html;
      $('html-preview').textContent = draft.body_html;
    };
  });
}

async function loadAgendaPreview() {
  if (!state.week) return;
  const preview = await api(`/api/weeks/${state.week.id}/agenda-preview`);
  $('html-preview').textContent = preview.html;
  if (state.previewTab === 'html') $('page-preview').innerHTML = preview.html;
}

document.querySelectorAll('[data-preview-tab]').forEach((tab) => {
  tab.addEventListener('click', async () => {
    await flushAll();
    state.previewTab = tab.dataset.previewTab;
    document.querySelectorAll('[data-preview-tab]').forEach((x) => x.classList.toggle('active', x === tab));
    $('page-preview').classList.toggle('hidden', state.previewTab !== 'text');
    $('html-preview').classList.toggle('hidden', state.previewTab !== 'html');
    if (state.previewTab === 'html') await loadAgendaPreview();
  });
});

async function createSelectedWeek() {
  const code = state.selectedWeekCode;
  const startsOn = weekCodeToStartsOn(code);
  if (!startsOn) return;
  await flushAll();
  const created = await api('/api/weeks', { method: 'POST', body: JSON.stringify({ startsOn }) });
  state.week = created;
  state.startupNote = `Created week ${code}.`;
  renderWeekHeader();
  renderWeekGrid();
  $('metric-validation').textContent = `${state.week.validation.length} items`;
  $('validation-list').innerHTML = state.week.validation.map((v) => `<li class="${v.severity}">${v.severity.toUpperCase()}: ${esc(v.message)}</li>`).join('');
  $('deployment-list').innerHTML = (state.week.deploymentPreview?.items || []).map((item) => `<li>${esc(item.target)} — ${esc(item.status)}</li>`).join('');
  renderDrafts(state.week.drafts || []);
  await loadAgendaPreview();
}

async function main() {
  state.boot = await api('/api/bootstrap');
  const pacing = (await api('/api/pacing')).entries;
  const resources = (await api('/api/resources')).resources;
  const explicitWeek = canonicalWeekCode(new URLSearchParams(location.search).get('week'));
  const savedWeek = getSavedSelectedWeekCode();
  const bootWeek = canonicalWeekCode(state.boot.currentWeek?.instructionalWeek?.code || state.boot.currentWeek?.week?.payload?.instructionalWeek?.code || state.boot.currentWeek?.week?.starts_on);
  const chosenWeek = explicitWeek || savedWeek || bootWeek;
  state.startupNote = explicitWeek
    ? `Opened requested week ${explicitWeek}.`
    : savedWeek
      ? `Restored saved week ${savedWeek}.`
      : state.boot.currentWeek.startupPrompt || 'Current instructional week opened from SQLite.';
  const loaded = await loadWeekByCode(chosenWeek, {
    persist: true,
    source: explicitWeek ? 'explicit' : savedWeek ? 'saved' : 'bootstrap',
  });
  if (loaded === null) state.week = null;
  renderPacing(pacing);
  $('builder-panel').innerHTML = '<p>Reading and Spelling share one agenda page. Reading Tests and Checkouts form one assessment family. Checkout study guides are never created.</p>';
  $('resource-list').innerHTML = resources.map((r) => `<article>${esc(r.canonical_name)} — ${esc(r.sensitivity)} (${esc(r.verification_status)})</article>`).join('') || '<p>No resources registered yet.</p>';
  $('settings-json').textContent = JSON.stringify(await api('/api/settings'), null, 2);
  $('health-json').textContent = JSON.stringify(await api('/api/health'), null, 2);

  $('generate-week').onclick = async () => {
    if (!state.week) return;
    await flushAll();
    state.week = await api(`/api/weeks/${state.week.id}/generate`, { method: 'POST', body: '{}' });
    renderWeekGrid();
    renderDrafts(state.week.drafts || []);
    $('metric-validation').textContent = `${state.week.validation.length} items`;
    $('validation-list').innerHTML = state.week.validation.map((v) => `<li class="${v.severity}">${v.severity.toUpperCase()}: ${esc(v.message)}</li>`).join('');
    $('deployment-list').innerHTML = (state.week.deploymentPreview?.items || []).map((item) => `<li>${esc(item.target)} — ${esc(item.status)}</li>`).join('');
    await loadAgendaPreview();
  };
  $('manual-backup').onclick = async () => alert((await api('/api/backups', { method: 'POST', body: '{}' })).backupPath);
  $('add-resource').onclick = async () => {
    await api('/api/resources', { method: 'POST', body: JSON.stringify({ canonicalName: 'RM4 Reading Test 2 Study Guide', subject: 'reading', resourceType: 'study-guide', audience: 'student', sensitivity: 'student-facing', verificationStatus: 'unverified' }) });
    location.reload();
  };
  $('import-pacing').onclick = async () => {
    const result = await api('/api/pacing/import', { method: 'POST', body: '{}' });
    alert(`Imported ${result.importReport.entriesImported}; excluded ${result.importReport.excludedCells}`);
  };
}

main().catch((error) => {
  document.querySelector('.workspace').innerHTML = `<section class="view active"><h2>Load failed</h2><p>${esc(error.message)}</p></section>`;
});
