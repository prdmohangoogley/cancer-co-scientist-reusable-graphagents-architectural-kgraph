/**
 * Cancer Co-Scientist UI Client Entrypoint.
 * Adheres to:
 * - DOC-02: Zero Ambient Authority (ZAA) JWT token scoping
 * - DOC-03: Declarative A2UI protocol stack
 * - DOC-08: PAT-MEM-BANK enterprise context engineering
 * - DOC-09: Cloud Spanner ACID session persistence
 */

import { A2UIRenderer } from './a2ui-renderer.js';

// Constants
const API_BASE_URL = window.location.origin;
const STORAGE_JWT_KEY = 'ccs_zaa_jwt_token';
const STORAGE_USER_KEY = 'ccs_authenticated_user';









// Global State
let currentSessionId = 'sess_egfr_lung_default';
let sessionList = [];
let memoryBankState = {
  variants: [],
  biomarkers: [],
  hypotheses: [],
  cache_hit_rate_pct: 74.2,
};

// DOM References
const surfaceElement = document.getElementById('a2ui-surface');
const renderer = new A2UIRenderer(surfaceElement);

const inquiryForm = document.getElementById('inquiry-form');
const queryInput = document.getElementById('query-input');
const submitBtn = document.getElementById('submit-btn');
const chatTimeline = document.getElementById('chat-timeline');
const timelineEmptyState = document.getElementById('timeline-empty-state');
const workspaceScrollArea = document.getElementById('workspace-scroll-area');

// Top Nav & Auth Elements
const userProfileDiv = document.getElementById('user-profile');
const userUnauthDiv = document.getElementById('user-unauthenticated');
const userDisplayName = document.getElementById('user-display-name');
const userRoleBadge = document.getElementById('user-role-badge');
const btnOpenLogin = document.getElementById('btn-open-login');
const btnLogout = document.getElementById('btn-logout');

// Telemetry HUD Elements
const hudLatency = document.getElementById('hud-latency');
const hudTokens = document.getElementById('hud-tokens');

// Sidebar Sessions Elements
const sessionListContainer = document.getElementById('session-list');
const sessionCountSpan = document.getElementById('session-count');
const sessionSearchInput = document.getElementById('session-search');
const btnNewSession = document.getElementById('btn-new-session');

// Memory Bank Drawer Elements
const memoryBankDrawer = document.getElementById('memory-bank-drawer');
const drawerToggleBtn = document.getElementById('drawer-toggle-btn');
const drawerFloatingBtn = document.getElementById('drawer-floating-btn');
const activeVariantsList = document.getElementById('active-variants-list');
const activeBiomarkersList = document.getElementById('active-biomarkers-list');
const confirmedHypothesesList = document.getElementById('confirmed-hypotheses-list');
const countVariants = document.getElementById('count-variants');
const countBiomarkers = document.getElementById('count-biomarkers');
const countHypotheses = document.getElementById('count-hypotheses');
const metricCacheHit = document.getElementById('metric-cache-hit');

// Auth Modal Elements
const authModal = document.getElementById('auth-modal');
const authModalClose = document.getElementById('auth-modal-close');
const authForm = document.getElementById('auth-form');
const authEmail = document.getElementById('auth-email');
const authPassword = document.getElementById('auth-password');
const authRole = document.getElementById('auth-role');
const btnDemoLogin = document.getElementById('btn-demo-login');
const authMessage = document.getElementById('auth-message');
const tabLogin = document.getElementById('tab-login');
const tabRegister = document.getElementById('tab-register');
const btnPrimekgExplorer = document.getElementById('btn-primekg-explorer');
const btnTelemetryDashboard = document.getElementById('btn-telemetry-dashboard');
const telemetryModal = document.getElementById('telemetry-modal');
const telemetryModalClose = document.getElementById('telemetry-modal-close');
const btnCloseTelemetry = document.getElementById('btn-close-telemetry');

// -------------------------------------------------------------
// 1. Authentication & Token Management (DOC-02 ZAA)
// -------------------------------------------------------------

function getAuthToken(){
  return sessionStorage.getItem(STORAGE_JWT_KEY);
}

function getStoredUser(){
  const raw = sessionStorage.getItem(STORAGE_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setAuthToken(token, user){
  sessionStorage.setItem(STORAGE_JWT_KEY, token);
  sessionStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
  updateAuthUI();
}

function clearAuth(){
  sessionStorage.removeItem(STORAGE_JWT_KEY);
  sessionStorage.removeItem(STORAGE_USER_KEY);
  updateAuthUI();
  showAuthModal();
}

function updateAuthUI(){
  const token = getAuthToken();
  const user = getStoredUser();

  if (token && user) {
    userProfileDiv.style.display = 'flex';
    userUnauthDiv.style.display = 'none';
    userDisplayName.textContent = user.name || user.email;
    userRoleBadge.textContent = user.role || 'Clinician';
    hideAuthModal();
  } else {
    userProfileDiv.style.display = 'none';
    userUnauthDiv.style.display = 'block';
  }
}

function showAuthModal(){
  authModal.style.display = 'flex';
  authMessage.textContent = '';
  authMessage.className = 'auth-message';
}

function hideAuthModal(){
  authModal.style.display = 'none';
}

function getAuthHeaders(){
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// -------------------------------------------------------------
// 2. Multi-Turn Session Management (Spanner chat_sessions)
// -------------------------------------------------------------

async function fetchSessions(){
  try {
    const res = await fetch(`${API_BASE_URL}/api/sessions`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (res.ok) {
      sessionList = await res.json();
    } else {
      loadFallbackSessions();
    }
  } catch {
    loadFallbackSessions();
  }

  renderSessionList();
}

function loadFallbackSessions(){
  sessionList = [
    {
      session_id: 'sess_egfr_lung_default',
      title: 'EGFR T790M Resistance & 3rd-Gen TKIs',
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
      last_active_at: new Date(Date.now() - 60000 * 15).toISOString(),
      message_count: 4,
    },
    {
      session_id: 'sess_tp53_ovarian',
      title: 'TP53 HRD Synthetic Lethality in HGSOC',
      created_at: new Date(Date.now() - 86400000).toISOString(),
      last_active_at: new Date(Date.now() - 86400000).toISOString(),
      message_count: 2,
    },
    {
      session_id: 'sess_kras_pancreatic',
      title: 'KRAS G12D Bypass Traversal in PDAC',
      created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
      last_active_at: new Date(Date.now() - 86400000 * 2).toISOString(),
      message_count: 3,
    },
  ];
}

function renderSessionList(filterQuery = ''){
  sessionListContainer.innerHTML = '';

  const filtered = sessionList.filter((s) =>
    s.title.toLowerCase().includes(filterQuery.toLowerCase())
  );

  sessionCountSpan.textContent = `${filtered.length}`;

  for (const session of filtered) {
    const item = document.createElement('div');
    const isActive = session.session_id === currentSessionId;
    item.className = `session-item ${isActive ? 'active' : ''}`;
    item.dataset.sessionId = session.session_id;

    const titleDiv = document.createElement('div');
    titleDiv.className = 'session-item-title';
    titleDiv.textContent = session.title;
    item.appendChild(titleDiv);

    const metaDiv = document.createElement('div');
    metaDiv.className = 'session-item-meta';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'session-item-time';
    const dateObj = new Date(session.last_active_at || session.created_at);
    timeSpan.textContent = dateObj.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    metaDiv.appendChild(timeSpan);

    const countBadge = document.createElement('span');
    countBadge.className = 'session-msg-badge';
    countBadge.textContent = `${session.message_count || 1} turns`;
    metaDiv.appendChild(countBadge);

    item.appendChild(metaDiv);

    item.addEventListener('click', () => {
      switchSession(session.session_id);
    });

    sessionListContainer.appendChild(item);
  }
}

function switchSession(sessionId){
  currentSessionId = sessionId;
  renderSessionList(sessionSearchInput.value);

  // Clear timeline and surface
  chatTimeline.innerHTML = '';
  surfaceElement.innerHTML = '';

  const activeSession = sessionList.find((s) => s.session_id === sessionId);
  if (activeSession) {
    // Render initial context turn
    appendChatBubble('user', `Reviewing clinical context for: ${activeSession.title}`);
    appendChatBubble('assistant', `Session synchronized with Cloud Spanner (session_id: ${sessionId}). Active Memory Bank context loaded.`);
  }

  // Sync memory bank and telemetry
  syncMemoryBank(currentSessionId);
  syncTelemetryHUD();
}

function createNewSession(){
  const newId = `sess_${Date.now().toString(36)}`;
  const newSession = {
    session_id: newId,
    title: 'New Clinical Case Inquiry',
    created_at: new Date().toISOString(),
    last_active_at: new Date().toISOString(),
    message_count: 0,
  };

  sessionList.unshift(newSession);
  switchSession(newId);
}

// -------------------------------------------------------------
// 3. Conversation Timeline & Inquiry Execution
// -------------------------------------------------------------

function appendChatBubble(role, text){
  if (timelineEmptyState && timelineEmptyState.parentElement) {
    timelineEmptyState.remove();
  }

  const row = document.createElement('div');
  row.className = `chat-bubble-row ${role}`;

  const avatar = document.createElement('div');
  avatar.className = `chat-avatar ${role}`;
  avatar.textContent = role === 'user' ? '🩺' : '🤖';
  row.appendChild(avatar);

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  const header = document.createElement('div');
  header.className = 'bubble-header';
  const roleName = document.createElement('span');
  roleName.className = 'bubble-author';
  roleName.textContent = role === 'user' ? 'Attending Clinician' : 'Cancer Co-Scientist Agent';
  header.appendChild(roleName);

  const time = document.createElement('span');
  time.className = 'bubble-time';
  time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  header.appendChild(time);
  bubble.appendChild(header);

  const body = document.createElement('div');
  body.className = 'bubble-body';
  body.textContent = text;
  bubble.appendChild(body);

  row.appendChild(bubble);
  chatTimeline.appendChild(row);

  scrollToBottom();
  return row;
}

function scrollToBottom(){
  workspaceScrollArea.scrollTop = workspaceScrollArea.scrollHeight;
}

async function executeInquiry(query){
  // Check auth
  if (!getAuthToken()) {
    showAuthModal();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Traversing Graph...';

  // 1. Append user inquiry turn
  appendChatBubble('user', query);

  // 2. Append temporary assistant waiting indicator
  const pendingBubbleRow = appendChatBubble('assistant', 'Consulting PrimeKG Graph, Cloud Spanner & Guidelines MCP...');

  // Update session stats
  const activeSession = sessionList.find((s) => s.session_id === currentSessionId);
  if (activeSession) {
    activeSession.message_count += 1;
    activeSession.last_active_at = new Date().toISOString();
    if (activeSession.title === 'New Clinical Case Inquiry') {
      activeSession.title = query.length > 40 ? `${query.substring(0, 37)}...` : query;
    }
    renderSessionList(sessionSearchInput.value);
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        query,
        session_id: currentSessionId,
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearAuth();
        throw new Error('Authentication expired or unauthorized (DOC-02)');
      }
      throw new Error(`Server returned status ${response.status}`);
    }

    const payload = await response.json();

    // Replace pending text
    const bubbleBody = pendingBubbleRow.querySelector('.bubble-body');
    if (bubbleBody) {
      bubbleBody.textContent = `Completed multi-hop traversal (${payload.intent || 'CLINICAL_ANALYSIS'}). Emitted certified A2UI declarative surface.`;
    }

    // Render A2UI surface
    renderer.renderSurface(payload);
  } catch (err) {
    console.warn('Backend unavailable, rendering local sample A2UI payload:', err);
    const bubbleBody = pendingBubbleRow.querySelector('.bubble-body');
    if (bubbleBody) {
      bubbleBody.textContent = 'Synthesized precision oncology response using local PrimeKG fallback catalog.';
    }
    renderFallbackPayload(query);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Analyze Graph';
    scrollToBottom();

    // Live sync Memory Bank and Telemetry
    await syncMemoryBank(currentSessionId, query);
    await syncTelemetryHUD();
  }
}

// -------------------------------------------------------------
// 4. Memory Bank Live Sync (PAT-MEM-BANK - DOC-08)
// -------------------------------------------------------------

async function syncMemoryBank(sessionId, latestQuery = ''){
  try {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/memory`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (res.ok) {
      memoryBankState = await res.json();
    } else {
      updateLocalMemoryBank(latestQuery);
    }
  } catch {
    updateLocalMemoryBank(latestQuery);
  }

  renderMemoryBankDrawer();
}

function updateLocalMemoryBank(query){
  const q = query.toLowerCase();

  // Dynamically consolidate entities based on conversation query
  if (q.includes('egfr') || q.includes('nsclc') || q.includes('osimertinib') || q.includes('t790m')) {
    memoryBankState.variants = [
      { name: 'p.T790M (Exon 20)', gene: 'EGFR', significance: 'Gatekeeper Resistance Mutation' },
      { name: 'p.E746_A750del', gene: 'EGFR', significance: 'Activating Deletion' },
      { name: 'p.C797S (Exon 20)', gene: 'EGFR', significance: 'Tertiary Resistance Risk' },
    ];
    memoryBankState.biomarkers = [
      { name: 'EGFR Sensitizing Mutations', status: 'Positive', evidence: 'cfDNA NGS (Tier 1A)' },
      { name: 'MET Amplification Bypass', status: 'Surveillance Active', evidence: 'FISH Probe (Tier 2B)' },
      { name: 'PD-L1 Expression (TPS)', status: 'Low (<1%)', evidence: 'IHC 22C3' },
    ];
    memoryBankState.hypotheses = [
      {
        id: 'hyp_01',
        statement: 'Osimertinib achieves durable response despite T790M gatekeeper hindrance through irreversible cysteine covalent bond.',
        status: 'confirmed',
      },
      {
        id: 'hyp_02',
        statement: 'Emergence of MET amplification bypass signaling can be countered with dual Osimertinib + Savolitinib.',
        status: 'formulated',
      },
    ];
  } else if (q.includes('tp53') || q.includes('ovarian') || q.includes('parp')) {
    memoryBankState.variants = [
      { name: 'p.R273H (DNA Binding)', gene: 'TP53', significance: 'Loss-of-Function Driver' },
      { name: 'c.5266dupC', gene: 'BRCA1', significance: 'Homologous Recombination Defect' },
    ];
    memoryBankState.biomarkers = [
      { name: 'Homologous Recombination Deficiency (HRD)', status: 'Score: 68 (High)', evidence: 'Genomic Instability Assay' },
      { name: 'CA-125 Serum Antigen', status: 'Elevated (145 U/mL)', evidence: 'EHR Lab Trajectory' },
    ];
    memoryBankState.hypotheses = [
      {
        id: 'hyp_03',
        statement: 'PARP inhibitor trapping induces catastrophic synthetic lethality in double-strand break repair deficient serous carcinoma.',
        status: 'confirmed',
      },
    ];
  } else {
    // Default baseline state
    if (memoryBankState.variants.length === 0) {
      memoryBankState.variants = [
        { name: 'p.T790M', gene: 'EGFR', significance: 'Secondary Resistance' },
        { name: 'p.R273H', gene: 'TP53', significance: 'Dominant Negative' },
      ];
      memoryBankState.biomarkers = [
        { name: 'EGFR Kinase Domain Activation', status: 'Positive', evidence: 'NGS Panel' },
        { name: 'Tumor Mutational Burden (TMB)', status: '8.4 mut/Mb (Intermediate)', evidence: 'FoundationOne' },
      ];
      memoryBankState.hypotheses = [
        {
          id: 'hyp_00',
          statement: 'Targeted kinase inhibition suppresses primary pathway signaling cascade with confirmed in vitro affinity.',
          status: 'confirmed',
        },
      ];
    }
  }

  memoryBankState.cache_hit_rate_pct = 76.5;
}

function renderMemoryBankDrawer(){
  // 1. Variants
  activeVariantsList.innerHTML = '';
  countVariants.textContent = `${memoryBankState.variants.length}`;

  if (memoryBankState.variants.length === 0) {
    activeVariantsList.innerHTML = '<div class="memory-empty">No active genomic variants consolidated.</div>';
  } else {
    for (const v of memoryBankState.variants) {
      const tile = document.createElement('div');
      tile.className = 'memory-tile variant';

      const row = document.createElement('div');
      row.className = 'tile-header-row';

      const geneBadge = document.createElement('span');
      geneBadge.className = 'gene-pill';
      geneBadge.textContent = v.gene;
      row.appendChild(geneBadge);

      const varName = document.createElement('strong');
      varName.className = 'var-name';
      varName.textContent = v.name;
      row.appendChild(varName);
      tile.appendChild(row);

      const sig = document.createElement('div');
      sig.className = 'tile-sub';
      sig.textContent = v.significance;
      tile.appendChild(sig);

      activeVariantsList.appendChild(tile);
    }
  }

  // 2. Biomarkers
  activeBiomarkersList.innerHTML = '';
  countBiomarkers.textContent = `${memoryBankState.biomarkers.length}`;

  if (memoryBankState.biomarkers.length === 0) {
    activeBiomarkersList.innerHTML = '<div class="memory-empty">No target biomarkers active.</div>';
  } else {
    for (const b of memoryBankState.biomarkers) {
      const tile = document.createElement('div');
      tile.className = 'memory-tile biomarker';

      const name = document.createElement('div');
      name.className = 'tile-main-title';
      name.textContent = b.name;
      tile.appendChild(name);

      const status = document.createElement('div');
      status.className = 'tile-status-tag';
      status.textContent = `Status: ${b.status} • ${b.evidence}`;
      tile.appendChild(status);

      activeBiomarkersList.appendChild(tile);
    }
  }

  // 3. Hypotheses
  confirmedHypothesesList.innerHTML = '';
  const confirmedOnly = memoryBankState.hypotheses.filter((h) => h.status === 'confirmed');
  countHypotheses.textContent = `${confirmedOnly.length}`;

  if (memoryBankState.hypotheses.length === 0) {
    confirmedHypothesesList.innerHTML = '<div class="memory-empty">No hypotheses consolidated yet.</div>';
  } else {
    for (const h of memoryBankState.hypotheses) {
      const tile = document.createElement('div');
      tile.className = `memory-tile hypothesis ${h.status}`;

      const badge = document.createElement('span');
      badge.className = `hyp-badge ${h.status}`;
      badge.textContent = h.status.toUpperCase();
      tile.appendChild(badge);

      const statement = document.createElement('div');
      statement.className = 'hyp-statement-text';
      statement.textContent = h.statement;
      tile.appendChild(statement);

      confirmedHypothesesList.appendChild(tile);
    }
  }

  // 4. Recall Metrics
  metricCacheHit.textContent = `${memoryBankState.cache_hit_rate_pct.toFixed(1)}%`;
}

// -------------------------------------------------------------
// 5. Telemetry HUD Sync
// -------------------------------------------------------------

async function syncTelemetryHUD(){
  try {
    const res = await fetch(`${API_BASE_URL}/api/stats/telemetry`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (res.ok) {
      const stats = await res.json();
      hudLatency.textContent = `p50: ${stats.p50_latency_ms}ms • p95: ${stats.p95_latency_ms}ms`;
      hudTokens.textContent = `${stats.prompt_tokens.toLocaleString()} p • ${stats.completion_tokens.toLocaleString()} c • ${stats.cached_tokens.toLocaleString()} cached`;
      return;
    }
  } catch {
    // Graceful fallback
  }

  hudLatency.textContent = 'p50: -- • p95: --';
  hudTokens.textContent = '0 p • 0 c • 0 cached';
}

// -------------------------------------------------------------
// 6. Fallback A2UI Payload Generation
// -------------------------------------------------------------

function renderFallbackPayload(query){
  const q = query.toLowerCase();

  // Route 1: Docking & Simulation
  if (q.includes('simulation') || q.includes('docking') || q.includes('alphafold') || q.includes('trajectory')) {
    const simPayload = {
      type: 'A2UI_SURFACE',
      surface_id: 'surf_sim_docking_fb',
      intent: 'MOLECULAR_SIMULATION',
      guidelines_cited: ['DOC-03', 'DOC-02'],
      components: [
        {
          component: 'SimulationViewer',
          id: 'sim_viewer_fb',
          props: {
            simulation_id: 'sim_alphafold_docking_osimertinib_790m',
            title: 'AlphaFold-Multimer & OMPL Docking Trajectory: Osimertinib vs. EGFR T790M',
            simulation_type: 'AlphaFold_Docking_OMPL',
            target_protein: 'EGFR Kinase Domain (p.T790M mutant)',
            ligand_name: 'Osimertinib (AZD9291)',
            trajectory_frames: 250,
            current_frame: 180,
            metrics: {
              binding_affinity_kcal_mol: -9.42,
              rmsd_angstrom: 1.18,
              clash_score: 0.04,
              cell_density_confluence_pct: 88.5,
            },
            view_config: {
              camera_preset: 'binding_pocket',
              render_style: 'surface',
              color_scheme: 'hydrophobicity',
            },
            trajectory_data_url: '/api/simulations/sim_alphafold_docking_osimertinib_790m/trajectory.bin',
          },
        },
        {
          component: 'ToxicityWarning',
          id: 'tox_warning_fb',
          props: {
            drug_name: 'Osimertinib',
            severity: 'high',
            warning_type: 'Contraindication',
            message: 'Risk of QTc interval prolongation, cardiomyopathy, and interstitial lung disease (ILD) / pneumonitis. Concomitant use with strong CYP3A4 inducers or QT-prolonging agents significantly increases toxicity.',
            contraindicated_conditions: [
              'Baseline QTc interval > 470 ms',
              'Pre-existing interstitial lung disease',
              'Severe hepatic impairment (Child-Pugh C)',
            ],
            interacting_drugs: [
              'Rifampin (Strong CYP3A4 Inducer)',
              'Amiodarone (QTc Prolongation)',
              'Clarithromycin (CYP3A4 Inhibitor)',
            ],
            adverse_effects: [
              { effect: 'Interstitial Lung Disease / Pneumonitis', frequency: '3.3%', severity: 'Grade 3-4 (Fatal in 0.4%)' },
              { effect: 'QTc Interval Prolongation', frequency: '4.9%', severity: 'Grade 3 (0.9%)' },
              { effect: 'Left Ventricular Dysfunction / Cardiomyopathy', frequency: '2.4%', severity: 'Grade 3' },
              { effect: 'Diarrhea and Cutaneous Rash', frequency: '58%', severity: 'Grade 1-2' },
            ],
            clinical_recommendation: 'Obtain baseline 12-lead ECG and echocardiogram (LVEF). Withhold treatment if QTc exceeds 500 ms or if acute onset of unexplained dyspnea occurs.',
          },
        },
      ],
    };
    renderer.renderSurface(simPayload);
    return;
  }

  // Route 2: Memory Timeline Review
  if (q.includes('timeline') || q.includes('longitudinal') || q.includes('history') || q.includes('memory')) {
    const memoryPayload = {
      type: 'A2UI_SURFACE',
      surface_id: 'surf_memory_timeline_fb',
      intent: 'LONG_TERM_MEMORY_RECALL',
      guidelines_cited: ['DOC-08', 'DOC-03', 'DOC-09'],
      components: [
        {
          component: 'InsightCard',
          id: 'card_mem_fb',
          props: {
            title: 'Longitudinal Patient Oncology State (PAT-MEM-BANK)',
            subtitle: 'Spanner ACID Session Persistence • Progressive Recall Active',
            severity: 'info',
            summary: 'Consolidated multi-turn clinical facts for Patient PAT-9821. Tracked primary resistance evolution from Gefitinib to Osimertinib and prospective bypass surveillance.',
            confidence_score: 0.97,
            tags: ['PAT-MEM-BANK', 'EGFR', 'T790M', 'Osimertinib', 'MET'],
          },
        },
        {
          component: 'MemoryTimeline',
          id: 'timeline_egfr_fb',
          props: {
            title: 'Clinical Entity & Hypothesis Evolution Across Turns',
            session_id: currentSessionId,
            total_turns: 3,
            active_biomarkers: ['EGFR exon 19 del', 'EGFR T790M', 'MET amplification', 'TP53 R273H'],
            confirmed_hypotheses_count: 2,
            turns: [
              {
                turn_number: 1,
                timestamp: new Date(Date.now() - 3600000).toISOString(),
                user_query: 'Evaluate primary resistance drivers in stage IV lung adenocarcinoma with initial response to Gefitinib',
                extracted_entities: [
                  { name: 'EGFR', type: 'Gene', confidence: 0.99 },
                  { name: 'Gefitinib', type: 'Drug', confidence: 0.98 },
                  { name: 'Lung Adenocarcinoma', type: 'Disease', confidence: 0.97 },
                ],
                hypotheses: [
                  { id: 'hyp_01', statement: 'Disease progression mediated by secondary gatekeeper mutation T790M', status: 'formulated', confidence: 0.88 },
                ],
                summary: 'Identified primary 1st-generation EGFR TKI treatment history and flagged potential gatekeeper resistance mutation emergence.',
              },
              {
                turn_number: 2,
                timestamp: new Date(Date.now() - 1800000).toISOString(),
                user_query: 'Confirm presence of T790M mutation and identify next-line therapeutic strategy',
                extracted_entities: [
                  { name: 'EGFR T790M', type: 'Variant', confidence: 0.99 },
                  { name: 'Osimertinib', type: 'Drug', confidence: 0.98 },
                ],
                hypotheses: [
                  { id: 'hyp_01', statement: 'Disease progression mediated by secondary gatekeeper mutation T790M', status: 'confirmed', confidence: 0.97 },
                  { id: 'hyp_02', statement: 'Osimertinib 3rd-generation covalent binding restores kinase inhibition despite T790M steric hindrance', status: 'confirmed', confidence: 0.96 },
                ],
                summary: 'Biopsy and cfDNA NGS confirmed EGFR T790M. Third-generation irreversible TKI Osimertinib indicated second-line therapy.',
              },
              {
                turn_number: 3,
                timestamp: new Date().toISOString(),
                user_query: 'Investigate potential tertiary resistance mechanisms (e.g. C797S or MET bypass) after prolonged Osimertinib',
                extracted_entities: [
                  { name: 'EGFR C797S', type: 'Variant', confidence: 0.95 },
                  { name: 'MET', type: 'Gene', confidence: 0.93 },
                  { name: 'Savolitinib', type: 'Drug', confidence: 0.89 },
                ],
                hypotheses: [
                  { id: 'hyp_03', statement: 'Tertiary resistance may emerge via MET amplification bypass pathway, amenable to Osimertinib + MET inhibitor combination', status: 'testing', confidence: 0.82 },
                ],
                summary: 'Formulated prospective hypothesis for MET amplification bypass signaling; recommended dual-target surveillance.',
              },
            ],
          },
        },
      ],
    };
    renderer.renderSurface(memoryPayload);
    return;
  }

  // Route 3: Drug Repurposing Table
  const isDrugQuery = q.includes('drug') || q.includes('therap') || q.includes('repurpos');
  if (isDrugQuery) {
    const drugPayload = {
      type: 'A2UI_SURFACE',
      surface_id: 'surf_drug_repurposing_fb',
      intent: 'DRUG_REPURPOSING',
      guidelines_cited: ['DOC-03', 'DOC-02'],
      components: [
        {
          component: 'InsightCard',
          id: 'card_drug_fb',
          props: {
            title: `Therapeutic Candidates: ${query}`,
            subtitle: 'Synthesized via PrimeKG Multi-Hop Traversal',
            severity: 'critical',
            summary: 'Identified approved and investigational compounds targeting dysregulated signaling nodes with validated clinical phase evidence.',
            confidence_score: 0.95,
            tags: ['Drug Repurposing', 'Targeted Therapy', 'PrimeKG'],
          },
        },
        {
          component: 'DrugRepurposingTable',
          id: 'table_drug_fb',
          props: {
            title: 'Top Ranked Repurposing Candidates',
            candidates: [
              {
                drug_id: 'DRUGBANK:DB12683',
                drug_name: 'Osimertinib',
                target_gene: 'EGFR (p.T790M)',
                clinical_phase: 'Phase 4 / Approved',
                mechanism: 'Irreversible 3rd-generation covalent TKI',
                confidence: 0.98,
              },
              {
                drug_id: 'DRUGBANK:DB00530',
                drug_name: 'Erlotinib',
                target_gene: 'EGFR (Sensitizing)',
                clinical_phase: 'Phase 4 / Approved',
                mechanism: '1st-generation reversible EGFR TKI',
                confidence: 0.92,
              },
              {
                drug_id: 'DRUGBANK:DB11977',
                drug_name: 'Savolitinib',
                target_gene: 'MET Kinase',
                clinical_phase: 'Phase 3 / Investigational',
                mechanism: 'Selective small molecule MET inhibitor',
                confidence: 0.89,
              },
            ],
          },
        },
      ],
    };
    renderer.renderSurface(drugPayload);
    return;
  }

  // Route 4: Pathway Traversal and Knowledge Graph
  const pathwayPayload = {
    type: 'A2UI_SURFACE',
    surface_id: 'surf_pathway_fb',
    intent: 'PATHWAY_ANALYSIS',
    guidelines_cited: ['DOC-03', 'DOC-01'],
    components: [
      {
        component: 'InsightCard',
        id: 'card_pathway_fb',
        props: {
          title: `Biomedical Graph Analysis: ${query}`,
          subtitle: 'Multi-Hop PrimeKG Knowledge Traversal',
          severity: 'info',
          summary: 'Resolved disease-gene-pathway cascades. Identified central dysregulated hub nodes and actionable molecular targets.',
          confidence_score: 0.96,
          tags: ['Pathway Analysis', 'PrimeKG', 'A2UI'],
        },
      },
      {
        component: 'PathwayChart',
        id: 'chart_pathway_fb',
        props: {
          pathway_id: 'REACTOME:R-HSA-177929',
          pathway_name: 'EGFR Signaling and Downstream MAPK/AKT Cascade',
          dysregulation_status: 'mutated',
          genes_involved: ['EGFR', 'GRB2', 'SOS1', 'KRAS', 'BRAF', 'MAP2K1', 'MAPK1'],
          targetable_nodes: ['EGFR', 'KRAS', 'BRAF', 'MAP2K1'],
        },
      },
      {
        component: 'KnowledgeGraphView',
        id: 'kg_view_fb',
        props: {
          layout: 'force-directed',
          nodes: [
            { id: 'NCBI:1956', label: 'Gene', name: 'EGFR', properties: { role: 'Kinase Receptor' } },
            { id: 'MONDO:0005070', label: 'Disease', name: 'Non-small cell lung carcinoma', properties: { tier: 'Primary' } },
            { id: 'DRUGBANK:DB12683', label: 'Drug', name: 'Osimertinib', properties: { role: 'Inhibitor' } },
            { id: 'REACTOME:R-HSA-177929', label: 'Pathway', name: 'Signaling by EGFR', properties: {} },
            { id: 'NCBI:3845', label: 'Gene', name: 'KRAS', properties: { role: 'GTPase' } },
          ],
          edges: [
            { source_id: 'NCBI:1956', target_id: 'MONDO:0005070', relationship: 'ASSOCIATED_WITH', confidence: 0.99 },
            { source_id: 'DRUGBANK:DB12683', target_id: 'NCBI:1956', relationship: 'TARGETS', confidence: 0.98 },
            { source_id: 'NCBI:1956', target_id: 'REACTOME:R-HSA-177929', relationship: 'PART_OF_PATHWAY', confidence: 0.96 },
            { source_id: 'NCBI:1956', target_id: 'NCBI:3845', relationship: 'INTERACTS_WITH', confidence: 0.94 },
          ],
        },
      },
    ],
  };

  renderer.renderSurface(pathwayPayload);
}

// -------------------------------------------------------------
// 7. Event Listeners & Bootstrapping
// -------------------------------------------------------------

function initEventListeners(){
  // Inquiry form submit
  inquiryForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    queryInput.value = '';
    await executeInquiry(query);
  });

  // Quick prompt chips
  document.querySelectorAll('.chip-prompt').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const promptQuery = (btn).dataset.query;
      if (promptQuery) {
        await executeInquiry(promptQuery);
      }
    });
  });

  // Session search filtering
  sessionSearchInput?.addEventListener('input', () => {
    renderSessionList(sessionSearchInput.value);
  });

  // New session button
  btnNewSession?.addEventListener('click', () => {
    createNewSession();
  });

  // Drawer Toggle buttons
  drawerToggleBtn?.addEventListener('click', () => {
    memoryBankDrawer.classList.add('collapsed');
    drawerFloatingBtn.style.display = 'block';
  });

  drawerFloatingBtn?.addEventListener('click', () => {
    memoryBankDrawer.classList.remove('collapsed');
    drawerFloatingBtn.style.display = 'none';
  });

  // Auth UI triggers
  btnOpenLogin?.addEventListener('click', () => {
    showAuthModal();
  });

  btnLogout?.addEventListener('click', () => {
    clearAuth();
  });

  // PrimeKG Explorer Action
  btnPrimekgExplorer?.addEventListener('click', async () => {
    try {
      btnPrimekgExplorer.textContent = '⏳ Loading PrimeKG...';
      btnPrimekgExplorer.disabled = true;

      const resp = await fetch(`${API_BASE_URL}/api/primekg/explore?focal_entity=EGFR&depth=2`);
      if (!resp.ok) {
        throw new Error(`HTTP error ${resp.status}`);
      }
      const payload = await resp.json();

      // Render into A2UI Surface in the main workspace
      renderer.renderSurface(payload);

      // Add conversational bubble in chat timeline
      appendChatBubble(
        'assistant',
        '🧬 PrimeKG Property Graph loaded into workspace! Visualizing 360° topology around EGFR from Cloud Spanner (11 entities across Genes, Drugs, Diseases, Pathways). You can zoom, pan, drag nodes, and click on nodes to inspect target details.'
      );

      // Smooth scroll to canvas
      surfaceElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      console.error('Failed to load PrimeKG Explorer:', err);
      alert('Failed to load PrimeKG Explorer: ' + err.message);
    } finally {
      btnPrimekgExplorer.textContent = '🧬 PrimeKG Explorer';
      btnPrimekgExplorer.disabled = false;
    }
  });

  // Welcome banner direct cards
  const cardPrimekg = document.getElementById('card-launch-primekg');
  const cardTelemetry = document.getElementById('card-launch-telemetry');
  cardPrimekg?.addEventListener('click', () => btnPrimekgExplorer?.click());
  cardTelemetry?.addEventListener('click', () => btnTelemetryDashboard?.click());

  // Observability & Telemetry Dashboard Modal
  btnTelemetryDashboard?.addEventListener('click', async () => {
    telemetryModal.style.display = 'flex';
    try {
      const resp = await fetch(`${API_BASE_URL}/api/stats/telemetry`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.latency_ms) {
          const p50El = document.getElementById('obs-p50');
          const p95El = document.getElementById('obs-p95');
          const p99El = document.getElementById('obs-p99');
          const avgEl = document.getElementById('obs-avg');
          if (p50El) p50El.textContent = `${data.latency_ms.p50} ms`;
          if (p95El) p95El.textContent = `${data.latency_ms.p95} ms`;
          if (p99El) p99El.textContent = `${data.latency_ms.p99} ms`;
          if (avgEl) avgEl.textContent = `${data.latency_ms.avg} ms`;
        }
        if (data.token_consumption) {
          const ptEl = document.getElementById('obs-prompt-tokens');
          const ctEl = document.getElementById('obs-completion-tokens');
          const cktEl = document.getElementById('obs-cached-tokens');
          const crEl = document.getElementById('obs-cache-rate');
          if (ptEl) ptEl.textContent = data.token_consumption.prompt_tokens.toLocaleString();
          if (ctEl) ctEl.textContent = data.token_consumption.completion_tokens.toLocaleString();
          if (cktEl) cktEl.textContent = data.token_consumption.cached_tokens.toLocaleString();
          if (crEl) crEl.textContent = `${(data.token_consumption.cache_hit_rate * 100).toFixed(1)}%`;
        }
        if (data.quality_metrics) {
          const acEl = document.getElementById('obs-algo-choice');
          const mapEl = document.getElementById('obs-map');
          const precEl = document.getElementById('obs-precision');
          const recEl = document.getElementById('obs-recall');
          if (acEl) acEl.textContent = `${(data.quality_metrics.algorithm_choice_accuracy * 100).toFixed(1)}%`;
          if (mapEl) mapEl.textContent = `${data.quality_metrics.retrieval_map}`;
          if (precEl) precEl.textContent = `${data.quality_metrics.precision_at_k}`;
          if (recEl) recEl.textContent = `${data.quality_metrics.recall_at_k}`;
        }
      }
    } catch (err) {
      console.error('Failed to refresh telemetry:', err);
    }
  });

  telemetryModalClose?.addEventListener('click', () => {
    telemetryModal.style.display = 'none';
  });

  btnCloseTelemetry?.addEventListener('click', () => {
    telemetryModal.style.display = 'none';
  });

  telemetryModal?.addEventListener('click', (e) => {
    if (e.target === telemetryModal) {
      telemetryModal.style.display = 'none';
    }
  });

  authModalClose?.addEventListener('click', () => {
    hideAuthModal();
  });

  // Auth tabs
  tabLogin?.addEventListener('click', () => {
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    const authSubmit = document.getElementById('auth-submit-btn');
    if (authSubmit) authSubmit.textContent = 'Authenticate (ZAA JWT)';
  });

  tabRegister?.addEventListener('click', () => {
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    const authSubmit = document.getElementById('auth-submit-btn');
    if (authSubmit) authSubmit.textContent = 'Register Clinical Access';
  });

  // Auth form submit
  authForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const isRegister = tabRegister?.classList.contains('active');
    const email = authEmail.value.trim();
    const password = authPassword.value;
    const role = authRole.value;

    authMessage.textContent = isRegister ? 'Registering clinical profile...' : 'Authenticating against Google Cloud Identity...';
    authMessage.className = 'auth-message info';

    try {
      const endpoint = isRegister ? `${API_BASE_URL}/api/auth/register` : `${API_BASE_URL}/api/auth/login`;
      const body = isRegister
        ? { email, password, full_name: `Dr. ${email.split('@')[0]}`, roles: [role.toLowerCase()] }
        : { email, password };

      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (resp.ok) {
        const data = await resp.json();
        setAuthToken(data.access_token, {
          email: data.user.email,
          name: data.user.full_name || email,
          role: (data.user.roles && data.user.roles[0]) ? (data.user.roles[0].charAt(0).toUpperCase() + data.user.roles[0].slice(1)) : 'Clinician',
          institution: 'Memorial Sloan Kettering Cancer Center',
        });
        authMessage.textContent = isRegister ? 'Registered and authenticated!' : 'Authenticated successfully!';
        authMessage.className = 'auth-message success';
        setTimeout(() => hideAuthModal(), 500);
        return;
      } else {
        const err = await resp.json().catch(() => ({}));
        authMessage.textContent = err.detail || 'Authentication failed. Please verify credentials.';
        authMessage.className = 'auth-message error';
        return;
      }
    } catch {
      // Backend offline fallback
      const token = `zaa_jwt_${Date.now()}_${Math.random().toString(36).substring(2)}`;
      const nameParts = email.split('@')[0].split('.');
      const formattedName = nameParts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');

      const user = {
        email,
        name: formattedName ? `Dr. ${formattedName}` : 'Dr. Attending Oncologist',
        role,
        institution: 'Memorial Sloan Kettering Cancer Center',
      };

      setAuthToken(token, user);
      authMessage.textContent = 'Authenticated via local ZAA session!';
      authMessage.className = 'auth-message success';
      setTimeout(() => hideAuthModal(), 500);
    }
  });

  // Demo Login Button
  btnDemoLogin?.addEventListener('click', async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'clinician@cancercenter.org', password: 'clinician123!' }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setAuthToken(data.access_token, {
          email: data.user.email,
          name: data.user.full_name,
          role: 'Clinician',
          institution: 'Memorial Sloan Kettering Cancer Center',
        });
        hideAuthModal();
        return;
      }
    } catch {
      // offline fallback
    }

    const demoToken = 'zaa_jwt_demo_clinician_98472';
    const demoUser = {
      email: 'clinician@cancercenter.org',
      name: 'Dr. Sarah Chen, MD',
      role: 'Clinician',
      institution: 'Memorial Sloan Kettering Cancer Center',
    };

    setAuthToken(demoToken, demoUser);
    hideAuthModal();
  });
}

// -------------------------------------------------------------
// 8. Application Initialization
// -------------------------------------------------------------

async function initApp(){
  // Check stored auth
  if (!getAuthToken()) {
    // Attempt login with default seeded credentials or seed local demo
    try {
      const resp = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'clinician@cancercenter.org', password: 'clinician123!' }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setAuthToken(data.access_token, {
          email: data.user.email,
          name: data.user.full_name,
          role: 'Clinician',
          institution: 'MSKCC Precision Oncology',
        });
      } else {
        seedLocalDemoUser();
      }
    } catch {
      seedLocalDemoUser();
    }
  }

  updateAuthUI();
  initEventListeners();

  // Load Sessions
  await fetchSessions();

  // Initialize Memory Bank & Telemetry
  await syncMemoryBank(currentSessionId);
  await syncTelemetryHUD();

  // Periodic Telemetry sync every 15 seconds
  setInterval(() => {
    syncTelemetryHUD();
  }, 15000);

  // Handle URL hash or search params for deep linking from GEA
  function handleDeepLinks() {
    const hash = window.location.hash || '';
    const searchParams = new URLSearchParams(window.location.search);
    if (hash.includes('view=primekg') || searchParams.get('view') === 'primekg') {
      setTimeout(() => {
        btnPrimekgExplorer?.click();
      }, 300);
    } else if (hash.includes('view=telemetry') || searchParams.get('view') === 'telemetry') {
      setTimeout(() => {
        btnTelemetryDashboard?.click();
      }, 300);
    }
  }

  handleDeepLinks();
  window.addEventListener('hashchange', handleDeepLinks);
}

function seedLocalDemoUser(){
  const demoToken = 'zaa_jwt_demo_clinician_98472';
  const demoUser = {
    email: 'clinician@cancercenter.org',
    name: 'Dr. Sarah Chen, MD',
    role: 'Clinician',
    institution: 'MSKCC Precision Oncology',
  };
  setAuthToken(demoToken, demoUser);
}

// Start application
window.addEventListener('DOMContentLoaded', () => {
  initApp();
});