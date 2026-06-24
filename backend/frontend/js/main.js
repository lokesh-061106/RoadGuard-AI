// RoadGuard AI - Global Frontend Operations

// Override fetch to automatically attach X-User-Id header if user is logged in
const originalFetch = window.fetch;
window.fetch = function(url, options) {
  options = options || {};
  options.headers = options.headers || {};
  
  const localUserStr = localStorage.getItem('user');
  if (localUserStr) {
    try {
      const user = JSON.parse(localUserStr);
      if (options.headers instanceof Headers) {
        options.headers.set('X-User-Id', user.id);
      } else {
        options.headers['X-User-Id'] = user.id;
      }
    } catch (e) {}
  }
  return originalFetch(url, options);
};

// State Management
const State = {
  user: null,
  activeIncidentId: null,
  map: null,
  mapMarker: null,
  charts: {}
};

// Initialization on DOM Content Loaded
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuthStatus();
  if (State.user) {
    syncLocalIncidentsWithServer();
  }
  routePageLogic();
});

// =====================================================================
// AUTHENTICATION & UI NAVIGATION STATE
// =====================================================================

async function checkAuthStatus() {
  const localUserStr = localStorage.getItem('user');
  if (localUserStr) {
    try {
      State.user = JSON.parse(localUserStr);
      updateNavbar(true);
      return;
    } catch (err) {
      localStorage.removeItem('user');
    }
  }

  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      State.user = data.user;
      localStorage.setItem('user', JSON.stringify(data.user));
      updateNavbar(true);
    } else {
      State.user = null;
      updateNavbar(false);
    }
  } catch (err) {
    console.error("Auth check failed:", err);
    State.user = null;
    updateNavbar(false);
  }
}

async function syncLocalIncidentsWithServer() {
  const localIncidents = JSON.parse(localStorage.getItem('local_incidents') || '[]');
  if (localIncidents.length === 0) return;
  
  try {
    const res = await fetch('/api/sync-incidents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ incidents: localIncidents })
    });
    if (res.ok) {
      console.log("Local incidents synced successfully with transient server DB.");
    }
  } catch (err) {
    console.error("Failed to sync local incidents with server:", err);
  }
}

function updateNavbar(isLoggedIn) {
  const authContainer = document.getElementById('nav-auth-container');
  const navMenu = document.getElementById('nav-menu-links');
  if (!authContainer) return;

  if (isLoggedIn) {
    // Logged in Navbar
    let menuHtml = `
      <li><a href="/citizen.html" class="nav-link">Dashboard</a></li>
      <li><a href="/report.html" class="nav-link">Report Issue</a></li>
      <li><a href="/rewards.html" class="nav-link">Rewards</a></li>
      <li><a href="/leaderboard.html" class="nav-link">Leaderboard</a></li>
      <li><a href="/analytics.html" class="nav-link">Analytics</a></li>
      <li><a href="/tracker.html" class="nav-link">Tracker</a></li>
    `;
    
    // Add Authority links if applicable
    if (State.user.role === 'authority' || State.user.role === 'admin') {
      menuHtml += `<li><a href="/authority.html" class="nav-link">Gov Panel</a></li>`;
    }
    if (State.user.role === 'admin') {
      menuHtml += `<li><a href="/admin.html" class="nav-link">Admin</a></li>`;
    }
    
    if (navMenu) navMenu.innerHTML = menuHtml;

    authContainer.innerHTML = `
      <div class="user-pill" style="display:flex; align-items:center; gap:1rem;">
        <a href="/profile.html" style="color:#fff; text-decoration:none; font-weight:600; font-size:0.9rem;">
          👤 ${State.user.name} (${State.user.points} pts)
        </a>
        <button onclick="handleLogout()" class="btn btn-secondary" style="padding:0.4rem 0.8rem; font-size:0.8rem;">Logout</button>
      </div>
    `;
  } else {
    // Logged out Navbar
    if (navMenu) {
      navMenu.innerHTML = `
        <li><a href="/" class="nav-link">Home</a></li>
        <li><a href="/leaderboard.html" class="nav-link">Leaderboard</a></li>
        <li><a href="/analytics.html" class="nav-link">Analytics</a></li>
        <li><a href="/tracker.html" class="nav-link">Tracker</a></li>
      `;
    }
    authContainer.innerHTML = `
      <a href="/login.html" class="btn btn-secondary" style="padding:0.5rem 1rem; font-size:0.9rem;">Login</a>
      <a href="/register.html" class="btn btn-primary" style="padding:0.5rem 1rem; font-size:0.9rem;">Sign Up</a>
    `;
  }

  // Set active link highlighting
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

async function handleLogout() {
  try {
    localStorage.removeItem('user');
    await fetch('/api/auth/logout', { method: 'POST' });
    alert("Successfully logged out.");
    window.location.href = '/';
  } catch (err) {
    localStorage.removeItem('user');
    window.location.href = '/';
  }
}


// =====================================================================
// ROUTING PAGE SPECIFIC SCRIPTS
// =====================================================================

function routePageLogic() {
  const path = window.location.pathname;
  
  if (path === '/login.html') {
    initLoginPage();
  } else if (path === '/register.html') {
    initRegisterPage();
  } else if (path === '/report.html') {
    initReportPage();
  } else if (path === '/monitoring.html') {
    initMonitoringPage();
  } else if (path === '/citizen.html') {
    initCitizenDashboard();
  } else if (path === '/rewards.html') {
    initRewardsPage();
  } else if (path === '/leaderboard.html') {
    initLeaderboardPage();
  } else if (path === '/authority.html') {
    initAuthorityPage();
  } else if (path === '/analytics.html') {
    initAnalyticsPage();
  } else if (path === '/tracker.html') {
    initTrackerPage();
  } else if (path === '/admin.html') {
    initAdminPage();
  } else if (path === '/profile.html') {
    initProfilePage();
  }
}


// =====================================================================
// 1. LOGIN & REGISTER
// =====================================================================

function initLoginPage() {
  const form = document.getElementById('login-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('user', JSON.stringify(data.user));
        window.location.href = data.user.role === 'citizen' ? '/citizen.html' : '/authority.html';
      } else {
        alert("Login failed: " + data.message);
      }
    } catch (err) {
      alert("Error: " + err);
    }
  });
}

function initRegisterPage() {
  const form = document.getElementById('register-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('user', JSON.stringify(data.user));
        alert("Account created successfully!");
        window.location.href = '/citizen.html';
      } else {
        alert("Registration failed: " + data.message);
      }
    } catch (err) {
      alert("Error: " + err);
    }
  });
}


// =====================================================================
// 2. REPORT SUBMISSION
// =====================================================================

function initReportPage() {
  if (!State.user) {
    alert("Please log in to submit a report.");
    window.location.href = '/login.html';
    return;
  }

  // Setup Leaflet map for coordinate selection
  const defaultLat = 12.9716;
  const defaultLon = 77.5946; // Bengaluru center
  
  const mapElement = document.getElementById('report-map');
  if (!mapElement) return;

  State.map = L.map('report-map').setView([defaultLat, defaultLon], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(State.map);

  // Set default coordinates in form inputs
  document.getElementById('lat-input').value = defaultLat;
  document.getElementById('lon-input').value = defaultLon;

  // Add click handler on map
  State.mapMarker = L.marker([defaultLat, defaultLon], { draggable: true }).addTo(State.map);
  
  const updateCoords = (lat, lon) => {
    document.getElementById('lat-input').value = lat.toFixed(6);
    document.getElementById('lon-input').value = lon.toFixed(6);
  };

  State.mapMarker.on('dragend', (e) => {
    const pos = e.target.getLatLng();
    updateCoords(pos.lat, pos.lng);
  });

  State.map.on('click', (e) => {
    State.mapMarker.setLatLng(e.latlng);
    updateCoords(e.latlng.lat, e.latlng.lng);
  });

  // Handle Drag & Drop Upload zones
  const uploadZone = document.getElementById('upload-zone');
  const fileInput = document.getElementById('file-input');
  const uploadPreview = document.getElementById('upload-preview');

  uploadZone.addEventListener('click', () => fileInput.click());
  
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        uploadPreview.src = e.target.result;
        uploadPreview.style.display = 'inline-block';
      };
      reader.readAsDataURL(file);
    }
  });

  // Submission Form handler
  const form = document.getElementById('report-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerText = "Uploading Incident Asset...";

    const formData = new FormData();
    formData.append('latitude', document.getElementById('lat-input').value);
    formData.append('longitude', document.getElementById('lon-input').value);
    formData.append('description', document.getElementById('desc-input').value);
    formData.append('image', fileInput.files[0]);

    try {
      const res = await fetch('/api/submit-report', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        if (data.events) {
          sessionStorage.setItem(`telemetry_${data.incident_id}`, JSON.stringify(data.events));
        }
        if (data.incident) {
          try {
            let localIncidents = JSON.parse(localStorage.getItem('local_incidents') || '[]');
            localIncidents = localIncidents.filter(i => i.id !== data.incident.id);
            localIncidents.push(data.incident);
            localStorage.setItem('local_incidents', JSON.stringify(localIncidents));
          } catch (e) {
            console.error("Failed to save incident to localStorage:", e);
          }
        }
        window.location.href = data.redirect_url;
      } else {
        alert("Submission failed: " + data.message);
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit Report";
      }
    } catch (err) {
      alert("Error: " + err);
      submitBtn.disabled = false;
      submitBtn.innerText = "Submit Report";
    }
  });
}


// =====================================================================
// 3. LIVE MULTI-AGENT SSE MONITORING
// =====================================================================

function renderAgentOutput(agentName, output) {
  if (!output) return `<p style="color:var(--text-muted); font-size:0.85rem;">No output data returned.</p>`;
  
  if (agentName.includes("Detection")) {
    const severity = output.severity || 'Medium';
    const sevClass = severity.toLowerCase();
    const confidence = output.confidence || '92%';
    return `
      <div class="agent-output-card">
        <div class="output-grid">
          <div class="output-cell">
            <span class="cell-label">Hazard Type</span>
            <span class="cell-value">🛠️ ${output.damage_type || 'Unknown'}</span>
          </div>
          <div class="output-cell">
            <span class="cell-label">Category</span>
            <span class="cell-value">${output.category || 'General'}</span>
          </div>
          <div class="output-cell">
            <span class="cell-label">Severity Level</span>
            <div><span class="badge badge-${sevClass}">${severity}</span></div>
          </div>
          <div class="output-cell">
            <span class="cell-label">AI Confidence</span>
            <div class="cell-value-confidence">
              <span class="confidence-number">${confidence}</span>
              <div class="confidence-bar-bg"><div class="confidence-bar-fill" style="width: ${confidence.includes('%') ? confidence : confidence + '%'}"></div></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  if (agentName.includes("Risk")) {
    const priority = output.priority || 'Medium';
    const prioClass = priority.toLowerCase();
    const score = output.risk_score || 0;
    const scoreColor = score > 75 ? 'var(--neon-red)' : (score > 40 ? 'var(--neon-amber)' : 'var(--neon-teal)');
    return `
      <div class="agent-output-card">
        <div class="output-grid" style="grid-template-columns: 1fr 2fr;">
          <div class="output-cell" style="display:flex; flex-direction:column; align-items:center; justify-content:center; border-right: 1px solid var(--border-glass); padding-right:1rem;">
            <span class="cell-label">Risk Index</span>
            <span class="risk-score-display" style="color: ${scoreColor}; font-size:1.8rem; font-weight:800; margin-top:0.25rem;">${score}/100</span>
            <div style="margin-top:0.4rem;"><span class="badge badge-${prioClass}">${priority}</span></div>
          </div>
          <div class="output-cell" style="padding-left:0.5rem; justify-content:center;">
            <span class="cell-label">Safety Officer Assessment</span>
            <p style="font-size:0.85rem; line-height:1.4; color:var(--text-muted); margin-top:0.25rem;">${output.explanation || 'No assessment explanation provided.'}</p>
          </div>
        </div>
      </div>
    `;
  }
  
  if (agentName.includes("Repair")) {
    const materialsList = output.materials || [];
    const materialsHtml = materialsList.map(mat => `<span class="badge badge-medium" style="font-size:0.75rem; padding:0.25rem 0.5rem; border-radius:6px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#fff; display:inline-block; margin-right:0.25rem; margin-bottom:0.25rem;">🧱 ${mat}</span>`).join(' ');
    return `
      <div class="agent-output-card">
        <div class="repair-title" style="font-size:0.92rem; font-weight:700; color:var(--primary-glow);">🛠️ Action Plan: ${output.repair_method || 'Standard Resurfacing'}</div>
        <div style="display:flex; gap:1.5rem; margin-top:0.5rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top:0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:0.5rem;">
          <div>
            <span class="cell-label" style="display:block;">Estimated Cost</span>
            <span style="font-weight:800; color:var(--neon-amber); font-size:1.05rem;">${output.estimated_cost || '$150'}</span>
          </div>
          <div>
            <span class="cell-label" style="display:block;">Duration Estimate</span>
            <span style="font-weight:700; color:#fff; font-size:1.05rem;">🕒 ${output.estimated_duration || '3 hours'}</span>
          </div>
        </div>
        <div style="margin-top:0.5rem;">
          <span class="cell-label" style="margin-bottom:0.3rem; display:block;">Bill of Materials (BOM)</span>
          <div style="display:flex; flex-wrap:wrap; gap:0.25rem; margin-top:0.25rem;">
            ${materialsHtml || '<span style="color:var(--text-muted); font-size:0.85rem;">Standard asphalt patch mixture</span>'}
          </div>
        </div>
      </div>
    `;
  }
  
  if (agentName.includes("Government")) {
    const incId = output.incident_id || 'inc_pending';
    const cleanId = incId.includes('_') ? incId.split('_')[1] : incId;
    return `
      <div class="agent-output-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
          <div>
            <span class="cell-label">Assigned Agency</span>
            <span style="font-weight:700; color:#fff; display:block; margin-top:0.15rem; font-size:0.92rem;">🏢 ${output.department || 'Municipal Maintenance Dept'}</span>
          </div>
          <span class="badge" style="background: rgba(5, 249, 226, 0.1); color: var(--neon-teal); border: 1px solid var(--neon-teal); animation: pulse 2s infinite; font-size:0.75rem; padding:0.15rem 0.5rem;">
            ● Dispatch Initiated
          </span>
        </div>
        <div style="background:rgba(255,255,255,0.02); padding:0.65rem; border-radius:8px; border: 1px solid rgba(255,255,255,0.05); margin-top:0.25rem;">
          <span class="cell-label" style="font-family:var(--font-mono); font-size:0.72rem; display:block; margin-bottom:0.25rem;">Registry Work Order ID: #${cleanId}</span>
          <p style="font-size:0.84rem; color:var(--text-muted); line-height:1.45;">
            ${output.government_summary || 'Work order logged successfully.'}
          </p>
        </div>
      </div>
    `;
  }
  
  if (agentName.includes("Civic")) {
    const badgeName = output.badge || 'None';
    const badgeEarnedHtml = badgeName !== "None" ? `
      <div style="display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem; background:rgba(255,170,0,0.1); border:1px solid var(--neon-amber); padding:0.5rem; border-radius:8px;">
        <span style="font-size:1.3rem;">🏅</span>
        <div>
          <div style="font-weight:700; color:var(--neon-amber); font-size:0.75rem;">New Badge Unlocked!</div>
          <div style="color:#fff; font-size:0.85rem; font-weight:800;">${badgeName}</div>
        </div>
      </div>
    ` : '';
    
    return `
      <div class="agent-output-card">
        <div style="display:grid; grid-template-columns:1.2fr 1fr; gap:1rem;">
          <div style="border-right: 1px solid var(--border-glass); padding-right:1rem; display:flex; flex-direction:column; justify-content:center;">
            <span class="cell-label">Civic Payout</span>
            <div style="font-size:1.8rem; font-weight:800; color:var(--neon-teal); display:flex; align-items:center; gap:0.25rem; margin-top:0.15rem;">
              +${output.reward_points || 0} <span style="font-size:0.85rem; font-weight:600; color:var(--text-muted);">pts</span>
            </div>
          </div>
          <div style="display:flex; flex-direction:column; justify-content:center; padding-left:0.5rem;">
            <span class="cell-label">Status Upgrade</span>
            <span style="font-weight:700; color:#fff; font-size:0.92rem; display:flex; align-items:center; gap:0.25rem; margin-top:0.15rem;">🛡️ ${output.contribution_level || 'Active Citizen'}</span>
          </div>
        </div>
        ${badgeEarnedHtml}
      </div>
    `;
  }
  
  if (agentName.includes("Analytics")) {
    const active = output.total_active_hazards || '0';
    const rating = output.average_risk_rating || output.average_risk_score || 0;
    const ratingVal = typeof rating === 'number' ? rating : (parseFloat(rating) || 0.0);
    return `
      <div class="agent-output-card">
        <div class="output-grid" style="grid-template-columns:1fr 1fr;">
          <div class="output-cell">
            <span class="cell-label">City Active Hazards</span>
            <span style="font-size:1.15rem; font-weight:800; color:#fff; display:block; margin-top:0.15rem;">📊 ${active} Hazards</span>
          </div>
          <div class="output-cell">
            <span class="cell-label">Metropolitan Avg Risk</span>
            <span style="font-size:1.15rem; font-weight:800; color:var(--neon-amber); display:block; margin-top:0.15rem;">⚠️ ${ratingVal.toFixed(1)}/100</span>
          </div>
        </div>
        <div style="margin-top:0.4rem; text-align:center; font-size:0.8rem; color:var(--neon-teal); font-weight:600; border-top:1px dashed var(--border-glass); padding-top:0.4rem;">
          ✓ Metropolitan hot-spot registries successfully updated
        </div>
      </div>
    `;
  }

  // Fallback
  return `<pre class="timeline-output-fallback" style="margin:0; font-family:var(--font-mono); font-size:0.8rem; color:var(--text-muted);">${JSON.stringify(output, null, 2)}</pre>`;
}

function initMonitoringPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = urlParams.get('id');
  if (!incidentId) {
    alert("No incident ID provided.");
    window.location.href = '/citizen.html';
    return;
  }

  const logConsole = document.getElementById('console-log');
  const timelineItems = {
    1: document.getElementById('step-1'),
    2: document.getElementById('step-2'),
    3: document.getElementById('step-3'),
    4: document.getElementById('step-4'),
    5: document.getElementById('step-5'),
    6: document.getElementById('step-6')
  };

  const logToConsole = (text, type = 'progress') => {
    const line = document.createElement('div');
    line.className = `console-line ${type}`;
    line.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
    logConsole.appendChild(line);
    logConsole.scrollTop = logConsole.scrollHeight;
  };

  logToConsole(`Starting stream interface client for incident ${incidentId}...`, 'system');

  let syncFallbackInitiated = false;

  const handleEvent = (eventType, eventData) => {
    if (eventType === 'pipeline_start') {
      logToConsole(eventData.message, 'system');
    } else if (eventType === 'agent_start') {
      logToConsole(`>>> Agent activated: "${eventData.agent}" (${eventData.role})`, 'start');
      logToConsole(`Status: ${eventData.status}`, 'progress');
      
      const stepNum = getStepNum(eventData.agent);
      if (stepNum && timelineItems[stepNum]) {
        resetTimelineClasses();
        timelineItems[stepNum].classList.add('active');
        timelineItems[stepNum].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    } else if (eventType === 'agent_progress') {
      logToConsole(eventData.log, 'progress');
      if (eventData.tool_calls && eventData.tool_calls.length > 0) {
        eventData.tool_calls.forEach(tc => {
          logToConsole(`[Tool Call] Executing: ${tc.name}(${JSON.stringify(tc.args)})`, 'system');
        });
      }
    } else if (eventType === 'agent_success') {
      logToConsole(`<<< Agent "${eventData.agent}" executed successfully.`, 'success');
      
      const stepNum = getStepNum(eventData.agent);
      if (stepNum && timelineItems[stepNum]) {
        timelineItems[stepNum].classList.remove('active');
        timelineItems[stepNum].classList.add('done');
        
        const outputBox = timelineItems[stepNum].querySelector('.timeline-output');
        if (outputBox) {
          outputBox.innerHTML = renderAgentOutput(eventData.agent, eventData.output);
          outputBox.style.display = 'block';
        }
      }
    } else if (eventType === 'pipeline_complete') {
      logToConsole(`*** PIPELINE RUN FINISHED: ${eventData.message} Status: ${eventData.final_status} ***`, 'system');
      
      resetTimelineClasses();
      if (timelineItems[6]) {
        timelineItems[6].classList.add('done');
        const outputBox = timelineItems[6].querySelector('.timeline-output');
        if (outputBox && !outputBox.innerHTML) {
          outputBox.innerHTML = `
            <div class="agent-output-card" style="text-align:center; padding: 0.5rem 0;">
              <div style="font-weight:800; color:var(--neon-teal); font-size:1.05rem; margin-bottom:0.25rem;">🌐 Pipeline Completed Successfully</div>
              <p style="font-size:0.85rem; color:var(--text-muted);">Hotspots updated. Analytics dashboards compiled.</p>
            </div>
          `;
          outputBox.style.display = 'block';
        }
      }
      document.getElementById('complete-controls').style.display = 'block';
    }
  };

  const runSyncFallback = async () => {
    if (syncFallbackInitiated) return;
    syncFallbackInitiated = true;
    
    logToConsole("Vercel serverless buffering detected. Switching to high-speed REST sync-channel...", "system");
    
    try {
      const res = await fetch(`/api/incidents/${incidentId}/run-sync`, { method: 'POST' });
      if (!res.ok) {
        throw new Error(`Sync API returned status ${res.status}`);
      }
      
      const resData = await res.json();
      if (resData.status === 'success') {
        logToConsole("Sync-channel data received. Playing back multi-agent execution telemetry...", "system");
        
        // Play back the events with typewriter delays to preserve the visual wow effect
        let index = 0;
        const playNext = () => {
          if (index < resData.events.length) {
            const ev = resData.events[index];
            handleEvent(ev.event, ev.data);
            index++;
            
            // Delays simulate live agents processing
            let delay = 1000;
            if (ev.event === 'agent_progress') delay = 500;
            setTimeout(playNext, delay);
          }
        };
        playNext();
      } else {
        logToConsole(`Pipeline execution failed: ${resData.message}`, 'error');
        document.getElementById('complete-controls').style.display = 'block';
      }
    } catch (err) {
      logToConsole(`Failed to execute fallback pipeline: ${err.message}`, 'error');
      document.getElementById('complete-controls').style.display = 'block';
    }
  };

  // Check if we have pre-computed telemetry in sessionStorage
  const cachedTelemetry = sessionStorage.getItem(`telemetry_${incidentId}`);
  if (cachedTelemetry) {
    logToConsole("Stateless telemetry cache found. Playing back multi-agent execution telemetry...", "system");
    try {
      const events = JSON.parse(cachedTelemetry);
      let index = 0;
      const playNext = () => {
        if (index < events.length) {
          const ev = events[index];
          handleEvent(ev.event, ev.data);
          index++;
          let delay = 1000;
          if (ev.event === 'agent_progress') delay = 500;
          setTimeout(playNext, delay);
        }
      };
      playNext();
      return;
    } catch (err) {
      logToConsole("Error parsing cached telemetry: " + err.message, "error");
    }
  }

  // Open EventSource connection for Server-Sent Events (SSE)
  const es = new EventSource(`/api/incidents/${incidentId}/stream`);

  es.addEventListener('pipeline_start', (e) => {
    const data = JSON.parse(e.data);
    handleEvent('pipeline_start', data);
  });

  es.addEventListener('agent_start', (e) => {
    const data = JSON.parse(e.data);
    handleEvent('agent_start', data);
  });

  es.addEventListener('agent_progress', (e) => {
    const data = JSON.parse(e.data);
    handleEvent('agent_progress', data);
  });

  es.addEventListener('agent_success', (e) => {
    const data = JSON.parse(e.data);
    handleEvent('agent_success', data);
  });

  es.addEventListener('pipeline_complete', (e) => {
    const data = JSON.parse(e.data);
    handleEvent('pipeline_complete', data);
    es.close();
  });

  es.addEventListener('error', (e) => {
    es.close();
    // Fallback immediately to the synchronous REST channel on Vercel
    runSyncFallback();
  });
}

function getStepNum(agentName) {
  if (agentName.includes("Detection")) return 1;
  if (agentName.includes("Risk")) return 2;
  if (agentName.includes("Repair")) return 3;
  if (agentName.includes("Government")) return 4;
  if (agentName.includes("Civic")) return 5;
  if (agentName.includes("Analytics")) return 6;
  return null;
}

function resetTimelineClasses() {
  for (let i = 1; i <= 6; i++) {
    const el = document.getElementById(`step-${i}`);
    if (el) el.classList.remove('active');
  }
}


// =====================================================================
// 4. CITIZEN DASHBOARD
// =====================================================================

async function initCitizenDashboard() {
  if (!State.user) {
    window.location.href = '/login.html';
    return;
  }

  // Load points and stats
  const pointsVal = document.getElementById('citizen-points-val');
  const levelVal = document.getElementById('citizen-level-val');
  const badgeCount = document.getElementById('citizen-badges-count');

  try {
    const resRewards = await fetch('/api/rewards');
    if (resRewards.ok) {
      const rData = await resRewards.json();
      if (pointsVal) pointsVal.innerText = rData.points;
      
      // Count unique badges
      if (badgeCount) badgeCount.innerText = rData.badges.length;
      if (levelVal) {
        if (rData.points > 300) levelVal.innerText = "Veteran Builder";
        else if (rData.points > 100) levelVal.innerText = "City Guardian";
        else levelVal.innerText = "Active Citizen";
      }

      // Render recent badges on dashboard
      const badgeBox = document.getElementById('dashboard-badges-container');
      if (badgeBox) {
        badgeBox.innerHTML = rData.badges.map(b => `
          <div class="badge-pill gold">🏅 ${b}</div>
        `).join('') || `<p style="color:var(--text-muted); font-size:0.9rem;">No badges earned yet. Submit verified reports to earn badges.</p>`;
      }
    }

    // Load reports
    const resInc = await fetch(`/api/incidents?user_id=${State.user.id}`);
    if (resInc.ok) {
      let incidents = await resInc.json();
      
      // Merge with local incidents to combat Vercel container recycling
      try {
        const localIncidents = JSON.parse(localStorage.getItem('local_incidents') || '[]')
          .filter(i => i.reporter_id === State.user.id);
          
        const existingIds = new Set(incidents.map(i => i.id));
        localIncidents.forEach(li => {
          if (!existingIds.has(li.id)) {
            incidents.push(li);
          }
        });
        
        incidents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      } catch (err) {
        console.error("Error merging local incidents:", err);
      }

      const listContainer = document.getElementById('citizen-reports-list');
      if (listContainer) {
        listContainer.innerHTML = incidents.map(inc => {
          const incId = inc.id || 'inc_0000';
          const cleanId = incId.includes('_') ? incId.split('_')[1] : incId;
          return `
            <div class="glass-panel report-item">
              <div>
                <h4 style="font-weight:700;">#${cleanId} - ${inc.detection?.damage_type || 'Infrastructure Hazard'}</h4>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.25rem;">
                  📍 Coordinate: ${inc.latitude.toFixed(4)}, ${inc.longitude.toFixed(4)} | Reported: ${new Date(inc.created_at).toLocaleDateString()}
                </p>
              </div>
              <div style="display:flex; align-items:center; gap:1rem;">
                <span class="badge badge-${getSeverityClass(inc.risk?.priority || 'Low')}">${inc.risk?.priority || 'Pending'}</span>
                <span style="font-size:0.85rem; font-weight:700; color:var(--text-muted);">${inc.status.toUpperCase()}</span>
                <a href="/tracker.html?id=${inc.id}" class="btn btn-secondary" style="padding:0.4rem 0.8rem; font-size:0.8rem;">Track</a>
              </div>
            </div>
          `;
        }).join('') || `<p style="color:var(--text-muted); font-size:0.95rem;">You haven't reported any infrastructure issues yet.</p>`;
      }
    }
  } catch (err) {
    console.error("Dashboard loading error:", err);
  }
}

function getSeverityClass(priority) {
  priority = priority.toLowerCase();
  if (priority === 'critical') return 'critical';
  if (priority === 'high') return 'high';
  if (priority === 'medium') return 'medium';
  return 'low';
}


// =====================================================================
// 5. REWARD CENTER
// =====================================================================

async function initRewardsPage() {
  if (!State.user) {
    window.location.href = '/login.html';
    return;
  }

  // Load balances
  const loadBalances = async () => {
    const res = await fetch('/api/rewards');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('rewards-points-balance').innerText = data.points;
      
      // Load History
      const hist = document.getElementById('rewards-history-table');
      if (hist) {
        hist.innerHTML = data.transactions.map(tx => `
          <tr>
            <td style="font-family:var(--font-mono); font-size:0.85rem;">#${tx.id.split('_')[1]}</td>
            <td>${new Date(tx.timestamp).toLocaleString()}</td>
            <td>
              <span style="color:${tx.type === 'earn' ? 'var(--neon-teal)' : 'var(--neon-red)'}">
                ${tx.type === 'earn' ? '+' : '-'}${tx.points} pts
              </span>
            </td>
            <td style="font-size:0.9rem;">${tx.reason || tx.reward_name}</td>
          </tr>
        `).join('') || `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No reward transaction history.</td></tr>`;
      }
    }
  };

  await loadBalances();

  // Setup click handlers for redemptions
  window.redeemItem = async (rewardId) => {
    if (!confirm("Are you sure you want to redeem points for this simulated coupon?")) return;
    try {
      const res = await fetch('/api/rewards/redeem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reward_id: rewardId })
      });
      const data = await res.json();
      if (res.ok) {
        // Show simulation coupon code
        const codeBox = document.getElementById('coupon-reveal-box');
        codeBox.style.display = 'block';
        document.getElementById('revealed-coupon-code').innerText = data.coupon_code;
        document.getElementById('revealed-coupon-text').innerText = data.message;
        
        await loadBalances();
        // Update user state
        await checkAuthStatus();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        alert("Redemption failed: " + data.message);
      }
    } catch (err) {
      alert("Error: " + err);
    }
  };
}


// =====================================================================
// 6. LEADERBOARDS
// =====================================================================

async function initLeaderboardPage() {
  try {
    const res = await fetch('/api/leaderboard');
    if (res.ok) {
      const data = await res.json();
      const boardBody = document.getElementById('leaderboard-tbody');
      if (boardBody) {
        boardBody.innerHTML = data.map(item => `
          <tr>
            <td><span class="rank-badge rank-${item.rank <= 3 ? item.rank : 'default'}">${item.rank}</span></td>
            <td style="font-weight:700;">${item.name}</td>
            <td style="font-weight:800; color:var(--neon-amber);">${item.points} pts</td>
            <td>
              <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                ${item.badges.map(b => `<span class="badge badge-medium" style="font-size:0.75rem;">🏅 ${b}</span>`).join('') || '<span style="color:var(--text-muted); font-size:0.85rem;">None</span>'}
              </div>
            </td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error("Leaderboard fetch error:", err);
  }
}


// =====================================================================
// 7. GOVERNMENT PORTAL (AUTHORITY)
// =====================================================================

async function initAuthorityPage() {
  const check = requireAdminOrAuthority();
  if (!check) return;

  const loadIncidents = async (filter = 'all') => {
    try {
      const res = await fetch('/api/incidents');
      if (res.ok) {
        const incidents = await res.json();
        const tbody = document.getElementById('authority-incidents-tbody');
        if (!tbody) return;

        // Apply local filtering
        let displayList = incidents;
        if (filter !== 'all') {
          displayList = incidents.filter(inc => inc.status === filter);
        }

        tbody.innerHTML = displayList.map(inc => {
          const detail = inc.detection || {};
          const risk = inc.risk || {};
          const dispatch = inc.dispatch || {};
          
          let actionBtn = '';
          if (inc.status === 'reported') {
            actionBtn = `<button onclick="updateStatus('${inc.id}', 'dispatched')" class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.78rem;">⚡ Dispatch Crew</button>`;
          } else if (inc.status === 'dispatched' || inc.status === 'in-progress') {
            actionBtn = `<button onclick="updateStatus('${inc.id}', 'resolved')" class="btn btn-secondary" style="padding:0.4rem 0.8rem; font-size:0.78rem; border-color:var(--neon-teal); color:var(--neon-teal);">✓ Complete Repair</button>`;
          } else {
            actionBtn = `<span style="color:var(--text-muted); font-size:0.85rem;">None Required</span>`;
          }

          return `
            <tr>
              <td style="font-family:var(--font-mono); font-size:0.82rem;">#${inc.id.split('_')[1]}</td>
              <td style="font-weight:700;">${detail.damage_type || 'Unknown'}</td>
              <td><span class="badge badge-${getSeverityClass(risk.priority || 'Low')}">${risk.priority || 'Low'}</span></td>
              <td style="font-size:0.85rem; color:var(--text-muted);">${dispatch.department || 'Not Assigned'}</td>
              <td style="font-weight:700; font-size:0.88rem; text-transform:uppercase;">${inc.status}</td>
              <td>${actionBtn}</td>
            </tr>
          `;
        }).join('') || `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:2rem;">No incidents match the active filter.</td></tr>`;
      }
    } catch (err) {
      console.error("Gov incidents load error:", err);
    }
  };

  await loadIncidents();

  // Setup tab filters
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadIncidents(tab.dataset.filter);
    });
  });

  // Action dispatcher
  window.updateStatus = async (id, status) => {
    if (!confirm(`Confirm incident status transition to "${status}"?`)) return;
    try {
      const res = await fetch(`/api/incidents/${id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        alert("Status updated successfully.");
        await loadIncidents(document.querySelector('.filter-tab.active').dataset.filter);
      } else {
        const err = await res.json();
        alert("Failed to update: " + err.message);
      }
    } catch (err) {
      alert("Error: " + err);
    }
  };
}

function requireAdminOrAuthority() {
  if (!State.user) {
    alert("Access Denied. Authority portal requires login.");
    window.location.href = '/login.html';
    return false;
  }
  if (State.user.role !== 'authority' && State.user.role !== 'admin') {
    alert("Access Denied. Government permissions required.");
    window.location.href = '/citizen.html';
    return false;
  }
  return true;
}


// =====================================================================
// 8. DATA ANALYTICS & HOTSPOT MAP
// =====================================================================

async function initAnalyticsPage() {
  try {
    const res = await fetch('/api/analytics');
    if (!res.ok) return;
    const data = await res.json();

    // Populate text fields
    document.getElementById('anal-total').innerText = data.summary.total_incidents;
    document.getElementById('anal-resolved').innerText = data.summary.resolved;
    document.getElementById('anal-active').innerText = data.summary.in_progress;
    document.getElementById('anal-risk').innerText = data.summary.average_risk_score;

    // 1. Setup Hotspot Map using Leaflet
    const defaultLat = 12.9716;
    const defaultLon = 77.5946;
    const map = L.map('analytics-map').setView([defaultLat, defaultLon], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Overlay circles on coordinates representing danger
    data.hotspots.forEach(hs => {
      if (hs.latitude && hs.longitude) {
        // Color based on risk weight
        let color = '#05f9e2'; // Low
        if (hs.weight > 0.8) color = '#ff3366'; // Critical
        else if (hs.weight > 0.6) color = '#ffaa00'; // High
        else if (hs.weight > 0.4) color = '#4facfe'; // Medium

        L.circle([hs.latitude, hs.longitude], {
          color: color,
          fillColor: color,
          fillOpacity: 0.35,
          radius: 200 // 200 meters footprint
        }).addTo(map).bindPopup(`<b>${hs.description}</b><br>Danger Weight: ${Math.round(hs.weight*100)}/100`);
      }
    });

    // 2. Setup Chart.js Charts
    // Chart 1: Severity Doughnut
    const sevCtx = document.getElementById('chart-severity').getContext('2d');
    const sevLabels = Object.keys(data.severity_distribution);
    const sevValues = Object.values(data.severity_distribution);
    State.charts.severity = new Chart(sevCtx, {
      type: 'doughnut',
      data: {
        labels: sevLabels,
        datasets: [{
          data: sevValues,
          backgroundColor: ['#ff3366', '#ffaa00', '#4facfe', '#05f9e2'],
          borderColor: 'rgba(255, 255, 255, 0.08)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#fff' } }
        }
      }
    });

    // Chart 2: Category Bar
    const catCtx = document.getElementById('chart-category').getContext('2d');
    const catLabels = Object.keys(data.category_distribution);
    const catValues = Object.values(data.category_distribution);
    State.charts.category = new Chart(catCtx, {
      type: 'bar',
      data: {
        labels: catLabels,
        datasets: [{
          label: 'Active Infrastructure Incidents',
          data: catValues,
          backgroundColor: 'rgba(79, 172, 254, 0.6)',
          borderColor: '#4facfe',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#fff' } },
          x: { grid: { display: false }, ticks: { color: '#fff' } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });

    // Chart 3: Monthly risk trend
    const trendCtx = document.getElementById('chart-trend').getContext('2d');
    const trendLabels = data.monthly_risk_trend.map(t => t.month);
    const trendValues = data.monthly_risk_trend.map(t => t.risk_index);
    State.charts.trend = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: trendLabels,
        datasets: [{
          label: 'Danger Index Trend',
          data: trendValues,
          borderColor: '#a124f5',
          backgroundColor: 'rgba(161, 36, 245, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#fff' } },
          x: { grid: { display: false }, ticks: { color: '#fff' } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });

  } catch (err) {
    console.error("Analytics loading crash:", err);
  }
}


// =====================================================================
// 9. PUBLIC INCIDENT LIFECYCLE TRACKER
// =====================================================================

function initTrackerPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const searchId = urlParams.get('id');
  
  const searchInput = document.getElementById('tracker-search-input');
  const searchBtn = document.getElementById('tracker-search-btn');

  const executeSearch = async (incidentId) => {
    if (!incidentId) return;
    try {
      const res = await fetch(`/api/incidents/${incidentId}`);
      if (res.ok) {
        const inc = await res.json();
        renderTrackerResult(inc);
      } else {
        // Fallback to localStorage cache
        try {
          const localIncidents = JSON.parse(localStorage.getItem('local_incidents') || '[]');
          const found = localIncidents.find(i => i.id === incidentId);
          if (found) {
            renderTrackerResult(found);
            return;
          }
        } catch (e) {
          console.error("Local incident search failed:", e);
        }
        
        document.getElementById('tracker-result-container').innerHTML = `
          <div class="glass-panel" style="text-align:center; padding:3rem;">
            <h3 style="color:var(--neon-red)">Incident Not Found</h3>
            <p style="color:var(--text-muted); margin-top:0.5rem;">Double check the ID (e.g., inc_1624...) and try again.</p>
          </div>
        `;
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (searchId) {
    searchInput.value = searchId;
    executeSearch(searchId);
  }

  searchBtn.addEventListener('click', () => {
    executeSearch(searchInput.value.trim());
  });

  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') executeSearch(searchInput.value.trim());
  });
}

function renderTrackerResult(inc) {
  const container = document.getElementById('tracker-result-container');
  
  // Calculate active steps based on state
  const status = inc.status; // reported, dispatched, resolved, duplicate
  
  let step1Class = 'done';
  let step2Class = 'reported';
  let step3Class = 'pending';
  let step4Class = 'pending';

  if (status === 'reported') {
    step2Class = 'active';
  } else if (status === 'dispatched' || status === 'in-progress') {
    step2Class = 'done';
    step3Class = 'active';
  } else if (status === 'resolved') {
    step2Class = 'done';
    step3Class = 'done';
    step4Class = 'done';
  } else if (status === 'duplicate') {
    step2Class = 'error';
  }

  container.innerHTML = `
    <div class="glass-panel" style="margin-top:2rem;">
      <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem; border-bottom:1px solid var(--border-glass); padding-bottom:1.5rem; margin-bottom:1.5rem;">
        <div>
          <span class="badge badge-medium" style="margin-bottom:0.5rem;">${inc.detection?.category || 'Category'}</span>
          <h2 style="font-weight:800;">Incident #${inc.id.split('_')[1]}</h2>
          <p style="color:var(--text-muted); font-size:0.9rem; margin-top:0.25rem;">Reported by: ${inc.reporter_name} | Date: ${new Date(inc.created_at).toLocaleString()}</p>
        </div>
        <div style="text-align:right;">
          <p style="font-size:0.8rem; text-transform:uppercase; color:var(--text-muted);">Current State</p>
          <h3 style="font-weight:800; color:var(--secondary-glow); text-transform:uppercase;">${inc.status}</h3>
        </div>
      </div>

      <div class="dashboard-grid">
        <div>
          <h3 style="font-weight:700; margin-bottom:1rem;">Issue Details</h3>
          <p style="font-size:1.05rem; margin-bottom:1.5rem; padding:1rem; background:rgba(255,255,255,0.02); border-radius:10px; border:1px solid var(--border-glass);">
            "${inc.description}"
          </p>

          <!-- Timeline lifecycle tracker -->
          <h3 style="font-weight:700; margin-bottom:1.5rem;">Maintenance Lifecycle</h3>
          <div class="lifecycle-steps" style="display:flex; justify-content:space-between; margin-bottom:2rem; position:relative;">
            <div style="position:absolute; left:10%; right:10%; top:25px; height:2px; background:rgba(255,255,255,0.05); z-index:0;"></div>
            
            <div class="lifecycle-step ${step1Class}" style="text-align:center; flex:1; z-index:1;">
              <div class="step-circle" style="width:50px; height:50px; border-radius:50%; background:var(--bg-cyber); border:3px solid var(--border-glass); display:flex; align-items:center; justify-content:center; margin:0 auto 0.5rem auto; font-weight:800;">1</div>
              <p style="font-size:0.85rem; font-weight:600;">Reported</p>
            </div>
            
            <div class="lifecycle-step ${step2Class}" style="text-align:center; flex:1; z-index:1;">
              <div class="step-circle" style="width:50px; height:50px; border-radius:50%; background:var(--bg-cyber); border:3px solid var(--border-glass); display:flex; align-items:center; justify-content:center; margin:0 auto 0.5rem auto; font-weight:800;">2</div>
              <p style="font-size:0.85rem; font-weight:600;">AI Review</p>
            </div>
            
            <div class="lifecycle-step ${step3Class}" style="text-align:center; flex:1; z-index:1;">
              <div class="step-circle" style="width:50px; height:50px; border-radius:50%; background:var(--bg-cyber); border:3px solid var(--border-glass); display:flex; align-items:center; justify-content:center; margin:0 auto 0.5rem auto; font-weight:800;">3</div>
              <p style="font-size:0.85rem; font-weight:600;">Dispatched</p>
            </div>
            
            <div class="lifecycle-step ${step4Class}" style="text-align:center; flex:1; z-index:1;">
              <div class="step-circle" style="width:50px; height:50px; border-radius:50%; background:var(--bg-cyber); border:3px solid var(--border-glass); display:flex; align-items:center; justify-content:center; margin:0 auto 0.5rem auto; font-weight:800;">4</div>
              <p style="font-size:0.85rem; font-weight:600;">Resolved</p>
            </div>
          </div>

          <style>
            .lifecycle-step.done .step-circle { border-color: var(--primary-glow); background: rgba(79, 172, 254, 0.15); color: #fff; }
            .lifecycle-step.active .step-circle { border-color: var(--neon-teal); background: rgba(5, 249, 226, 0.1); color: var(--neon-teal); box-shadow: 0 0 15px rgba(5,249,226,0.3); animation: pulse-glow 1.5s infinite; }
            .lifecycle-step.error .step-circle { border-color: var(--neon-red); background: rgba(255, 51, 102, 0.1); color: var(--neon-red); }
            @keyframes pulse-glow {
              0% { transform: scale(1); }
              50% { transform: scale(1.08); }
              100% { transform: scale(1); }
            }
          </style>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-top:2rem;">
            <div>
              <h4 style="font-weight:700; color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; margin-bottom:0.5rem;">AI Danger Assessment</h4>
              <p style="font-size:0.95rem;"><b>Priority:</b> ${inc.risk?.priority || 'Pending'}</p>
              <p style="font-size:0.95rem; margin-top:0.25rem;"><b>Explanation:</b> ${inc.risk?.explanation || 'Pending multi-agent parsing...'}</p>
            </div>
            <div>
              <h4 style="font-weight:700; color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; margin-bottom:0.5rem;">Civil Engineering Advisor</h4>
              <p style="font-size:0.95rem;"><b>Repair Plan:</b> ${inc.repair?.repair_method || 'Pending'}</p>
              <p style="font-size:0.95rem; margin-top:0.25rem;"><b>Materials:</b> ${inc.repair?.materials?.join(', ') || 'Pending'}</p>
              <p style="font-size:0.95rem; margin-top:0.25rem;"><b>Budget Estimate:</b> ${inc.repair?.estimated_cost || 'Pending'}</p>
            </div>
          </div>
        </div>

        <div>
          <h3 style="font-weight:700; margin-bottom:1rem;">Asset Image</h3>
          <div style="border-radius:12px; overflow:hidden; border:1px solid var(--border-glass); background:rgba(0,0,0,0.2);">
            <img src="${inc.image_url}" alt="Infrastructure damage" style="width:100%; height:auto; display:block;">
          </div>
          <div style="margin-top:1.5rem;">
            <p style="font-size:0.85rem; color:var(--text-muted);"><b>Dispatch Agency:</b></p>
            <p style="font-size:0.95rem; font-weight:700;">${inc.dispatch?.department || 'Awaiting Allocation'}</p>
            
            <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.75rem;"><b>Work Order ID:</b></p>
            <p style="font-size:0.95rem; font-family:var(--font-mono);">${inc.dispatch?.work_order_id || 'Pending Review'}</p>

            <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.75rem;"><b>Civic Rewards:</b></p>
            <p style="font-size:0.95rem; font-weight:700; color:var(--neon-teal);">${inc.reward?.reward_points || 0} Points Awarded</p>
          </div>
        </div>
      </div>
    </div>
  `;
}


// =====================================================================
// 10. SYSTEM ADMIN PANEL
// =====================================================================

async function initAdminPage() {
  const check = requireAdmin();
  if (!check) return;

  try {
    const res = await fetch('/api/admin/stats');
    if (res.ok) {
      const stats = await res.json();
      document.getElementById('admin-stat-users').innerText = stats.total_users;
      document.getElementById('admin-stat-citizens').innerText = stats.total_citizens;
      document.getElementById('admin-stat-reports').innerText = stats.total_reports;
      document.getElementById('admin-stat-points').innerText = stats.total_points_distributed;
      document.getElementById('admin-stat-redemptions').innerText = stats.total_redemptions;
    }
  } catch (err) {
    console.error("Admin stats failed:", err);
  }
}

function requireAdmin() {
  if (!State.user) {
    alert("Admin Login Required.");
    window.location.href = '/login.html';
    return false;
  }
  if (State.user.role !== 'admin') {
    alert("Access Denied. Administrator credentials required.");
    window.location.href = '/citizen.html';
    return false;
  }
  return true;
}


// =====================================================================
// 11. PROFILE PAGE
// =====================================================================

async function initProfilePage() {
  if (!State.user) {
    window.location.href = '/login.html';
    return;
  }

  document.getElementById('profile-name').innerText = State.user.name;
  document.getElementById('profile-email').innerText = State.user.email;
  document.getElementById('profile-role').innerText = State.user.role.toUpperCase();
  document.getElementById('profile-points').innerText = State.user.points;

  try {
    const res = await fetch('/api/rewards');
    if (res.ok) {
      const data = await res.json();
      const container = document.getElementById('profile-badges-container');
      if (container) {
        container.innerHTML = data.badges.map(b => `
          <div class="badge-pill gold" style="padding: 0.75rem 1.25rem; font-size:1rem;">
            🏆 <b>${b}</b>
          </div>
        `).join('') || `<p style="color:var(--text-muted);">No badges earned yet. Submit issues to earn badges!</p>`;
      }
    }
  } catch (err) {
    console.error("Profile load crash:", err);
  }
}
