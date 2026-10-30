// LifeLine Live Rescue & Relief Tracker JS Engine - Unified Citizen & Authority Tracking
let trackMap = null;
let victimMarker = null;
let unitMarker = null;
let stationMarker = null;
let trajectoryLine = null;
let currentIncidentCode = null;
let pollInterval = null;
let allIncidents = [];
let hasFitBounds = false;

document.addEventListener("DOMContentLoaded", () => {
  detectInterfaceMode();
  setupLookupControls();
  initIncidentResolution();
});

function detectInterfaceMode() {
  const isCommandCenter = window.location.port === '8001' || window.location.pathname.startsWith('/admin');
  const backToAdminBtn = document.getElementById('backToAdminBtn');
  const reportEmergencyNavBtn = document.getElementById('reportEmergencyNavBtn');

  if (isCommandCenter) {
    if (backToAdminBtn) backToAdminBtn.classList.remove('hidden');
    if (reportEmergencyNavBtn) reportEmergencyNavBtn.classList.add('hidden');
  } else {
    if (backToAdminBtn) backToAdminBtn.classList.add('hidden');
    if (reportEmergencyNavBtn) reportEmergencyNavBtn.classList.remove('hidden');
  }
}

async function initIncidentResolution() {
  const urlParams = new URLSearchParams(window.location.search);
  const codeParam = urlParams.get('id');

  // 1. Resolve from URL param
  if (codeParam && codeParam.trim()) {
    currentIncidentCode = codeParam.trim();
    try {
      localStorage.setItem('lifeline_active_incident', JSON.stringify({ code: currentIncidentCode }));
    } catch (e) {}
  } else {
    // 2. Resolve from personal report in localStorage
    try {
      const saved = localStorage.getItem('lifeline_active_incident');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && (parsed.code || parsed.incident_code)) {
          currentIncidentCode = (parsed.code || parsed.incident_code).trim();
        }
      }
    } catch (e) {}
  }

  // 3. Fetch all active incidents to populate the incident switcher dropdown
  await fetchAllIncidents();

  // 4. If still no incident code resolved, fallback to latest active incident from server
  if (!currentIncidentCode && allIncidents.length > 0) {
    currentIncidentCode = allIncidents[0].incident_code;
    window.history.replaceState(null, '', `/track?id=${currentIncidentCode}`);
  }

  const noReportState = document.getElementById('noReportState');
  const activeReportState = document.getElementById('activeReportState');
  const incidentCodeDisplay = document.getElementById('incidentCodeDisplay');

  if (!currentIncidentCode) {
    // Only show No Report state if the entire database has zero incidents
    if (noReportState) noReportState.classList.remove('hidden');
    if (activeReportState) activeReportState.classList.add('hidden');
  } else {
    if (noReportState) noReportState.classList.add('hidden');
    if (activeReportState) activeReportState.classList.remove('hidden');
    if (incidentCodeDisplay) incidentCodeDisplay.innerText = currentIncidentCode;

    initTrackMap();
    fetchIncidentTracker();
    connectWebSocket();

    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(fetchIncidentTracker, 3000);
  }
}

async function fetchAllIncidents() {
  try {
    const res = await fetch('/api/incidents');
    if (!res.ok) return;
    const data = await res.json();
    allIncidents = data.incidents || [];

    const select = document.getElementById('activeIncidentSelect');
    if (!select) return;

    if (allIncidents.length === 0) {
      select.innerHTML = '<option value="">No Active Operations</option>';
      return;
    }

    select.innerHTML = allIncidents.map(inc => {
      const unitTag = inc.assigned_unit ? `[${inc.assigned_unit}]` : '[Queued]';
      const sev = typeof inc.severity === 'number' ? inc.severity.toFixed(1) : '3.5';
      return `<option value="${inc.incident_code}" ${inc.incident_code === currentIncidentCode ? 'selected' : ''}>
        ${inc.incident_code} • ${inc.category} (${sev}) ${unitTag}
      </option>`;
    }).join('');

    select.onchange = () => {
      const chosen = select.value;
      if (chosen && chosen !== currentIncidentCode) {
        currentIncidentCode = chosen;
        hasFitBounds = false;
        try {
          localStorage.setItem('lifeline_active_incident', JSON.stringify({ code: chosen }));
        } catch (e) {}
        window.history.replaceState(null, '', `/track?id=${chosen}`);
        fetchIncidentTracker();
      }
    };
  } catch (err) {
    console.error("Error fetching incidents list:", err);
  }
}

function initTrackMap() {
  if (trackMap) {
    setTimeout(() => { if (trackMap) trackMap.invalidateSize(); }, 150);
    return;
  }
  const mapEl = document.getElementById('trackMap');
  if (!mapEl) return;

  trackMap = L.map('trackMap').setView([28.6752, 77.5020], 14);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(trackMap);

  setTimeout(() => { if (trackMap) trackMap.invalidateSize(); }, 200);
  setTimeout(() => { if (trackMap) trackMap.invalidateSize(); }, 600);
}

function setupLookupControls() {
  const toggleBtn = document.getElementById('toggleSearchBtn');
  const headerLookupBtn = document.getElementById('headerLookupBtn');
  const lookupContainer = document.getElementById('lookupContainer');
  const lookupSubmitBtn = document.getElementById('lookupSubmitBtn');
  const lookupInput = document.getElementById('lookupInput');
  const lookupMsg = document.getElementById('lookupMsg');

  function toggleLookup() {
    if (!lookupContainer) return;
    lookupContainer.classList.toggle('hidden');
    if (!lookupContainer.classList.contains('hidden') && lookupInput) {
      lookupInput.focus();
    }
  }

  if (toggleBtn) toggleBtn.addEventListener('click', toggleLookup);
  if (headerLookupBtn) headerLookupBtn.addEventListener('click', toggleLookup);

  async function performLookup() {
    if (!lookupInput) return;
    const q = lookupInput.value.trim();
    if (!q) {
      if (lookupMsg) {
        lookupMsg.className = "text-xs p-3 rounded-xl border bg-amber-950/60 border-amber-800 text-amber-300 block";
        lookupMsg.innerText = "Please enter an incident code (e.g. INC-2026-0003) or phone number.";
      }
      return;
    }

    if (lookupSubmitBtn) {
      lookupSubmitBtn.disabled = true;
      lookupSubmitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Searching...`;
    }

    try {
      const res = await fetch(`/api/incidents/lookup?query=${encodeURIComponent(q)}`);
      const data = await res.json();

      if (res.ok && data.incident) {
        const foundCode = data.incident.incident_code;
        currentIncidentCode = foundCode;
        hasFitBounds = false;

        try {
          localStorage.setItem('lifeline_active_incident', JSON.stringify({ code: foundCode }));
        } catch (e) {}

        window.history.replaceState(null, '', `/track?id=${foundCode}`);
        if (lookupMsg) lookupMsg.classList.add('hidden');
        if (lookupContainer) lookupContainer.classList.add('hidden');

        const activeReportState = document.getElementById('activeReportState');
        const noReportState = document.getElementById('noReportState');
        if (activeReportState) activeReportState.classList.remove('hidden');
        if (noReportState) noReportState.classList.add('hidden');

        initTrackMap();
        fetchIncidentTracker();
        fetchAllIncidents();
      } else {
        if (lookupMsg) {
          lookupMsg.className = "text-xs p-3 rounded-xl border bg-red-950/60 border-red-800 text-red-300 block";
          lookupMsg.innerText = `No emergency report found for "${q}". Please check the incident code or phone number.`;
        }
      }
    } catch (err) {
      if (lookupMsg) {
        lookupMsg.className = "text-xs p-3 rounded-xl border bg-red-950/60 border-red-800 text-red-300 block";
        lookupMsg.innerText = "Lookup request failed. Check server connection.";
      }
    } finally {
      if (lookupSubmitBtn) {
        lookupSubmitBtn.disabled = false;
        lookupSubmitBtn.innerHTML = `<i class="fa-solid fa-search"></i> Find Report`;
      }
    }
  }

  if (lookupSubmitBtn) lookupSubmitBtn.addEventListener('click', performLookup);
  if (lookupInput) {
    lookupInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        performLookup();
      }
    });
  }
}

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371.0;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

async function fetchIncidentTracker() {
  if (!currentIncidentCode) return;

  try {
    const res = await fetch(`/api/incidents/${encodeURIComponent(currentIncidentCode)}`);
    if (!res.ok) {
      document.getElementById('etaTitle').innerText = "Incident Not Found";
      document.getElementById('etaSub').innerText = "Unable to locate tracking data for this code. Please verify.";
      return;
    }

    const data = await res.json();
    const inc = data.incident;
    const unit = data.assigned_unit;
    const disp = data.dispatch;
    const station = data.station;

    // Reporter Info Display
    const nameEl = document.getElementById('reporterNameDisplay');
    const phoneEl = document.getElementById('reporterPhoneDisplay');
    const catBadge = document.getElementById('categoryBadge');
    const timeEl = document.getElementById('reportedTimeDisplay');

    if (nameEl) nameEl.innerText = inc.reporter_name ? `Reported by ${inc.reporter_name}` : 'Disaster Distress Operation';
    if (phoneEl) phoneEl.innerText = inc.reporter_phone || 'Emergency Direct Line';
    if (catBadge) catBadge.innerText = inc.category || 'Disaster Alert';
    if (timeEl && inc.created_at) {
      const dt = new Date(inc.created_at);
      timeEl.innerText = isNaN(dt.getTime()) ? inc.created_at : dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    document.getElementById('lastUpdatedText').innerText = "Live tracking updated at " + new Date().toLocaleTimeString();
    document.getElementById('incidentDesc').innerText = inc.description || "No situation description provided.";
    document.getElementById('demandsText').innerText = inc.demands || (inc.needs ? `Services Needed: ${inc.needs}` : "Standard Disaster Emergency Relief");

    // Render Evidence Media
    renderEvidenceMedia(inc.image_url, inc.video_url);

    // Victim Disaster Coordinates
    const vLat = parseFloat(inc.latitude);
    const vLng = parseFloat(inc.longitude);

    if (trackMap && !isNaN(vLat) && !isNaN(vLng)) {
      if (!victimMarker) {
        const vIcon = L.divIcon({
          className: 'v-pin',
          html: `<div style="background-color:#ef4444; width:24px; height:24px; border-radius:50%; border:2px solid white; box-shadow:0 0 16px #ef4444; display:flex; align-items:center; justify-content:center; color:white; font-size:11px;"><i class="fa-solid fa-location-dot"></i></div>`,
          iconSize: [24, 24]
        });
        victimMarker = L.marker([vLat, vLng], { icon: vIcon }).addTo(trackMap).bindPopup(`<b>Disaster Location</b><br>${inc.category || 'Emergency'}`);
        trackMap.setView([vLat, vLng], 14);
      } else {
        victimMarker.setLatLng([vLat, vLng]);
      }
    }

    // Populate Nearest Emergency Station Origin Card
    const stationCard = document.getElementById('stationCard');
    if (station || (disp && disp.station_name)) {
      if (stationCard) stationCard.classList.remove('hidden');
      const stName = (station && station.name) || disp.station_name || "Emergency Response Base";
      const stCode = (station && station.station_code) || disp.station_code || "STATION-01";
      const stAddress = (station && station.address) || "Regional Emergency Logistics Hub";
      const stPhone = (station && station.contact_number) || "+91 120-2734101";
      const stType = (station && station.station_type) || "Disaster Response Depot";

      const nameEl = document.getElementById('stationNameDisplay');
      const codeEl = document.getElementById('stationCodeDisplay');
      const addrEl = document.getElementById('stationAddressDisplay');
      const phoneEl = document.getElementById('stationPhoneDisplay');
      const distEl = document.getElementById('stationDistDisplay');
      const vehTypeEl = document.getElementById('vehicleTypeDisplay');
      const transitEtaEl = document.getElementById('transitEtaDisplay');
      const iconEl = document.getElementById('stationIcon');

      if (nameEl) nameEl.innerText = stName;
      if (codeEl) codeEl.innerText = stCode;
      if (addrEl) addrEl.innerText = `${stType} • ${stAddress}`;
      if (phoneEl) {
        phoneEl.innerText = stPhone;
        phoneEl.href = `tel:${stPhone.replace(/[^0-9+]/g, '')}`;
      }

      let sDistKm = (disp && typeof disp.distance_km === 'number') ? disp.distance_km : 0;
      if (station && station.latitude && station.longitude && !isNaN(vLat) && !isNaN(vLng)) {
        sDistKm = haversine(station.latitude, station.longitude, vLat, vLng);
      }
      if (distEl) distEl.innerText = `${sDistKm.toFixed(2)} km from disaster site`;
      if (vehTypeEl) vehTypeEl.innerText = unit ? `${unit.type} (${unit.unit_code})` : (inc.assigned_unit_code || 'Dispatched Team');
      if (transitEtaEl) {
        const tTime = (disp && typeof disp.travel_time_minutes === 'number') ? disp.travel_time_minutes.toFixed(1) : ((sDistKm / 40.0) * 60.0).toFixed(1);
        transitEtaEl.innerText = `${tTime} mins fastest arrival`;
      }

      if (iconEl) {
        if (/fire/i.test(stType)) iconEl.className = 'fa-solid fa-fire-flame-curved text-amber-400';
        else if (/water|boat|flood/i.test(stType)) iconEl.className = 'fa-solid fa-sailboat text-blue-400';
        else if (/trauma|medical|hospital/i.test(stType)) iconEl.className = 'fa-solid fa-hospital text-emerald-400';
        else if (/ndrf|search|collapse/i.test(stType)) iconEl.className = 'fa-solid fa-person-digging text-purple-400';
        else iconEl.className = 'fa-solid fa-building-shield text-indigo-400';
      }

      // Render Station Marker on Leaflet Map
      if (trackMap && station && station.latitude && station.longitude) {
        const sLat = parseFloat(station.latitude);
        const sLng = parseFloat(station.longitude);
        if (!isNaN(sLat) && !isNaN(sLng)) {
          if (!stationMarker) {
            const sIcon = L.divIcon({
              className: 's-pin',
              html: `<div style="background-color:#6366f1; width:30px; height:30px; border-radius:8px; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-size:13px; box-shadow:0 4px 14px rgba(99,102,241,0.7);"><i class="fa-solid fa-building-shield"></i></div>`,
              iconSize: [30, 30]
            });
            stationMarker = L.marker([sLat, sLng], { icon: sIcon }).addTo(trackMap).bindPopup(`<b>Nearest Station: ${stName}</b><br>${stType}`);
          } else {
            stationMarker.setLatLng([sLat, sLng]);
          }
        }
      }
    }

    // Populate On-Board Life-Saving Supplies Card
    const suppliesCard = document.getElementById('suppliesCard');
    const pillsContainer = document.getElementById('suppliesPillsContainer');
    const suppliesText = (disp && disp.supplies_dispatched) || (unit && unit.supplies_payload) || null;

    if (suppliesCard && pillsContainer) {
      if (suppliesText) {
        suppliesCard.classList.remove('hidden');
        const items = suppliesText.split(',').map(s => s.trim()).filter(Boolean);
        pillsContainer.innerHTML = items.map(item => {
          let icon = 'fa-solid fa-box-open text-amber-400';
          const lower = item.toLowerCase();
          if (/oxygen|ventilator|breathing/.test(lower)) icon = 'fa-solid fa-lungs text-cyan-400';
          else if (/defibrillator|aed|cardiac|heart/.test(lower)) icon = 'fa-solid fa-heart-pulse text-red-400';
          else if (/trauma|bandage|first aid|burn|dressing|splint/.test(lower)) icon = 'fa-solid fa-kit-medical text-rose-400';
          else if (/lifejacket|buoy|raft|boat|diving|pfd/.test(lower)) icon = 'fa-solid fa-life-ring text-amber-400';
          else if (/water|bottle|jerry can|filtration|purification/.test(lower)) icon = 'fa-solid fa-bottle-water text-sky-400';
          else if (/food|ration|meal/.test(lower)) icon = 'fa-solid fa-utensils text-emerald-400';
          else if (/foam|extinguisher|fire/.test(lower)) icon = 'fa-solid fa-fire-extinguisher text-amber-500';
          else if (/ladder|cutter|spreader|hydraulic/.test(lower)) icon = 'fa-solid fa-screwdriver-wrench text-orange-400';
          else if (/radar|sensor|sonar|acoustic/.test(lower)) icon = 'fa-solid fa-satellite-dish text-violet-400';
          else if (/blanket|tent|shelter/.test(lower)) icon = 'fa-solid fa-campground text-teal-400';
          else if (/stretcher/.test(lower)) icon = 'fa-solid fa-bed text-indigo-400';

          return `<span class="bg-slate-950 text-slate-200 border border-slate-800 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm">
            <i class="${icon}"></i> ${item}
          </span>`;
        }).join('');
      } else {
        suppliesCard.classList.add('hidden');
      }
    }

    // Update Assigned Rescue Unit & Trajectory
    if (unit || inc.assigned_unit_code) {
      const unitCode = unit ? unit.unit_code : inc.assigned_unit_code;
      const uLat = unit ? parseFloat(unit.latitude) : (vLat + 0.012);
      const uLng = unit ? parseFloat(unit.longitude) : (vLng + 0.012);
      const speed = unit ? parseFloat(unit.speed_kmh) : 35.0;
      const uType = unit ? unit.type : 'Emergency Rescue Vehicle';
      const originStation = (station && station.name) || (disp && disp.station_name) || 'Nearest Station';

      const distKm = (!isNaN(uLat) && !isNaN(vLat)) ? haversine(uLat, uLng, vLat, vLng) : 0;
      const timeMins = (disp && typeof disp.travel_time_minutes === 'number') ? disp.travel_time_minutes : ((distKm / Math.max(10.0, speed)) * 60.0);

      document.getElementById('etaTitle').innerText = `ETA: ${timeMins.toFixed(1)} Minutes`;
      document.getElementById('etaSub').innerText = `Dispatched from ${originStation}. Unit ${unitCode} (${uType}) is en route to location.`;
      document.getElementById('distDisplay').innerText = `${distKm.toFixed(2)} km`;
      document.getElementById('unitCodeDisplay').innerText = unitCode;

      if (trackMap && !isNaN(uLat) && !isNaN(uLng)) {
        if (!unitMarker) {
          const uIcon = L.divIcon({
            className: 'u-pin',
            html: `<div style="background-color:#3b82f6; width:28px; height:28px; border-radius:8px; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-size:13px; box-shadow:0 4px 14px rgba(59,130,246,0.6);"><i class="fa-solid fa-truck-fast"></i></div>`,
            iconSize: [28, 28]
          });
          unitMarker = L.marker([uLat, uLng], { icon: uIcon }).addTo(trackMap).bindPopup(`<b>Rescue Unit: ${unitCode}</b><br>${uType}`);
        } else {
          unitMarker.setLatLng([uLat, uLng]);
        }

        if (trajectoryLine) trackMap.removeLayer(trajectoryLine);

        // Path points: Station (if present) -> Unit -> Victim
        const pathPoints = [];
        if (station && station.latitude && station.longitude) {
          pathPoints.push([parseFloat(station.latitude), parseFloat(station.longitude)]);
        }
        pathPoints.push([uLat, uLng]);
        if (!isNaN(vLat) && !isNaN(vLng)) {
          pathPoints.push([vLat, vLng]);
        }

        trajectoryLine = L.polyline(pathPoints, {
          color: '#f59e0b',
          weight: 4,
          dashArray: '6, 8'
        }).addTo(trackMap);

        if (!hasFitBounds && pathPoints.length > 1) {
          trackMap.fitBounds(pathPoints, { padding: [40, 40] });
          hasFitBounds = true;
        }
      }

      // Update Stepper Progress
      const step3 = document.getElementById('step3');
      if (step3) {
        step3.className = "p-3 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 font-semibold flex flex-col items-center gap-1.5";
        step3.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 text-lg"></i><span>3. Rescue Team Sent</span>`;
      }

      if (distKm <= 0.1) {
        const step4 = document.getElementById('step4');
        if (step4) {
          step4.className = "p-3 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 font-semibold flex flex-col items-center gap-1.5";
          step4.innerHTML = `<i class="fa-solid fa-flag-checkered text-emerald-400 text-lg"></i><span>4. Rescue Team Arrived</span>`;
        }
      }

    } else {
      document.getElementById('etaTitle').innerText = "Dispatch Pending";
      document.getElementById('etaSub').innerText = "Your emergency alert has been prioritized and is queued for resource allocation.";
      document.getElementById('distDisplay').innerText = "Queued";
      document.getElementById('unitCodeDisplay').innerText = "Dispatch Pending";
    }

  } catch (err) {
    console.error("Tracking error:", err);
  }
}

function renderEvidenceMedia(imageUrl, videoUrl) {
  const box = document.getElementById('evidenceMediaBox');
  const grid = document.getElementById('evidenceGrid');
  if (!box || !grid) return;

  const images = (imageUrl || '').split(',').map(s => s.trim()).filter(Boolean);
  const videos = (videoUrl || '').split(',').map(s => s.trim()).filter(Boolean);

  if (images.length === 0 && videos.length === 0) {
    box.classList.add('hidden');
    return;
  }

  box.classList.remove('hidden');
  grid.innerHTML = '';

  images.forEach(imgSrc => {
    const card = document.createElement('div');
    card.className = "relative rounded-xl overflow-hidden bg-black border border-slate-800 h-40";
    card.innerHTML = `
      <img src="${imgSrc}" class="w-full h-full object-cover cursor-pointer hover:scale-105 transition" onclick="window.open('${imgSrc}', '_blank')">
      <span class="absolute top-2 left-2 bg-blue-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1">
        <i class="fa-solid fa-camera"></i> Photo
      </span>
    `;
    grid.appendChild(card);
  });

  videos.forEach(vidSrc => {
    const card = document.createElement('div');
    card.className = "relative rounded-xl overflow-hidden bg-black border border-slate-800 h-40";
    card.innerHTML = `
      <video src="${vidSrc}" controls class="w-full h-full object-cover"></video>
      <span class="absolute top-2 left-2 bg-red-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1">
        <i class="fa-solid fa-video"></i> Video
      </span>
    `;
    grid.appendChild(card);
  });
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  try {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = () => {
      fetchIncidentTracker();
      fetchAllIncidents();
    };
  } catch (e) {}
}
