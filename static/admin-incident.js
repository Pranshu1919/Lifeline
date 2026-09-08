// LifeLine Incident Detail & Human Manual Resource Manager JS Engine
let detailMap;
let incidentMarker = null;
let currentIncidentCode = "INC-2026-0001";
let currentIncidentData = null;

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const codeParam = urlParams.get('id');
  if (codeParam) {
    currentIncidentCode = codeParam;
  }

  document.getElementById('codeTitle').innerText = currentIncidentCode;
  const trackBtn = document.getElementById('trackIncidentBtn');
  if (trackBtn) trackBtn.href = `/track?id=${currentIncidentCode}`;

  initDetailMap();
  fetchIncidentDetails();
  fetchUnits();

  // Manual Unit Assign Event
  document.getElementById('manualAssignBtn').addEventListener('click', handleManualAssign);
  
  // AI MILP Assign Event
  document.getElementById('aiAssignBtn').addEventListener('click', handleAiAssign);
});

function initDetailMap() {
  detailMap = L.map('detailMap').setView([28.6752, 77.5020], 14);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(detailMap);
}

async function fetchIncidentDetails() {
  try {
    const res = await fetch(`/api/incidents/${currentIncidentCode}`);
    if (!res.ok) {
      alert("Incident code not found.");
      window.location.href = "/";
      return;
    }

    const data = await res.json();
    const inc = data.incident;
    const assignedUnit = data.assigned_unit;
    currentIncidentData = inc;

    document.getElementById('descriptionText').innerText = inc.description || "No situation description provided.";
    document.getElementById('demandsText').innerText = inc.demands || "Standard Disaster Emergency Relief";
    document.getElementById('severityBadge').innerText = `Severity Level ${floatFormat(inc.composite_severity || inc.severity)} / 5.0`;
    document.getElementById('statusBadge').innerText = inc.status;
    document.getElementById('coordsDisplay').innerText = `Lat: ${inc.latitude.toFixed(4)} | Lng: ${inc.longitude.toFixed(4)}`;
    document.getElementById('reporterName').innerText = inc.reporter_name || "Anonymous";
    document.getElementById('reporterPhone').innerText = inc.reporter_phone || "Not provided";
    document.getElementById('reportTime').innerText = inc.created_at || "Recently";

    // Needs Chips
    const needsContainer = document.getElementById('needsChipsContainer');
    if (inc.needs) {
      needsContainer.innerHTML = inc.needs.split(',').map(n => `<span class="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700 font-medium">${n.trim()}</span>`).join('');
    } else {
      needsContainer.innerHTML = `<span class="text-slate-500 italic">General Rescue Assistance</span>`;
    }

    // Media Box
    const mediaBox = document.getElementById('mediaBox');
    if (inc.video_url) {
      mediaBox.innerHTML = `<video src="${inc.video_url}" controls autoplay class="max-h-64 rounded-xl border border-slate-800 w-full object-cover"></video>`;
    } else if (inc.image_url) {
      mediaBox.innerHTML = `<img src="${inc.image_url}" class="max-h-64 rounded-xl border border-slate-800 object-contain">`;
    } else {
      mediaBox.innerHTML = `<span class="text-xs text-slate-500"><i class="fa-solid fa-camera text-slate-600 text-xl block mb-1"></i> No media attached</span>`;
    }

    // Map Marker
    const pinColor = inc.composite_severity >= 4 ? '#ef4444' : '#f59e0b';
    if (!incidentMarker) {
      const customIcon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background-color:${pinColor}; width:22px; height:22px; border-radius:50%; border:2px solid white; box-shadow:0 0 12px ${pinColor};"></div>`,
        iconSize: [22, 22]
      });
      incidentMarker = L.marker([inc.latitude, inc.longitude], { icon: customIcon }).addTo(detailMap);
      detailMap.setView([inc.latitude, inc.longitude], 14);
    } else {
      incidentMarker.setLatLng([inc.latitude, inc.longitude]);
    }

    // Assigned Unit Status Card
    if (assignedUnit) {
      document.getElementById('assignedUnitDisplay').innerText = `${assignedUnit.unit_code} (${assignedUnit.type})`;
      document.getElementById('assignedUnitSub').innerText = `Vehicle capacity: ${assignedUnit.capacity} persons | Speed: ${assignedUnit.speed_kmh} km/h`;
    } else if (inc.assigned_unit_code) {
      document.getElementById('assignedUnitDisplay').innerText = inc.assigned_unit_code;
      document.getElementById('assignedUnitSub').innerText = `Dispatched to incident location.`;
    } else {
      document.getElementById('assignedUnitDisplay').innerText = "Dispatch Pending";
      document.getElementById('assignedUnitSub').innerText = "Select a vehicle below to manually assign.";
    }

  } catch (err) {
    console.error("Error fetching incident details:", err);
  }
}

async function fetchUnits() {
  try {
    const res = await fetch('/api/units');
    const data = await res.json();
    const units = data.units || [];

    const select = document.getElementById('unitSelect');
    select.innerHTML = units.map(u => `
      <option value="${u.unit_code}">
        ${u.unit_code} - ${u.type} (${u.status}) [Cap: ${u.capacity}]
      </option>
    `).join('');
  } catch (err) {
    console.error("Error fetching units:", err);
  }
}

async function handleManualAssign() {
  const selectedUnitCode = document.getElementById('unitSelect').value;
  if (!selectedUnitCode) {
    alert("Please select a vehicle to assign.");
    return;
  }

  const btn = document.getElementById('manualAssignBtn');
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Assigning...`;

  try {
    const res = await fetch('/api/incidents/assign-manual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        incident_code: currentIncidentCode,
        unit_code: selectedUnitCode
      })
    });

    const data = await res.json();
    if (res.ok) {
      alert(`Successfully allocated ${selectedUnitCode} to incident ${currentIncidentCode}!`);
      fetchIncidentDetails();
      fetchUnits();
    } else {
      alert("Allocation error: " + (data.error || "Server error"));
    }
  } catch (err) {
    alert("Manual allocation failed.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-truck-dispatch"></i> Manually Assign Vehicle`;
  }
}

async function handleAiAssign() {
  const btn = document.getElementById('aiAssignBtn');
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running Solver...`;

  try {
    const res = await fetch('/api/ml/optimize-dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    const data = await res.json();
    if (res.ok && data.dispatch_plan) {
      const match = data.dispatch_plan.find(item => item.incident_code === currentIncidentCode);
      if (match) {
        document.getElementById('xaiBox').classList.remove('hidden');
        document.getElementById('xaiText').innerText = match.xai_rationale;
      } else {
        alert("AI solver finished. Check assigned unit status.");
      }
      fetchIncidentDetails();
      fetchUnits();
    }
  } catch (err) {
    alert("AI Solver failed.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles text-yellow-300"></i> Auto-Assign Rescue Units`;
  }
}

function floatFormat(val) {
  const num = parseFloat(val) || 3.5;
  return num.toFixed(1);
}
