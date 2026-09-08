// LifeLine Official Emergency Control Center Admin JS Engine
let adminMap;
let incidentMarkers = [];
let unitMarkers = [];
let shelterMarkers = [];
let activeIncidents = [];
let activeUnits = [];
let activeShelters = [];

document.addEventListener("DOMContentLoaded", () => {
  initAdminMap();
  fetchStats();
  fetchIncidents();
  fetchUnits();
  fetchShelters();

  document.getElementById('runOptimizerBtn').addEventListener('click', runOptimizer);

  // Search & Filters
  document.getElementById('tableSearchInput').addEventListener('input', renderIncidentsTable);
  document.getElementById('categoryFilter').addEventListener('change', renderIncidentsTable);

  // Fast Polling Fallback (Every 2 Seconds)
  setInterval(() => {
    fetchStats();
    fetchIncidents();
    fetchUnits();
    fetchShelters();
  }, 2000);

  connectWebSocket();
});

function initAdminMap() {
  adminMap = L.map('adminMap').setView([28.6752, 77.5020], 13);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(adminMap);
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('statTotal').innerText = data.total_incidents || 0;
    document.getElementById('statCritical').innerText = data.critical_incidents || 0;
    document.getElementById('statUnits').innerText = data.available_units || 0;
    document.getElementById('statShelters').innerText = data.active_shelters || 2;
  } catch (err) {
    console.error("Stats fetch error:", err);
  }
}

async function fetchIncidents() {
  try {
    const res = await fetch('/api/incidents');
    const data = await res.json();
    activeIncidents = data.incidents || [];

    activeIncidents.sort((a, b) => b.severity - a.severity);

    incidentMarkers.forEach(m => adminMap.removeLayer(m));
    incidentMarkers = [];

    activeIncidents.forEach(inc => {
      const pinColor = inc.severity >= 4 ? '#ef4444' : inc.severity >= 3 ? '#f59e0b' : '#3b82f6';
      const customIcon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background-color:${pinColor}; width:20px; height:20px; border-radius:50%; border:2px solid white; box-shadow:0 2px 10px rgba(0,0,0,0.4);"></div>`,
        iconSize: [20, 20]
      });

      const m = L.marker([inc.latitude, inc.longitude], { icon: customIcon }).addTo(adminMap);
      let popupContent = `
        <div class="p-1 font-sans text-xs text-slate-800">
          <div class="font-bold text-slate-900 text-sm mb-1">${inc.category} Emergency</div>
          <div class="text-slate-600 mb-1">${inc.description}</div>
          ${inc.demands ? `<div class="bg-amber-50 text-amber-900 p-1.5 rounded font-mono mb-1"><strong>Demands:</strong> ${inc.demands}</div>` : ''}
          <div class="pt-1.5 flex gap-1 justify-between items-center">
            <a href="/incident?id=${inc.incident_code}" class="text-[11px] bg-red-600 text-white font-bold px-2 py-1 rounded">Assign ➔</a>
            <a href="/track?id=${inc.incident_code}" class="text-[11px] bg-amber-600 text-white font-bold px-2 py-1 rounded">Track 📍</a>
          </div>
        </div>
      `;
      m.bindPopup(popupContent, { className: 'custom-popup' });
      incidentMarkers.push(m);
    });

    renderIncidentsTable();
  } catch (err) {
    console.error("Incidents fetch error:", err);
  }
}

function renderIncidentsTable() {
  const tbody = document.getElementById('incidentsTableBody');
  const searchVal = document.getElementById('tableSearchInput').value.toLowerCase();
  const catFilter = document.getElementById('categoryFilter').value;

  let filtered = activeIncidents.filter(inc => {
    const matchCat = (catFilter === 'ALL' || inc.category === catFilter);
    const matchSearch = (inc.description || '').toLowerCase().includes(searchVal) ||
                        (inc.demands || '').toLowerCase().includes(searchVal) ||
                        (inc.incident_code || '').toLowerCase().includes(searchVal);
    return matchCat && matchSearch;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-500">No incidents found matching criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(inc => {
    const badgeColor = inc.severity >= 4 ? 'bg-red-500/20 text-red-400 border-red-500/30' : inc.severity >= 3 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-blue-500/20 text-blue-400 border-blue-500/30';

    return `
      <tr onclick="window.location.href='/incident?id=${inc.incident_code}'" class="hover:bg-slate-800/60 transition cursor-pointer border-b border-slate-800/60">
        <td class="p-3 font-mono text-yellow-300 font-bold">${inc.incident_code}</td>
        <td class="p-3"><span class="px-2.5 py-1 rounded border text-xs font-bold ${badgeColor}">Level ${inc.severity.toFixed(1)} / 5.0</span></td>
        <td class="p-3 font-semibold text-white">${inc.category}</td>
        <td class="p-3 max-w-xs truncate text-slate-300" title="${inc.description}">${inc.description}</td>
        <td class="p-3 max-w-xs text-amber-300 font-mono text-xs truncate" title="${inc.demands || ''}">${inc.demands || '<span class="text-slate-600">Standard Relief</span>'}</td>
        <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${inc.status === 'DISPATCHED' ? 'bg-emerald-900/60 text-emerald-300' : 'bg-slate-800 text-slate-400'}">${inc.status}</span></td>
        <td class="p-3 font-mono text-blue-300">${inc.assigned_unit || '<span class="text-slate-600">Unassigned</span>'}</td>
        <td class="p-3 text-right">
          <div class="inline-flex gap-1.5">
            <a href="/incident?id=${inc.incident_code}" onclick="event.stopPropagation();" class="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-2.5 py-1.5 rounded-xl transition inline-flex items-center gap-1 shadow-sm">
              Manage <i class="fa-solid fa-chevron-right text-[10px]"></i>
            </a>
            <a href="/track?id=${inc.incident_code}" onclick="event.stopPropagation();" class="text-xs bg-amber-600 hover:bg-amber-500 text-white font-bold px-2.5 py-1.5 rounded-xl transition inline-flex items-center gap-1 shadow-sm">
              Track 📍
            </a>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function fetchUnits() {
  try {
    const res = await fetch('/api/units');
    const data = await res.json();
    activeUnits = data.units || [];

    unitMarkers.forEach(m => adminMap.removeLayer(m));
    unitMarkers = [];

    const unitsContainer = document.getElementById('unitsList');
    unitsContainer.innerHTML = activeUnits.map(u => {
      const uIcon = L.divIcon({
        className: 'unit-pin',
        html: `<div style="background-color:#3b82f6; width:20px; height:20px; border-radius:6px; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-size:10px;"><i class="fa-solid fa-truck-medical"></i></div>`,
        iconSize: [20, 20]
      });

      const m = L.marker([u.latitude, u.longitude], { icon: uIcon }).addTo(adminMap);
      m.bindPopup(`<div class="text-xs"><strong>${u.unit_code}</strong><br>Type: ${u.type}<br>Status: ${u.status}</div>`);
      unitMarkers.push(m);

      const statusBadge = u.status === 'AVAILABLE' ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700' : 'bg-amber-900/60 text-amber-300 border-amber-700';

      return `
        <div class="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 flex justify-between items-center text-xs">
          <div>
            <div class="font-bold text-white flex items-center gap-2">
              <span>${u.unit_code}</span>
              <span class="text-[10px] text-slate-400 font-normal">(${u.type})</span>
            </div>
            <div class="text-[10px] text-slate-400 mt-0.5">Capacity: ${u.capacity} persons | Speed: ${u.speed_kmh} km/h</div>
          </div>
          <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${statusBadge}">${u.status}</span>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error("Units fetch error:", err);
  }
}

async function fetchShelters() {
  try {
    const res = await fetch('/api/shelters');
    const data = await res.json();
    activeShelters = data.shelters || [];

    shelterMarkers.forEach(m => adminMap.removeLayer(m));
    shelterMarkers = [];

    const shelterContainer = document.getElementById('sheltersList');
    shelterContainer.innerHTML = activeShelters.map(s => {
      const sIcon = L.divIcon({
        className: 'shelter-pin',
        html: `<div style="background-color:#10b981; width:22px; height:22px; border-radius:50%; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-size:11px;"><i class="fa-solid fa-hospital"></i></div>`,
        iconSize: [22, 22]
      });

      const m = L.marker([s.latitude, s.longitude], { icon: sIcon }).addTo(adminMap);
      m.bindPopup(`<div class="text-xs"><strong>${s.name}</strong><br>Occupancy: ${s.occupied_beds} / ${s.total_capacity} beds</div>`);
      shelterMarkers.push(m);

      const percent = Math.round((s.occupied_beds / s.total_capacity) * 100);

      return `
        <div class="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 space-y-1">
          <div class="flex justify-between items-center text-xs">
            <span class="font-bold text-white">${s.name}</span>
            <span class="text-slate-400 font-mono text-[10px]">${s.occupied_beds}/${s.total_capacity} Beds</span>
          </div>
          <div class="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden">
            <div class="bg-emerald-500 h-1.5 rounded-full" style="width: ${percent}%"></div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error("Shelters fetch error:", err);
  }
}

async function runOptimizer() {
  const btn = document.getElementById('runOptimizerBtn');
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> RUNNING SOLVER...`;

  try {
    const res = await fetch('/api/ml/optimize-dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    const data = await res.json();
    if (res.ok && data.dispatch_plan) {
      renderXaiPanel(data.dispatch_plan);
      fetchIncidents();
      fetchUnits();
    } else {
      alert("No unassigned incidents or available units.");
    }
  } catch (err) {
    console.error("Optimizer error:", err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles text-yellow-300"></i> Auto-Assign Rescue Units`;
  }
}

function renderXaiPanel(plan) {
  const xaiPanel = document.getElementById('xaiPanel');
  const xaiContent = document.getElementById('xaiContent');

  if (plan.length === 0) {
    xaiContent.innerHTML = `<div class="text-slate-400 italic">All active incidents have already been assigned rescue units.</div>`;
  } else {
    xaiContent.innerHTML = plan.map(item => `
      <div class="bg-slate-800 p-2.5 rounded-xl border border-amber-500/30 font-mono text-[11px] space-y-1">
        <div class="text-amber-300 font-bold"><i class="fa-solid fa-truck-dispatch mr-1"></i> ${item.unit_code} ➔ ${item.incident_code}</div>
        <div class="text-slate-300">${item.xai_rationale}</div>
        <div class="text-slate-400 text-[10px]">Est Arrival: ${item.travel_time_minutes} minutes</div>
      </div>
    `).join('');
  }
  xaiPanel.classList.remove('hidden');
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  try {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = () => {
      fetchIncidents();
      fetchUnits();
      fetchStats();
    };
  } catch (e) {}
}
