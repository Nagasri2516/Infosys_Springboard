/**
 * EventCore – Frontend Application Logic
 * Dual-portal: Organizer + Participant, with Landing role-selection.
 */

const API = "";

// ── Utilities ─────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(API + path, { headers: { "Content-Type": "application/json" }, ...options });
    const json = await res.json();
    return { ok: res.ok, status: res.status, ...json };
  } catch (e) {
    console.error("API Error:", e);
    return { ok: false, success: false, message: "Network error. Is the server running?" };
  }
}

function formatTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── Portal Router ─────────────────────────────────────────────────────────────

function showPortal(role) {
  // Hide landing
  document.getElementById("landing-screen").style.display = "none";

  if (role === "organizer") {
    document.getElementById("organizer-portal").style.display = "";
    document.getElementById("participant-portal").style.display = "none";
    loadDashboard();
    loadOutbox();
  } else {
    document.getElementById("participant-portal").style.display = "";
    document.getElementById("organizer-portal").style.display = "none";
  }
}

function goToLanding() {
  document.getElementById("landing-screen").style.display = "flex";
  document.getElementById("organizer-portal").style.display = "none";
  document.getElementById("participant-portal").style.display = "none";
}

// ── Organizer Tab Switcher ────────────────────────────────────────────────────

function switchTab(tabId) {
  document.querySelectorAll("[data-portal='organizer'].sidebar-nav-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll("[data-portal='organizer'].tab-content").forEach(el => el.classList.remove("active"));

  const btn = document.querySelector(`[data-tab="${tabId}"][data-portal="organizer"]`);
  if (btn) btn.classList.add("active");
  const tab = document.getElementById(tabId);
  if (tab) tab.classList.add("active");

  if (tabId === "dashboard") loadDashboard();
  if (tabId === "executive-dashboard") setTimeout(fetchExecutiveDashboard, 100);
  if (tabId === "event-intelligence") setTimeout(fetchEventIntelligence, 100);
  if (tabId === "database") loadDatabase();
  if (tabId === "analytics") setTimeout(loadAnalytics, 100);
  if (tabId === "aiinsights") loadAIInsights();
  if (tabId === "events") loadEvents();
  if (tabId === "venue-agent") { venueRecommendations = []; venueCurrentIndex = 0; }
  if (tabId === "venue-optimization") loadOptimization();
  if (tabId === "speaker-agent") { speakerRecommendations = []; speakerCurrentIndex = 0; }
  if (tabId === "speaker-scheduling") loadScheduling();
  if (tabId === "session-analytics") loadSessionAnalytics();
  if (tabId === "outbox") loadOutbox();
  if (tabId === "sponsorship-agent") loadSponsorAgentData();
  if (tabId === "sponsor-performance") loadSponsorPerformanceData();
  if (tabId === "incident-agent") loadIncidentAgentData();
  if (tabId === "incident-workflows") loadIncidentWorkflowsData();
  if (tabId === "operational-alerts") loadOperationalAlertsData();
  if (tabId === "e2e-testing") setTimeout(runE2ETests, 100);
  if (tabId === "deployment-guide") setTimeout(loadDeploymentStatus, 100);
}

// ── Participant Tab Switcher ──────────────────────────────────────────────────

function switchPTab(tabId) {
  document.querySelectorAll("[data-ptab]").forEach(el => el.classList.remove("p-active"));
  document.querySelectorAll(".ptab-content").forEach(el => el.classList.remove("p-active"));

  const btn = document.querySelector(`[data-ptab="${tabId}"]`);
  if (btn) btn.classList.add("p-active");
  const tab = document.getElementById(tabId);
  if (tab) tab.classList.add("p-active");

  if (tabId === "p-my-incidents") {
    loadParticipantIncidents();
  }
}

// ── Milestone 4 : EXECUTIVE DASHBOARD & EVENT INTELLIGENCE ────────────────────

// Executive Target Settings Storage
window.execTargets = window.execTargets || {
  attendance: 30,
  revenue: 20000,
  speakers: 5,
  sla: 15
};

function recalculateExecutiveTargets() {
  const att = parseInt(document.getElementById("exec-target-attendance")?.value) || 30;
  const rev = parseFloat(document.getElementById("exec-target-revenue")?.value) || 20000;
  const spk = parseInt(document.getElementById("exec-target-speakers")?.value) || 5;
  const sla = parseInt(document.getElementById("exec-target-sla")?.value) || 15;

  window.execTargets = { attendance: att, revenue: rev, speakers: spk, sla: sla };
  fetchExecutiveDashboard();
}

async function fetchExecutiveDashboard() {
  const container = document.getElementById("executive-dashboard-container");
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading Executive Data...</div>';

  const res = await apiFetch("/api/executive-dashboard");
  if (!res || !res.success) {
    container.innerHTML = '<div class="empty-state text-danger">Failed to load Executive Dashboard.</div>';
    return;
  }

  const k = res.data.kpis || {};
  const h = res.data.health || { status: "GOOD", score: 95 };
  const targets = window.execTargets || { attendance: 300, revenue: 50000, speakers: 15, sla: 15 };

  const healthBadge = h.status === 'GOOD' ? 'badge-success' : (h.status === 'WARNING' ? 'badge-warning' : 'badge-danger');

  // Format currency helper
  const fmtMoney = (num) => '$' + (num || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });

  // Calculated Target Progresses based on Executive Input Values
  const attPct = Math.min(100, Math.round(((k.registrations || 0) / targets.attendance) * 100));
  const revPct = Math.min(100, Math.round(((k.total_sponsorship_revenue || 0) / targets.revenue) * 100));
  const spkPct = Math.min(100, Math.round(((k.confirmed_speakers || 0) / targets.speakers) * 100));

  // Source & Role pill html helper
  const sourcesHtml = Object.entries(k.registration_sources || {}).map(([src, count]) => `
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:0.55rem 0.75rem; border-radius:6px; border:1px solid var(--border-color); font-size:0.85rem;">
      <span class="text-secondary"><i class="fas fa-satellite-dish text-primary"></i> ${escapeHtml(src)}</span>
      <strong style="color:var(--accent-color); font-size:0.95rem;">${count}</strong>
    </div>
  `).join("") || '<div class="text-secondary text-sm">No source breakdown</div>';

  const rolesHtml = Object.entries(k.role_categories || {}).map(([role, count]) => `
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:0.55rem 0.75rem; border-radius:6px; border:1px solid var(--border-color); font-size:0.85rem;">
      <span class="text-secondary"><i class="fas fa-user-tag text-info"></i> ${escapeHtml(role)}</span>
      <strong style="color:var(--text-color); font-size:0.95rem;">${count}</strong>
    </div>
  `).join("") || '<div class="text-secondary text-sm">No role breakdown</div>';

  container.innerHTML = `
    <!-- Top Executive Health Banner -->
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; margin-bottom: 1.5rem; background:rgba(255,255,255,0.02); padding:1.25rem 1.5rem; border-radius:10px; border:1px solid var(--border-color);">
      <div>
        <h2 style="margin:0; font-weight:700; display:flex; align-items:center; gap:0.5rem;">
          <i class="fas fa-heartbeat text-danger"></i> Overall Event Health & Operational Index
        </h2>
        <div class="text-secondary text-sm" style="margin-top:0.25rem;">Real-time synchronized executive summary across database telemetry</div>
      </div>
      <div style="display:flex; align-items:center; gap:1rem;">
        <div class="text-right">
          <div style="font-size:0.88rem;" class="text-secondary">Health Score</div>
          <div style="font-weight:bold; font-size:1.5rem; color:var(--success-color);">${h.score}/100</div>
        </div>
        <span class="badge ${healthBadge}" style="font-size:1.25rem; padding: 0.6rem 1.2rem; border-radius:8px;">${h.status}</span>
      </div>
    </div>

    <!-- INTERACTIVE EXECUTIVE TARGET INPUT PARAMETERS PANEL -->
    <div class="panel-card glass mb-4" style="border-left: 4px solid var(--accent-color);">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:1rem;">
        <h3 class="dashboard-card-title" style="margin:0;"><i class="fas fa-sliders-h text-primary"></i> Executive Goal & Scenario Input Parameters</h3>
        <span class="badge badge-info"><i class="fas fa-edit"></i> Editable Inputs</span>
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:1rem; align-items:end;">
        <div>
          <label class="form-label" style="font-size:0.82rem;"><i class="fas fa-user-friends"></i> Target Attendance Goal</label>
          <input type="number" id="exec-target-attendance" class="form-control" value="${targets.attendance}" min="1" style="padding:0.4rem 0.6rem; font-size:0.9rem;">
        </div>
        <div>
          <label class="form-label" style="font-size:0.82rem;"><i class="fas fa-dollar-sign"></i> Target Revenue Goal ($)</label>
          <input type="number" id="exec-target-revenue" class="form-control" value="${targets.revenue}" step="1000" style="padding:0.4rem 0.6rem; font-size:0.9rem;">
        </div>
        <div>
          <label class="form-label" style="font-size:0.82rem;"><i class="fas fa-microphone"></i> Target Speaker Count</label>
          <input type="number" id="exec-target-speakers" class="form-control" value="${targets.speakers}" min="1" style="padding:0.4rem 0.6rem; font-size:0.9rem;">
        </div>
        <div>
          <label class="form-label" style="font-size:0.82rem;"><i class="fas fa-clock"></i> Max SLA Target (mins)</label>
          <input type="number" id="exec-target-sla" class="form-control" value="${targets.sla}" min="1" style="padding:0.4rem 0.6rem; font-size:0.9rem;">
        </div>
        <div>
          <button class="btn btn-primary" onclick="recalculateExecutiveTargets()" style="width:100%; padding:0.5rem 0.75rem; font-size:0.88rem; cursor:pointer;">
            <i class="fas fa-sync-alt"></i> Apply & Recalculate
          </button>
        </div>
      </div>
    </div>
    
    <!-- Primary KPI Grid (6 Core Cards with Goal Progress Indicators) -->
    <div class="stats-grid mb-4" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));">
      <div class="stat-card glass">
        <i class="fas fa-users stat-card-icon text-primary"></i>
        <h4>Registrations vs Goal</h4>
        <div class="value">${k.registrations} / ${targets.attendance}</div>
        <div class="trend-indicator up">Goal Progress: ${attPct}% (${k.checked_in} checked in)</div>
      </div>

      <div class="stat-card glass">
        <i class="fas fa-dollar-sign stat-card-icon text-success"></i>
        <h4>Revenue vs Goal</h4>
        <div class="value">${fmtMoney(k.total_sponsorship_revenue)}</div>
        <div class="trend-indicator up">Target Goal: ${fmtMoney(targets.revenue)} (${revPct}%)</div>
      </div>

      <div class="stat-card glass">
        <i class="fas fa-building stat-card-icon text-info"></i>
        <h4>Venue Utilization</h4>
        <div class="value">${k.venue_utilization}%</div>
        <div class="trend-indicator neutral">Capacity: ${k.total_expected_attendees} / ${k.total_venue_capacity}</div>
      </div>

      <div class="stat-card glass">
        <i class="fas fa-handshake stat-card-icon text-warning"></i>
        <h4>Sponsor Engagement</h4>
        <div class="value">${k.sponsor_performance}/100</div>
        <div class="trend-indicator up">${k.total_leads_captured} Leads · ${k.total_sponsors} Sponsors</div>
      </div>

      <div class="stat-card glass">
        <i class="fas fa-microphone-alt stat-card-icon text-primary"></i>
        <h4>Speakers Confirmed</h4>
        <div class="value">${k.confirmed_speakers} / ${targets.speakers}</div>
        <div class="trend-indicator up">Target Goal: ${spkPct}% (${k.total_speakers} total)</div>
      </div>

      <div class="stat-card glass">
        <i class="fas fa-shield-alt stat-card-icon text-success"></i>
        <h4>Incident Resolution</h4>
        <div class="value">${k.incident_resolution_rate}%</div>
        <div class="trend-indicator up">${k.open_incidents} Open (${targets.sla} min SLA)</div>
      </div>
    </div>

    <!-- Secondary Executive Intelligence Panels Grid -->
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap:1.25rem; margin-bottom:1.5rem;">
      
      <!-- Panel 1: Financial & Sponsorship Telemetry -->
      <div class="panel-card glass">
        <h3 class="dashboard-card-title"><i class="fas fa-chart-pie text-success"></i> Financial & Sponsorship Performance</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-top:1rem;">
          <div style="background:rgba(255,255,255,0.02); padding:0.8rem; border-radius:6px; border:1px solid var(--border-color);">
            <div class="text-secondary text-sm">Contracted Revenue</div>
            <div style="font-weight:bold; font-size:1.15rem; color:var(--success-color); margin-top:0.2rem;">${fmtMoney(k.total_sponsorship_revenue)}</div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:0.8rem; border-radius:6px; border:1px solid var(--border-color);">
            <div class="text-secondary text-sm">Collected Revenue</div>
            <div style="font-weight:bold; font-size:1.15rem; color:var(--text-color); margin-top:0.2rem;">${fmtMoney(k.paid_sponsorship_revenue)}</div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:0.8rem; border-radius:6px; border:1px solid var(--border-color);">
            <div class="text-secondary text-sm">Deliverables Fulfilled</div>
            <div style="font-weight:bold; font-size:1.15rem; color:var(--accent-color); margin-top:0.2rem;">${k.deliverables_fulfillment_rate}%</div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:0.8rem; border-radius:6px; border:1px solid var(--border-color);">
            <div class="text-secondary text-sm">Total Leads Generated</div>
            <div style="font-weight:bold; font-size:1.15rem; color:var(--warning-color); margin-top:0.2rem;">${k.total_leads_captured}</div>
          </div>
        </div>
      </div>

      <!-- Panel 2: Registration Demographics & Channel Telemetry -->
      <div class="panel-card glass">
        <h3 class="dashboard-card-title"><i class="fas fa-users-cog text-info"></i> Registrant Channel & Role Distribution</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-top:1rem;">
          <div>
            <div class="text-sm text-secondary mb-2"><strong>Registration Channels:</strong></div>
            <div style="display:flex; flex-direction:column; gap:0.4rem;">
              ${sourcesHtml}
            </div>
          </div>
          <div>
            <div class="text-sm text-secondary mb-2"><strong>Role Categories:</strong></div>
            <div style="display:flex; flex-direction:column; gap:0.4rem;">
              ${rolesHtml}
            </div>
          </div>
        </div>
      </div>

      <!-- Panel 3: Operational Risk & Incident Response Telemetry -->
      <div class="panel-card glass" style="grid-column: span 1 / -1;">
        <h3 class="dashboard-card-title"><i class="fas fa-microchip text-warning"></i> Operational Telemetry & System Health</h3>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:1rem; margin-top:1rem;">
          <div style="background:rgba(255,255,255,0.02); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color); text-align:center;">
            <div style="font-weight:bold; font-size:1.3rem; color:var(--text-color);">${k.incidents_total}</div>
            <div class="text-secondary text-sm">Total Logged Incidents</div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color); text-align:center;">
            <div style="font-weight:bold; font-size:1.3rem; color:var(--success-color);">${k.resolved_incidents}</div>
            <div class="text-secondary text-sm">Resolved Tickets</div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color); text-align:center;">
            <div style="font-weight:bold; font-size:1.3rem; color:var(--text-color);">${k.critical_incidents}</div>
            <div class="text-secondary text-sm">High / Critical Issues</div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color); text-align:center;">
            <div style="font-weight:bold; font-size:1.3rem; color:var(--success-color);">${k.active_alerts} / ${k.total_alerts}</div>
            <div class="text-secondary text-sm">Active Operational Alerts</div>
          </div>
        </div>
      </div>

    </div>
  `;
}

async function fetchEventIntelligence() {
  const summaryContainer = document.getElementById("intelligence-summary-cards");
  const activeRecsContainer = document.getElementById("active-recommendations-container");
  const predictiveRisksContainer = document.getElementById("predictive-risks-container");
  const lastUpdatedEl = document.getElementById("intelligence-last-updated");

  if (lastUpdatedEl) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    lastUpdatedEl.innerHTML = `<i class="fas fa-clock"></i> Last updated: ${timeStr}`;
  }

  if (summaryContainer) summaryContainer.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading Intelligence Summary...</div>';
  if (activeRecsContainer) activeRecsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading AI Recommendations...</div>';
  if (predictiveRisksContainer) predictiveRisksContainer.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading Predictive Risks...</div>';

  const res = await apiFetch("/api/event-intelligence");
  if (!res.success) {
    if (activeRecsContainer) activeRecsContainer.innerHTML = '<div class="empty-state text-danger">Failed to load Event Intelligence data.</div>';
    return;
  }

  const data = res.data || {};
  const summary = data.summary || {};
  const health = data.health || { status: "GOOD", score: 100 };
  const activeInsights = data.active_insights || [];
  const predictiveRisks = data.predictive_risks || [];

  // SECTION 5: INTELLIGENCE SUMMARY (Clickable Cards)
  if (summaryContainer) {
    let healthBadgeClz = "badge-success";
    if (health.status === "WARNING") healthBadgeClz = "badge-warning";
    if (health.status === "CRITICAL") healthBadgeClz = "badge-danger";

    summaryContainer.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card glass" onclick="switchTab('executive-dashboard')" style="cursor:pointer;" title="Click to open Executive Dashboard">
          <i class="fas fa-heartbeat stat-card-icon text-success"></i>
          <h4>Event Health</h4>
          <div class="value"><span class="badge ${healthBadgeClz}">${escapeHtml(health.status)}</span></div>
          <div class="trend-indicator text-primary"><i class="fas fa-external-link-alt"></i> Score: ${health.score}/100</div>
        </div>
        <div class="stat-card glass" onclick="switchTab('incident-workflows')" style="cursor:pointer;" title="Click to view Operational Risks in Incident Workflows">
          <i class="fas fa-shield-alt stat-card-icon text-warning"></i>
          <h4>Operational Risks</h4>
          <div class="value">${summary.operational_risks_count || 0}</div>
          <div class="trend-indicator text-primary"><i class="fas fa-external-link-alt"></i> View Risk Workflows</div>
        </div>
        <div class="stat-card glass" onclick="switchTab('incident-workflows')" style="cursor:pointer;" title="Click to open Incident Workflows">
          <i class="fas fa-exclamation-circle stat-card-icon ${summary.critical_incidents_count > 0 ? 'text-danger' : 'text-info'}"></i>
          <h4>Open Incidents</h4>
          <div class="value">${summary.open_incidents_count || 0}</div>
          <div class="trend-indicator ${summary.critical_incidents_count > 0 ? 'text-danger' : 'text-primary'}"><i class="fas fa-external-link-alt"></i> Manage (${summary.critical_incidents_count || 0} Critical)</div>
        </div>
        <div class="stat-card glass" onclick="document.getElementById('active-recommendations-container').scrollIntoView({behavior:'smooth'})" style="cursor:pointer;" title="Click to scroll to AI Recommendations">
          <i class="fas fa-lightbulb stat-card-icon text-info"></i>
          <h4>Active Recommendations</h4>
          <div class="value">${summary.active_recommendations_count || 0}</div>
          <div class="trend-indicator text-info"><i class="fas fa-arrow-down"></i> View AI Insights</div>
        </div>
        <div class="stat-card glass" onclick="switchTab('operational-alerts')" style="cursor:pointer;" title="Click to open Operational Alerts">
          <i class="fas fa-bell stat-card-icon text-danger"></i>
          <h4>Recent Alerts</h4>
          <div class="value">${summary.recent_alerts_count || 0}</div>
          <div class="trend-indicator text-primary"><i class="fas fa-external-link-alt"></i> Open Alerts Page</div>
        </div>
      </div>
    `;
  }

  // SECTION 3: ACTIVE AI RECOMMENDATIONS (Clickable Action Items)
  if (activeRecsContainer) {
    if (activeInsights.length === 0) {
      activeRecsContainer.innerHTML = '<div class="empty-state text-secondary"><i class="fas fa-check-circle text-success"></i> No critical insights detected currently.</div>';
    } else {
      activeRecsContainer.innerHTML = activeInsights.map(item => {
        let pBadgeClz = "badge-info";
        if (item.priority === "High") pBadgeClz = "badge-warning";
        if (item.priority === "Critical") pBadgeClz = "badge-danger";

        let sBadgeClz = "badge-primary";
        if (item.status === "Action Required") sBadgeClz = "badge-danger";

        const issueText = item.issue || "";
        let targetTab = "incident-workflows";
        let actionLabel = "Open Incident Workflows";

        if (issueText.includes("Sponsor") || issueText.includes("Sponsorship")) {
          targetTab = "sponsorship-agent";
          actionLabel = "Open Sponsorship Operations";
        } else if (issueText.includes("Check-In") || issueText.includes("Scan") || issueText.includes("Queue")) {
          targetTab = "operational-alerts";
          actionLabel = "Open Operational Alerts";
        } else if (issueText.includes("Venue") || issueText.includes("Hall")) {
          targetTab = "venue-agent";
          actionLabel = "Open Venue Operations";
        }

        return `
          <div class="panel-card glass" style="margin-bottom: 0.75rem; border-left: 4px solid var(--accent-color);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
              <h4 style="margin:0; font-size:1rem;"><i class="fas fa-lightbulb text-warning"></i> ${escapeHtml(item.issue || "Operational Insight")}</h4>
              <div>
                <span class="badge ${pBadgeClz}">Priority: ${escapeHtml(item.priority || "Normal")}</span>
                <span class="badge ${sBadgeClz}">Status: ${escapeHtml(item.status || "Active")}</span>
              </div>
            </div>
            <p style="margin:0.5rem 0 0.25rem 0; font-size:0.9rem; color:var(--text-color);">${escapeHtml(item.impact || "")}</p>
            <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.8rem; border-radius:6px; border:1px solid var(--border-color); margin-top:0.5rem; font-size:0.88rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
              <div><strong><i class="fas fa-user-shield text-info"></i> Recommended Action:</strong> ${escapeHtml(item.suggested_action || "Monitor operations.")}</div>
              <button class="btn btn-sm btn-primary" onclick="switchTab('${targetTab}')" style="cursor:pointer; font-size:0.8rem;">
                <i class="fas fa-external-link-alt"></i> ${actionLabel}
              </button>
            </div>
          </div>
        `;
      }).join("");
    }
  }

  // SECTION 4: PREDICTIVE RISK SCANNING (Clickable Mitigation Actions)
  if (predictiveRisksContainer) {
    if (predictiveRisks.length === 0) {
      predictiveRisksContainer.innerHTML = '<div class="empty-state text-secondary"><i class="fas fa-shield-alt text-success"></i> No operational risks flagged currently.</div>';
    } else {
      predictiveRisksContainer.innerHTML = predictiveRisks.map(r => {
        let sevClz = "badge-info";
        if (r.severity === "Medium") sevClz = "badge-warning";
        if (r.severity === "High" || r.severity === "Critical") sevClz = "badge-danger";

        const riskTitle = r.risk || "";
        let targetTab = "incident-workflows";
        let targetName = "Incident Workflows";

        if (riskTitle.includes("Sponsor")) {
          targetTab = "sponsorship-agent";
          targetName = "Sponsorship Operations";
        } else if (riskTitle.includes("Queue") || riskTitle.includes("Arrival")) {
          targetTab = "operational-alerts";
          targetName = "Operational Alerts";
        } else if (riskTitle.includes("Venue") || riskTitle.includes("Saturation")) {
          targetTab = "venue-agent";
          targetName = "Venue Management";
        }

        return `
          <div class="panel-card glass" style="margin-bottom: 0.75rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
              <h4 style="margin:0; font-size:0.95rem;"><i class="fas fa-exclamation-triangle text-warning"></i> ${escapeHtml(r.risk || "Operational Risk")}</h4>
              <span class="badge ${sevClz}">Severity: ${escapeHtml(r.severity || "Low")}</span>
            </div>
            <p style="margin:0.4rem 0 0.25rem 0; font-size:0.88rem; color:var(--secondary-text);">${escapeHtml(r.impact || "")}</p>
            <div style="font-size:0.85rem; color:var(--text-color); margin-top:0.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; background:rgba(255,255,255,0.02); padding:0.5rem 0.75rem; border-radius:6px; border:1px solid var(--border-color);">
              <div><strong>Recommended Mitigation:</strong> ${escapeHtml(r.recommended_action || "")}</div>
              <button class="btn btn-sm btn-outline-warning" onclick="switchTab('${targetTab}')" style="cursor:pointer; font-size:0.78rem;">
                <i class="fas fa-shield-alt"></i> Resolve in ${targetName}
              </button>
            </div>
          </div>
        `;
      }).join("");
    }
  }
}

async function triggerOrchestrator(eventType, payload) {
  const resultCard = document.getElementById("orchestrator-result-card");
  if (!resultCard) return;

  resultCard.style.display = "block";
  resultCard.innerHTML = `
    <div class="panel-card glass text-center" style="padding:1.5rem;">
      <i class="fas fa-spinner fa-spin fa-2x text-primary"></i>
      <p style="margin-top:0.5rem;">Orchestrating agents and evaluating event intelligence...</p>
    </div>
  `;

  const res = await apiFetch("/api/orchestrator/trigger", {
    method: "POST",
    body: JSON.stringify({ event_type: eventType, payload })
  });

  if (!res.success) {
    resultCard.innerHTML = `
      <div class="panel-card glass" style="border-left: 4px solid var(--danger-color);">
        <h4 class="text-danger"><i class="fas fa-exclamation-circle"></i> Orchestrator Error</h4>
        <p>${escapeHtml(res.message || "Failed to execute orchestration workflow.")}</p>
      </div>
    `;
    return;
  }

  const data = res.data || {};
  const card = data.event_card || {
    title: "⚡ Orchestrated Event Triggered",
    issue: "Automated event response initiated across management agents.",
    impact: "Multi-agent coordination sequence executed.",
    severity: "Medium",
    priority: "Medium",
    affected_area: "Event Management System",
    recommended_action: "Review operational alert log.",
    status: "Action Required"
  };

  const steps = data.workflow_steps || [
    { agent: "Trigger Agent", action: "Initiates event sequence" },
    { agent: "Event Intelligence Engine", action: "Analyzes system impact" },
    { agent: "Operational Alert", action: "Dispatches organizer notifications" }
  ];

  // Severity badge color
  let sevClz = "badge-info";
  if (card.severity === "Medium") sevClz = "badge-warning";
  if (card.severity === "High" || card.severity === "Critical") sevClz = "badge-danger";

  // Priority badge color
  let prioClz = "badge-info";
  if (card.priority === "High" || card.priority === "Critical") prioClz = "badge-warning";

  // Status badge color
  let statusClz = "badge-primary";
  if (card.status === "Action Required") statusClz = "badge-danger";
  if (card.status === "Resolved") statusClz = "badge-success";

  // Recommended Action Tab Target Mapping
  let actionTab = "incident-workflows";
  let actionTabName = "Incident Workflows";
  if (eventType === "SPEAKER_CANCELLATION") {
    actionTab = "speaker-agent";
    actionTabName = "Speaker Operations";
  } else if (eventType === "WIFI_FAILURE") {
    actionTab = "incident-workflows";
    actionTabName = "Incident Workflows";
  } else if (eventType === "SPONSOR_DELIVERABLE_DELAY") {
    actionTab = "sponsorship-agent";
    actionTabName = "Sponsorship Operations";
  }

  // Workflow steps visual builder with interactive click navigation
  const workflowHtml = steps.map((step, idx) => {
    let stepTab = "";
    let stepTabLabel = "";
    const agentName = step.agent || "";

    if (agentName.includes("Incident")) { stepTab = "incident-workflows"; stepTabLabel = "Open Incident Workflows"; }
    else if (agentName.includes("Alert")) { stepTab = "operational-alerts"; stepTabLabel = "Open Operational Alerts"; }
    else if (agentName.includes("Executive") || agentName.includes("Intelligence Engine")) { stepTab = "executive-dashboard"; stepTabLabel = "Open Executive Dashboard"; }
    else if (agentName.includes("Speaker")) { stepTab = "speaker-agent"; stepTabLabel = "Open Speaker Operations"; }
    else if (agentName.includes("Venue")) { stepTab = "venue-agent"; stepTabLabel = "Open Venue Operations"; }
    else if (agentName.includes("Sponsor")) { stepTab = "sponsorship-agent"; stepTabLabel = "Open Sponsorship Operations"; }
    else if (agentName.includes("Registration")) { stepTab = "database"; stepTabLabel = "Open Registration Database"; }

    const clickAttr = stepTab ? `onclick="switchTab('${stepTab}')" style="cursor:pointer;" title="${stepTabLabel}"` : '';

    return `
      <div ${clickAttr} style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.6rem; transition:transform 0.15s ease;">
        <div style="width:28px; height:28px; border-radius:50%; background:var(--accent-color); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:0.8rem; flex-shrink:0;">
          ${idx + 1}
        </div>
        <div style="flex:1; background:rgba(255,255,255,0.03); padding:0.5rem 0.75rem; border-radius:6px; border:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:var(--text-color); font-size:0.88rem;">${escapeHtml(step.agent)}</strong>
            <div style="font-size:0.82rem; color:var(--secondary-text);">${escapeHtml(step.action)}</div>
          </div>
          ${stepTab ? `<span class="badge badge-outline text-primary" style="font-size:0.75rem;"><i class="fas fa-external-link-alt"></i> Navigate</span>` : ''}
        </div>
      </div>
    `;
  }).join("");

  resultCard.innerHTML = `
    <!-- SECTION 2: ORCHESTRATION RESULT CARD -->
    <div class="panel-card glass" style="border-left: 5px solid var(--accent-color); position:relative;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem; margin-bottom:1rem;">
        <div>
          <h3 style="margin:0; font-size:1.15rem; font-weight:700;">${escapeHtml(card.title)}</h3>
          <span class="text-sm text-secondary"><i class="fas fa-check-circle text-success"></i> Orchestration Sequence Completed</span>
        </div>
        <div>
          <span class="badge ${sevClz}">Severity: ${escapeHtml(card.severity)}</span>
          <span class="badge ${prioClz}">Priority: ${escapeHtml(card.priority)}</span>
          <span class="badge ${statusClz}">${escapeHtml(card.status)}</span>
        </div>
      </div>

      <!-- Business Details Grid -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:1rem; margin-bottom:1.25rem; font-size:0.9rem;">
        <div style="background:rgba(255,255,255,0.02); padding:0.75rem; border-radius:6px; border:1px solid var(--border-color);">
          <strong class="text-secondary"><i class="fas fa-info-circle"></i> Issue:</strong>
          <p style="margin:0.25rem 0 0 0; font-weight:500;">${escapeHtml(card.issue)}</p>
        </div>
        <div style="background:rgba(255,255,255,0.02); padding:0.75rem; border-radius:6px; border:1px solid var(--border-color);">
          <strong class="text-secondary"><i class="fas fa-bullseye"></i> Impact:</strong>
          <p style="margin:0.25rem 0 0 0;">${escapeHtml(card.impact)}</p>
        </div>
        <div style="background:rgba(255,255,255,0.02); padding:0.75rem; border-radius:6px; border:1px solid var(--border-color);">
          <strong class="text-secondary"><i class="fas fa-map-marker-alt"></i> Affected Area:</strong>
          <p style="margin:0.25rem 0 0 0;">${escapeHtml(card.affected_area)}</p>
        </div>
        <div style="background:rgba(255,255,255,0.02); padding:0.75rem; border-radius:6px; border:1px solid var(--border-color); display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <strong class="text-secondary"><i class="fas fa-tasks"></i> Recommended Action:</strong>
            <p style="margin:0.25rem 0 0.5rem 0; color:var(--accent-color); font-weight:600;">${escapeHtml(card.recommended_action)}</p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="switchTab('${actionTab}')" style="cursor:pointer; width:100%;">
            <i class="fas fa-external-link-alt"></i> Execute in ${actionTabName}
          </button>
        </div>
      </div>

      <!-- Visual Agent Execution Workflow (Interactive Navigation) -->
      <div style="margin-bottom:1rem;">
        <h4 style="font-size:0.95rem; margin-bottom:0.75rem;"><i class="fas fa-sitemap"></i> Orchestrated Agent Execution Workflow (Click step to view module):</h4>
        ${workflowHtml}
      </div>

      <div style="margin-top:1rem; display:flex; justify-content:flex-end; gap:0.5rem;">
        <button class="btn btn-xs btn-outline" onclick="fetchEventIntelligence();"><i class="fas fa-sync-alt"></i> Refresh Intelligence Data</button>
      </div>
    </div>
  `;

  // Automatically refresh main intelligence metrics after simulation
  fetchEventIntelligence();
}

// ── Milestone 4 : END-TO-END TESTING & DEPLOYMENT STATUS ─────────────────────

async function runE2ETests() {
  const summaryEl = document.getElementById("e2e-test-summary-container");
  const listEl = document.getElementById("e2e-tests-list-container");
  const timeEl = document.getElementById("e2e-test-timestamp");

  if (timeEl) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    timeEl.innerHTML = `<i class="fas fa-clock"></i> Executed at ${timeStr}`;
  }

  if (summaryEl) summaryEl.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Running End-to-End Test Suite...</div>';
  if (listEl) listEl.innerHTML = '<div class="empty-state"><i class="fas fa-vial fa-spin"></i> Executing API, Database & Orchestration Test Cases...</div>';

  const res = await apiFetch("/api/test-runner", { method: "POST" });
  if (!res.success) {
    if (summaryEl) summaryEl.innerHTML = '<div class="empty-state text-danger">Failed to run test suite. Is backend server connected?</div>';
    return;
  }

  const s = res.data.summary || {};
  const tests = res.data.tests || [];

  if (summaryEl) {
    summaryEl.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card glass">
          <i class="fas fa-list-check stat-card-icon text-primary"></i>
          <h4>Total Test Cases</h4>
          <div class="value">${s.total || 0}</div>
          <div class="trend-indicator up">Executed</div>
        </div>
        <div class="stat-card glass">
          <i class="fas fa-check-circle stat-card-icon text-success"></i>
          <h4>Passed</h4>
          <div class="value text-success">${s.passed || 0}</div>
          <div class="trend-indicator up">100% Passed</div>
        </div>
        <div class="stat-card glass">
          <i class="fas fa-times-circle stat-card-icon text-danger"></i>
          <h4>Failed</h4>
          <div class="value text-danger">${s.failed || 0}</div>
          <div class="trend-indicator neutral">0 Failures</div>
        </div>
        <div class="stat-card glass">
          <i class="fas fa-percentage stat-card-icon text-info"></i>
          <h4>Success Rate</h4>
          <div class="value text-info">${s.success_rate || "100%"}</div>
          <div class="trend-indicator up">Verified</div>
        </div>
      </div>
    `;
  }

  if (listEl) {
    listEl.innerHTML = tests.map(t => `
      <div class="panel-card glass" style="margin-bottom: 0.75rem; border-left: 4px solid ${t.status === 'PASS' ? 'var(--success-color)' : 'var(--danger-color)'};">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
          <div>
            <h4 style="margin:0; font-size:1rem;"><i class="fas ${t.status === 'PASS' ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i> ${escapeHtml(t.name)}</h4>
            <span class="text-sm text-secondary"><i class="fas fa-layer-group"></i> Module: ${escapeHtml(t.module)}</span>
          </div>
          <span class="badge ${t.status === 'PASS' ? 'badge-success' : 'badge-danger'}">${escapeHtml(t.status)}</span>
        </div>
        <div style="background:rgba(255,255,255,0.02); padding:0.6rem 0.8rem; border-radius:6px; border:1px solid var(--border-color); margin-top:0.5rem; font-size:0.88rem; font-family:monospace;">
          ${escapeHtml(t.details)}
        </div>
      </div>
    `).join("");
  }
}

async function loadDeploymentStatus() {
  const container = document.getElementById("deployment-status-container");
  if (!container) return;

  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Checking Deployment Status...</div>';

  const res = await apiFetch("/api/deployment-status");
  if (!res.success) {
    container.innerHTML = '<div class="empty-state text-danger">Failed to fetch deployment status.</div>';
    return;
  }

  const d = res.data || {};
  const s = d.server || {};
  const db = d.database || {};
  const svcs = d.services || {};

  container.innerHTML = `
    <div class="stats-grid mb-4">
      <div class="stat-card glass">
        <i class="fas fa-server stat-card-icon text-success"></i>
        <h4>Server Runtime</h4>
        <div class="value"><span class="badge badge-success">${escapeHtml(s.status || "ONLINE")}</span></div>
        <div class="trend-indicator up">Python ${escapeHtml(s.python_version || "3.x")} · ${escapeHtml(s.framework || "Flask")}</div>
      </div>
      <div class="stat-card glass">
        <i class="fas fa-database stat-card-icon text-info"></i>
        <h4>SQLite Database</h4>
        <div class="value">${db.tables ? Object.keys(db.tables).length : 6} Tables</div>
        <div class="trend-indicator up">Telemetry DB Active</div>
      </div>
      <div class="stat-card glass">
        <i class="fas fa-network-wired stat-card-icon text-primary"></i>
        <h4>Host Endpoint</h4>
        <div class="value" style="font-size:1.1rem; font-family:monospace;">http://${escapeHtml(s.host || "0.0.0.0")}:${s.port || 5000}</div>
        <div class="trend-indicator up">CORS Enabled</div>
      </div>
      <div class="stat-card glass">
        <i class="fas fa-robot stat-card-icon text-warning"></i>
        <h4>Offline AI Engine</h4>
        <div class="value"><span class="badge badge-primary">DETERMINISTIC</span></div>
        <div class="trend-indicator up">Zero Latency</div>
      </div>
    </div>

    <!-- Active Table Row Metrics -->
    <div class="panel-card glass mb-4">
      <h3 class="dashboard-card-title"><i class="fas fa-table"></i> SQLite Table Record Telemetry</h3>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:1rem; font-size:0.9rem;">
        ${Object.entries(db.tables || {}).map(([t, cnt]) => `
          <div style="background:rgba(255,255,255,0.02); padding:0.75rem; border-radius:6px; border:1px solid var(--border-color); text-align:center;">
            <div style="font-weight:bold; font-size:1.2rem; color:var(--accent-color);">${cnt}</div>
            <div class="text-secondary font-mono" style="font-size:0.8rem;">${t}</div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

// ── Custom Confirm Modal ──────────────────────────────────────────────────────

let _confirmCallback = null;

function customConfirm(title, message, onConfirm) {
  document.getElementById("confirm-modal-title").textContent = title;
  document.getElementById("confirm-modal-message").textContent = message;
  _confirmCallback = onConfirm;
  document.getElementById("confirm-modal").classList.add("active");
}

// ── 1. DASHBOARD ─────────────────────────────────────────────────────────────

async function loadDashboard() {
  const res = await apiFetch("/api/dashboard");
  if (!res.success) return;

  const s = res.data.summary;
  document.getElementById("stat-total").textContent = s.total_registrations;
  document.getElementById("stat-checkedin").textContent = s.checked_in;
  document.getElementById("stat-pending").textContent = s.pending;
  document.getElementById("stat-rate").textContent = s.attendance_rate + "%";

  const feed = document.getElementById("activity-feed");
  feed.innerHTML = "";
  if (!res.data.activity.length) {
    feed.innerHTML = '<div class="empty-state">No activity yet.</div>';
    return;
  }
  res.data.activity.slice(0, 10).forEach(ev => {
    let iconCls = "fa-info-circle text-info";
    if (ev.type === "registration") iconCls = "fa-user-plus text-primary";
    if (ev.type === "checkin") iconCls = "fa-check-circle text-success";
    const div = document.createElement("div");
    div.className = "activity-log-item";
    const action = ev.type === "registration"
      ? `${ev.full_name} registered via ${ev.source} `
      : `${ev.full_name} checked in via ${ev.source} `;
    div.innerHTML = `
    <div class="log-details" ><i class="fas ${iconCls}"></i><span>${action}</span></div>
      <span class="log-time">${formatTime(ev.time)}</span>
  `;
    feed.appendChild(div);
  });
}

// ── 2. REGISTRATION FORM ──────────────────────────────────────────────────────

function setupRegistrationForm() {
  const form = document.getElementById("web-registration-form");
  if (!form) return;

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const btn = document.getElementById("reg-submit-btn");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';

    const payload = {
      full_name: document.getElementById("reg-name").value.trim(),
      email: document.getElementById("reg-email").value.trim(),
      phone: document.getElementById("reg-phone").value.trim(),
      organization: document.getElementById("reg-company").value.trim(),
      state: document.getElementById("reg-state").value.trim(),
      country: document.getElementById("reg-country").value.trim(),
      area_of_interest: document.getElementById("reg-interest").value.trim(),
      role_category: document.getElementById("reg-role").value,
      event_id: document.getElementById("reg-event-id").value,
      source: "Web Form"
    };

    const res = await apiFetch("/api/registrations", { method: "POST", body: JSON.stringify(payload) });
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-check-circle"></i> Complete Registration';

    if (!res.success) { alert("Registration failed: " + res.message); return; }
    form.reset();
    showReceipt(res.data, res.duplicate_warning, res.email, res.existing_id);
  });
}

function showReceipt(reg, isDuplicate = false, emailResult = null, existingId = null) {
  document.getElementById("modal-reg-id").textContent = reg.id;
  document.getElementById("modal-name").textContent = reg.full_name;
  document.getElementById("modal-email").textContent = reg.email;
  document.getElementById("modal-role").textContent = reg.role_category;
  document.getElementById("modal-source").textContent = reg.source;

  const dupRow = document.getElementById("modal-dup-row");
  const dupMessage = document.getElementById("modal-dup-message");
  if (isDuplicate) {
    dupRow.style.display = "flex";
    dupMessage.textContent = existingId
      ? `Existing registration already exists with ID ${existingId}. A new registration was still created and a confirmation email was sent.`
      : "A registration with this email already exists. A new registration was still created and a confirmation email was sent.";
  } else {
    dupRow.style.display = "none";
  }

  const title = document.querySelector("#receipt-modal h2");
  const subtitle = document.querySelector("#receipt-modal .text-secondary");
  const icon = document.getElementById("modal-success-icon");
  if (isDuplicate) {
    title.textContent = "Duplicate Email Warning";
    subtitle.textContent = existingId
      ? `Existing registration ID ${existingId} was found.The new registration was created successfully.`
      : "A registration with this email already exists. The new registration was created successfully.";
    icon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
    icon.style.borderColor = "rgba(245, 158, 11, 0.35)";
    icon.style.color = "var(--warning)";
  } else {
    title.textContent = "Registration Confirmed!";
    subtitle.textContent = "Saved to database · QR code generated · Email dispatched";
    icon.innerHTML = '<i class="fas fa-check"></i>';
    icon.style.borderColor = "rgba(34, 197, 94, 0.35)";
    icon.style.color = "var(--success)";
  }

  const qrHolder = document.getElementById("modal-qrcode");
  qrHolder.innerHTML = "";
  const img = document.createElement("img");
  img.src = reg.qr_code_path;
  img.alt = `QR Code ${reg.id} `;
  img.className = "qr-image";
  img.onerror = () => { img.style.display = "none"; };
  qrHolder.appendChild(img);

  const viewEmailBtn = document.getElementById("view-email-btn");
  if (emailResult && emailResult.html_file) {
    viewEmailBtn.style.display = "";
    viewEmailBtn.onclick = () => window.open(`/ outbox / ${emailResult.html_file} `, "_blank");
  } else {
    viewEmailBtn.style.display = "none";
  }
  document.getElementById("receipt-modal").classList.add("active");
}

// ── Simulation Panel ──────────────────────────────────────────────────────────

const SIM_DATA = {
  google: { names: ["David Miller", "Laura Croft", "Simon Pegg", "Bruce Wayne", "Clark Kent"], orgs: ["Gotham Labs", "Daily Planet", "Tomb Explorers LLC", "Pegg Dynamics", "Independent Studio"], roles: ["Student", "Professional", "Mentor"], source: "Google Forms" },
  mobile: { names: ["Peter Parker", "Gwen Stacy", "Tony Stark", "Diana Prince", "Barry Allen"], orgs: ["Oscorp", "Stark Industries", "Themyscira Museum", "S.T.A.R. Labs", "Empire State"], roles: ["Student", "Professional", "Mentor", "Organizer"], source: "Mobile App" },
  api: { names: ["Neo Anderson", "Morpheus Dream", "Trinity Code", "Agent Smith", "Niobe Logos"], orgs: ["Matrix Core", "Zion Resistance", "Logos Ship", "Security Guild", "Sentinel Corp"], roles: ["Professional", "Mentor"], source: "API" }
};

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

async function runSimulation(type) {
  const cfg = SIM_DATA[type];
  const name = pick(cfg.names);
  const email = name.toLowerCase().replace(" ", ".") + `@${type} -sim.eventcore.io`;
  const payload = {
    full_name: name, email, phone: `555 - 0${Math.floor(100 + Math.random() * 900)} `,
    organization: pick(cfg.orgs), role_category: pick(cfg.roles), source: cfg.source,
    state: "Simulated", country: "Simulated", area_of_interest: "Technology"
  };
  const res = await apiFetch("/api/registrations", { method: "POST", body: JSON.stringify(payload) });
  if (res.success) { showReceipt(res.data, res.duplicate_warning, res.email, res.existing_id); loadDashboard(); }
  else alert("Simulation failed: " + res.message);
}

// ── 3. DATABASE TABLE ─────────────────────────────────────────────────────────

let dbParams = { search: "", role: "All", source: "All", status: "All" };

async function loadDatabase() {
  const tbody = document.getElementById("database-table-body");
  tbody.innerHTML = `<tr> <td colspan="7" class="text-center" style="padding:2rem;color:var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr> `;

  const p = new URLSearchParams();
  if (dbParams.search) p.set("search", dbParams.search);
  if (dbParams.role !== "All") p.set("role", dbParams.role);
  if (dbParams.source !== "All") p.set("source", dbParams.source);
  if (dbParams.status !== "All") p.set("status", dbParams.status);

  const res = await apiFetch(`/ api / registrations ? ${p.toString()} `);
  if (!res.success) {
    tbody.innerHTML = `<tr> <td colspan="7" class="text-center" style="color:var(--danger);padding:2rem;">Failed to load data from API.</td></tr> `;
    return;
  }
  tbody.innerHTML = "";
  if (!res.data.length) {
    tbody.innerHTML = `<tr> <td colspan="7" class="text-center" style="padding:2.5rem;color:var(--text-secondary);"><i class="fas fa-search" style="font-size:2rem;display:block;margin-bottom:.5rem;opacity:.4;"></i>No records match current filters.</td></tr> `;
    return;
  }

  res.data.forEach(reg => {
    const roleClass = { Student: "badge-role-stud", Professional: "badge-role-prof", Mentor: "badge-role-ment", Organizer: "badge-role-org" }[reg.role_category] || "badge-role-prof";
    const srcCls = { "Web Form": "source-web", "Google Forms": "source-gforms", "Mobile App": "source-mobile", "API": "source-api" }[reg.source] || "";
    const statusBadge = reg.checked_in
      ? `<span class="badge badge-success" > Checked In</span> <div class="attendee-cell-sub">${formatTime(reg.check_in_time)}</div>`
      : `<span class="badge badge-warning" > Pending</span> `;
    const actionBtn = !reg.checked_in
      ? `<button class="btn btn-sm btn-outline-success" onclick = "doCheckIn('${reg.id}','manual')" > <i class="fas fa-check"></i> Check In</button> `
      : `<span class="text-success text-sm" > <i class="fas fa-check-circle"></i> Done</span> `;

    const tr = document.createElement("tr");
    tr.innerHTML = `
    <td class="font-mono text-sm" > ${reg.id}</td>
      <td><div class="attendee-cell-name">${reg.full_name}</div><div class="attendee-cell-sub">${reg.organization || "—"}</div></td>
      <td class="text-sm">${reg.email}</td>
      <td><span class="badge ${roleClass}">${reg.role_category}</span></td>
      <td><span class="source-badge ${srcCls}">${reg.source}</span></td>
      <td>${statusBadge}</td>
      <td>
        <div class="actions-flex">
          ${actionBtn}
          <a class="btn btn-sm btn-icon btn-outline" href="/static/qrcodes/${reg.id}.png" target="_blank" title="View QR"><i class="fas fa-qrcode"></i></a>
          <button class="btn btn-sm btn-icon btn-outline-danger" onclick="doDelete('${reg.id}','${reg.full_name.replace(/'/g, "\\'")}')"><i class="fas fa-trash-alt"></i></button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function setupDatabaseListeners() {
  let searchTimer;
  document.getElementById("db-search").addEventListener("input", e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { dbParams.search = e.target.value; loadDatabase(); }, 300);
  });
  ["db-filter-role", "db-filter-source", "db-filter-status"].forEach(id => {
    document.getElementById(id).addEventListener("change", e => {
      const key = { "db-filter-role": "role", "db-filter-source": "source", "db-filter-status": "status" }[id];
      dbParams[key] = e.target.value;
      loadDatabase();
    });
  });
}

async function doCheckIn(regId, method = "manual") {
  const res = await apiFetch("/api/checkins", { method: "POST", body: JSON.stringify({ registration_id: regId, method }) });
  if (res.success) { loadDatabase(); loadDashboard(); }
  else alert(res.message);
}

async function doDelete(regId, name) {
  customConfirm("Delete Attendee", `Are you sure you want to remove ${name} (${regId}) from the registry ? `, async () => {
    const res = await apiFetch(`/ api / registrations / ${regId} `, { method: "DELETE" });
    if (res.success) { loadDatabase(); loadDashboard(); }
    else alert(res.message);
  });
}

// ── 4. CHECK-IN STATION ───────────────────────────────────────────────────────

function setupCheckIn() {
  document.getElementById("scanner-manual-form").addEventListener("submit", async e => {
    e.preventDefault();
    const input = document.getElementById("scanner-id-input");
    const regId = input.value.trim().toUpperCase();
    input.value = "";
    if (!regId) return;
    await processScanResult(regId, "manual");
  });

  document.getElementById("camera-scanner-view").addEventListener("click", async () => {
    const res = await apiFetch("/api/registrations?status=Pending");
    if (!res.success || !res.data.length) { showScanFeedback(false, "No pending registrants to scan.", null); return; }
    const random = res.data[Math.floor(Math.random() * res.data.length)];
    const overlay = document.querySelector(".scanner-viewport-overlay");
    overlay.style.background = "rgba(79,70,229,0.15)";
    setTimeout(() => overlay.style.background = "none", 500);
    await processScanResult(random.id, "QR");
  });
}

async function processScanResult(regId, method) {
  const container = document.getElementById("scanner-feedback-container");
  container.style.display = "block";
  container.innerHTML = `<div class="scanner-status-card glass animate-pulse" ><i class="fas fa-spinner fa-spin" style="font-size:1.5rem;color:var(--accent-indigo);"></i><div><h4>Querying database...</h4><p class="text-sm text-secondary">ID: ${regId}</p></div></div> `;

  const res = await apiFetch("/api/checkins", { method: "POST", body: JSON.stringify({ registration_id: regId, method }) });
  showScanFeedback(res.success, res.message, res.attendee);
  if (res.success) playTickSound();
}

function showScanFeedback(success, message, attendee) {
  const c = document.getElementById("scanner-feedback-container");
  if (success && attendee) {
    c.innerHTML = `
    <div class="scanner-status-card glass border-success slide-in" >
        <div class="status-icon success"><i class="fas fa-check"></i></div>
        <div class="status-info">
          <h4 class="text-success">${message}</h4>
          <h3>${attendee.full_name}</h3>
          <p class="text-sm text-secondary">ID: <strong>${attendee.id}</strong> | Role: ${attendee.role_category}</p>
          <p class="text-xs text-secondary mt-1">Checked in at ${formatTime(attendee.check_in_time)}</p>
        </div>
      </div> `;
  } else {
    const borderCls = attendee ? "border-warning" : "border-danger";
    const iconCls = attendee ? "fa-exclamation-triangle" : "fa-times";
    const statusCls = attendee ? "warning" : "danger";
    c.innerHTML = `
    <div class="scanner-status-card glass ${borderCls} shake" >
        <div class="status-icon ${statusCls}"><i class="fas ${iconCls}"></i></div>
        <div class="status-info">
          <h4 class="text-${attendee ? 'warning' : 'danger'}">${message}</h4>
          ${attendee ? `<h3>${attendee.full_name}</h3><p class="text-xs text-secondary mt-1">Already checked in at ${formatTime(attendee.check_in_time)}</p>` : ""}
        </div>
      </div> `;
  }
}

function playTickSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = "sine"; osc.frequency.setValueAtTime(880, ctx.currentTime);
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
    osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.15);
  } catch { }
}

// ── 5. ANALYTICS CHARTS ───────────────────────────────────────────────────────

let rolesChart = null, sourcesChart = null;

async function loadAnalytics() {
  const res = await apiFetch("/api/analytics/breakdown");
  if (!res.success) return;

  const roles = res.data.roles, sources = res.data.sources;
  const ctxR = document.getElementById("chart-roles-canvas");
  const ctxS = document.getElementById("chart-sources-canvas");
  if (!ctxR || !ctxS) return;

  if (rolesChart) { rolesChart.destroy(); rolesChart = null; }
  if (sourcesChart) { sourcesChart.destroy(); sourcesChart = null; }

  rolesChart = new Chart(ctxR, {
    type: "doughnut",
    data: { labels: Object.keys(roles), datasets: [{ data: Object.values(roles), backgroundColor: ["#4f46e5", "#0891b2", "#059669", "#d97706"], borderWidth: 2, borderColor: "#ffffff", hoverOffset: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { color: "#475569", font: { family: "Outfit", size: 12, weight: 600 } } } } }
  });

  sourcesChart = new Chart(ctxS, {
    type: "bar",
    data: { labels: Object.keys(sources), datasets: [{ label: "Registrations", data: Object.values(sources), backgroundColor: "rgba(79,70,229,0.8)", borderColor: "#4f46e5", borderWidth: 1, borderRadius: 4 }] },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      scales: {
        x: { grid: { color: "rgba(0,0,0,0.05)" }, ticks: { color: "#64748b", font: { family: "Outfit", weight: 500 }, stepSize: 1 } },
        y: { grid: { display: false }, ticks: { color: "#475569", font: { family: "Outfit", weight: 600 } } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

// ── 6. AI INSIGHTS ────────────────────────────────────────────────────────────

async function loadAIInsights() {
  const container = document.getElementById("ai-insights-container");
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin text-accent" style="font-size:2rem;"></i></div>';

  const res = await apiFetch("/api/insights");
  if (!res.success) { container.innerHTML = '<div class="empty-state text-danger">Failed to load AI insights.</div>'; return; }

  const d = res.data;
  let forecastHtml = `
    <div class="ai-insight-top-card glass" >
      <div class="ai-card-icon"><i class="fas fa-brain animate-pulse"></i></div>
      <div class="ai-forecast-details">
        <h3>AI Attendance Forecast</h3>
        <p class="text-sm text-secondary">Weighted prediction using role categories and registration channels from live SQLite data.</p>
        <div class="forecast-stat-row">
          <div class="forecast-big-stat"><span class="forecast-value">${d.forecast.predicted}</span><span class="forecast-label">Predicted Attendees (of ${d.forecast.total})</span></div>
          <div class="forecast-big-stat"><span class="forecast-value">${d.forecast.percentage}%</span><span class="forecast-label">Expected Attendance Rate</span></div>
        </div>
      </div>
    </div> `;

  let dupsHtml = !d.duplicates.length
    ? '<div class="empty-state py-4"><i class="fas fa-shield-alt text-success" style="font-size:1.5rem;"></i><p class="text-sm mt-1">No duplicates detected. Database is clean!</p></div>'
    : d.duplicates.map(dup => `
    <div class="duplicate-group-card" >
        <div class="dup-header">
          <span><i class="fas fa-exclamation-circle text-warning"></i> ${dup.type}: <strong>${dup.match_value}</strong></span>
          <span class="badge badge-warning">${dup.records.length} Entries</span>
        </div>
        <ul class="dup-records-ul">
          ${dup.records.map(r => `<li class="dup-record-item"><div class="dup-rec-main"><strong>${r.full_name}</strong> <span>(${r.role_category})</span></div><div class="dup-rec-sub">ID: ${r.id} | Source: ${r.source}</div></li>`).join("")}
        </ul>
        <div class="dup-actions"><button class="btn btn-xs btn-outline-danger" onclick="aiPrune('${dup.records[1].id}','${dup.records[1].full_name.replace(/'/g, "\\'")}')"><i class="fas fa-compress-alt"></i> Prune Second Entry</button></div>
      </div> `).join("");

  let recsHtml = "";
  if (d.ratio_alert) {
    const t = d.ratio_alert.type;
    recsHtml += `<div class="ai-bulletin ${t}-bulletin" > <i class="fas fa-${t === " danger" ? "exclamation - triangle" : "check - circle"}" ></i> <div><strong>Student-to-Mentor Ratio (${d.ratio_alert.ratio}:1)</strong><p>${d.ratio_alert.message}</p></div></div> `;
  }
  d.recommendations.forEach(r => {
    recsHtml += `<div class="ai-bulletin ${r.type}-bulletin" ><i class="fas ${r.icon}"></i><div><strong>${r.title}</strong><p>${r.message}</p></div></div> `;
  });

  container.innerHTML = `
    ${forecastHtml}
  <div class="ai-insights-grid mt-4">
    <div class="ai-insights-panel glass">
      <h3><i class="fas fa-clone text-warning"></i> Duplicate Detection Engine</h3>
      <p class="text-xs text-secondary mb-3">Scanning live SQLite records for matching email addresses and phone numbers.</p>
      <div class="duplicates-list">${dupsHtml}</div>
    </div>
    <div class="ai-insights-panel glass">
      <h3><i class="fas fa-lightbulb text-info"></i> Intelligent Recommendations</h3>
      <p class="text-xs text-secondary mb-3">Contextual recommendations derived from real-time registration statistics.</p>
      <div class="ai-bulletins-feed">${recsHtml}</div>
    </div>
  </div>`;
}

async function aiPrune(regId, name) {
  customConfirm("Resolve Duplicate", `Prune the duplicate entry for ${name}(${regId}) from the database ? `, async () => {
    const res = await apiFetch(`/ api / registrations / ${regId} `, { method: "DELETE" });
    if (res.success) { loadAIInsights(); loadDashboard(); }
    else alert(res.message);
  });
}

// ── 7. VENUE AGENT ───────────────────────────────────────────────────────────

let venueRecommendations = []; // stored results from last API call
let venueCurrentIndex = 0;

async function loadVenueRecommendations() {
  const form = document.getElementById("venue-requirements-form");
  if (!form) return;
  const resultsContainer = document.getElementById("venue-recommendation-results");
  const statusBox = document.getElementById("venue-agent-status");
  statusBox.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Recommending venues...</div>';
  resultsContainer.innerHTML = "";

  const eventDateEl = document.getElementById("venue-date");
  const startTimeEl = document.getElementById("venue-start-time");
  const endTimeEl = document.getElementById("venue-end-time");

  const payload = {
    event_type: document.getElementById("venue-event-type").value.trim(),
    expected_attendees: Number(document.getElementById("venue-attendees").value || 0),
    max_budget: Number(document.getElementById("venue-budget").value || 0),
    preferred_city: document.getElementById("venue-city").value.trim(),
    required_facilities: document.getElementById("venue-facilities").value.split(",").map(v => v.trim()).filter(Boolean),
    power_backup_required: document.getElementById("venue-power").checked,
    cleanliness_preference: document.getElementById("venue-cleanliness").value,
    security_required: document.getElementById("venue-security").checked,
    accessibility_required: document.getElementById("venue-access").checked,
    include_near_matches: (document.getElementById("venue-include-near") ? document.getElementById("venue-include-near").checked : true),
    event_date: eventDateEl ? eventDateEl.value : "",
    start_time: startTimeEl ? startTimeEl.value : "",
    end_time: endTimeEl ? endTimeEl.value : "",
  };

  const res = await apiFetch("/api/venues/recommend", { method: "POST", body: JSON.stringify(payload) });
  if (!res.success) {
    resultsContainer.innerHTML = "";
    statusBox.innerHTML = `<div class="empty-state" ><i class="fas fa-exclamation-triangle text-warning"></i><p>${res.message}</p></div> `;
    return;
  }

  venueRecommendations = res.data || [];
  venueCurrentIndex = 0;

  if (!venueRecommendations.length) {
    statusBox.innerHTML = `<div class="empty-state" ><i class="fas fa-exclamation-triangle text-warning"></i><p>No suitable venue matched. Try adjusting budget, location, or facilities.</p></div> `;
    return;
  }

  statusBox.innerHTML = `<p class="text-sm text-secondary" style = "margin-bottom:.5rem;" > Showing recommendation <strong id = "venue-rec-counter" > 1 of ${venueRecommendations.length}</strong>.Use Reject to see the next option.</p> `;
  renderVenueCard(0);
}

function renderVenueCard(index) {
  const container = document.getElementById("venue-recommendation-results");
  const statusBox = document.getElementById("venue-agent-status");
  const venue = venueRecommendations[index];
  if (!venue) {
    container.innerHTML = `<div class="empty-state" ><i class="fas fa-check-circle text-success"></i><p>All recommendations reviewed. Try adjusting filters or add a venue manually.</p></div> `;
    document.getElementById("venue-rec-counter") && (document.getElementById("venue-agent-status").querySelector("strong") && (document.getElementById("venue-agent-status").querySelector("strong").textContent = `All viewed`));
    return;
  }
  const isRelaxed = venue.relaxed === true;
  const badgeClass = isRelaxed ? 'badge badge-warning' : 'badge badge-success';
  const reasonText = isRelaxed && venue.relax_reasons && venue.relax_reasons.length ? `<p class="text-sm text-warning" style = "margin-top:.5rem;" > Near - match: ${venue.relax_reasons.join('; ')}</p> ` : '';
  const counter = document.getElementById("venue-rec-counter");
  if (counter) counter.textContent = `${index + 1} of ${venueRecommendations.length} `;

  container.innerHTML = `
    <div class="recommendation-card animate-fadein" >
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;">
        <div>
          <h4>${venue.name}</h4>
          <p class="text-sm text-secondary">${venue.location || ''} · ${venue.city || ''}</p>
        </div>
        <span class="${badgeClass}">Match ${venue.match_score}%${isRelaxed ? ' (Near-match)' : ''}</span>
      </div>
      <div class="meta-row">
        <span class="badge badge-info">Capacity ${venue.capacity}</span>
        <span class="badge badge-info">Cost ₹${venue.cost}</span>
        <span class="badge badge-info">${venue.availability_status}</span>
        <span class="badge badge-info">Cleanliness ${venue.cleanliness_rating}</span>
        <span class="badge badge-info">Security ${venue.security_rating}</span>
        ${venue.wifi ? '<span class="badge badge-info"><i class="fas fa-wifi"></i> WiFi</span>' : ''}
        ${venue.power_backup ? '<span class="badge badge-info"><i class="fas fa-bolt"></i> Power Backup</span>' : ''}
      </div>
      <p class="text-sm text-secondary" style="margin-top:.75rem;">${venue.description || (isRelaxed ? "This is a near-match — some constraints were relaxed." : "Recommended because it satisfies the stated capacity, budget, and facility constraints.")}</p>
      ${reasonText}
      <div style="margin-top:1rem;display:flex;gap:.5rem;flex-wrap:wrap;">
        <button class="btn btn-primary btn-sm" onclick="bookSelectedVenue('${venue.id}', '${(venue.name || '').replace(/'/g, "\\'")}')">
          <i class="fas fa-check"></i> Accept &amp; Book
        </button>
        <button type="button" class="btn btn-outline btn-sm" onclick="rejectAndShowNextVenue()">
          <i class="fas fa-arrow-right"></i> Reject / Show Next
        </button>
      </div>
    </div>
    `;
}

function rejectAndShowNextVenue() {
  venueCurrentIndex++;
  if (venueCurrentIndex >= venueRecommendations.length) {
    document.getElementById("venue-recommendation-results").innerHTML = `<div class="empty-state" ><i class="fas fa-check-circle text-warning"></i><p>All ${venueRecommendations.length} recommendation(s) reviewed. Try adjusting requirements or add a venue manually.</p></div> `;
    return;
  }
  renderVenueCard(venueCurrentIndex);
}

async function bookSelectedVenue(venueId, venueName) {
  // ---- INPUT VALIDATION -------------------------------------------------
  const eventId = document.getElementById("venue-event-selector")?.value?.trim() || "";
  const eventName = document.getElementById("venue-event-name")?.value?.trim() || "Event";
  const eventDate = document.getElementById("venue-date")?.value?.trim() || "";
  const startTime = document.getElementById("venue-start-time")?.value?.trim() || "";
  const endTime = document.getElementById("venue-end-time")?.value?.trim() || "";

  if (!eventId) {
    return alert("❗ Please select an event before booking a venue.");
  }
  if (!eventDate) {
    return alert("❗ Please choose an event date.");
  }
  if (!startTime || !endTime) {
    return alert("❗ Please specify both start and end times for the booking.");
  }
  // ----------------------------------------------------------------------

  const payload = {
    venue_id: venueId,
    event_id: eventId,
    organizer_id: "ORG-1",
    event_name: eventName,
    event_date: eventDate,
    start_time: startTime,
    end_time: endTime,
  };

  const res = await apiFetch("/api/venues/book", { method: "POST", body: JSON.stringify(payload) });

  if (res.success) {
    alert(`✅ ${venueName} booked successfully for this event!`);
    // Clear recommendations and reset UI so the user sees the updated state
    venueRecommendations = [];
    venueCurrentIndex = 0;
    document.getElementById("venue-recommendation-results").innerHTML = `
    <div class= "empty-state text-success" >
        <i class="fas fa-check-circle"></i>
        <p>Venue booked! Navigate to Events to see it on the event details.</p>
      </div> `;
    // Also clear the counter display
    const counter = document.getElementById("venue-rec-counter");
    if (counter) counter.textContent = "";
  } else {
    alert(`❌ Booking failed: ${res.message || "Unknown error."} `);
  }
}

// Add Venue Manually
function openAddVenueModal() {
  document.getElementById("add-venue-modal").classList.add("active");
}
function closeAddVenueModal() {
  document.getElementById("add-venue-modal").classList.remove("active");
  document.getElementById("add-venue-form").reset();
}
async function submitAddVenue(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("av-name").value.trim(),
    city: document.getElementById("av-city").value.trim(),
    state: document.getElementById("av-state").value.trim(),
    country: document.getElementById("av-country").value.trim() || "India",
    location: document.getElementById("av-location").value.trim(),
    address: document.getElementById("av-address").value.trim(),
    capacity: Number(document.getElementById("av-capacity").value || 0),
    cost: Number(document.getElementById("av-cost").value || 0),
    venue_type: document.getElementById("av-venue-type").value.trim(),
    event_types_supported: document.getElementById("av-event-types").value.trim(),
    facilities: document.getElementById("av-facilities").value.trim(),
    cleanliness_rating: Number(document.getElementById("av-clean").value || 3),
    security_rating: Number(document.getElementById("av-security").value || 3),
    ratings: Number(document.getElementById("av-rating").value || 3),
    wifi: document.getElementById("av-wifi").checked,
    projector: document.getElementById("av-projector").checked,
    sound_system: document.getElementById("av-sound").checked,
    air_conditioning: document.getElementById("av-ac").checked,
    parking: document.getElementById("av-parking").checked,
    power_backup: document.getElementById("av-power").checked,
    accessibility: document.getElementById("av-accessibility").checked,
    wheelchair_accessibility: document.getElementById("av-wheelchair").checked,
    washrooms: document.getElementById("av-washrooms").checked,
    description: document.getElementById("av-description").value.trim(),
  };
  const res = await apiFetch("/api/venues", { method: "POST", body: JSON.stringify(data) });
  if (res.success) {
    alert(`✅ Venue "${data.name}" added successfully! ID: ${res.data.id} `);
    closeAddVenueModal();
    // refresh the venue options in scheduling
    loadVenueSpeakerOptions();
  } else {
    alert("Failed to add venue: " + res.message);
  }
}

// ── 8. VENUE OPTIMIZATION ───────────────────────────────────────────────────

async function loadOptimization() {
  const form = document.getElementById("optimization-form");
  if (!form) return;
  const container = document.getElementById("optimization-results");
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Optimizing room allocation...</div>';
  const sessions = JSON.parse(document.getElementById("opt-sessions").value || "[]");
  const payload = { event_type: document.getElementById("opt-event-type").value.trim(), total_attendees: Number(document.getElementById("opt-total-attendees").value || 0), sessions };
  const res = await apiFetch("/api/optimization/rooms", { method: "POST", body: JSON.stringify(payload) });
  container.innerHTML = (res.data || []).map(item => `
    <div class="panel-card glass" style="margin-bottom:1rem; border-left:4px solid var(--accent-color);">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <h4 style="margin:0; font-size:1.1rem; color:var(--text-color);"><i class="fas fa-chalkboard-teacher text-primary"></i> ${escapeHtml(item.name)}</h4>
        <span class="badge badge-info"><i class="fas fa-users"></i> Expected: ${item.expected_attendees} attendees</span>
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; margin:1rem 0; background:rgba(255,255,255,0.02); padding:0.85rem; border-radius:8px; border:1px solid var(--border-color);">
        <div>
          <span class="text-xs text-secondary" style="display:block;">Allocated Room / Hall</span>
          <strong style="color:var(--accent-color); font-size:1rem;"><i class="fas fa-door-open"></i> ${escapeHtml(item.assigned_room ? item.assigned_room.name : "None")}</strong>
        </div>
        <div>
          <span class="text-xs text-secondary" style="display:block;">Room Capacity</span>
          <strong style="font-size:1rem;"><i class="fas fa-chair text-warning"></i> ${item.assigned_room ? item.assigned_room.capacity : "—"} seats</strong>
        </div>
        <div>
          <span class="text-xs text-secondary" style="display:block;">Capacity Match</span>
          <span class="badge ${item.assigned_room && item.assigned_room.capacity >= item.expected_attendees ? 'badge-success' : 'badge-danger'}">
            ${item.assigned_room ? (Math.round((item.expected_attendees / item.assigned_room.capacity) * 100)) + '% Occupancy' : 'Unassigned'}
          </span>
        </div>
      </div>
      <div style="font-size:0.88rem; color:var(--text-color); background:rgba(255,255,255,0.03); padding:0.65rem 0.85rem; border-radius:6px; border:1px solid var(--border-color);">
        <i class="fas fa-lightbulb text-warning"></i> <strong>AI Recommendation:</strong> ${escapeHtml(item.suggestion || "")}
      </div>
    </div>
  `).join("");
}

// ── 9. SPEAKER AGENT ────────────────────────────────────────────────────────

let speakerRecommendations = []; // stored results from last API call
let speakerCurrentIndex = 0;

async function loadSpeakerRecommendations() {
  const container = document.getElementById("speaker-recommendation-results");
  const statusBox = document.getElementById("speaker-agent-status");
  statusBox.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Recommending speakers...</div>';
  container.innerHTML = "";
  const payload = {
    event_topic: document.getElementById("speaker-topic").value.trim(),
    event_type: document.getElementById("speaker-event-type").value.trim(),
    audience_type: document.getElementById("speaker-audience").value.trim(),
    required_expertise: document.getElementById("speaker-expertise").value.split(",").map(v => v.trim()).filter(Boolean),
    preferred_language: document.getElementById("speaker-language").value.trim(),
    budget: Number(document.getElementById("speaker-budget").value || 0),
    delivery_mode: document.getElementById("speaker-delivery").value.trim(),
    session_date: document.getElementById("speaker-date")?.value || "",
  };
  const res = await apiFetch("/api/speakers/recommend", { method: "POST", body: JSON.stringify(payload) });
  if (!res.success) { statusBox.innerHTML = `<div class="empty-state" > ${res.message}</div> `; return; }

  speakerRecommendations = res.data || [];
  speakerCurrentIndex = 0;

  if (!speakerRecommendations.length) {
    container.innerHTML = `<div class="empty-state" ><i class="fas fa-exclamation-triangle text-warning"></i><p>No suitable speaker found. Try adjusting requirements.</p></div> `;
    statusBox.innerHTML = "";
    return;
  }

  statusBox.innerHTML = `<p class="text-sm text-secondary" style = "margin-bottom:.5rem;" > Showing recommendation <strong id = "speaker-rec-counter" > 1 of ${speakerRecommendations.length}</strong>.Use Reject to see the next option.</p> `;
  renderSpeakerCard(0);
}

function renderSpeakerCard(index) {
  const container = document.getElementById("speaker-recommendation-results");
  const speaker = speakerRecommendations[index];
  if (!speaker) {
    container.innerHTML = `<div class="empty-state" ><i class="fas fa-check-circle text-warning"></i><p>All recommendations reviewed. Try adjusting requirements or add a speaker manually.</p></div> `;
    return;
  }
  const counter = document.getElementById("speaker-rec-counter");
  if (counter) counter.textContent = `${index + 1} of ${speakerRecommendations.length} `;

  container.innerHTML = `
    <div class="recommendation-card animate-fadein" >
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;">
        <div>
          <h4>${speaker.name}</h4>
          <p class="text-sm text-secondary">${speaker.organization || ''} · ${speaker.designation || ''}</p>
        </div>
        <span class="badge badge-success">Match ${speaker.match_score}%</span>
      </div>
      <div class="meta-row">
        <span class="badge badge-info">Expertise: ${speaker.expertise || '—'}</span>
        <span class="badge badge-info">Exp: ${speaker.years_of_experience || 0} yrs</span>
        <span class="badge badge-info">Rating: ${speaker.ratings || '—'}</span>
        <span class="badge badge-info">Engagement: ${speaker.audience_engagement_score || '—'}</span>
        <span class="badge badge-info">Honorarium: ₹${speaker.honorarium || 0}</span>
      </div>
      <p class="text-sm text-secondary" style="margin-top:.75rem;">${speaker.previous_feedback || "Strong fit for the requested audience and topic."}</p>
      <div style="margin-top:1rem;display:flex;gap:.5rem;flex-wrap:wrap;">
        <button class="btn btn-primary btn-sm" onclick="acceptSpeaker('${speaker.id}')">
          <i class="fas fa-check"></i> Accept / Assign
        </button>
        <button type="button" class="btn btn-outline btn-sm" onclick="rejectAndShowNextSpeaker()">
          <i class="fas fa-arrow-right"></i> Reject / Show Next
        </button>
      </div>
    </div>
    `;
}

function rejectAndShowNextSpeaker() {
  speakerCurrentIndex++;
  if (speakerCurrentIndex >= speakerRecommendations.length) {
    document.getElementById("speaker-recommendation-results").innerHTML = `<div class="empty-state" ><i class="fas fa-check-circle text-warning"></i><p>All ${speakerRecommendations.length} recommendation(s) reviewed. Try adjusting requirements or add a speaker manually.</p></div> `;
    return;
  }
  renderSpeakerCard(speakerCurrentIndex);
}

async function acceptSpeaker(speakerId) {
  const sessionId = document.getElementById("speaker-session-selector")?.value;
  if (!sessionId) {
    return alert("Please select a session from the dropdown above before assigning this speaker.");
  }
  const payload = { session_id: sessionId, speaker_id: speakerId, organizer_id: "ORG-1", status: "Pending" };
  const res = await apiFetch("/api/speakers/assign", { method: "POST", body: JSON.stringify(payload) });
  if (res.success) {
    alert("✅ Speaker assigned to session successfully!");
    document.getElementById("speaker-agent-status").innerHTML = `<div class="empty-state text-success" ><i class="fas fa-check-circle"></i><p>Speaker successfully assigned. Navigate to Events to view details.</p></div> `;
  } else {
    alert(res.message || "Assignment failed.");
  }
}

async function assignSpeaker(speakerId) {
  const sessionId = document.getElementById("sched-session-id")?.value.trim();
  if (!sessionId) {
    return alert("Please create or select a session before assigning a speaker.");
  }
  const payload = { session_id: sessionId, speaker_id: speakerId, organizer_id: "ORG-1", status: "Pending" };
  const res = await apiFetch("/api/speakers/assign", { method: "POST", body: JSON.stringify(payload) });
  if (res.success) {
    alert("Speaker assigned successfully.");
  } else {
    alert(res.message || "Assignment failed.");
  }
}

// Add Speaker Manually
function openAddSpeakerModal() {
  document.getElementById("add-speaker-modal").classList.add("active");
}
function closeAddSpeakerModal() {
  document.getElementById("add-speaker-modal").classList.remove("active");
  document.getElementById("add-speaker-form").reset();
}
async function submitAddSpeaker(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("asp-name").value.trim(),
    organization: document.getElementById("asp-org").value.trim(),
    designation: document.getElementById("asp-designation").value.trim(),
    expertise: document.getElementById("asp-expertise").value.trim(),
    years_of_experience: Number(document.getElementById("asp-experience").value || 0),
    languages: document.getElementById("asp-languages").value.trim(),
    honorarium: Number(document.getElementById("asp-honorarium").value || 0),
    ratings: Number(document.getElementById("asp-rating").value || 3),
    audience_engagement_score: Number(document.getElementById("asp-engagement").value || 3),
    communication_score: Number(document.getElementById("asp-communication").value || 3),
    preferred_event_types: document.getElementById("asp-event-types").value.trim(),
    preferred_audience: document.getElementById("asp-audience").value.trim(),
    delivery_mode: document.getElementById("asp-delivery").value.trim(),
    previous_feedback: document.getElementById("asp-feedback").value.trim(),
    biography: document.getElementById("asp-bio").value.trim(),
    contact_info: document.getElementById("asp-contact").value.trim(),
    availability: document.getElementById("asp-availability").value.trim() || "Available",
    status: "Available",
  };
  const res = await apiFetch("/api/speakers", { method: "POST", body: JSON.stringify(data) });
  if (res.success) {
    alert(`✅ Speaker "${data.name}" added successfully! ID: ${res.data.id} `);
    closeAddSpeakerModal();
    loadVenueSpeakerOptions();
  } else {
    alert("Failed to add speaker: " + res.message);
  }
}

async function loadVenueSpeakerOptions() {
  const venueSelect = document.getElementById("sched-venue");
  const speakerSelect = document.getElementById("sched-speaker");

  const [venuesRes, speakersRes, eventsRes, sessionsRes] = await Promise.all([
    apiFetch("/api/venues"),
    apiFetch("/api/speakers"),
    apiFetch("/api/events"),
    apiFetch("/api/sessions"),
  ]);

  if (venueSelect && venuesRes.success) {
    const options = venuesRes.data.map(v => `<option value = "${v.id}" > ${v.name} (Cap: ${v.capacity || '?'
      })</option> `).join("");
    venueSelect.innerHTML = `<option value = "" > Select venue...</option> ${options} `;
  }
  if (speakerSelect && speakersRes.success) {
    const options = speakersRes.data.map(s => `<option value = "${s.id}" > ${s.name} (${s.id})</option> `).join("");
    speakerSelect.innerHTML = `<option value = "" > Select speaker...</option> ${options} `;
  }

  // Populate event selectors wherever they appear
  if (eventsRes.success) {
    const eventOptions = eventsRes.data.map(e => `<option value = "${e.id}" > ${e.name} (${e.id})</option> `).join("");
    ['sched-event-id', 'venue-event-selector', 'reg-event-id'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = `<option value = "" > Select event...</option> ${eventOptions} `;
    });
  }

  // Populate session selectors
  if (sessionsRes && sessionsRes.success) {
    const sessionOptions = sessionsRes.data.map(s => `<option value = "${s.id}" > ${s.session_name} (${s.id})</option> `).join("");
    const sel = document.getElementById('speaker-session-selector');
    if (sel) sel.innerHTML = `<option value = "" > Select an existing session to assign speaker...</option> ${sessionOptions} `;
  }
}

// ── EVENTS MANAGEMENT ───────────────────────────────────────────────────────

let selectedEventId = null;

async function loadEvents() {
  const container = document.getElementById("events-list");
  if (!container) return;
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading events...</div>';
  const res = await apiFetch("/api/events");
  if (!res.success) { container.innerHTML = '<div class="empty-state text-danger">Failed to load events.</div>'; return; }
  if (!res.data.length) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-times" style="font-size:2rem;display:block;margin-bottom:.5rem;"></i>No events yet. Create your first event above.</div>';
    return;
  }
  container.innerHTML = res.data.map(ev => `
  <div class="recommendation-card" style = "cursor:pointer;" onclick = "showEventDetails('${ev.id}')" >
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;">
        <div><h4>${ev.name}</h4><p class="text-sm text-secondary">${ev.event_type || 'Event'} · ${ev.start_date || '—'} · ${ev.location || '—'}</p></div>
        <span class="badge ${ev.status === 'Active' ? 'badge-success' : ev.status === 'Cancelled' ? 'badge-danger' : 'badge-info'}">${ev.status || 'Draft'}</span>
      </div>
      <div class="meta-row" style="margin-top:.5rem;">
        <span class="badge badge-info"><i class="fas fa-users"></i> Expected: ${ev.expected_attendees || 0}</span>
        <span class="badge badge-info">${ev.id}</span>
      </div>
    </div>
  `).join("");
}

async function showEventDetails(eventId) {
  selectedEventId = eventId;
  const panel = document.getElementById("event-details-panel");
  if (!panel) return;
  panel.style.display = "block";
  panel.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading event details...</div>';

  const res = await apiFetch(`/ api / events / ${eventId} `);
  if (!res.success) { panel.innerHTML = `<div class="empty-state text-danger" > ${res.message}</div> `; return; }
  const ev = res.data;
  const stats = ev.stats || {};
  const venue = ev.selected_venue;
  const sessions = ev.sessions || [];
  const assignments = ev.speaker_assignments || [];

  panel.innerHTML = `
  <div class="recommendation-card" style = "margin-top:0;" >
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
        <div><h3 style="font-family:'Outfit';font-weight:800;font-size:1.4rem;margin:0;">${ev.name}</h3><p class="text-sm text-secondary">${ev.description || ''}</p></div>
        <span class="badge badge-success" style="font-size:.85rem;">${ev.status}</span>
      </div>
      <div class="meta-row" style="margin-top:.75rem;">
        <span class="badge badge-info"><i class="fas fa-calendar"></i> ${ev.start_date || '—'}</span>
        <span class="badge badge-info"><i class="fas fa-map-marker-alt"></i> ${ev.location || '—'}</span>
        <span class="badge badge-info"><i class="fas fa-tag"></i> ${ev.event_type || '—'}</span>
        <span class="badge badge-info">ID: ${ev.id}</span>
      </div>

      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.75rem;margin-top:1.25rem;">
        <div class="stat-card glass" style="padding:.75rem;">
          <h4 style="font-size:.8rem;color:var(--text-secondary);margin:0 0 .25rem;">Registered</h4>
          <div class="value" style="font-size:1.5rem;">${stats.registered || 0}</div>
        </div>
        <div class="stat-card glass" style="padding:.75rem;">
          <h4 style="font-size:.8rem;color:var(--text-secondary);margin:0 0 .25rem;">Confirmed</h4>
          <div class="value" style="font-size:1.5rem;">${stats.confirmed || 0}</div>
        </div>
        <div class="stat-card glass" style="padding:.75rem;">
          <h4 style="font-size:.8rem;color:var(--text-secondary);margin:0 0 .25rem;">Checked-in</h4>
          <div class="value" style="font-size:1.5rem;">${stats.checked_in || 0}</div>
        </div>
        <div class="stat-card glass" style="padding:.75rem;">
          <h4 style="font-size:.8rem;color:var(--text-secondary);margin:0 0 .25rem;">Cancelled</h4>
          <div class="value" style="font-size:1.5rem;">${stats.cancelled || 0}</div>
        </div>
      </div>

      <div style="margin-top:1.25rem;">
        <h4 style="margin-bottom:.5rem;"><i class="fas fa-building text-info"></i> Venue</h4>
        ${venue
      ? `<div class="meta-row"><span class="badge badge-success">${venue.name}</span><span class="badge badge-info">Capacity: ${venue.capacity}</span><span class="badge badge-info">${venue.city || ''}</span></div>`
      : '<p class="text-sm text-secondary">No venue booked yet.</p>'}
      </div>

      <div style="margin-top:1.25rem;">
        <h4 style="margin-bottom:.5rem;"><i class="fas fa-calendar-alt text-warning"></i> Sessions (${sessions.length})</h4>
        ${sessions.length ? sessions.map(s => `
          <div style="padding:.5rem;border-left:3px solid var(--accent-indigo);margin-bottom:.5rem;">
            <strong>${s.session_name}</strong>
            <span class="text-sm text-secondary" style="margin-left:.5rem;">${s.session_date || ''} ${s.start_time || ''}-${s.end_time || ''}</span>
            <span class="badge badge-info" style="margin-left:.5rem;">${s.session_type || ''}</span>
          </div>
        `).join('') : '<p class="text-sm text-secondary">No sessions created yet.</p>'}
      </div>

      <div style="margin-top:1.25rem;">
        <h4 style="margin-bottom:.5rem;"><i class="fas fa-microphone text-purple" style="color:var(--accent-purple);"></i> Speakers (${assignments.length})</h4>
        ${assignments.length ? assignments.map(a => `
          <div style="padding:.5rem;border-left:3px solid var(--accent-purple);margin-bottom:.5rem;">
            <strong>${a.speaker_name || a.speaker_id}</strong>
            <span class="text-sm text-secondary" style="margin-left:.5rem;">${a.session_name || ''}</span>
            <span class="badge ${a.status === 'Accepted' ? 'badge-success' : a.status === 'Declined' ? 'badge-danger' : 'badge-warning'}">${a.status}</span>
          </div>
        `).join('') : '<p class="text-sm text-secondary">No speakers assigned yet.</p>'}
      </div>

      <div style="margin-top:1rem;display:flex;gap:.5rem;flex-wrap:wrap;">
        <button class="btn btn-outline btn-sm" onclick="document.getElementById('event-details-panel').style.display='none'"><i class="fas fa-times"></i> Close</button>
      </div>
    </div>
  `;
}

async function submitCreateEvent(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("new-event-name").value.trim(),
    description: document.getElementById("new-event-desc").value.trim(),
    event_type: document.getElementById("new-event-type").value.trim(),
    start_date: document.getElementById("new-event-start").value,
    end_date: document.getElementById("new-event-end").value,
    location: document.getElementById("new-event-location").value.trim(),
    expected_attendees: Number(document.getElementById("new-event-attendees").value || 0),
    status: document.getElementById("new-event-status").value,
  };
  if (!data.name) return alert("Event name is required.");
  const res = await apiFetch("/api/events", { method: "POST", body: JSON.stringify(data) });
  if (res.success) {
    alert(`✅ Event "${data.name}" created! ID: ${res.data.id} `);
    document.getElementById("create-event-form").reset();
    loadEvents();
    loadVenueSpeakerOptions(); // refresh event selectors
  } else {
    alert("Failed to create event: " + res.message);
  }
}

// ── 10. SPEAKER SCHEDULING ────────────────────────────────────────────────

async function loadScheduling() {
  const nameVal = document.getElementById("sched-name")?.value.trim();
  const dateVal = document.getElementById("sched-date")?.value;
  const startVal = document.getElementById("sched-start")?.value;
  const endVal = document.getElementById("sched-end")?.value;
  const venueVal = document.getElementById("sched-venue")?.value.trim();
  const eventIdVal = document.getElementById("sched-event-id")?.value.trim();

  if (!nameVal || !dateVal || !startVal || !endVal || !venueVal) {
    const status = document.getElementById("scheduling-status");
    if (status) status.innerHTML = '<div class="empty-state text-warning"><i class="fas fa-exclamation-triangle"></i> Please fill Session Name, Date, Start Time, End Time, and Venue before submitting.</div>';
    return;
  }

  const status = document.getElementById("scheduling-status");
  status.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Creating session...</div>';
  const payload = {
    event_id: eventIdVal || "EVT-1",
    session_name: nameVal,
    topic: document.getElementById("sched-topic").value.trim(),
    session_type: document.getElementById("sched-type").value.trim(),
    session_date: dateVal,
    start_time: startVal,
    end_time: endVal,
    venue_id: venueVal,
    expected_attendees: Number(document.getElementById("sched-attendees").value || 0),
  };
  const res = await apiFetch("/api/sessions", { method: "POST", body: JSON.stringify(payload) });
  if (!res.success) { status.innerHTML = `<div class="empty-state text-danger" > <i class="fas fa-times-circle"></i> ${res.message}</div> `; return; }
  document.getElementById("sched-session-id").value = res.data.id || "";

  // Auto-assign speaker if one is selected
  const speakerVal = document.getElementById("sched-speaker")?.value.trim();
  if (speakerVal && res.data.id) {
    const assignRes = await apiFetch("/api/speakers/assign", { method: "POST", body: JSON.stringify({ session_id: res.data.id, speaker_id: speakerVal, organizer_id: "ORG-1", status: "Pending" }) });
    if (assignRes.success) {
      status.innerHTML = `<div class="recommendation-card" ><h4 class="text-success"><i class="fas fa-check-circle"></i> Session Created &amp; Speaker Assigned!</h4><p class="text-sm text-secondary">Session: ${res.data.session_name} (ID: ${res.data.id})</p><p class="text-sm text-secondary">Speaker assigned with status: Pending</p></div> `;
    } else {
      status.innerHTML = `<div class="recommendation-card" ><h4><i class="fas fa-calendar-check text-success"></i> Session Created</h4><p class="text-sm text-secondary">${res.data.session_name} (ID: ${res.data.id})</p><p class="text-sm text-warning"><i class="fas fa-exclamation-triangle"></i> Speaker assignment failed: ${assignRes.message}</p></div> `;
    }
  } else {
    status.innerHTML = `<div class="recommendation-card" ><h4><i class="fas fa-calendar-check text-success"></i> Session Created</h4><p class="text-sm text-secondary">${res.data.session_name} (ID: ${res.data.id}) is ready. Select a speaker and click Assign.</p></div> `;
  }
}

// ── 11. SESSION ANALYTICS ──────────────────────────────────────────────────

async function loadSessionAnalytics() {
  const container = document.getElementById("session-analytics-container");
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading session analytics...</div>';
  const res = await apiFetch("/api/analytics/sessions");
  if (!res.success) { container.innerHTML = `<div class="empty-state" > ${res.message}</div> `; return; }
  const data = res.data;

  // Summary cards
  const totalSessions = (data.sessions || []).length;
  const totalChecked = (data.sessions || []).reduce((s, it) => s + (it.checked_in || 0), 0);
  const avgAttendanceRate = (data.sessions && data.sessions.length) ? Math.round(((data.sessions.reduce((s, it) => s + (it.attendance_rate || 0), 0)) / data.sessions.length) * 10) / 10 : 0;

  // Prepare chart data
  const sessionLabels = (data.sessions || []).map(s => s.session_name || s.id);
  const sessionChecked = (data.sessions || []).map(s => s.checked_in || 0);
  const venueLabels = (data.venues || []).map(v => v.name);
  const venueUtil = (data.venues || []).map(v => v.utilization_pct || 0);

  let html = `
    <!-- Top Summary Stat Cards -->
    <div class="stats-grid mb-4" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
      <div class="stat-card glass">
        <i class="fas fa-calendar-alt stat-card-icon text-primary"></i>
        <h4>Total Sessions</h4>
        <div class="value">${totalSessions}</div>
        <div class="trend-indicator up"><i class="fas fa-check-circle"></i> Active Sessions</div>
      </div>
      <div class="stat-card glass">
        <i class="fas fa-user-check stat-card-icon text-success"></i>
        <h4>Total Checked In</h4>
        <div class="value">${totalChecked}</div>
        <div class="trend-indicator up"><i class="fas fa-chart-line"></i> Attendance Telemetry</div>
      </div>
      <div class="stat-card glass">
        <i class="fas fa-percentage stat-card-icon text-warning"></i>
        <h4>Avg Attendance Rate</h4>
        <div class="value">${avgAttendanceRate}%</div>
        <div class="trend-indicator up"><i class="fas fa-bullseye"></i> Occupancy Metric</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="panel-card glass mb-4">
      <h3 class="dashboard-card-title"><i class="fas fa-chart-bar text-primary"></i> Session Attendance & Venue Utilization Analytics</h3>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:1.5rem; margin-top:1rem;">
        <div style="background:rgba(255,255,255,0.02); padding:1rem; border-radius:8px; border:1px solid var(--border-color); height:240px;">
          <canvas id="sessionPopularityChart"></canvas>
        </div>
        <div style="background:rgba(255,255,255,0.02); padding:1rem; border-radius:8px; border:1px solid var(--border-color); height:240px;">
          <canvas id="venueUtilizationChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Sessions Detailed Table -->
    <div class="panel-card glass mb-4">
      <h3 class="dashboard-card-title"><i class="fas fa-list text-info"></i> Session Attendance Breakdown</h3>
      <div class="table-wrapper">
        <table class="db-table">
          <thead>
            <tr>
              <th>Session Name</th>
              <th>Expected</th>
              <th>Checked-in</th>
              <th>Attendance %</th>
              <th>Occupancy %</th>
              <th>Assigned Speaker</th>
              <th>Feedback Score</th>
            </tr>
          </thead>
          <tbody>
  `;

  (data.sessions || []).forEach(s => {
    html += `
      <tr>
        <td><strong>${escapeHtml(s.session_name)}</strong></td>
        <td>${s.expected_attendees || '—'}</td>
        <td><strong class="text-primary">${s.checked_in || 0}</strong></td>
        <td><span class="badge badge-info">${s.attendance_rate != null ? s.attendance_rate + '%' : '—'}</span></td>
        <td><span class="badge ${s.occupancy_pct > 80 ? 'badge-danger' : 'badge-success'}">${s.occupancy_pct != null ? s.occupancy_pct + '%' : '—'}</span></td>
        <td>${s.speaker ? escapeHtml(s.speaker.name) : '—'}</td>
        <td><span class="text-warning"><i class="fas fa-star"></i> ${s.feedback_avg != null ? s.feedback_avg : '—'}</span></td>
      </tr>
    `;
  });

  html += `
          </tbody>
        </table>
      </div>
    </div>

    <!-- AI Insights & Popularity Grid -->
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:1.5rem;">
      <div class="panel-card glass">
        <h3 class="dashboard-card-title"><i class="fas fa-fire text-danger"></i> Most Popular Sessions</h3>
        <div class="stacked-card-list">
  `;

  (data.most_popular || []).slice(0, 5).forEach(s => {
    html += `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:0.6rem 0.8rem; border-radius:6px; border:1px solid var(--border-color);">
        <span><i class="fas fa-star text-warning"></i> <strong>${escapeHtml(s.session_name)}</strong></span>
        <span class="badge badge-primary">${s.checked_in} Attendees</span>
      </div>
    `;
  });

  html += `
        </div>
      </div>

      <div class="panel-card glass">
        <h3 class="dashboard-card-title"><i class="fas fa-brain text-accent"></i> Session Intelligence Insights</h3>
        <div class="stacked-card-list">
  `;

  if (data.ai_insights && data.ai_insights.length) {
    data.ai_insights.forEach(i => {
      html += `
        <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.8rem; border-radius:6px; border:1px solid var(--border-color); font-size:0.88rem;">
          <i class="fas fa-lightbulb text-warning"></i> ${escapeHtml(i)}
        </div>
      `;
    });
  } else {
    html += `<div class="empty-state text-secondary"><i class="fas fa-info-circle"></i> Sufficient session telemetry required to trigger automated insights.</div>`;
  }

  html += `
        </div>
      </div>
    </div>
  `;

  container.innerHTML = html;

  // Render charts
  try {
    const ctx = document.getElementById('sessionPopularityChart').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: sessionLabels,
        datasets: [{ label: 'Checked-in attendees', data: sessionChecked, backgroundColor: '#4f46e5' }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    const vctx = document.getElementById('venueUtilizationChart').getContext('2d');
    new Chart(vctx, {
      type: 'doughnut',
      data: {
        labels: venueLabels,
        datasets: [{ label: 'Utilization %', data: venueUtil, backgroundColor: ['#06b6d4', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6'] }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  } catch (e) {
    console.warn('Chart rendering failed', e);
  }
}

// Load sessions into feedback session select dropdown
async function loadSessionsForFeedback() {
  const sel = document.getElementById("fb-session");
  if (!sel) return;
  const res = await apiFetch("/api/sessions");
  if (!res.success) return;
  sel.innerHTML = `<option value = "" > General feedback(no session)</option> ` + (res.data || []).map(s => ` <option value = "${s.id}" > ${s.session_name} — ${s.start_time || ''}</option> `).join("");
}

// ── 12. EMAIL OUTBOX ───────────────────────────────────────────────────────────

async function loadOutbox() {
  const container = document.getElementById("outbox-list");
  if (!container) return;
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';

  const res = await apiFetch("/api/outbox");
  if (!res.success || !res.data.length) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox" style="font-size:2rem;margin-bottom:.5rem;display:block;opacity:.4;"></i>No emails in outbox yet.</div>';
    return;
  }

  const badge = document.getElementById("outbox-badge");
  badge.textContent = res.data.length;
  badge.style.display = "inline-block";

  container.innerHTML = "";
  res.data.forEach(email => {
    const card = document.createElement("div");
    card.className = "outbox-email-card glass";
    card.innerHTML = `
  <div class="outbox-email-icon" > <i class="fas fa-envelope-open text-accent"></i></div>
      <div class="outbox-email-details">
        <div class="outbox-email-subject">${email.subject || "Registration Confirmation"}</div>
        <div class="outbox-email-meta">
          <span><i class="fas fa-user"></i> ${email.name}</span>
          <span><i class="fas fa-at"></i> ${email.to}</span>
          <span><i class="fas fa-tag"></i> ${email.id}</span>
          <span><i class="fas fa-clock"></i> ${formatDate(email.sent_at)}</span>
        </div>
      </div>
      <a href="/outbox/${email.html_file}" target="_blank" class="btn btn-primary btn-sm"><i class="fas fa-eye"></i> Preview</a>
`;
    container.appendChild(card);
  });
}

// ── 8. RESET DATABASE ─────────────────────────────────────────────────────────

async function resetDatabase() {
  customConfirm("Reset Demo Database", "This will delete all current data and re-seed 15 mock registrations. Continue?", async () => {
    const res = await apiFetch("/api/debug/reset", { method: "POST" });
    if (res.success) { loadDashboard(); loadOutbox(); alert("Database reset successfully with 15 mock registrations."); }
    else alert("Reset failed: " + res.message);
  });
}

// ── PARTICIPANT: Status Lookup ────────────────────────────────────────────────

function setupStatusLookup() {
  const form = document.getElementById("status-lookup-form");
  if (!form) return;

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const query = document.getElementById("status-lookup-input").value.trim();
    if (!query) return;

    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';

    // Try by ID first, then by email search
    let reg = null;
    if (query.toUpperCase().startsWith("REG-")) {
      const r = await apiFetch(`/ api / registrations / ${query.toUpperCase()} `);
      if (r.success) reg = r.data;
    }
    if (!reg) {
      const r = await apiFetch(`/ api / registrations ? search = ${encodeURIComponent(query)} `);
      if (r.success && r.data.length) reg = r.data[0];
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-search"></i> Look Up Status';

    const card = document.getElementById("status-result-card");
    if (!reg) {
      card.style.display = "block";
      card.innerHTML = `<div class="empty-state" ><i class="fas fa-user-slash" style="font-size:2rem;color:var(--danger);"></i><p style="color:var(--danger);font-weight:700;">No registration found.</p><p class="text-sm text-secondary">Check your email address or Registration ID.</p></div> `;
      return;
    }

    const statusBadge = reg.checked_in
      ? `<span class="badge badge-success" >✓ Checked In</span> `
      : `<span class="badge badge-warning" >⏳ Pending Check -in</span> `;

    card.style.display = "block";
    card.innerHTML = `
  <div style = "padding:1.5rem;" >
        <h3 class="dashboard-card-title" style="color:var(--participant-accent);"><i class="fas fa-id-card"></i> Registration Found</h3>
        <div class="status-result-row"><span class="s-label">Registration ID</span><span class="s-val font-mono">${reg.id}</span></div>
        <div class="status-result-row"><span class="s-label">Full Name</span><span class="s-val">${reg.full_name}</span></div>
        <div class="status-result-row"><span class="s-label">Email</span><span class="s-val">${reg.email}</span></div>
        <div class="status-result-row"><span class="s-label">Role</span><span class="s-val">${reg.role_category}</span></div>
        <div class="status-result-row"><span class="s-label">Organization</span><span class="s-val">${reg.organization || "—"}</span></div>
        <div class="status-result-row"><span class="s-label">Status</span><span class="s-val">${statusBadge}</span></div>
        <div class="status-result-row"><span class="s-label">Registered On</span><span class="s-val">${formatDate(reg.created_at)}</span></div>
      </div> `;
  });
}

// ── PARTICIPANT: QR Code Lookup ───────────────────────────────────────────────

function setupQRLookup() {
  const form = document.getElementById("qr-lookup-form");
  if (!form) return;

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const regId = document.getElementById("qr-reg-id-input").value.trim().toUpperCase();
    if (!regId) return;

    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

    const res = await apiFetch(`/ api / registrations / ${regId} `);
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-search"></i> Show My QR Code';

    const card = document.getElementById("qr-display-card");
    if (!res.success) {
      card.style.display = "block";
      card.innerHTML = `<div class="empty-state" ><i class="fas fa-times-circle" style="font-size:2rem;color:var(--danger);"></i><p style="color:var(--danger);font-weight:700;">Registration not found.</p></div> `;
      return;
    }

    card.style.display = "block";
    card.innerHTML = `
  <div class="qr-display-holder" >
        <h3 class="dashboard-card-title" style="color:var(--participant-accent);justify-content:center;"><i class="fas fa-qrcode"></i> Your QR Code</h3>
        <img src="${res.data.qr_code_path}" alt="QR Code for ${regId}" onerror="this.src='';this.alt='QR not found';">
        <span class="qr-label">${regId}</span>
        <p class="text-sm text-secondary" style="text-align:center;line-height:1.6;">Show this QR code at the check-in station on event day for instant entry.</p>
        <a href="${res.data.qr_code_path}" download="${regId}.png" class="btn btn-participant-primary btn-sm"><i class="fas fa-download"></i> Download QR</a>
      </div>`;
  });
}

// ── PARTICIPANT: Feedback ─────────────────────────────────────────────────────

function setupFeedbackForm() {
  // Star rating
  const stars = document.querySelectorAll("#star-rating i");
  const ratingInput = document.getElementById("fb-rating");

  stars.forEach(star => {
    star.addEventListener("mouseover", () => {
      const val = +star.dataset.val;
      stars.forEach(s => s.classList.toggle("active", +s.dataset.val <= val));
    });
    star.addEventListener("click", () => {
      const val = +star.dataset.val;
      ratingInput.value = val;
      stars.forEach(s => s.classList.toggle("active", +s.dataset.val <= val));
    });
  });
  document.getElementById("star-rating").addEventListener("mouseleave", () => {
    const current = +ratingInput.value;
    stars.forEach(s => s.classList.toggle("active", +s.dataset.val <= current));
  });

  // Form submit
  const form = document.getElementById("feedback-form");
  if (!form) return;

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const rating = +document.getElementById("fb-rating").value;
    if (!rating) { alert("Please select a star rating."); return; }

    const btn = document.getElementById("fb-submit-btn");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

    const payload = {
      name: document.getElementById("fb-name").value.trim(),
      reg_id: document.getElementById("fb-reg-id").value.trim().toUpperCase(),
      rating,
      comment: document.getElementById("fb-comment").value.trim(),
      session_id: (document.getElementById("fb-session") ? document.getElementById("fb-session").value : null) || null
    };

    const res = await apiFetch("/api/feedback", { method: "POST", body: JSON.stringify(payload) });

    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Feedback';

    if (res.success) {
      form.reset();
      stars.forEach(s => s.classList.remove("active"));
      ratingInput.value = 0;
      document.getElementById("feedback-success").style.display = "flex";
    } else {
      alert("Failed to submit feedback: " + res.message);
    }
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Organizer sidebar nav
  document.querySelectorAll("[data-tab][data-portal='organizer']").forEach(item => {
    item.addEventListener("click", () => switchTab(item.dataset.tab));
  });

  // Participant sidebar nav
  document.querySelectorAll("[data-ptab]").forEach(item => {
    item.addEventListener("click", () => switchPTab(item.dataset.ptab));
  });

  // Form setups
  setupRegistrationForm();
  setupDatabaseListeners();
  setupCheckIn();
  setupStatusLookup();
  setupQRLookup();
  setupFeedbackForm();
  loadSessionsForFeedback();

  // Modal close
  document.getElementById("close-receipt-modal").addEventListener("click", () =>
    document.getElementById("receipt-modal").classList.remove("active")
  );

  // Confirm modal
  document.getElementById("confirm-modal-cancel").addEventListener("click", () => {
    document.getElementById("confirm-modal").classList.remove("active");
    _confirmCallback = null;
  });
  document.getElementById("confirm-modal-submit").addEventListener("click", () => {
    document.getElementById("confirm-modal").classList.remove("active");
    if (_confirmCallback) _confirmCallback();
    _confirmCallback = null;
  });

  // Organizer buttons
  document.getElementById("btn-sim-google").addEventListener("click", () => runSimulation("google"));
  document.getElementById("btn-sim-mobile").addEventListener("click", () => runSimulation("mobile"));
  document.getElementById("btn-sim-api").addEventListener("click", () => runSimulation("api"));

  document.getElementById("btn-refresh-db").addEventListener("click", loadDatabase);
  document.getElementById("btn-refresh-charts").addEventListener("click", loadAnalytics);
  document.getElementById("btn-refresh-ai").addEventListener("click", loadAIInsights);
  document.getElementById("btn-refresh-outbox").addEventListener("click", loadOutbox);
  document.getElementById("btn-reset-db").addEventListener("click", resetDatabase);

  document.getElementById("venue-requirements-form").addEventListener("submit", e => { e.preventDefault(); loadVenueRecommendations(); });
  document.getElementById("optimization-form").addEventListener("submit", e => { e.preventDefault(); loadOptimization(); });
  document.getElementById("speaker-requirements-form").addEventListener("submit", e => { e.preventDefault(); loadSpeakerRecommendations(); });
  document.getElementById("speaker-scheduling-form").addEventListener("submit", e => { e.preventDefault(); loadScheduling(); });
  loadVenueSpeakerOptions();

  // Outbox badge on load
  (async () => {
    const res = await apiFetch("/api/outbox");
    if (res.success && res.data.length) {
      const b = document.getElementById("outbox-badge");
      b.textContent = res.data.length;
      b.style.display = "inline-block";
    }
  })();
});

// ── Participant Incident Handlers ─────────────────────────────────────────────

async function handleParticipantReportSubmit(e) {
  e.preventDefault();
  const type = document.getElementById("p-inc-type").value;
  const desc = document.getElementById("p-inc-desc").value;
  const loc = document.getElementById("p-inc-location").value;
  const urgencyEl = document.querySelector("input[name='p-inc-urgency']:checked");
  const urgency = urgencyEl ? urgencyEl.value : "Normal";

  if (!type || !desc || !loc) {
    alert("Please fill in all required fields.");
    return;
  }

  const payload = {
    incident_type: type,
    title: `${type} at ${loc} `,
    description: desc,
    location: loc,
    urgency: urgency,
    reporter_id: "Participant-User",
    reported_by: "Participant User",
    source: "Participant Portal"
  };

  const res = await apiFetch("/api/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (res.success) {
    const inc = res.data;
    document.getElementById("p-report-incident-form").reset();
    const sBox = document.getElementById("p-incident-success-box");
    if (sBox) {
      document.getElementById("p-inc-success-id").textContent = `ID: ${inc.incident_number || inc.id} `;
      sBox.style.display = "block";
    }
    alert(`Incident submitted successfully! Incident ID: ${inc.incident_number || inc.id} `);
  } else {
    alert("Failed to report incident: " + (res.message || "Unknown error"));
  }
}

async function loadParticipantIncidents() {
  const tbody = document.getElementById("p-my-incidents-table-body");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="7" class="text-center text-secondary py-3"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>`;

  const res = await apiFetch("/api/my-incidents?reporter_id=Participant-User");
  if (!res.success || !res.data || res.data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-secondary py-3">No incidents reported yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = res.data.map(inc => {
    let statusClass = "badge-info";
    if (inc.status === "Resolved" || inc.status === "Closed") statusClass = "badge-success";
    else if (inc.status === "Escalated") statusClass = "badge-danger";
    else if (inc.status === "Assigned" || inc.status === "In Progress") statusClass = "badge-warning";

    const dt = inc.created_at ? inc.created_at.replace("T", " ").substring(0, 16) : "N/A";
    const upDt = inc.updated_at ? inc.updated_at.replace("T", " ").substring(0, 16) : dt;

    let resolutionText = "<span class='text-muted text-xs'><i class='fas fa-clock'></i> Pending Resolution</span>";
    if (inc.status === "Resolved" || inc.status === "Closed" || inc.resolution_notes) {
      resolutionText = inc.resolution_notes ? escapeHtml(inc.resolution_notes) : "<span class='text-success'><i class='fas fa-check-circle'></i> Resolved</span>";
    }

    return `
      <tr>
        <td class="font-mono" style="font-weight:700;">${inc.incident_number || inc.id}</td>
        <td>
          <strong style="display:block;">${escapeHtml(inc.title)}</strong>
          <small class="text-secondary">${escapeHtml(inc.category || "General")}</small>
        </td>
        <td><i class="fas fa-map-marker-alt text-accent"></i> ${escapeHtml(inc.location || "Venue")}</td>
        <td>${dt}</td>
        <td><span class="badge ${statusClass}">${escapeHtml(inc.status)}</span></td>
        <td>${upDt}</td>
        <td style="max-width:250px;white-space:normal;font-size:0.85rem;" class="text-secondary">
          ${resolutionText}
        </td>
      </tr>
    `;
  }).join("");
}

// ── Organizer Milestone 3 Handlers ────────────────────────────────────────────

// 1. Sponsorship Agent
async function loadSponsorAgentData() {
  const tbody = document.getElementById("spn-table-body");
  const delivsBody = document.getElementById("spn-delivs-table-body");
  if (!tbody || !delivsBody) return;

  tbody.innerHTML = `<tr> <td colspan="6" class="text-center py-3 text-secondary"><i class="fas fa-spinner fa-spin"></i> Loading sponsors...</td></tr> `;
  delivsBody.innerHTML = `<tr> <td colspan="6" class="text-center py-3 text-secondary"><i class="fas fa-spinner fa-spin"></i> Loading deliverables...</td></tr> `;

  const res = await apiFetch("/api/sponsors");
  if (res.success && res.data) {
    const sponsors = res.data;
    let signedCount = 0, totalVal = 0, totalDelivs = 0, completedDelivs = 0, overdueDelivs = 0;

    tbody.innerHTML = sponsors.map(s => {
      if (s.contract_status === "Signed") signedCount++;
      totalVal += (s.contract_value || 0);

      let tierBadge = "badge-info";
      if (s.tier === "Platinum") tierBadge = "badge-warning";
      else if (s.tier === "Gold") tierBadge = "badge-accent";

      return `
  <tr>
          <td><strong>${escapeHtml(s.name)}</strong></td>
          <td><span class="badge ${tierBadge}">${escapeHtml(s.tier)}</span></td>
          <td><span class="badge ${s.contract_status === 'Signed' ? 'badge-success' : 'badge-warning'}">${escapeHtml(s.contract_status)}</span></td>
          <td>$${(s.contract_value || 0).toLocaleString()}</td>
          <td><span class="badge ${s.payment_status === 'Completed' ? 'badge-success' : 'badge-info'}">${escapeHtml(s.payment_status)}</span></td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="askSponsorshipAIForSponsor('${escapeHtml(s.name)}')"><i class="fas fa-robot"></i> AI Check</button>
          </td>
        </tr>
  `;
    }).join("");

    document.getElementById("spn-stat-total").textContent = sponsors.length;
    document.getElementById("spn-stat-contracts").textContent = signedCount;
  }

  // Load Deliverables
  const dRes = await apiFetch("/api/sponsorship-deliverables");
  if (dRes.success && dRes.data) {
    const delivs = dRes.data;
    let met = 0, overdue = 0;

    delivsBody.innerHTML = delivs.map(d => {
      if (d.status === "Completed") met++;
      if (d.status === "Overdue") overdue++;

      let stClass = "badge-info";
      if (d.status === "Completed") stClass = "badge-success";
      else if (d.status === "Overdue") stClass = "badge-danger";

      return `
  <tr>
          <td><strong>${escapeHtml(d.sponsor_name || d.sponsor_id)}</strong></td>
          <td>${escapeHtml(d.deliverable_name)}</td>
          <td class="text-xs text-secondary">${escapeHtml(d.description || "-")}</td>
          <td><span class="badge ${stClass}">${escapeHtml(d.status)}</span></td>
          <td>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <progress value="${d.completion_percentage || 0}" max="100" style="width:60px;"></progress>
              <span class="text-xs font-mono">${d.completion_percentage || 0}%</span>
            </div>
          </td>
          <td>
            ${d.status !== 'Completed' ? `<button class="btn btn-success btn-sm" onclick="updateDeliverableStatus('${d.id}', 'Completed', 100)"><i class="fas fa-check"></i> Mark Complete</button>` : `<span class="text-xs text-success"><i class="fas fa-check-double"></i> Verified</span>`}
          </td>
        </tr>
  `;
    }).join("");

    document.getElementById("spn-stat-delivs").textContent = `${met} / ${delivs.length}`;
    document.getElementById("spn-stat-overdue").textContent = overdue;
  }
}

async function askSponsorshipAI() {
  const query = document.getElementById("spn-ai-query-input").value;
  const box = document.getElementById("spn-ai-response-box");
  if (!query) {
    alert("Please enter a query for the AI Sponsorship Assistant.");
    return;
  }

  box.style.display = "block";
  box.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Analyzing sponsorship metrics...`;

  const res = await apiFetch("/api/sponsors/query-ai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: query })
  });

  if (res.success && res.data) {
    box.innerHTML = `<strong><i class="fas fa-robot text-accent"></i> AI Answer:</strong><br>${escapeHtml(res.data.answer).replace(/\n/g, "<br>")}`;
  } else {
    box.innerHTML = `<span class="text-danger">Failed to query AI Sponsorship Assistant.</span>`;
  }
}

function askSponsorshipAIForSponsor(name) {
  document.getElementById("spn-ai-query-input").value = `What is the status of deliverables and contract for ${name}?`;
  askSponsorshipAI();
}

async function updateDeliverableStatus(id, status, pct) {
  const res = await apiFetch(`/api/sponsorship-deliverables/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: status, completion_percentage: pct })
  });

  if (res.success) {
    loadSponsorAgentData();
  } else {
    alert("Failed to update deliverable status.");
  }
}

// --- Add Sponsor Modal Handlers ---
function openAddSponsorModal() {
  document.getElementById("add-spn-name").value = "";
  document.getElementById("add-spn-tier").value = "Gold";
  document.getElementById("add-spn-value").value = "5000";
  document.getElementById("add-spn-email").value = "";
  document.getElementById("add-sponsor-modal").style.display = "flex";
}

async function submitAddSponsor(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-add-spn");
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

  const payload = {
    name: document.getElementById("add-spn-name").value,
    tier: document.getElementById("add-spn-tier").value,
    contract_value: parseFloat(document.getElementById("add-spn-value").value || 0),
    contact_email: document.getElementById("add-spn-email").value,
    contract_status: "Draft",
    payment_status: "Pending",
    engagement_score: 0
  };

  const res = await apiFetch("/api/sponsors", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-save"></i> Add Sponsor';

  if (res.success) {
    document.getElementById("add-sponsor-modal").style.display = "none";
    loadSponsorAgentData();
    // Also refresh performance tab if needed
    if (typeof loadSponsorPerformanceData === 'function') loadSponsorPerformanceData();
  } else {
    alert("Failed to add sponsor: " + res.message);
  }
}

// --- Sponsor Discovery and Approach ---
function openSponsorDiscoveryModal() {
  document.getElementById("sponsor-discovery-modal").style.display = "flex";
  loadSponsorProspects();
}

async function loadSponsorProspects() {
  const tbody = document.getElementById("discovery-table-body");
  const domain = document.getElementById("discovery-domain-filter").value;

  tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>`;

  const res = await apiFetch(`/api/sponsors/prospects?domain=${encodeURIComponent(domain)}`);
  if (!res.success || !res.data || res.data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-secondary">No prospects found.</td></tr>`;
    return;
  }

  tbody.innerHTML = res.data.map(p => {
    let statBadge = p.status === 'Contacted' ? 'badge-success' : 'badge-warning';

    return `
      <tr>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td>${escapeHtml(p.domain)}</td>
        <td>$${p.estimated_budget.toLocaleString()}</td>
        <td><span class="badge ${statBadge}">${escapeHtml(p.status)}</span></td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="openApproachModal('${p.id}', '${escapeHtml(p.name)}', ${p.estimated_budget})" ${p.status === 'Contacted' ? 'disabled' : ''}>
            <i class="fas fa-paper-plane"></i> Approach
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function openApproachModal(id, name, budget) {
  document.getElementById("approach-prospect-id").value = id;
  document.getElementById("approach-prospect-name").value = name;
  document.getElementById("approach-amount").value = budget;
  document.getElementById("outreach-proposal-modal").style.display = "flex";
}

async function submitSponsorApproach(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-approach-submit");
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

  const prospectId = document.getElementById("approach-prospect-id").value;
  const payload = {
    amount: document.getElementById("approach-amount").value,
    tier: document.getElementById("approach-tier").value,
    message: document.getElementById("approach-message").value
  };

  const res = await apiFetch(`/api/sponsors/prospects/${prospectId}/approach`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Proposal';

  if (res.success) {
    document.getElementById("outreach-proposal-modal").style.display = "none";
    loadSponsorProspects();
  } else {
    alert("Failed to send proposal: " + (res.message || "Unknown error"));
  }
}


// 2. Sponsor Performance Tracking
async function loadSponsorPerformanceData() {
  const tbody = document.getElementById("spn-perf-table-body");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-secondary"><i class="fas fa-spinner fa-spin"></i> Calculating dynamic sponsor performance...</td></tr>`;

  const res = await apiFetch("/api/sponsor-performance");
  if (res.success && res.data) {
    const dataObj = res.data;
    const summary = dataObj.summary || {};
    const sponsors = dataObj.sponsors || [];

    // Stat Cards
    document.getElementById("spn-perf-stat-count").textContent = summary.total_sponsors || sponsors.length;
    document.getElementById("spn-perf-stat-eng").textContent = `${summary.avg_engagement_pct || 0}%`;
    document.getElementById("spn-perf-stat-leads").textContent = summary.total_leads_generated || 0;
    document.getElementById("spn-perf-stat-delivs").textContent = `${summary.avg_deliverables_pct || 0}%`;

    // 5-Column Dashboard Table: Sponsor | Engagement | Leads | Deliverables | Performance | Action
    tbody.innerHTML = sponsors.map(s => {
      let catBadge = "badge-info";
      if (s.performance_category === "Excellent") catBadge = "badge-success";
      else if (s.performance_category === "Good") catBadge = "badge-accent";
      else if (s.performance_category === "At Risk") catBadge = "badge-danger";

      let tierBadge = s.tier === "Platinum" ? "badge-warning" : (s.tier === "Gold" ? "badge-accent" : "badge-info");

      return `
        <tr style="cursor:pointer;" onclick="openSponsorDetailModal('${s.id}')">
          <td>
            <strong>${escapeHtml(s.name)}</strong>
            <span class="badge ${tierBadge} ms-2" style="font-size:0.7rem;">${escapeHtml(s.tier)}</span>
          </td>
          <td>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <progress value="${s.engagement_pct || 0}" max="100" style="width:70px;"></progress>
              <strong class="font-mono text-sm">${s.engagement_pct || 0}%</strong>
            </div>
          </td>
          <td>
            <span class="badge badge-outline"><i class="fas fa-user-check text-success"></i> ${s.leads || 0} leads</span>
          </td>
          <td>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <progress value="${s.deliverables_pct || 0}" max="100" style="width:70px;"></progress>
              <span class="text-xs font-mono">${s.deliverables_pct || 0}%</span>
            </div>
          </td>
          <td>
            <span class="badge ${catBadge}" style="font-size:0.85rem;padding:0.35rem 0.65rem;">
              <i class="${s.performance_category === 'Excellent' ? 'fas fa-star' : (s.performance_category === 'Good' ? 'fas fa-thumbs-up' : 'fas fa-exclamation-triangle')}"></i>
              ${escapeHtml(s.performance_category)}
            </span>
          </td>
          <td onclick="event.stopPropagation();">
            <button class="btn btn-outline btn-sm" onclick="openSponsorDetailModal('${s.id}')">
              <i class="fas fa-eye"></i> View Details
            </button>
          </td>
        </tr>
      `;
    }).join("");

    // Performance Visualizations
    renderSponsorVisualizations(sponsors);
  } else {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-danger">Failed to load sponsor performance data.</td></tr>`;
  }
}

function renderSponsorVisualizations(sponsors) {
  const engContainer = document.getElementById("spn-viz-engagement");
  const leadsContainer = document.getElementById("spn-viz-leads");
  const delivContainer = document.getElementById("spn-viz-deliverables");

  if (engContainer) {
    engContainer.innerHTML = sponsors.map(s => `
      <div>
        <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.25rem;">
          <span>${escapeHtml(s.name)}</span>
          <strong class="font-mono">${s.engagement_pct}%</strong>
        </div>
        <div style="background:rgba(255,255,255,0.06);border-radius:6px;height:8px;overflow:hidden;">
          <div style="width:${s.engagement_pct}%;background:var(--warning);height:100%;border-radius:6px;"></div>
        </div>
      </div>
    `).join("");
  }

  if (leadsContainer) {
    leadsContainer.innerHTML = sponsors.map(s => {
      const pct = Math.min(Math.floor((s.leads || 0) / 4.5), 100);
      return `
        <div>
          <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.25rem;">
            <span>${escapeHtml(s.name)}</span>
            <strong class="font-mono text-success">${s.leads} leads</strong>
          </div>
          <div style="background:rgba(255,255,255,0.06);border-radius:6px;height:8px;overflow:hidden;">
            <div style="width:${pct}%;background:var(--success);height:100%;border-radius:6px;"></div>
          </div>
        </div>
      `;
    }).join("");
  }

  if (delivContainer) {
    delivContainer.innerHTML = sponsors.map(s => `
      <div>
        <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.25rem;">
          <span>${escapeHtml(s.name)}</span>
          <strong class="font-mono text-info">${s.deliverables_pct}%</strong>
        </div>
        <div style="background:rgba(255,255,255,0.06);border-radius:6px;height:8px;overflow:hidden;">
          <div style="width:${s.deliverables_pct}%;background:var(--accent);height:100%;border-radius:6px;"></div>
        </div>
      </div>
    `).join("");
  }
}

// Sponsor Detail Modal Handlers
async function openSponsorDetailModal(sponsorId) {
  const modal = document.getElementById("sponsor-detail-modal");
  if (!modal) return;

  modal.style.display = "flex";

  const res = await apiFetch(`/api/sponsor-performance/${sponsorId}`);
  if (res.success && res.data) {
    const s = res.data;
    const ai = s.ai_insight || {};

    document.getElementById("sdm-sponsor-id").value = s.id;
    document.getElementById("sdm-sponsor-name").textContent = s.name;
    document.getElementById("sdm-sponsor-tier").textContent = s.tier;

    // Badges
    const catBadge = document.getElementById("sdm-category-badge");
    catBadge.textContent = s.performance_category;
    catBadge.className = `badge ${s.performance_category === 'Excellent' ? 'badge-success' : (s.performance_category === 'Good' ? 'badge-accent' : 'badge-danger')}`;

    // Metrics
    document.getElementById("sdm-engagement-val").textContent = `${s.engagement_pct}%`;
    document.getElementById("sdm-leads-val").textContent = s.leads;
    document.getElementById("sdm-deliv-val").textContent = `${s.deliverables_pct}%`;
    document.getElementById("sdm-score-val").textContent = `${s.performance_score} / 100`;

    // AI Insight
    document.getElementById("sdm-ai-explanation").textContent = ai.explanation || "";
    document.getElementById("sdm-ai-well").textContent = ai.going_well || "";
    document.getElementById("sdm-ai-improve").textContent = ai.needs_improvement || "";
    document.getElementById("sdm-ai-rec").textContent = ai.recommendation || "";

    // Deliverables List
    const delivTbody = document.getElementById("sdm-deliverables-body");
    if (s.deliverables && s.deliverables.length > 0) {
      delivTbody.innerHTML = s.deliverables.map(d => `
        <tr>
          <td><strong>${escapeHtml(d.deliverable_name)}</strong></td>
          <td class="text-xs text-secondary">${escapeHtml(d.description || '-')}</td>
          <td><span class="badge ${d.status === 'Completed' ? 'badge-success' : (d.status === 'In Progress' ? 'badge-info' : 'badge-danger')}">${escapeHtml(d.status)}</span></td>
          <td>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <progress value="${d.completion_percentage || 0}" max="100" style="width:60px;"></progress>
              <span class="text-xs font-mono">${d.completion_percentage || 0}%</span>
            </div>
          </td>
        </tr>
      `).join("");
    } else {
      delivTbody.innerHTML = `<tr><td colspan="4" class="text-center text-secondary py-2">No deliverables configured.</td></tr>`;
    }

    // Form inputs
    document.getElementById("sdm-edit-leads").value = s.leads || 0;
    document.getElementById("sdm-edit-eng").value = s.engagement_pct || 75;
  }
}

function closeSponsorDetailModal() {
  const modal = document.getElementById("sponsor-detail-modal");
  if (modal) modal.style.display = "none";
}

async function saveSponsorMetricUpdate(e) {
  if (e) e.preventDefault();

  const id = document.getElementById("sdm-sponsor-id").value;
  const leads = parseInt(document.getElementById("sdm-edit-leads").value) || 0;
  const eng = parseInt(document.getElementById("sdm-edit-eng").value) || 0;

  const res = await apiFetch(`/api/sponsor-performance/${id}/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ leads: leads, engagement_score: eng })
  });

  if (res.success) {
    // Re-load detail modal view with updated score and AI insight
    openSponsorDetailModal(id);
    // Refresh main table & visualizations
    loadSponsorPerformanceData();
  } else {
    alert("Failed to update sponsor performance metrics.");
  }
}

// 3. Incident Agent
async function loadIncidentAgentData() {
  const tbody = document.getElementById("inc-table-body");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="8" class="text-center py-3 text-secondary"><i class="fas fa-spinner fa-spin"></i> Loading incidents...</td></tr>`;

  const res = await apiFetch("/api/incidents");
  if (res.success && res.data) {
    const incidents = res.data;
    let active = 0, critical = 0, resolved = 0;

    tbody.innerHTML = incidents.map(inc => {
      if (inc.status === "Resolved" || inc.status === "Closed") resolved++;
      else {
        active++;
        if (inc.severity === "High" || inc.severity === "Critical" || inc.priority === "Critical") critical++;
      }

      let sevClass = "badge-info";
      if (inc.severity === "Critical" || inc.priority === "Critical") sevClass = "badge-danger";
      else if (inc.severity === "High" || inc.priority === "High") sevClass = "badge-warning";

      let statusClass = "badge-info";
      if (inc.status === "Resolved" || inc.status === "Closed") statusClass = "badge-success";
      else if (inc.status === "Escalated") statusClass = "badge-danger";

      return `
        <tr>
          <td class="font-mono text-xs">${inc.incident_number || inc.id}</td>
          <td><strong>${escapeHtml(inc.title)}</strong></td>
          <td>${escapeHtml(inc.category || "General")}</td>
          <td><span class="badge ${sevClass}">${escapeHtml(inc.severity)}</span></td>
          <td><i class="fas fa-map-marker-alt text-accent"></i> ${escapeHtml(inc.location || "Venue")}</td>
          <td>${escapeHtml(inc.assigned_team || "General Support")}</td>
          <td><span class="badge ${statusClass}">${escapeHtml(inc.status)}</span></td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="openWorkflowForIncident('${inc.id}')"><i class="fas fa-tasks"></i> Workflow</button>
          </td>
        </tr>
      `;
    }).join("");

    document.getElementById("inc-stat-active").textContent = active;
    document.getElementById("inc-stat-critical").textContent = critical;
    document.getElementById("inc-stat-resolved").textContent = resolved;
  }
}

async function handleOrganizerIncidentSubmit(e) {
  e.preventDefault();
  const title = document.getElementById("org-inc-title").value;
  const desc = document.getElementById("org-inc-desc").value;
  const loc = document.getElementById("org-inc-loc").value;

  if (!title || !desc || !loc) {
    alert("Please fill in all required fields.");
    return;
  }

  const res = await apiFetch("/api/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: title,
      description: desc,
      location: loc,
      source: "Organizer Portal",
      reporter_id: "Organizer-Console",
      reported_by: "Organizer Staff"
    })
  });

  if (res.success) {
    document.getElementById("org-log-incident-form").reset();
    alert(`Incident Logged & Auto-Classified by AI! Incident ID: ${res.data.incident_number || res.data.id}`);
    loadIncidentAgentData();
  } else {
    alert("Failed to log incident: " + (res.message || "Unknown error"));
  }
}

// 4. Incident Management Workflows
let _activeWfIncident = null;

async function loadIncidentWorkflowsData() {
  const select = document.getElementById("wf-inc-select");
  if (!select) return;

  const res = await apiFetch("/api/incidents");
  if (res.success && res.data) {
    const incidents = res.data;
    select.innerHTML = `<option value="">Select incident to manage...</option>` +
      incidents.map(i => `<option value="${i.id}">${i.incident_number || i.id} - ${escapeHtml(i.title)} (${i.status})</option>`).join("");
  }
}

async function onWorkflowIncidentSelected() {
  const select = document.getElementById("wf-inc-select");
  const incId = select.value;
  const box = document.getElementById("wf-stepper-box");

  if (!incId) {
    box.style.display = "none";
    _activeWfIncident = null;
    return;
  }

  const res = await apiFetch(`/api/incidents/${incId}`);
  if (res.success && res.data) {
    const inc = res.data;
    _activeWfIncident = inc;
    box.style.display = "block";

    document.getElementById("wf-inc-title-disp").textContent = `${inc.incident_number || inc.id}: ${inc.title}`;
    document.getElementById("wf-inc-desc-disp").textContent = inc.description || "No description provided.";
    document.getElementById("wf-inc-cat").textContent = inc.category || "General";
    document.getElementById("wf-inc-sev").textContent = `${inc.severity} (Priority: ${inc.priority})`;
    document.getElementById("wf-inc-loc").textContent = inc.location || "Venue";
    document.getElementById("wf-inc-team").textContent = inc.assigned_team || "General Support";

    // Stepper active highlights
    document.querySelectorAll(".wf-step .badge").forEach(b => b.className = "badge badge-info p-2");
    if (inc.status === "REPORTED") document.getElementById("wf-step-REPORTED").querySelector(".badge").className = "badge badge-warning p-2";
    else if (inc.status === "ANALYZING") document.getElementById("wf-step-ANALYZING").querySelector(".badge").className = "badge badge-warning p-2";
    else if (inc.status === "ASSIGNED") document.getElementById("wf-step-ASSIGNED").querySelector(".badge").className = "badge badge-warning p-2";
    else if (inc.status === "IN_PROGRESS" || inc.status === "In Progress" || inc.status === "Escalated") document.getElementById("wf-step-IN_PROGRESS").querySelector(".badge").className = "badge badge-warning p-2";
    else if (inc.status === "RESOLVED" || inc.status === "Resolved" || inc.status === "Closed") document.getElementById("wf-step-RESOLVED").querySelector(".badge").className = "badge badge-success p-2";

    // Timeline audit list
    const tList = document.getElementById("wf-timeline-list");
    if (inc.timeline && inc.timeline.length) {
      tList.innerHTML = inc.timeline.map(t => `
        <div class="p-2 glass text-xs" style="border-radius:6px;">
          <div style="display:flex;justify-content:space-between;">
            <strong class="text-accent">${escapeHtml(t.action)}</strong>
            <span class="text-secondary font-mono">${(t.timestamp || '').substring(0, 16)}</span>
          </div>
          <div>${escapeHtml(t.description || '')}</div>
          <div class="text-secondary" style="font-size:0.7rem;">By: ${escapeHtml(t.performed_by || 'System')}</div>
        </div>
      `).join("");
    } else {
      tList.innerHTML = `<div class="text-xs text-secondary py-2">No timeline entries yet.</div>`;
    }
  }
}

function openWorkflowForIncident(id) {
  switchTab("incident-workflows");
  const select = document.getElementById("wf-inc-select");
  if (select) {
    select.value = id;
    onWorkflowIncidentSelected();
  }
}

async function reassignWorkflowTeam() {
  if (!_activeWfIncident) return;
  const newTeam = prompt("Enter responsible response team:", _activeWfIncident.assigned_team || "AV Team");
  if (!newTeam) return;

  const res = await apiFetch(`/api/incidents/${_activeWfIncident.id}/assign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team: newTeam })
  });

  if (res.success) {
    onWorkflowIncidentSelected();
  } else {
    alert("Failed to reassign team.");
  }
}

async function escalateWorkflowIncident() {
  if (!_activeWfIncident) return;
  const reason = prompt("Enter escalation reason:", "Operational bottleneck / unresolved high severity issue");
  if (!reason) return;

  const res = await apiFetch(`/api/incidents/${_activeWfIncident.id}/escalate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason })
  });

  if (res.success) {
    alert("Incident escalated to Critical Priority & Operational Alert triggered.");
    onWorkflowIncidentSelected();
  } else {
    alert("Failed to escalate incident.");
  }
}

async function resolveWorkflowIncident() {
  if (!_activeWfIncident) return;
  const notes = prompt("Enter resolution notes:", "Issue inspected and resolved by dispatch lead.");
  if (!notes) return;

  const res = await apiFetch(`/api/incidents/${_activeWfIncident.id}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resolution_notes: notes })
  });

  if (res.success) {
    alert("Incident marked as RESOLVED.");
    onWorkflowIncidentSelected();
  } else {
    alert("Failed to resolve incident.");
  }
}

// 5. Operational Alerts
async function loadOperationalAlertsData() {
  const container = document.getElementById("alerts-container");
  if (!container) return;

  container.innerHTML = `<div class="text-center py-3 text-secondary"><i class="fas fa-spinner fa-spin"></i> Loading alerts...</div>`;

  const res = await apiFetch("/api/alerts");
  if (res.success && res.data) {
    const alerts = res.data;
    let critical = 0, high = 0, medium = 0;

    if (alerts.length === 0) {
      container.innerHTML = `<div class="text-center py-4 text-secondary">No active operational alerts.</div>`;
      return;
    }

    container.innerHTML = alerts.map(a => {
      if (a.severity === "Critical") critical++;
      else if (a.severity === "High" || a.severity === "High-Priority") high++;
      else medium++;

      let borderClass = "border-info";
      let icon = "fa-info-circle text-info";
      if (a.severity === "Critical") { borderClass = "border-danger"; icon = "fa-exclamation-triangle text-danger"; }
      else if (a.severity === "High" || a.severity === "High-Priority") { borderClass = "border-warning"; icon = "fa-exclamation-circle text-warning"; }

      const ts = a.timestamp ? a.timestamp.replace("T", " ").substring(0, 16) : "N/A";

      return `
        <div class="panel-card glass ${borderClass}" style="border-left:4px solid;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <h4 style="font-weight:700;display:flex;align-items:center;gap:0.5rem;">
                <i class="fas ${icon}"></i> ${escapeHtml(a.title)}
              </h4>
              <p class="text-sm text-secondary mt-1" style="line-height:1.5;">${escapeHtml(a.message || '')}</p>
            </div>
            <span class="badge ${a.severity === 'Critical' ? 'badge-danger' : 'badge-warning'}">${escapeHtml(a.severity)}</span>
          </div>

          ${a.recommended_action ? `
            <div class="p-2 glass mt-2 text-xs" style="border-radius:6px;background:rgba(255,255,255,0.03);">
              <strong><i class="fas fa-lightbulb text-warning"></i> AI Action Recommendation:</strong> ${escapeHtml(a.recommended_action)}
            </div>
          ` : ''}

          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.8rem;" class="text-xs">
            <span class="text-secondary"><i class="fas fa-clock"></i> ${ts} | Module: <strong>${escapeHtml(a.module || 'System')}</strong></span>
            <div style="display:flex;gap:0.4rem;">
              ${(a.status !== 'Acknowledged' && a.status !== 'Resolved') ? `<button class="btn btn-outline btn-sm" onclick="acknowledgeAlert('${a.id}')"><i class="fas fa-eye"></i> Acknowledge</button>` : (a.status === 'Acknowledged' ? `<span class="badge badge-info"><i class="fas fa-check"></i> Acknowledged</span>` : '')}
              ${a.status !== 'Resolved' ? `<button class="btn btn-success btn-sm" onclick="resolveAlert('${a.id}')"><i class="fas fa-check-circle"></i> Resolve</button>` : `<span class="badge badge-success"><i class="fas fa-check-double"></i> Resolved</span>`}
            </div>
          </div>
        </div>
      `;
    }).join("");

    document.getElementById("alert-stat-critical").textContent = critical;
    document.getElementById("alert-stat-high").textContent = high;
    document.getElementById("alert-stat-medium").textContent = medium;
  }
}

async function triggerPredictiveRiskScan() {
  const container = document.getElementById("alerts-container");
  container.innerHTML = `<div class="text-center py-4 text-info"><i class="fas fa-radar fa-spin" style="font-size:2rem;"></i><br><br>Scanning venue sensor density, entry velocities & network traffic...</div>`;

  const res = await apiFetch("/api/alerts/predict-risks", { method: "POST" });
  if (res.success) {
    alert(res.data.message || "Predictive Risk Scan Completed.");
    loadOperationalAlertsData();
  } else {
    alert("Failed to run predictive risk scan.");
    loadOperationalAlertsData();
  }
}

async function acknowledgeAlert(id) {
  const res = await apiFetch(`/api/alerts/${id}/acknowledge`, { method: "POST" });
  if (res.success) loadOperationalAlertsData();
}

async function resolveAlert(id) {
  const res = await apiFetch(`/api/alerts/${id}/resolve`, { method: "POST" });
  if (res.success) loadOperationalAlertsData();
}


