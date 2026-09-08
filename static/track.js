// Citizen Live Rescue & Relief Tracker JS Engine
let trackMap;
let victimMarker = null;
let unitMarker = null;
let trajectoryLine = null;
let currentIncidentCode = "INC-2026-0001";

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const codeParam = urlParams.get('id');
  if (codeParam) {
    currentIncidentCode = codeParam;
  }

  document.getElementById('incidentCodeDisplay').innerText = currentIncidentCode;

  initTrackMap();
  fetchIncidentTracker();
  connectWebSocket();

  // Fast Polling Fallback (Every 2 Seconds)
  setInterval(fetchIncidentTracker, 2000);
});

function initTrackMap() {
  trackMap = L.map('trackMap').setView([28.6752, 77.5020], 13);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(trackMap);
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
  try {
    const res = await fetch(`/api/incidents/${currentIncidentCode}`);
    if (!res.ok) {
      document.getElementById('etaTitle').innerText = "Incident Code Not Found";
      document.getElementById('etaSub').innerText = "Please verify your incident tracking code.";
      return;
    }

    const data = await res.json();
    const inc = data.incident;
    const unit = data.assigned_unit;

    document.getElementById('lastUpdatedText').innerText = "Updated at " + new Date().toLocaleTimeString();
    document.getElementById('incidentDesc').innerText = inc.description || "No situation description provided.";
    document.getElementById('demandsText').innerText = inc.demands || (inc.needs ? `Services Needed: ${inc.needs}` : "Standard Disaster Emergency Relief");

    // Update Victim Marker
    const vLat = inc.latitude;
    const vLng = inc.longitude;

    if (!victimMarker) {
      const vIcon = L.divIcon({
        className: 'v-pin',
        html: `<div style="background-color:#ef4444; width:22px; height:22px; border-radius:50%; border:2px solid white; box-shadow:0 0 12px #ef4444;"></div>`,
        iconSize: [22, 22]
      });
      victimMarker = L.marker([vLat, vLng], { icon: vIcon }).addTo(trackMap).bindPopup("Your Reported Location");
      trackMap.setView([vLat, vLng], 14);
    } else {
      victimMarker.setLatLng([vLat, vLng]);
    }

    // Update Assigned Unit & Trajectory
    if (unit || inc.assigned_unit_code) {
      const unitCode = unit ? unit.unit_code : inc.assigned_unit_code;
      const uLat = unit ? unit.latitude : (vLat + 0.015);
      const uLng = unit ? unit.longitude : (vLng + 0.015);
      const speed = unit ? unit.speed_kmh : 30.0;
      const uType = unit ? unit.type : 'Emergency Vehicle';

      const distKm = haversine(uLat, uLng, vLat, vLng);
      const timeMins = (distKm / speed) * 60.0;

      document.getElementById('etaTitle').innerText = `ETA: ${timeMins.toFixed(1)} Minutes`;
      document.getElementById('etaSub').innerText = `Assigned Unit ${unitCode} (${uType}) is traveling to your location.`;
      document.getElementById('distDisplay').innerText = `${distKm.toFixed(1)} km`;
      document.getElementById('unitCodeDisplay').innerText = unitCode;

      if (!unitMarker) {
        const uIcon = L.divIcon({
          className: 'u-pin',
          html: `<div style="background-color:#3b82f6; width:26px; height:26px; border-radius:6px; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-size:12px; box-shadow:0 4px 12px rgba(0,0,0,0.4);"><i class="fa-solid fa-truck-medical"></i></div>`,
          iconSize: [26, 26]
        });
        unitMarker = L.marker([uLat, uLng], { icon: uIcon }).addTo(trackMap).bindPopup(`Rescue Unit: ${unitCode}`);
      } else {
        unitMarker.setLatLng([uLat, uLng]);
      }

      if (trajectoryLine) trackMap.removeLayer(trajectoryLine);
      trajectoryLine = L.polyline([[uLat, uLng], [vLat, vLng]], {
        color: '#f59e0b',
        weight: 4,
        dashArray: '6, 8'
      }).addTo(trackMap);

      // Update Stepper Progress
      const step3 = document.getElementById('step3');
      if (step3) {
        step3.className = "p-3 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 font-semibold flex flex-col items-center gap-1.5";
        step3.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 text-lg"></i><span>3. Rescue Team Sent</span>`;
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

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  try {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = () => {
      fetchIncidentTracker();
    };
  } catch (e) {}
}
