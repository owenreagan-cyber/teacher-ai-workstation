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
  await loadPhase27();
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

// Mirrors approval_gate.NON_APPROVABLE_STATUSES exactly. The server is the
// real enforcement point (this only controls whether the button is shown
// disabled); BLOCKED covers both archived-course targets and unresolved
// due-time assignments, since both set that comparisonStatus.
const PHASE27_NON_APPROVABLE = new Set(['CONFLICT', 'BLOCKED', 'OMIT', 'DELETE_CANDIDATE']);

const PHASE27_FRIENDLY_LABEL = {
  CREATE: 'New',
  UPDATE: 'Changed',
  UNCHANGED: 'Unchanged',
  BLOCKED: 'Blocked',
  CONFLICT: 'Conflict',
  OMIT: 'Omitted',
  DELETE_CANDIDATE: 'Delete candidate',
};

const PHASE27_STATUS_CLASS = {
  BLOCKED: 'bad',
  CONFLICT: 'bad',
  OMIT: 'warn',
  DELETE_CANDIDATE: 'warn',
};

function phase27DiffCard(item) {
  const statusClass = PHASE27_STATUS_CLASS[item.comparisonStatus] || '';
  const canApprove = !PHASE27_NON_APPROVABLE.has(item.comparisonStatus);
  const label = PHASE27_FRIENDLY_LABEL[item.comparisonStatus] || item.comparisonStatus;
  const body = item.localBody || '';
  return `
    <article class="card" data-object-id="${esc(item.objectId)}">
      <h3>${esc(item.localTitle || item.objectId)}</h3>
      <p class="status ${statusClass}">${esc(label)}</p>
      <p class="muted">${esc(item.objectType)} • course ${esc(item.targetCourse)}</p>
      ${(item.blockers || []).length ? `<p class="status bad">Blocked: ${esc(item.blockers.join('; '))}</p>` : ''}
      <p class="muted">Approval: ${esc(item.approvalState)}</p>
      <div class="preview-frame">
        <p class="muted">${esc(item.localTitle || '')}</p>
        <pre class="code-block phase27-copy-body">${esc(body)}</pre>
      </div>
      <div class="week-row">
        <button class="btn phase27-approve-btn" type="button" data-object-id="${esc(item.objectId)}" ${canApprove ? '' : 'disabled'}>Approve</button>
        <button class="btn phase27-revoke-btn" type="button" data-object-id="${esc(item.objectId)}">Revoke</button>
        <button class="btn phase27-copy-btn" type="button" data-object-id="${esc(item.objectId)}">Copy</button>
      </div>
      <details>
        <summary>Expert Details</summary>
        <p class="muted">Match: ${esc(item.matchReason || 'none')} (confidence ${item.matchConfidence}) • Module: ${esc((item.modulePlacement || {}).status || 'n/a')}</p>
        <pre class="code-block">${esc(JSON.stringify(item.fieldDiffs, null, 2))}</pre>
      </details>
    </article>
  `;
}

function phase27PlacementCard(item) {
  const mp = item.modulePlacement || {};
  const statusClass = mp.status === 'already-correct' || mp.status === 'omitted' ? '' : mp.status === 'blocked' ? 'bad' : 'warn';
  return `
    <article class="card">
      <h3>${esc(item.localTitle || item.objectId)}</h3>
      <p class="status ${statusClass}">${esc(mp.status || 'n/a')}</p>
      <p class="muted">Current: ${esc(mp.currentModule || '—')} @ ${mp.currentPosition ?? '—'} &rarr; Desired: ${esc(mp.desiredModule || '—')} @ ${mp.desiredPosition ?? '—'}</p>
      ${mp.conflictReason ? `<p class="muted">${esc(mp.conflictReason)}</p>` : ''}
    </article>
  `;
}

function phase27HealthCard(h) {
  const statusClass = h.status === 'FAIL' ? 'bad' : (h.status === 'WARN' || h.status === 'BLOCKED') ? 'warn' : '';
  return `
    <article class="card">
      <h3>${esc(h.check)}</h3>
      <p class="status ${statusClass}">${esc(h.status)}</p>
      <p class="muted">${esc(h.detail)}</p>
    </article>
  `;
}

function phase27RollbackCard(r) {
  return `
    <article class="card">
      <h3>${esc(r.operationId)}</h3>
      <p class="muted">${esc(r.rollbackType)} • risk: ${esc(r.risk)} • executable: ${String(r.executable)}</p>
      <details><summary>Prior state</summary><pre class="code-block">${esc(JSON.stringify(r.priorState, null, 2))}</pre></details>
    </article>
  `;
}

function renderPhase27(payload) {
  const manifest = payload.deploymentManifestV1;
  $('phase27-mode').textContent = `Phase 27: ${manifest.mode}`;
  $('phase27-snapshot-age').textContent = `Snapshot: ${manifest.targetSnapshotFreshness || manifest.targetSnapshotAge}`;
  // Two different questions, shown separately: is the *software* correct
  // (systemValidationStatus, from dependency-graph structural checks), and
  // is *this week's content* ready to deploy (overallReadiness, which is
  // expected to read "blocked" whenever a demo conflict/blocked item is
  // present -- that is not a software defect).
  $('phase27-system-validation').textContent = `System validation: ${manifest.systemValidationStatus}`;
  $('phase27-manifest-readiness').textContent = `Demo manifest readiness: ${manifest.overallReadiness.toUpperCase()}`;

  const remoteObjects = (payload.snapshot && payload.snapshot.remoteObjects) || [];
  $('phase27-snapshot').innerHTML = remoteObjects.map((obj) => `
    <article class="card">
      <h3>${esc(obj.title || obj.slug || obj.canvasId)}</h3>
      <p class="muted">${esc(obj.objectType)} • course ${esc(obj.courseRef)} • canvasId ${esc(obj.canvasId)} • ${esc(obj.publication || 'unknown')}</p>
    </article>
  `).join('') || '<p class="muted">No remote objects in this snapshot.</p>';

  const transport = payload.transportReadiness || {};
  $('phase27-transport').innerHTML = `
    <article class="card">
      <h3>${esc(transport.defaultTransport || 'DisabledCanvasTransport')}</h3>
      <p class="status ${transport.mutationRejectionVerified ? '' : 'bad'}">${transport.mutationRejectionVerified ? 'Mutation rejection verified' : 'NOT VERIFIED'}</p>
      <p class="muted">Live read-only transport enabled: ${transport.liveReadOnlyEnabled ? 'yes' : 'no'}</p>
    </article>
  `;

  $('phase27-diff').innerHTML = (payload.safetyDiff || []).map(phase27DiffCard).join('');
  $('phase27-placement').innerHTML = (payload.safetyDiff || []).map(phase27PlacementCard).join('');
  $('phase27-manifest').textContent = JSON.stringify(manifest, null, 2);
  $('phase27-health-checks').innerHTML = (payload.healthChecks || []).map(phase27HealthCard).join('');
  $('phase27-rollback').innerHTML = (manifest.rollbackPlan || []).map(phase27RollbackCard).join('')
    || '<p class="muted">No rollback instructions (nothing pending deployment).</p>';

  document.querySelectorAll('.phase27-approve-btn').forEach((button) => {
    button.addEventListener('click', () => phase27Approve(button.dataset.objectId));
  });
  document.querySelectorAll('.phase27-revoke-btn').forEach((button) => {
    button.addEventListener('click', () => phase27Revoke(button.dataset.objectId));
  });
  document.querySelectorAll('.phase27-copy-btn').forEach((button) => {
    button.addEventListener('click', () => phase27Copy(button.dataset.objectId));
  });
}

async function phase27Copy(objectId) {
  const payload = window.__phase27;
  if (!payload) return;
  const item = payload.safetyDiff.find((d) => d.objectId === objectId);
  if (!item) return;
  const text = `${item.localTitle || ''}\n\n${item.localBody || ''}`;
  try {
    await navigator.clipboard.writeText(text);
    $('phase27-status-note').textContent = `Copied "${item.localTitle || objectId}" to clipboard.`;
  } catch (error) {
    $('phase27-status-note').textContent = `Could not copy to clipboard: ${error.message}`;
  }
}

async function loadPhase27Ledger() {
  try {
    const status = await request('/api/phase27/ledger-status');
    $('phase27-ledger').innerHTML = `
      <article class="card">
        <h3>Ledger ${status.exists ? '' : '(not yet created)'}</h3>
        <p class="status ${status.integrityOk === false ? 'bad' : ''}">${status.exists ? (status.integrityOk ? 'integrity ok' : 'integrity FAILED') : 'no ledger yet'}</p>
        <p class="muted">schema version ${status.schemaVersion ?? '—'} • ${status.eventCount} event(s)</p>
        <details><summary>Recent events</summary><pre class="code-block">${esc(JSON.stringify(status.recentEvents, null, 2))}</pre></details>
      </article>
    `;
  } catch (error) {
    $('phase27-ledger').innerHTML = `<p class="muted">Ledger status unavailable: ${esc(error.message)}</p>`;
  }
}

async function loadPhase27() {
  let payload = null;
  try {
    payload = await request('/api/phase27/packet');
  } catch (liveError) {
    try {
      payload = await request('./data/phase27-demo.json');
    } catch (fallbackError) {
      payload = null;
    }
  }
  window.__phase27 = payload;
  if (!payload) {
    $('phase27-status-note').textContent = 'Phase 27 data is unavailable (no live endpoint and no static demo file).';
    return;
  }
  $('phase27-status-note').textContent = '';
  renderPhase27(payload);
  await loadPhase27Ledger();
}

async function phase27Approve(objectId) {
  const payload = window.__phase27;
  if (!payload) return;
  const item = payload.safetyDiff.find((d) => d.objectId === objectId);
  const manifest = payload.deploymentManifestV1;
  if (!item) return;
  try {
    const result = await request('/api/phase27/approve', {
      method: 'POST',
      body: JSON.stringify({
        objectId,
        comparisonStatus: item.comparisonStatus,
        blockers: item.blockers,
        manifestRevision: manifest.packetRevision,
        snapshotId: manifest.targetSnapshotId,
        snapshotFreshness: manifest.targetSnapshotFreshness || manifest.targetSnapshotAge,
        approvedBy: 'teacher',
      }),
    });
    if (result.ok) {
      item.approvalState = 'Approved';
      renderPhase27(payload);
      await loadPhase27Ledger();
    }
  } catch (error) {
    $('phase27-status-note').textContent = `Could not approve ${objectId}: ${error.message}`;
  }
}

async function phase27Revoke(objectId) {
  const payload = window.__phase27;
  if (!payload) return;
  const manifest = payload.deploymentManifestV1;
  try {
    await request('/api/phase27/revoke', {
      method: 'POST',
      body: JSON.stringify({
        objectId,
        manifestRevision: manifest.packetRevision,
        snapshotId: manifest.targetSnapshotId,
      }),
    });
    const item = payload.safetyDiff.find((d) => d.objectId === objectId);
    if (item) item.approvalState = 'Needs Review';
    renderPhase27(payload);
    await loadPhase27Ledger();
  } catch (error) {
    $('phase27-status-note').textContent = `Could not revoke ${objectId}: ${error.message}`;
  }
}

$('phase27-refresh-btn').addEventListener('click', async () => {
  $('phase27-status-note').textContent = 'Refreshing...';
  await loadPhase27();
  $('phase27-status-note').textContent = 'Refreshed.';
});

$('phase27-export-btn').addEventListener('click', async () => {
  try {
    const result = await request('/api/phase27/export', { method: 'POST', body: JSON.stringify({}) });
    $('phase27-status-note').textContent = `Export written to ${result.exportDir}`;
  } catch (error) {
    $('phase27-status-note').textContent = `Export failed: ${error.message}`;
  }
});

document.querySelectorAll('.tab').forEach((button) => {
  button.addEventListener('click', () => setActiveTab(button.dataset.tab));
});

loadWorkstation().catch((error) => {
  document.body.innerHTML = `<main class="shell"><section class="card-panel"><h2>Load failed</h2><p>${esc(error.message)}</p></section></main>`;
});
