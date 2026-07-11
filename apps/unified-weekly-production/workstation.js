const $ = (id) => document.getElementById(id);

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw new Error(`Failed to parse ${path}: ${error.message}`);
  }
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status} ${data.error || response.statusText}`);
  }
  return data;
}

function esc(value) {
  return String(value ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

function setActiveTab(tab) {
  document.querySelectorAll('.tab').forEach((button) => button.classList.toggle('active', button.dataset.tab === tab));
  document.querySelectorAll('.preview').forEach((panel) => panel.classList.toggle('active', panel.dataset.panel === tab));
}

function subjectCard(subject) {
  const resourceCount = subject.resolvedResources.length;
  const unresolvedCount = subject.unresolvedResources.length;
  const blockedCount = subject.blockedResources.length;
  const statusClass = subject.readinessState === 'Blocked' ? 'bad' : subject.readinessState === 'Needs Review' ? 'warn' : '';
  const why = esc(subject.why);
  return `
    <article class="card">
      <h3>${esc(subject.title)}</h3>
      <p class="status ${statusClass}">${esc(subject.readinessState)}</p>
      <p class="muted">Approval: ${esc(subject.approvalState)} • Confidence: ${Number(subject.confidence || 0).toFixed(2)}</p>
      <p class="muted">Resources: ${resourceCount} resolved, ${unresolvedCount} unresolved, ${blockedCount} blocked</p>
      <p class="muted">Preview: ${esc(subject.productionPreviewStatus)}</p>
      <p>${esc(subject.assignmentPolicy === 'disabled' ? 'Assignments disabled' : 'Assignments enabled')}</p>
      <details>
        <summary>Why?</summary>
        <p>${why}</p>
      </details>
    </article>
  `;
}

function inboxCard(item) {
  return `
    <article class="card">
      <h3>${esc(item.issueType)}</h3>
      <p class="muted">${esc(item.weekCode)} • ${esc(item.subject)} • ${esc(item.day || 'any day')} • ${esc(item.event)}</p>
      <p>${esc(item.explanation)}</p>
      <p class="muted">Recommendation: ${esc(item.recommendedAction)}</p>
      <p class="muted">Effect: ${esc(item.effectOnFinalOutput)}</p>
    </article>
  `;
}

function revisionCard(item) {
  return `
    <article class="card">
      <h3>Revision ${esc(item.revision)}</h3>
      <p class="muted">${esc(item.kind)} • ${esc(item.createdAt)}</p>
      <p>${esc(item.summary)}</p>
    </article>
  `;
}

function approvalCard(item) {
  return `
    <article class="card">
      <h3>${esc(item.subject)}</h3>
      <p class="status ${item.status === 'Blocked' ? 'bad' : item.status === 'Needs Review' ? 'warn' : ''}">${esc(item.status)}</p>
      <p class="muted">Unresolved: ${esc(item.unresolvedCount)} • Blocked: ${esc(item.blockedCount)}</p>
      <button class="btn primary" data-approve-subject="${esc(item.subject)}" type="button" ${item.canApprove ? '' : 'disabled'}>Approve ${esc(item.subject)}</button>
    </article>
  `;
}

function traceCard(title, body) {
  return `
    <article class="card">
      <h3>${esc(title)}</h3>
      <pre class="code-block">${esc(body)}</pre>
    </article>
  `;
}

function renderPreview(packet) {
  $('agenda-html').innerHTML = packet.productionPacket.pages.map((page) => page.body_html || page.bodyHtml || '').join('');
  $('text-preview').textContent = packet.productionPacket.pages.map((page) => page.body_text || page.bodyText || '').join('\n\n');
  $('json-preview').textContent = JSON.stringify(packet.productionPacket, null, 2);
  $('assignments-preview').innerHTML = packet.productionPacket.assignments.map((item) => `<article class="card"><h3>${esc(item.title)}</h3><p>${esc(item.subject)}</p><pre>${esc(item.body_text || item.bodyText || '')}</pre></article>`).join('');
  $('reminders-preview').innerHTML = packet.productionPacket.assessmentReminders.map((item) => `<article class="card"><h3>${esc(item.title)}</h3><p>${esc(item.date || packet.weekSelection.startsOn)}</p><pre>${esc(item.body_text || item.bodyText || '')}</pre></article>`).join('');
  $('resources-preview').innerHTML = packet.resourceResolution.resolvedResources.map((item) => `<article class="card"><h3>${esc(item.resource ? item.resource.canonicalName : item.requirement.titleHint || item.requirement.resourceType)}</h3><p>${esc(item.resolutionMethod)}</p><pre>${esc(item.explanation.join(' '))}</pre></article>`).join('');
  $('manifest-preview').textContent = JSON.stringify(packet.deploymentManifestPreview, null, 2);
}

function renderWeekOptions(packet) {
  const select = $('week-select');
  select.innerHTML = packet.weekSelection.weeks.map((week) => `<option value="${esc(week.code)}">${esc(week.code)} • ${esc(week.displaySubtitle)}</option>`).join('');
  select.value = packet.weekCode;
}

async function loadWorkstation() {
  const packet = await request('/api/workstation');
  window.__packet = packet;
  renderWeekOptions(packet);
  $('week-meta').textContent = `${packet.weekCode} • ${packet.weekSelection.startsOn} to ${packet.weekSelection.endsOn} • ${packet.weekSelection.displaySubtitle}`;
  $('readiness-pill').textContent = `Readiness: ${packet.readiness.score}%`;
  $('approval-pill').textContent = `Full week: ${packet.approvalPanel.fullWeekApprovalState}`;
  $('manifest-pill').textContent = `Manifest: ${packet.deploymentManifestPreview.mode}`;
  $('state-pill').textContent = `State: ${packet.localState.selectedWeekCode}`;
  $('readiness-score').textContent = `${packet.readiness.score}%`;
  $('readiness-explainer').textContent = packet.readiness.explanation;
  $('exception-count').textContent = String(packet.exceptionInbox.length);
  $('revision-count').textContent = String(packet.revisionHistory.length);
  $('subject-grid').innerHTML = packet.subjectWorkspaces.map(subjectCard).join('');
  $('exception-inbox').innerHTML = packet.exceptionInbox.map(inboxCard).join('');
  $('revision-history').innerHTML = packet.revisionHistory.map(revisionCard).join('');
  $('approval-panel').innerHTML = packet.approvalPanel.subjectApprovals.map(approvalCard).join('') + `
    <article class="card">
      <h3>Full Week</h3>
      <p class="status ${packet.approvalPanel.fullWeekApprovalReady ? '' : 'warn'}">${esc(packet.approvalPanel.fullWeekApprovalState)}</p>
      <p class="muted">Requires all required subject approvals.</p>
      <button class="btn primary" id="approve-full-week" type="button" ${packet.approvalPanel.fullWeekApprovalReady ? '' : ''}>Approve full week</button>
    </article>
  `;
  $('trace-grid').innerHTML = [
    traceCard('Source pacing', JSON.stringify(packet.sourcePacing, null, 2)),
    traceCard('Teacher Brain prediction', JSON.stringify(packet.teacherBrain, null, 2)),
    traceCard('Resource resolution', JSON.stringify(packet.resourceResolution, null, 2)),
    traceCard('Final production packet', JSON.stringify(packet.productionPacket, null, 2)),
  ].join('');
  $('local-state').textContent = JSON.stringify(packet.localState, null, 2);
  renderPreview(packet);
  setActiveTab(document.querySelector('.tab.active')?.dataset.tab || 'agenda-html');

  document.querySelectorAll('[data-approve-subject]').forEach((button) => {
    button.addEventListener('click', async () => {
      const subject = button.dataset.approveSubject;
      await request('/api/approve', {
        method: 'POST',
        body: JSON.stringify({ weekCode: packet.weekCode, scope: subject, subject, status: 'approved', packetRevision: packet.localState.weekState?.revision || 0, contentHash: packet.packetId }),
      });
      await loadWorkstation();
    });
  });

  const fullWeekButton = $('approve-full-week');
  if (fullWeekButton) {
    fullWeekButton.addEventListener('click', async () => {
      await request('/api/approve', {
        method: 'POST',
        body: JSON.stringify({ weekCode: packet.weekCode, scope: 'full-week', status: 'approved', packetRevision: packet.localState.weekState?.revision || 0, contentHash: packet.packetId }),
      });
      await loadWorkstation();
    });
  }

  $('export-btn').onclick = async () => {
    const result = await request('/api/export', { method: 'POST', body: JSON.stringify({ weekCode: packet.weekCode }) });
    $('state-pill').textContent = `State: exported ${result.savedPath}`;
    await loadWorkstation();
  };

  $('regenerate-btn').onclick = async () => {
    const result = await request('/api/regenerate', { method: 'POST', body: JSON.stringify({ weekCode: packet.weekCode }) });
    $('state-pill').textContent = `State: regenerated ${result.packet.weekCode}`;
    await loadWorkstation();
  };

  $('generate-btn').onclick = async () => {
    await request('/api/select-week', { method: 'POST', body: JSON.stringify({ weekCode: $('week-select').value }) });
    await loadWorkstation();
  };

  $('week-select').onchange = async () => {
    await request('/api/select-week', { method: 'POST', body: JSON.stringify({ weekCode: $('week-select').value }) });
    await loadWorkstation();
  };

  $('correction-form').onsubmit = async (event) => {
    event.preventDefault();
    const body = {
      kind: 'instructional',
      weekCode: packet.weekCode,
      subject: $('correction-subject').value,
      day: $('correction-day').value,
      field: $('correction-field').value,
      originalValue: $('correction-original').value,
      editedValue: $('correction-edited').value,
      scope: $('correction-scope').value,
      reason: $('correction-reason').value,
      sourceRule: $('correction-source-rule').value,
      timestamp: new Date().toISOString(),
      revision: packet.localState.correctionCount + 1,
      invalidatesApproval: true,
    };
    await request('/api/correction', { method: 'POST', body: JSON.stringify(body) });
    $('correction-status').textContent = 'Correction saved locally and approvals invalidated.';
    await loadWorkstation();
  };
}

document.querySelectorAll('.tab').forEach((button) => {
  button.addEventListener('click', () => setActiveTab(button.dataset.tab));
});

loadWorkstation().catch((error) => {
  document.body.innerHTML = `<main class="shell"><section class="card-panel"><h2>Load failed</h2><p>${esc(error.message)}</p></section></main>`;
});
