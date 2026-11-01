/**
 * Google A2A Protocol Interactive Workspace
 * Orchestrates queries, visualizes JSON-RPC 2.0 message flow, Agent Cards, and output artifacts.
 */

// Determine API Base URL (works if served via FastAPI or opened as file://)
const API_BASE = window.location.origin.startsWith('http') ? '' : 'http://127.0.0.1:8000';

// Global state
let currentMode = 'auto';
let lastResponseData = null;
let currentTab = 'card-matrix';
let activeSessionId = null;
let lastPendingConfirmation = null;

// DOM Elements
const queryInput = document.getElementById('query-input');
const submitBtn = document.getElementById('submit-btn');
const outputContent = document.getElementById('output-content');
const outputRuntime = document.getElementById('output-runtime');
const sessionBadge = document.getElementById('session-badge');
const agentBadgeBanner = document.getElementById('agent-badge-banner');
const agentBadgeIcon = document.getElementById('agent-badge-icon');
const agentBadgeTitle = document.getElementById('agent-badge-title');
const agentBadgeDesc = document.getElementById('agent-badge-desc');
const executionEnginePill = document.getElementById('execution-engine-pill');
const engineIcon = document.getElementById('engine-icon');
const engineText = document.getElementById('engine-text');
const billingWarningCallout = document.getElementById('billing-warning-callout');
const billingWarningMsg = document.getElementById('billing-warning-msg');
const artifactsSection = document.getElementById('artifacts-section');
const artifactsList = document.getElementById('artifacts-list');
const flowStepsContainer = document.getElementById('flow-steps-container');
const traceTimer = document.getElementById('trace-timer');
const codeViewer = document.getElementById('code-viewer');
const matrixContainer = document.getElementById('matrix-container');
const matrixCardsList = document.getElementById('matrix-cards-list');
const modeButtons = document.querySelectorAll('.mode-btn');
const promptPills = document.querySelectorAll('.prompt-pill');
const telemetryTabs = document.querySelectorAll('.t-tab');
const protocolStatus = document.getElementById('protocol-status');
const keyDot = document.getElementById('key-dot');
const keyStatusText = document.getElementById('key-status-text');

// HITL & Tool Confirmation Elements
const hitlBox = document.getElementById('hitl-box');
const btnHitlApprove = document.getElementById('btn-hitl-approve');
const btnHitlRevise = document.getElementById('btn-hitl-revise');
const btnHitlReject = document.getElementById('btn-hitl-reject');
const hitlFeedbackContainer = document.getElementById('hitl-feedback-container');
const hitlCustomInput = document.getElementById('hitl-custom-input');
const btnHitlSend = document.getElementById('btn-hitl-send');
const revChips = document.querySelectorAll('.rev-chip');

const toolConfirmBox = document.getElementById('tool-confirm-box');
const toolNameLabel = document.getElementById('tool-name-label');
const toolCallIdLabel = document.getElementById('tool-call-id-label');
const toolConfirmHint = document.getElementById('tool-confirm-hint');
const btnConfirmTool = document.getElementById('btn-confirm-tool');
const btnRejectTool = document.getElementById('btn-reject-tool');

const audioPlayerBox = document.getElementById('audio-player-box');
const audioEpisodeTitle = document.getElementById('audio-episode-title');
const audioMetaText = document.getElementById('audio-meta-text');
const masterAudioElement = document.getElementById('master-audio-element');
const audioDownloadBtn = document.getElementById('audio-download-btn');

// Agent metadata dictionary
const AGENT_META = {
  sql_agent: {
    title: 'SQL Agent (LangChain + LangGraph + HITL + PII)',
    icon: '🗄️',
    cardId: 'card-sql',
    colorClass: '',
    endpoint: 'http://127.0.0.1:8000/sql/a2a'
  },
  rag_agent: {
    title: 'RAG Agent (LangChain + FAISS Vector Store)',
    icon: '📚',
    cardId: 'card-rag',
    colorClass: 'green',
    endpoint: 'http://127.0.0.1:8000/rag/a2a'
  },
  podcast_agent: {
    title: 'Podcast Agent (Google ADK Studio)',
    icon: '🎙️',
    cardId: 'card-podcast',
    colorClass: 'yellow',
    endpoint: 'http://127.0.0.1:8000/podcast/a2a'
  },
  orchestrator: {
    title: 'A2A Orchestrator (Multi-Agent Supervisor)',
    icon: '🌐',
    cardId: 'card-orchestrator',
    colorClass: '',
    endpoint: 'http://127.0.0.1:8000/a2a'
  }
};

// Initialize listeners
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkAgentStatus();
  checkApiKeyStatus();
});

function setupEventListeners() {
  // Mode selection buttons
  modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      modeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMode = btn.getAttribute('data-mode');
      highlightSelectedCard(currentMode);
    });
  });

  // Prompt suggestion pills
  promptPills.forEach(pill => {
    pill.addEventListener('click', () => {
      queryInput.value = pill.getAttribute('data-query');
      queryInput.focus();
    });
  });

  // Telemetry sub-tabs
  telemetryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      telemetryTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTab = tab.getAttribute('data-tab');
      renderActiveTab();
    });
  });

  // Submit button
  submitBtn.addEventListener('click', handleQuerySubmit);

  // Ctrl+Enter or Cmd+Enter to submit
  queryInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleQuerySubmit();
    }
  });

  // Human-in-the-Loop (HITL) Review Gate Buttons
  btnHitlApprove?.addEventListener('click', () => {
    sendFollowUpFeedback('Approve. Proceed with audio generation.', 'approve');
  });

  btnHitlRevise?.addEventListener('click', () => {
    if (hitlFeedbackContainer) {
      hitlFeedbackContainer.style.display = hitlFeedbackContainer.style.display === 'none' ? 'block' : 'none';
      hitlCustomInput?.focus();
    }
  });

  btnHitlReject?.addEventListener('click', () => {
    if (hitlFeedbackContainer) {
      hitlFeedbackContainer.style.display = 'block';
      if (hitlCustomInput) {
        hitlCustomInput.value = 'Re-research: Please investigate a different angle or topic: ';
        hitlCustomInput.focus();
      }
    }
  });

  // Revision quick suggestion chips
  revChips.forEach(chip => {
    chip.addEventListener('click', () => {
      if (hitlCustomInput) {
        hitlCustomInput.value = chip.getAttribute('data-text');
        if (hitlFeedbackContainer) hitlFeedbackContainer.style.display = 'block';
        hitlCustomInput.focus();
      }
    });
  });

  // Submit custom HITL revision feedback
  btnHitlSend?.addEventListener('click', () => {
    const text = hitlCustomInput ? hitlCustomInput.value.trim() : '';
    if (text) {
      sendFollowUpFeedback(text, 'revise');
    }
  });

  hitlCustomInput?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const text = hitlCustomInput.value.trim();
      if (text) sendFollowUpFeedback(text, 'revise');
    }
  });

  // Tool confirmation buttons
  btnConfirmTool?.addEventListener('click', () => {
    sendToolConfirmation(true);
  });

  btnRejectTool?.addEventListener('click', () => {
    sendToolConfirmation(false);
  });

  // Modal buttons
  document.getElementById('btn-mcp-modal')?.addEventListener('click', () => {
    openModal('mcp-modal');
  });

  document.getElementById('btn-key-modal')?.addEventListener('click', () => {
    openModal('key-modal');
  });

  document.getElementById('btn-save-key')?.addEventListener('click', handleSaveApiKey);
}

/**
 * Modal helpers
 */
window.openModal = function(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'flex';
};

window.closeModal = function(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
};

/**
 * Highlight corresponding agent card on top
 */
function highlightSelectedCard(mode) {
  document.querySelectorAll('.agent-mini-card').forEach(c => c.classList.remove('active'));
  if (mode === 'sql') document.getElementById('card-sql')?.classList.add('active');
  else if (mode === 'rag') document.getElementById('card-rag')?.classList.add('active');
  else if (mode === 'podcast') document.getElementById('card-podcast')?.classList.add('active');
  else if (mode === 'orchestrator') document.getElementById('card-orchestrator')?.classList.add('active');
}

/**
 * Check backend status on load
 */
async function checkAgentStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/agents`);
    if (res.ok) {
      const data = await res.json();
      protocolStatus.innerHTML = `<span class="status-dot"></span><span>A2A Server Online • ${data.agents?.length || 3} Agents Discovered</span>`;
      protocolStatus.style.background = 'var(--g-green-light)';
      protocolStatus.style.color = 'var(--g-green)';
    }
  } catch (err) {
    protocolStatus.innerHTML = `<span class="status-dot" style="background:var(--g-yellow);"></span><span>Server Offline (Run: python ui/run.py)</span>`;
    protocolStatus.style.background = 'var(--g-yellow-light)';
    protocolStatus.style.color = 'var(--g-yellow)';
  }
}

/**
 * Check Google Gemini API key status
 */
async function checkApiKeyStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/key-status`);
    if (res.ok) {
      const data = await res.json();
      const modalBox = document.getElementById('key-modal-status-box');
      if (data.status === 'active') {
        keyDot.style.background = 'var(--g-green)';
        keyStatusText.textContent = `Gemini Key: Active (${data.masked})`;
        if (modalBox) {
          modalBox.style.background = 'var(--g-green-light)';
          modalBox.style.color = 'var(--g-green)';
          modalBox.innerHTML = `<strong>Active:</strong> ${data.message} (${data.masked})`;
        }
      } else if (data.status === 'billing_blocked') {
        keyDot.style.background = 'var(--g-yellow)';
        keyStatusText.textContent = `Billing Blocked (${data.masked})`;
        if (modalBox) {
          modalBox.style.background = 'var(--g-yellow-light)';
          modalBox.style.color = '#b06000';
          modalBox.innerHTML = `<strong>Billing Balance Notice:</strong> ${data.message}`;
        }
      } else {
        keyDot.style.background = 'var(--g-red)';
        keyStatusText.textContent = `Key Missing / Error`;
        if (modalBox) {
          modalBox.style.background = 'var(--g-red-light)';
          modalBox.style.color = 'var(--g-red)';
          modalBox.innerHTML = `<strong>Notice:</strong> ${data.message}`;
        }
      }
    }
  } catch (e) {
    keyStatusText.textContent = 'Key Check Failed';
  }
}

/**
 * Save new API key from modal
 */
async function handleSaveApiKey() {
  const input = document.getElementById('input-api-key');
  const key = input ? input.value.trim() : '';
  if (!key) {
    alert('Please enter an API key.');
    return;
  }

  const btn = document.getElementById('btn-save-key');
  btn.disabled = true;
  btn.textContent = 'Testing key with Gemini...';

  try {
    const res = await fetch(`${API_BASE}/api/set-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: key })
    });
    const data = await res.json();
    if (data.success) {
      alert('Key successfully validated with Gemini and saved to .env!');
      closeModal('key-modal');
      checkApiKeyStatus();
    } else {
      alert(`Key error: ${data.message}`);
      checkApiKeyStatus();
    }
  } catch (e) {
    alert(`Failed to save key: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Save & Verify Key';
  }
}

/**
 * Main query submit handler
 */
async function handleQuerySubmit() {
  const query = queryInput.value.trim();
  if (!query) {
    queryInput.focus();
    return;
  }

  // Reset interactive components
  if (hitlBox) hitlBox.style.display = 'none';
  if (toolConfirmBox) toolConfirmBox.style.display = 'none';
  if (audioPlayerBox) audioPlayerBox.style.display = 'none';

  // Set loading state
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Executing A2A...</span><div class="status-dot" style="animation:pulse 1s infinite;"></div>`;
  outputRuntime.textContent = 'A2A Task In-Flight...';
  outputContent.innerHTML = `<div style="color:var(--g-muted); font-style:italic;">Processing request via Google A2A Protocol... Evaluating candidate Agent Cards and executing runtime...</div>`;
  artifactsSection.style.display = 'none';
  artifactsList.innerHTML = '';
  billingWarningCallout.style.display = 'none';
  
  // Reset flow steps to in-progress
  flowStepsContainer.innerHTML = `
    <div class="flow-step-item">
      <div class="flow-step-icon">1</div>
      <div class="flow-step-text">
        <strong>1. A2A Protocol Gateway</strong>
        <p>Ingested query: "${escapeHtml(query.substring(0, 75))}${query.length > 75 ? '...' : ''}"</p>
      </div>
    </div>
    <div class="flow-step-item">
      <div class="flow-step-icon" style="background:var(--g-yellow);">2</div>
      <div class="flow-step-text">
        <strong>2. Intent & Capability Matching</strong>
        <p>Scanning all registered Agent Cards for skill matches...</p>
      </div>
    </div>
  `;

  const startTime = performance.now();

  try {
    const response = await fetch(`${API_BASE}/api/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        mode: currentMode,
        session_id: activeSessionId
      })
    });

    const elapsed = Math.round(performance.now() - startTime);
    traceTimer.textContent = `Latency: ${elapsed} ms`;

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    lastResponseData = data;

    // Display execution results
    renderResults(data);

  } catch (err) {
    const elapsed = Math.round(performance.now() - startTime);
    traceTimer.textContent = `Error in ${elapsed} ms`;
    outputRuntime.textContent = 'Execution Failed';
    outputContent.innerHTML = `<div style="color:var(--g-red); font-weight:500;">⚠️ Error communicating with A2A Protocol:</div>
<div style="color:var(--g-muted); margin-top:6px;">${escapeHtml(err.message)}</div>
<div style="margin-top:12px; font-size:0.85rem; background:#fce8e6; padding:8px 12px; border-radius:6px; color:#c5221f;">
  Tip: Ensure the A2A server is running using:<br>
  <code>uv run python ui/run.py</code> (or <code>uv run python a2a/main.py</code>)
</div>`;

    flowStepsContainer.innerHTML += `
      <div class="flow-step-item" style="border-color:var(--g-red);">
        <div class="flow-step-icon" style="background:var(--g-red);">✕</div>
        <div class="flow-step-text">
          <strong style="color:var(--g-red);">A2A Gateway Exception</strong>
          <p>${escapeHtml(err.message)}</p>
        </div>
      </div>
    `;

    codeViewer.textContent = JSON.stringify({ error: err.message, stack: err.stack }, null, 2);

  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>Run A2A</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`;
  }
}

/**
 * Sends follow-up feedback (approval, revisions, or reject) to the active session
 */
async function sendFollowUpFeedback(feedbackText, action = 'feedback') {
  if (!feedbackText) return;

  if (btnHitlApprove) btnHitlApprove.disabled = true;
  if (btnHitlRevise) btnHitlRevise.disabled = true;
  if (btnHitlReject) btnHitlReject.disabled = true;
  if (btnHitlSend) btnHitlSend.disabled = true;
  outputRuntime.textContent = 'Agent Processing Human Input...';

  flowStepsContainer.innerHTML += `
    <div class="flow-step-item">
      <div class="flow-step-icon" style="background:var(--g-yellow);">⚡</div>
      <div class="flow-step-text">
        <strong>Human Feedback Handoff (${escapeHtml(action)})</strong>
        <p>"${escapeHtml(feedbackText.substring(0, 80))}${feedbackText.length > 80 ? '...' : ''}"</p>
      </div>
    </div>
  `;

  const startTime = performance.now();

  try {
    const response = await fetch(`${API_BASE}/api/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: feedbackText,
        mode: currentMode === 'auto' ? 'podcast' : currentMode,
        session_id: activeSessionId,
        action: action
      })
    });

    const elapsed = Math.round(performance.now() - startTime);
    traceTimer.textContent = `Latency: ${elapsed} ms`;

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    lastResponseData = data;
    renderResults(data);

  } catch (err) {
    alert(`Error sending feedback: ${err.message}`);
  } finally {
    if (btnHitlApprove) btnHitlApprove.disabled = false;
    if (btnHitlRevise) btnHitlRevise.disabled = false;
    if (btnHitlReject) btnHitlReject.disabled = false;
    if (btnHitlSend) btnHitlSend.disabled = false;
  }
}

/**
 * Sends tool confirmation or rejection to Google ADK
 */
async function sendToolConfirmation(confirmed) {
  if (!lastPendingConfirmation) return;

  if (btnConfirmTool) btnConfirmTool.disabled = true;
  if (btnRejectTool) btnRejectTool.disabled = true;
  outputRuntime.textContent = confirmed ? 'Tool Execution Confirmed...' : 'Tool Call Rejected...';

  flowStepsContainer.innerHTML += `
    <div class="flow-step-item">
      <div class="flow-step-icon" style="background:${confirmed ? 'var(--g-green)' : 'var(--g-red)'};">
        ${confirmed ? '✓' : '✕'}
      </div>
      <div class="flow-step-text">
        <strong>ADK Tool Confirmation (${confirmed ? 'Approved' : 'Rejected'})</strong>
        <p>Tool: ${escapeHtml(lastPendingConfirmation.tool_name || 'generate_podcast_audio')}</p>
      </div>
    </div>
  `;

  const startTime = performance.now();

  try {
    const response = await fetch(`${API_BASE}/api/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: confirmed ? 'Confirm tool execution' : 'Reject tool execution',
        mode: currentMode === 'auto' ? 'podcast' : currentMode,
        session_id: activeSessionId,
        action: 'tool_confirm',
        confirmation: {
          call_id: lastPendingConfirmation.call_id,
          confirmed: confirmed,
          tool_name: lastPendingConfirmation.tool_name
        }
      })
    });

    const elapsed = Math.round(performance.now() - startTime);
    traceTimer.textContent = `Latency: ${elapsed} ms`;

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    lastResponseData = data;
    renderResults(data);

  } catch (err) {
    alert(`Error sending tool confirmation: ${err.message}`);
  } finally {
    if (btnConfirmTool) btnConfirmTool.disabled = false;
    if (btnRejectTool) btnRejectTool.disabled = false;
  }
}

/**
 * Render output, telemetry steps, badge banner, artifacts, and tabs
 */
function renderResults(data) {
  const agentName = data.routed_agent || 'orchestrator';
  const meta = AGENT_META[agentName] || AGENT_META['orchestrator'];

  // Update Active Session ID
  activeSessionId = data.session_id || data.task_id || data.taskId || activeSessionId;
  if (sessionBadge && activeSessionId) {
    sessionBadge.style.display = 'inline-flex';
    sessionBadge.textContent = 'Session: ' + activeSessionId.substring(0, 16);
  }

  // 1. Highlight Top Agent Mini Card
  document.querySelectorAll('.agent-mini-card').forEach(c => c.classList.remove('active'));
  const targetCard = document.getElementById(meta.cardId);
  if (targetCard) targetCard.classList.add('active');

  // 2. Update Dynamic Agent Badge Banner
  agentBadgeBanner.style.display = 'flex';
  agentBadgeBanner.className = `agent-badge-banner ${meta.colorClass}`;
  agentBadgeIcon.textContent = meta.icon;
  agentBadgeTitle.textContent = `Routed Agent: ${meta.title}`;
  agentBadgeDesc.textContent = `A2A Endpoint: ${meta.endpoint} • Task ID: ${data.task_id || data.taskId || 'task_generated'}`;

  // 3. Update Engine Badge Pill
  executionEnginePill.style.display = 'inline-flex';
  if (data.execution_mode === 'live_gemini_success' || data.execution_mode === 'live_google_adk_success') {
    engineIcon.textContent = '🟢';
    engineText.textContent = `Live LLM (${data.model || 'Gemini'})`;
  } else if (data.execution_mode?.includes('billing_blocked')) {
    engineIcon.textContent = '🟡';
    engineText.textContent = `Real Agent (Billing Blocked on AI Studio)`;
    billingWarningCallout.style.display = 'block';
    billingWarningMsg.innerHTML = `
      <strong>Real Agent Invoked:</strong> The agent executed its live framework pipeline (Google ADK / LangChain). Google Gemini API returned <code>403 PERMISSION_DENIED</code> because the billing account has an outstanding balance.
      <br>To resolve: visit <a href="https://aistudio.google.com/billing" target="_blank" style="color:var(--g-blue);">Google AI Studio Billing</a> or click the API Key button in the header to update your key.
    `;
  } else {
    engineIcon.textContent = '⚙️';
    engineText.textContent = `Framework: ${data.model || 'Specialist Engine'}`;
  }

  // 4. Render Output Text
  outputRuntime.textContent = `State: ${data.state || 'COMPLETED'} • Duration: ${data.duration_ms} ms`;
  outputContent.innerHTML = formatOutputContent(data.output_text);

  // 5. Update HITL Review Gate Panel
  if (data.hitl_required && !data.audio_info) {
    if (hitlBox) hitlBox.style.display = 'block';
    if (hitlFeedbackContainer) hitlFeedbackContainer.style.display = 'none';
  } else {
    if (hitlBox) hitlBox.style.display = 'none';
  }

  // 6. Update Google ADK Native Tool Confirmation Gate
  if (data.tool_confirmation_required && data.tool_confirmation_details?.call_id && !data.audio_info) {
    if (toolConfirmBox) toolConfirmBox.style.display = 'block';
    lastPendingConfirmation = data.tool_confirmation_details;
    if (toolNameLabel) toolNameLabel.textContent = lastPendingConfirmation.tool_name || 'generate_podcast_audio';
    if (toolCallIdLabel) toolCallIdLabel.textContent = lastPendingConfirmation.call_id || '';
    if (toolConfirmHint && lastPendingConfirmation.hint) toolConfirmHint.textContent = lastPendingConfirmation.hint;
  } else {
    if (toolConfirmBox) toolConfirmBox.style.display = 'none';
  }

  // 7. Update Master Podcast Audio Player
  const audioObj = data.audio_info || (data.artifacts && data.artifacts.find(a => (a.metadata && (a.metadata.type === 'audio/mp3' || a.metadata.audio_url)))?.metadata);
  if (audioObj && (audioObj.url || audioObj.audio_url || audioObj.filename)) {
    const audioUrl = audioObj.url || audioObj.audio_url || `/audio/${audioObj.filename}`;
    if (audioPlayerBox) audioPlayerBox.style.display = 'block';
    if (audioEpisodeTitle) audioEpisodeTitle.textContent = `Episode Master Track: ${audioObj.filename || 'podcast_episode.mp3'}`;
    if (audioMetaText) audioMetaText.textContent = `File Size: ${audioObj.size_kb || 0} KB • Neural Multi-Speaker MP3 • Google ADK Pipeline`;
    if (masterAudioElement) {
      masterAudioElement.src = audioUrl;
      masterAudioElement.load();
    }
    if (audioDownloadBtn) {
      audioDownloadBtn.href = audioUrl;
      audioDownloadBtn.setAttribute('download', audioObj.filename || 'podcast_episode.mp3');
    }
  } else {
    if (audioPlayerBox) audioPlayerBox.style.display = 'none';
  }

  // 8. Render Artifacts if present
  if (data.artifacts && data.artifacts.length > 0) {
    artifactsSection.style.display = 'block';
    artifactsList.innerHTML = '';
    data.artifacts.forEach(art => {
      const pill = document.createElement('div');
      pill.className = 'artifact-pill';
      pill.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px;">
          <span>${art.metadata?.type === 'audio/mp3' ? '🎧' : '📦'}</span>
          <strong>${escapeHtml(art.name || 'Artifact')}</strong>
          <span style="color:var(--g-muted); font-size:0.75rem;">(${escapeHtml(art.type || 'Deliverable')})</span>
        </div>
        <span style="font-size:0.75rem; color:var(--g-blue); cursor:pointer;" onclick="viewArtifactContent('${encodeURIComponent(JSON.stringify(art))}')">Inspect ↗</span>
      `;
      artifactsList.appendChild(pill);
    });
  } else {
    artifactsSection.style.display = 'none';
  }

  // 9. Render Behind-the-Scenes Steps
  renderSteps(data.steps || []);

  // 10. Render Card Match Matrix
  renderMatrix(data.card_evaluations || []);

  // 11. Render Active Code Viewer Tab
  renderActiveTab();
}

/**
 * Format output text nicely
 */
function formatOutputContent(text) {
  if (!text) return '<span style="color:var(--g-muted);">(No text output returned)</span>';

  // If raw string representation of Event list is detected, extract clean text
  if (text.startsWith('[Event(') || text.includes('Event(model_version=')) {
    const textMatches = [...text.matchAll(/text=['"](.*?)['"]/g)];
    if (textMatches.length > 0) {
      text = textMatches.map(m => m[1].replace(/\\n/g, '\n')).join('\n\n');
    }
  }

  let escaped = escapeHtml(text);

  // Format Agent Section Dividers
  escaped = escaped.replace(/---/g, '<hr style="border:0; border-top:1px solid var(--g-border); margin:1.25rem 0;">');

  // Format Agent Headers
  escaped = escaped.replace(/(🎙️\s*&lt;strong&gt;Podcast Producer.*?&lt;\/strong&gt;|🔍\s*&lt;strong&gt;Research Agent.*?&lt;\/strong&gt;|✍️\s*&lt;strong&gt;Scriptwriter Agent.*?&lt;\/strong&gt;|🎧\s*&lt;strong&gt;Audio Producer Agent.*?&lt;\/strong&gt;)/g, '<div style="background:#f8f9fa; border-left:3px solid var(--g-blue); padding:6px 10px; border-radius:4px; margin:12px 0 8px; font-size:0.92rem;">$1</div>');

  // Format Bold & Italic markdown
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Format Headers
  escaped = escaped.replace(/^### (.*?)$/gm, '<h3 style="font-size:1.1rem; color:var(--g-dark); margin:0.8rem 0 0.4rem;">$1</h3>');
  escaped = escaped.replace(/^## (.*?)$/gm, '<h2 style="font-size:1.25rem; color:var(--g-dark); margin:1rem 0 0.5rem;">$1</h2>');
  escaped = escaped.replace(/^# (.*?)$/gm, '<h1 style="font-size:1.4rem; color:var(--g-dark); margin:1rem 0 0.6rem;">$1</h1>');

  // Format Bullet points
  escaped = escaped.replace(/^[•\*]\s+(.*?)$/gm, '<li style="margin-left:1.2rem;">$1</li>');

  // Format Speaker dialogue turns (Alex, Morgan, Taylor)
  escaped = escaped.replace(/&lt;strong&gt;Alex:&lt;\/strong&gt;/g, '<span style="display:inline-block; font-weight:700; color:#1a73e8; background:#e8f0fe; padding:2px 8px; border-radius:6px; margin-right:6px;">Alex (Host)</span>');
  escaped = escaped.replace(/&lt;strong&gt;Alex&lt;\/strong&gt;:/g, '<span style="display:inline-block; font-weight:700; color:#1a73e8; background:#e8f0fe; padding:2px 8px; border-radius:6px; margin-right:6px;">Alex (Host)</span>');

  escaped = escaped.replace(/&lt;strong&gt;Morgan:&lt;\/strong&gt;/g, '<span style="display:inline-block; font-weight:700; color:#1e8e3e; background:#e6f4ea; padding:2px 8px; border-radius:6px; margin-right:6px;">Morgan (Expert)</span>');
  escaped = escaped.replace(/&lt;strong&gt;Morgan&lt;\/strong&gt;:/g, '<span style="display:inline-block; font-weight:700; color:#1e8e3e; background:#e6f4ea; padding:2px 8px; border-radius:6px; margin-right:6px;">Morgan (Expert)</span>');

  escaped = escaped.replace(/&lt;strong&gt;Taylor:&lt;\/strong&gt;/g, '<span style="display:inline-block; font-weight:700; color:#8430ce; background:#f3e8fd; padding:2px 8px; border-radius:6px; margin-right:6px;">Taylor (Skeptic)</span>');
  escaped = escaped.replace(/&lt;strong&gt;Taylor&lt;\/strong&gt;:/g, '<span style="display:inline-block; font-weight:700; color:#8430ce; background:#f3e8fd; padding:2px 8px; border-radius:6px; margin-right:6px;">Taylor (Skeptic)</span>');

  // Line breaks
  escaped = escaped.replace(/\n\n/g, '<br><br>');
  escaped = escaped.replace(/\n/g, '<br>');

  return `<div style="line-height:1.65; font-size:0.92rem;">${escaped}</div>`;
}

/**
 * Render Card Match Matrix in Behind-the-Scenes
 */
function renderMatrix(candidates) {
  if (!matrixCardsList) return;
  if (!candidates || candidates.length === 0) {
    matrixCardsList.innerHTML = '<div style="color:var(--g-muted); font-size:0.8rem;">No card evaluations logged.</div>';
    return;
  }

  let html = '';
  candidates.forEach(c => {
    const isSelected = c.status?.includes('Selected');
    html += `
      <div class="matrix-card-item ${isSelected ? 'selected' : ''}">
        <div class="matrix-card-header">
          <div style="display:flex; align-items:center; gap:6px;">
            <span>${c.icon || '🏷️'}</span>
            <strong style="font-size:0.85rem; color:var(--g-dark);">${escapeHtml(c.name)}</strong>
          </div>
          <span style="font-size:0.75rem; font-weight:600; color:${isSelected ? 'var(--g-blue)' : 'var(--g-muted)'};">
            ${c.match_score}% Match ${isSelected ? '★ WINNER' : ''}
          </span>
        </div>
        <div class="matrix-bar-wrap">
          <div class="matrix-bar-fill" style="width:${c.match_score}%; background:${isSelected ? 'var(--g-blue)' : '#9aa0a6'};"></div>
        </div>
        <div style="font-size:0.76rem; color:var(--g-muted); margin-top:2px;">
          ${escapeHtml(c.reason || '')}
        </div>
      </div>
    `;
  });

  matrixCardsList.innerHTML = html;
}

/**
 * Render visual flow steps
 */
function renderSteps(steps) {
  flowStepsContainer.innerHTML = '';
  steps.forEach((stepStr, idx) => {
    const item = document.createElement('div');
    item.className = 'flow-step-item';
    
    let title = `Step ${idx + 1}`;
    let desc = stepStr;
    const colonIndex = stepStr.indexOf(':');
    if (colonIndex > -1 && colonIndex < 35) {
      title = stepStr.substring(0, colonIndex);
      desc = stepStr.substring(colonIndex + 1).trim();
    }

    item.innerHTML = `
      <div class="flow-step-icon">${idx + 1}</div>
      <div class="flow-step-text">
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(desc)}</p>
      </div>
    `;
    flowStepsContainer.appendChild(item);
  });
}

/**
 * Render telemetry active tab in code viewer
 */
function renderActiveTab() {
  if (currentTab === 'card-matrix') {
    matrixContainer.style.display = 'block';
    codeViewer.style.display = 'none';
    return;
  }

  matrixContainer.style.display = 'none';
  codeViewer.style.display = 'block';

  if (!lastResponseData) {
    codeViewer.textContent = '// Telemetry will display live JSON-RPC 2.0 payloads, Agent Cards, and lifecycle events here.';
    return;
  }

  let content = '';
  switch (currentTab) {
    case 'json-request':
      content = JSON.stringify(lastResponseData.jsonrpc_request || { note: 'No JSON-RPC request logged' }, null, 2);
      break;
    case 'json-response':
      content = JSON.stringify(lastResponseData.jsonrpc_response || { note: 'No JSON-RPC response logged' }, null, 2);
      break;
    case 'agent-card':
      content = JSON.stringify(lastResponseData.agent_card || { note: 'No agent card associated' }, null, 2);
      break;
    case 'trace-summary':
      content = JSON.stringify({
        task_id: lastResponseData.task_id || lastResponseData.taskId,
        query: lastResponseData.query,
        routed_agent: lastResponseData.routed_agent,
        mode: lastResponseData.mode,
        duration_ms: lastResponseData.duration_ms,
        execution_mode: lastResponseData.execution_mode,
        model: lastResponseData.model,
        llm_called: lastResponseData.llm_called,
        llm_error: lastResponseData.llm_error,
        state: lastResponseData.state,
        card_evaluations: lastResponseData.card_evaluations
      }, null, 2);
      break;
  }

  codeViewer.textContent = content;
}

/**
 * View artifact preview popup
 */
window.viewArtifactContent = function(encoded) {
  try {
    const art = JSON.parse(decodeURIComponent(encoded));
    alert(`Artifact: ${art.name}\nType: ${art.type}\n\nPreview:\n${art.preview || art.content || '(Empty)'}`);
  } catch (e) {
    console.error(e);
  }
};

/**
 * Utility escape HTML
 */
function escapeHtml(str) {
  if (typeof str !== 'string') return str;
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
