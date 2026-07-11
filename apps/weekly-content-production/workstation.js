const $ = (id) => document.getElementById(id);
const requireElement = (id) => {
  const element = $(id);
  if (!element) {
    throw new Error(`Missing required element #${id}`);
  }
  return element;
};
const esc = (value) => String(value ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
  } catch (error) {
    throw new Error(`Failed to load ${path}: ${error.message}`);
  }
  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw new Error(`Failed to parse ${path}: HTTP ${response.status} ${response.statusText}`);
  }
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: HTTP ${response.status} ${data.error || response.statusText}`);
  }
  return data;
}

function setTab(tab) {
  document.querySelectorAll('.tab').forEach((button) => button.classList.toggle('active', button.dataset.tab === tab));
  document.querySelectorAll('.panel').forEach((panel) => panel.classList.toggle('active', panel.id === `tab-${tab}`));
}

function cardHtml(item, fields) {
  const body = fields.map(([label, key]) => `<p><strong>${esc(label)}:</strong> ${esc(item[key])}</p>`).join('');
  return `<article class="card"><h3>${esc(item.title || item.canonical_name || item.resource_id)}</h3>${body}<pre>${esc(item.body_text || item.body_html || item.match_reason || '')}</pre></article>`;
}

function setLocalStatus(message, kind = 'idle') {
  const status = requireElement('local-approval-status');
  status.textContent = message;
  status.dataset.state = kind;
}

async function loadLocalState(weekCode) {
  const localState = await api(`/api/local-state?weekCode=${encodeURIComponent(weekCode)}`);
  const select = requireElement('local-approval-state');
  select.value = localState.approvalState;
  select.dataset.version = String(localState.version ?? 0);
  const statusLabel = localState.status === 'error'
    ? `Error: ${localState.error}`
    : localState.version === 0 && localState.source === 'default'
      ? 'Ready'
      : `Saved v${localState.version}`;
  setLocalStatus(
    statusLabel,
    localState.status === 'error' ? 'error' : 'saved',
  );
  return localState;
}

async function loadPacket() {
  const packet = await api('/api/packet');
  requireElement('packet-meta').textContent = `${packet.weekCode} • ${packet.weekStart} to ${packet.weekEnd} • ${packet.packetId}`;
  requireElement('warn-pill').textContent = `WARN ${packet.validation.warnCount}`;
  requireElement('approval-state').textContent = `Approval: ${packet.approvalState}`;
  requireElement('deployment-state').textContent = `Deployment: ${packet.deploymentState}`;
  requireElement('packet-summary').textContent = `Pages ${packet.pages.length}, assignments ${packet.assignments.length}, resources ${packet.resources.length}, reminders ${packet.assessmentReminders.length}. Approval ${packet.approvalState}, deployment ${packet.deploymentState}.`;
  requireElement('pages-grid').innerHTML = packet.pages.map((page) => cardHtml(page, [['Subject', 'subject_group'], ['Linked assignments', 'linked_assignment_ids']])).join('');
  requireElement('assignments-grid').innerHTML = packet.assignments.map((assignment) => cardHtml(assignment, [['Subject', 'subject'], ['Group', 'group'], ['Audience', 'audience']])).join('');
  requireElement('resources-grid').innerHTML = packet.resources.map((resource) => cardHtml(resource, [['Subject', 'subject'], ['Type', 'resource_type'], ['Confidence', 'match_confidence']])).join('');
  requireElement('reminders-grid').innerHTML = packet.assessmentReminders.map((reminder) => cardHtml(reminder, [['Date', 'date'], ['Linked assignments', 'linked_assignment_ids']])).join('');
  requireElement('html-preview').innerHTML = packet.pages.map((page) => page.body_html).join('');
  requireElement('text-preview').textContent = packet.pages.map((page) => page.body_text).join('\n\n');
  requireElement('packet-json-preview').textContent = JSON.stringify(packet, null, 2);
  requireElement('validation-list').innerHTML = packet.validation.findings.map((finding) => `<li class="${esc(finding.severity)}"><strong>${esc(finding.severity).toUpperCase()}</strong> ${esc(finding.message)}</li>`).join('');
  requireElement('validation-summary').textContent = `PASS ${packet.validation.passCount} • WARN ${packet.validation.warnCount} • FAIL ${packet.validation.failCount}`;
  requireElement('risks-list').innerHTML = packet.risks.map((risk) => `<li class="${esc(risk.severity)}"><strong>${esc(risk.severity).toUpperCase()}</strong> ${esc(risk.message)}</li>`).join('');
  requireElement('provenance-list').innerHTML = packet.provenance.map((item) => `<li><strong>${esc(item.source_type)}</strong> ${esc(item.source_ref)} — ${esc(item.details)}</li>`).join('');
  requireElement('export-status').textContent = 'Ready';
  await loadLocalState(packet.weekCode);
}

document.querySelectorAll('.tab').forEach((button) => {
  button.addEventListener('click', () => setTab(button.dataset.tab));
});

requireElement('export-btn').addEventListener('click', async () => {
  const result = await api('/api/export', { method: 'POST', body: JSON.stringify({}) });
  requireElement('export-status').textContent = `Saved ${result.savedPath}`;
});

requireElement('local-approval-save').addEventListener('click', async () => {
  try {
    const packet = await api('/api/packet');
    const select = requireElement('local-approval-state');
    setLocalStatus('Saving...', 'saving');
    const response = await fetch('/api/local-state', {
      method: 'POST',
      body: JSON.stringify({
        weekCode: packet.weekCode,
        approvalState: select.value,
        version: Number(select.dataset.version || '0'),
      }),
    });
    let result;
    try {
      result = await response.json();
    } catch (error) {
      throw new Error(`Failed to parse /api/local-state: HTTP ${response.status} ${response.statusText}`);
    }
    if (result.status === 'conflict') {
      select.value = result.approvalState;
      select.dataset.version = String(result.version);
      await loadPacket();
      setLocalStatus(`Conflict: v${result.version} already saved`, 'conflict');
      return;
    }
    if (!response.ok) {
      throw new Error(`Failed to save /api/local-state: HTTP ${response.status} ${result.error || response.statusText}`);
    }
    select.dataset.version = String(result.version);
    requireElement('approval-state').textContent = `Approval: ${result.approvalState}`;
    setLocalStatus(`Saved v${result.version}`, 'saved');
    await loadPacket();
  } catch (error) {
    if (String(error.message || '').includes('409')) {
      setLocalStatus(`Conflict: ${error.message}`, 'conflict');
      return;
    }
    setLocalStatus(`Error: ${error.message}`, 'error');
  }
});

loadPacket().catch((error) => {
  document.body.innerHTML = `<main class="workspace"><section class="panel active"><h2>Load failed</h2><p>${esc(error.message)}</p></section></main>`;
});
