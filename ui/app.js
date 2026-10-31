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

// DOM Elements
const queryInput = document.getElementById('query-input');
const submitBtn = document.getElementById('submit-btn');
const outputContent = document.getElementById('output-content');
const outputRuntime = document.getElementById('output-runtime');
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
      body: JSON.stringify({ query: query, mode: currentMode })
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
 * Render output, telemetry steps, badge banner, artifacts, and tabs
 */
function renderResults(data) {
  const agentName = data.routed_agent || 'orchestrator';
  const meta = AGENT_META[agentName] || AGENT_META['orchestrator'];

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

  // 5. Render Artifacts if present
  if (data.artifacts && data.artifacts.length > 0) {
    artifactsSection.style.display = 'block';
    artifactsList.innerHTML = '';
    data.artifacts.forEach(art => {
      const pill = document.createElement('div');
      pill.className = 'artifact-pill';
      pill.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px;">
          <span>📦</span>
          <strong>${escapeHtml(art.name || 'Artifact')}</strong>
          <span style="color:var(--g-muted); font-size:0.75rem;">(${escapeHtml(art.type || 'text/plain')})</span>
        </div>
        <span style="font-size:0.75rem; color:var(--g-blue); cursor:pointer;" onclick="viewArtifactContent('${encodeURIComponent(JSON.stringify(art))}')">Inspect ↗</span>
      `;
      artifactsList.appendChild(pill);
    });
  } else {
    artifactsSection.style.display = 'none';
  }

  // 6. Render Behind-the-Scenes Steps
  renderSteps(data.steps || []);

  // 7. Render Card Match Matrix
  renderMatrix(data.card_evaluations || []);

  // 8. Render Active Code Viewer Tab
  renderActiveTab();
}

/**
 * Render Card Match Matrix in Behind-the-Scenes
 */
function renderMatrix(candidates) {
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
            <span>${c.icon}</span>
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
 * Format output text nicely
 */
function formatOutputContent(text) {
  if (!text) return '<span style="color:var(--g-muted);">(No text output returned)</span>';
  return escapeHtml(text);
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
