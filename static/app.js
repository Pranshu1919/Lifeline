// LifeLine High-Accuracy Emergency Intake & Multiple Media Engine
let map, marker;
let selectedCategory = "Flood";
let selectedNeeds = ["Boat Evacuation"];
let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let attachedMedia = [];
let recInterval = null;
let recSeconds = 0;
let dbPromise = null;
let watchId = null;

// Register Service Worker for 100% Offline Access
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js').then((reg) => {
      console.log('[LifeLine PWA] Service Worker registered:', reg.scope);
    }).catch((err) => {
      console.warn('[LifeLine PWA] Service Worker registration failed:', err);
    });
  });
}

function initIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('lifeline_offline_db', 1);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offline_reports')) {
        db.createObjectStore('offline_reports', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = (event) => resolve(event.target.result);
    request.onerror = (event) => reject(event.target.error);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  dbPromise = initIndexedDB();
  initMap();
  initCategoryBtns();
  initNeedsChips();
  initCameraControls();
  initGpsControls();
  initNetworkStatus();
  initFormSubmit();
  checkActiveIncidentBanner();

  updateOfflineCount();
});

function initNetworkStatus() {
  const updateStatus = () => {
    const isOnline = navigator.onLine;
    const badge = document.getElementById('netStatusBadge');
    const text = document.getElementById('netStatusText');
    const notice = document.getElementById('offlineNotice');

    if (isOnline) {
      badge.className = "bg-emerald-950 text-emerald-300 text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1.5 border border-emerald-800/60";
      text.innerText = "ONLINE";
      notice.classList.add('hidden');
      syncOfflineReports();
    } else {
      badge.className = "bg-amber-950 text-amber-300 text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1.5 border border-amber-800/60";
      text.innerText = "OFFLINE (QUEUED)";
      notice.classList.remove('hidden');
    }
  };

  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  updateStatus();

  document.getElementById('syncNowBtn').addEventListener('click', () => {
    syncOfflineReports();
  });
}

function initMap() {
  const defaultLat = 28.6752;
  const defaultLng = 77.5020;

  map = L.map('map').setView([defaultLat, defaultLng], 13);
  
  // Official OpenStreetMap Tile Server - 100% Free Public Tiles, ZERO API Keys Required!
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  marker = L.marker([defaultLat, defaultLng], { draggable: true }).addTo(map);

  function updateCoords(lat, lng) {
    document.getElementById('latitude').value = lat.toFixed(6);
    document.getElementById('longitude').value = lng.toFixed(6);
    document.getElementById('latDisplay').innerText = lat.toFixed(6);
    document.getElementById('lngDisplay').innerText = lng.toFixed(6);
  }

  updateCoords(defaultLat, defaultLng);

  marker.on('dragend', () => {
    const latlng = marker.getLatLng();
    updateCoords(latlng.lat, latlng.lng);
  });

  map.on('click', (e) => {
    marker.setLatLng(e.latlng);
    updateCoords(e.latlng.lat, e.latlng.lng);
  });
}

function initCategoryBtns() {
  const catBtns = document.querySelectorAll('.cat-btn');
  catBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      catBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedCategory = btn.dataset.category;
    });
  });
}

function initNeedsChips() {
  const chips = document.querySelectorAll('.need-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('active');
      const need = chip.dataset.need;
      if (chip.classList.contains('active')) {
        if (!selectedNeeds.includes(need)) selectedNeeds.push(need);
      } else {
        selectedNeeds = selectedNeeds.filter(n => n !== need);
      }
    });
  });
}

function initGpsControls() {
  const useGpsBtn = document.getElementById('useGpsBtn');
  useGpsBtn.addEventListener('click', () => {
    if (navigator.geolocation) {
      document.getElementById('gpsStatus').innerText = "Locating Your GPS Position...";
      navigator.geolocation.getCurrentPosition((pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const acc = Math.round(pos.coords.accuracy);
        map.setView([lat, lng], 16);
        marker.setLatLng([lat, lng]);
        document.getElementById('latitude').value = lat.toFixed(6);
        document.getElementById('longitude').value = lng.toFixed(6);
        document.getElementById('latDisplay').innerText = lat.toFixed(6);
        document.getElementById('lngDisplay').innerText = lng.toFixed(6);
        document.getElementById('gpsStatus').innerText = `Location Identified (±${acc}m accuracy)`;
      }, (err) => {
        alert("GPS Error: " + err.message + "\nPlease enable Location/GPS permissions in browser.");
        document.getElementById('gpsStatus').innerText = "GPS Error";
      }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
    } else {
      alert("Geolocation is not supported by your browser.");
    }
  });

  document.getElementById('startLiveGpsBtn').addEventListener('click', () => {
    const btn = document.getElementById('startLiveGpsBtn');
    if (watchId === null) {
      if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition((pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          const acc = Math.round(pos.coords.accuracy);
          map.setView([lat, lng], 16);
          marker.setLatLng([lat, lng]);
          document.getElementById('latitude').value = lat.toFixed(6);
          document.getElementById('longitude').value = lng.toFixed(6);
          document.getElementById('latDisplay').innerText = lat.toFixed(6);
          document.getElementById('lngDisplay').innerText = lng.toFixed(6);
          document.getElementById('gpsStatus').innerText = `Continuous Tracking Active (±${acc}m accuracy)`;
        }, (err) => {
          alert("Continuous Tracking Error: " + err.message);
        }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });

        btn.classList.add('bg-emerald-600', 'text-white');
        btn.innerHTML = `<i class="fa-solid fa-satellite-dish animate-spin"></i> Continuous Tracking Active`;
      }
    } else {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
      btn.classList.remove('bg-emerald-600', 'text-white');
      btn.innerHTML = `<i class="fa-solid fa-satellite-dish text-red-500 animate-pulse"></i> Continuous GPS Tracking`;
      document.getElementById('gpsStatus').innerText = "Location Signal Ready";
    }
  });
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function renderMediaGallery() {
  const container = document.getElementById('mediaGalleryContainer');
  const grid = document.getElementById('attachedMediaGrid');
  const countSpan = document.getElementById('galleryCount');
  const summaryBadge = document.getElementById('mediaSummaryBadge');
  const summaryText = document.getElementById('mediaSummaryText');

  if (!attachedMedia || attachedMedia.length === 0) {
    if (container) container.classList.add('hidden');
    if (summaryBadge) summaryBadge.classList.add('hidden');
    return;
  }

  if (container) container.classList.remove('hidden');
  if (summaryBadge) summaryBadge.classList.remove('hidden');

  const photoCount = attachedMedia.filter(m => m.type === 'image').length;
  const videoCount = attachedMedia.filter(m => m.type === 'video').length;
  const totalCount = attachedMedia.length;

  if (countSpan) countSpan.innerText = totalCount;
  if (summaryText) {
    let parts = [];
    if (photoCount > 0) parts.push(`${photoCount} Photo${photoCount !== 1 ? 's' : ''}`);
    if (videoCount > 0) parts.push(`${videoCount} Video${videoCount !== 1 ? 's' : ''}`);
    summaryText.innerText = parts.join(' & ') + ' Attached';
  }

  if (grid) {
    grid.innerHTML = '';
    attachedMedia.forEach((item) => {
      const card = document.createElement('div');
      card.className = "relative bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex flex-col gap-2 shadow-md";

      let previewEl = '';
      if (item.type === 'image') {
        previewEl = `
          <div class="relative w-full h-32 rounded-lg overflow-hidden bg-black flex items-center justify-center">
            <img src="${item.previewUrl}" class="w-full h-full object-cover" alt="Captured Evidence">
            <span class="absolute top-2 left-2 bg-blue-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1 shadow">
              <i class="fa-solid fa-camera"></i> Photo
            </span>
          </div>`;
      } else {
        previewEl = `
          <div class="relative w-full h-32 rounded-lg overflow-hidden bg-black flex items-center justify-center">
            <video src="${item.previewUrl}" controls class="w-full h-full object-cover"></video>
            <span class="absolute top-2 left-2 bg-red-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1 shadow">
              <i class="fa-solid fa-video"></i> Video
            </span>
          </div>`;
      }

      card.innerHTML = `
        ${previewEl}
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span class="truncate max-w-[130px] font-mono text-slate-300" title="${item.name}">${item.name}</span>
          <span class="text-slate-500 font-mono">${item.sizeText}</span>
        </div>
        <button type="button" class="w-full text-[11px] font-semibold text-red-400 hover:text-red-300 bg-red-950/40 hover:bg-red-950/80 py-1.5 rounded-lg border border-red-900/60 transition flex items-center justify-center gap-1 cursor-pointer" data-remove-id="${item.id}">
          <i class="fa-solid fa-trash-can"></i> Remove
        </button>
      `;

      card.querySelector(`[data-remove-id="${item.id}"]`).addEventListener('click', () => {
        removeMediaItem(item.id);
      });

      grid.appendChild(card);
    });
  }
}

function removeMediaItem(id) {
  attachedMedia = attachedMedia.filter(m => m.id !== id);
  renderMediaGallery();
}

function initCameraControls() {
  const openCamBtn = document.getElementById('openCamBtn');
  const snapPhotoBtn = document.getElementById('snapPhotoBtn');
  const recordVideoBtn = document.getElementById('recordVideoBtn');
  const stopRecordBtn = document.getElementById('stopRecordBtn');
  const closeCamBtn = document.getElementById('closeCamBtn');
  const cameraVideo = document.getElementById('cameraVideo');
  const cameraPlaceholder = document.getElementById('cameraPlaceholder');
  const fileInput = document.getElementById('imageInput');
  const clearAllBtn = document.getElementById('clearAllMediaBtn');

  // Handle device file selections (photos and/or videos)
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
          const f = fileInput.files[i];
          const isVideo = f.type.startsWith('video/') || ['.webm', '.mp4', '.avi', '.mov', '.mkv', '.3gp'].some(ext => f.name.toLowerCase().endsWith(ext));
          attachedMedia.push({
            id: 'media_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
            file: f,
            type: isVideo ? 'video' : 'image',
            name: f.name,
            previewUrl: URL.createObjectURL(f),
            sizeText: formatBytes(f.size)
          });
        }
        renderMediaGallery();
        fileInput.value = '';
      }
    });
  }

  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', () => {
      attachedMedia = [];
      renderMediaGallery();
    });
  }

  // Open Camera
  openCamBtn.addEventListener('click', async () => {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: true });
      cameraVideo.srcObject = mediaStream;
      cameraVideo.classList.remove('hidden');
      cameraPlaceholder.classList.add('hidden');
      snapPhotoBtn.classList.remove('hidden');
      recordVideoBtn.classList.remove('hidden');
      if (closeCamBtn) closeCamBtn.classList.remove('hidden');
      openCamBtn.classList.add('hidden');
    } catch (err) {
      alert("Camera access error: " + err.message + "\nYou can still upload scene photos and videos using the file selector below.");
    }
  });

  // Close Camera
  if (closeCamBtn) {
    closeCamBtn.addEventListener('click', () => {
      if (mediaStream) {
        mediaStream.getTracks().forEach(t => t.stop());
        mediaStream = null;
      }
      cameraVideo.classList.add('hidden');
      cameraPlaceholder.classList.remove('hidden');
      snapPhotoBtn.classList.add('hidden');
      recordVideoBtn.classList.add('hidden');
      stopRecordBtn.classList.add('hidden');
      closeCamBtn.classList.add('hidden');
      openCamBtn.classList.remove('hidden');
    });
  }

  // Capture Live Photo (Keeps camera active for more photos/videos)
  snapPhotoBtn.addEventListener('click', () => {
    const canvas = document.getElementById('photoCanvas');
    canvas.width = cameraVideo.videoWidth || 640;
    canvas.height = cameraVideo.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);

    // Visual flash feedback
    const flash = document.getElementById('camFlash');
    if (flash) {
      flash.classList.remove('opacity-0');
      flash.classList.add('opacity-80');
      setTimeout(() => {
        flash.classList.remove('opacity-80');
        flash.classList.add('opacity-0');
      }, 120);
    }

    canvas.toBlob((blob) => {
      const fileName = `live_photo_${Date.now()}.jpg`;
      const file = new File([blob], fileName, { type: 'image/jpeg' });
      attachedMedia.push({
        id: 'media_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
        file: file,
        type: 'image',
        name: fileName,
        previewUrl: URL.createObjectURL(blob),
        sizeText: formatBytes(blob.size)
      });
      renderMediaGallery();
    }, 'image/jpeg', 0.9);
  });

  // Record Live Video
  recordVideoBtn.addEventListener('click', () => {
    recordedChunks = [];
    try {
      mediaRecorder = new MediaRecorder(mediaStream);
    } catch (e) {
      alert("MediaRecorder is not supported on this browser.");
      return;
    }

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' });
      const fileName = `live_video_${Date.now()}.webm`;
      const file = new File([blob], fileName, { type: 'video/webm' });
      attachedMedia.push({
        id: 'media_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
        file: file,
        type: 'video',
        name: fileName,
        previewUrl: URL.createObjectURL(blob),
        sizeText: formatBytes(blob.size)
      });
      renderMediaGallery();
      clearInterval(recInterval);
      document.getElementById('recBadge').classList.add('hidden');
    };

    mediaRecorder.start();
    recordVideoBtn.classList.add('hidden');
    stopRecordBtn.classList.remove('hidden');
    document.getElementById('recBadge').classList.remove('hidden');

    recSeconds = 0;
    recInterval = setInterval(() => {
      recSeconds++;
      const mins = String(Math.floor(recSeconds / 60)).padStart(2, '0');
      const secs = String(recSeconds % 60).padStart(2, '0');
      document.getElementById('recTimer').innerText = `${mins}:${secs}`;
    }, 1000);
  });

  stopRecordBtn.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    stopRecordBtn.classList.add('hidden');
    recordVideoBtn.classList.remove('hidden');
  });
}

function checkActiveIncidentBanner() {
  const banner = document.getElementById('activeIncidentAlertBanner');
  const codeSpan = document.getElementById('bannerIncidentCode');
  const trackBtn = document.getElementById('bannerTrackBtn');

  const saved = localStorage.getItem('lifeline_active_incident');
  if (saved && banner) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed && parsed.code) {
        banner.classList.remove('hidden');
        if (codeSpan) codeSpan.innerText = parsed.code;
        if (trackBtn) trackBtn.href = `/track?id=${parsed.code}`;

        // Also update navbar track links
        document.querySelectorAll('a[href="/track"]').forEach(a => {
          a.href = `/track?id=${parsed.code}`;
          a.innerHTML = `<i class="fa-solid fa-location-crosshairs text-amber-400 animate-pulse"></i> Track My Rescue (${parsed.code})`;
        });
      }
    } catch (e) {}
  }
}

function initFormSubmit() {
  const form = document.getElementById('incidentForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;

    // Contact Details & Description Strict Validation
    const nameInput = document.getElementById('reporter_name');
    const phoneInput = document.getElementById('reporter_phone');
    const descInput = document.getElementById('description');

    const name = (nameInput ? nameInput.value : '').trim();
    const phone = (phoneInput ? phoneInput.value : '').trim();
    const desc = (descInput ? descInput.value : '').trim();

    if (!name) {
      alert("⚠️ Your Full Name is required so rescue teams can identify and coordinate with you.");
      if (nameInput) nameInput.focus();
      submitBtn.disabled = false;
      return;
    }

    if (!phone || phone.length < 7) {
      alert("⚠️ A valid Contact Phone Number is required so emergency dispatchers can communicate with you directly.");
      if (phoneInput) phoneInput.focus();
      submitBtn.disabled = false;
      return;
    }

    if (!desc) {
      alert("⚠️ Please provide a brief situation description of the emergency.");
      if (descInput) descInput.focus();
      submitBtn.disabled = false;
      return;
    }

    const attachedFiles = attachedMedia.map(m => m.file);

    const reportData = {
      reporter_name: name,
      reporter_phone: phone,
      description: desc,
      demands: document.getElementById('demands')?.value || "",
      category: selectedCategory,
      needs: selectedNeeds.join(", "),
      latitude: document.getElementById('latitude').value,
      longitude: document.getElementById('longitude').value,
      timestamp: new Date().toISOString(),
      files: attachedFiles
    };

    if (!navigator.onLine) {
      await saveReportOffline(reportData);
      showOfflineModal();
      form.reset();
      attachedMedia = [];
      renderMediaGallery();
      submitBtn.disabled = false;
      return;
    }

    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting Emergency Alert...`;
    const formData = new FormData();
    formData.append("reporter_name", reportData.reporter_name);
    formData.append("reporter_phone", reportData.reporter_phone);
    formData.append("description", reportData.description);
    formData.append("demands", reportData.demands);
    formData.append("category", reportData.category);
    formData.append("needs", reportData.needs);
    formData.append("latitude", reportData.latitude);
    formData.append("longitude", reportData.longitude);

    attachedFiles.forEach(f => formData.append("files", f));

    try {
      const response = await fetch('/api/incidents/report', {
        method: 'POST',
        body: formData
      });
      const res = await response.json();
      if (response.ok && res.status === 'success') {
        showOnlineModal(res, reportData);
        form.reset();
        attachedMedia = [];
        renderMediaGallery();
        if (mediaStream) {
          mediaStream.getTracks().forEach(t => t.stop());
          mediaStream = null;
        }
      } else if (res.status === 'rejected_fake' || res.is_fake) {
        // AI Authenticity Filter Flagged Report as Fake/Prank!
        showFakeWarningModal(res);
      } else {
        alert(res.message || "Failed to submit report. Saving locally for offline retry.");
        await saveReportOffline(reportData);
        showOfflineModal();
      }
    } catch (err) {
      await saveReportOffline(reportData);
      showOfflineModal();
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane text-lg"></i> SUBMIT EMERGENCY ALERT`;
    }
  });
}

async function saveReportOffline(reportData) {
  const db = await dbPromise;
  return new Promise((resolve, reject) => {
    const tx = db.transaction('offline_reports', 'readwrite');
    const store = tx.objectStore('offline_reports');
    const req = store.add(reportData);
    req.onsuccess = () => {
      updateOfflineCount();
      resolve();
    };
    req.onerror = () => reject(req.error);
  });
}

async function updateOfflineCount() {
  const db = await dbPromise;
  const tx = db.transaction('offline_reports', 'readonly');
  const store = tx.objectStore('offline_reports');
  const req = store.count();
  req.onsuccess = () => {
    const count = req.result;
    const btn = document.getElementById('syncNowBtn');
    const countSpan = document.getElementById('offlineCount');
    countSpan.innerText = count;
    if (count > 0 && navigator.onLine) {
      btn.classList.remove('hidden');
    } else {
      btn.classList.add('hidden');
    }
  };
}

async function syncOfflineReports() {
  if (!navigator.onLine) return;
  const db = await dbPromise;
  const tx = db.transaction('offline_reports', 'readwrite');
  const store = tx.objectStore('offline_reports');
  const req = store.getAll();

  req.onsuccess = async () => {
    const reports = req.result;
    if (!reports || reports.length === 0) return;

    for (let r of reports) {
      const formData = new FormData();
      formData.append("reporter_name", r.reporter_name);
      formData.append("reporter_phone", r.reporter_phone);
      formData.append("description", r.description);
      formData.append("demands", r.demands || "");
      formData.append("category", r.category);
      formData.append("needs", r.needs);
      formData.append("latitude", r.latitude);
      formData.append("longitude", r.longitude);
      if (r.files && r.files.length > 0) {
        r.files.forEach(f => formData.append("files", f));
      }

      try {
        const response = await fetch('/api/incidents/report', {
          method: 'POST',
          body: formData
        });
        if (response.ok) {
          const deleteTx = db.transaction('offline_reports', 'readwrite');
          deleteTx.objectStore('offline_reports').delete(r.id);
        }
      } catch (err) {}
    }
    updateOfflineCount();
  };
}

function showOnlineModal(res, reportData) {
  const code = res.incident_code || res.incident_id || "INC-2026-0001";

  // Persist THIS individual citizen's reported incident in localStorage
  const myIncident = {
    code: code,
    category: res.category || selectedCategory,
    reporter_name: (reportData ? reportData.reporter_name : '') || '',
    reporter_phone: (reportData ? reportData.reporter_phone : '') || '',
    description: (reportData ? reportData.description : '') || '',
    timestamp: new Date().toISOString()
  };
  localStorage.setItem('lifeline_active_incident', JSON.stringify(myIncident));

  let myReports = [];
  try {
    myReports = JSON.parse(localStorage.getItem('lifeline_my_reports') || '[]');
  } catch (e) {}
  myReports = myReports.filter(r => r.code !== code);
  myReports.unshift(myIncident);
  localStorage.setItem('lifeline_my_reports', JSON.stringify(myReports));

  if (res.is_dispatched) {
    document.getElementById('modalTitle').innerHTML = `<i class="fa-solid fa-truck-fast text-emerald-400"></i> Rescue Team Dispatched!`;
    document.getElementById('modalSub').innerText = `Nearest station "${res.station_name}" (${res.distance_km} km away) has immediately dispatched ${res.unit_type || res.assigned_unit}. ETA: ${res.travel_time_minutes} mins.`;
    document.getElementById('modalDetails').innerHTML = `
      <div><strong>Incident Code:</strong> ${code}</div>
      <div><strong>Nearest Emergency Station:</strong> <span class="text-emerald-400 font-bold">${res.station_name}</span> (${res.distance_km} km)</div>
      <div><strong>Dispatched Vehicle:</strong> <span class="text-indigo-300 font-bold">${res.assigned_unit} (${res.unit_type})</span></div>
      <div><strong>Fastest Estimated Arrival:</strong> <span class="text-amber-300 font-bold">${res.travel_time_minutes} Minutes</span></div>
      <div><strong>On-Board Supplies:</strong> <span class="text-slate-300 text-xs">${res.supplies_dispatched || 'Emergency Life-Saving Supplies'}</span></div>
      <div><strong>Reporter:</strong> ${myIncident.reporter_name} (${myIncident.reporter_phone})</div>
    `;
  } else {
    document.getElementById('modalTitle').innerText = "Emergency Alert Sent";
    document.getElementById('modalSub').innerText = "Incident code " + code + ". Opening your personal live rescue tracking dashboard...";
    document.getElementById('modalDetails').innerHTML = `
      <div><strong>Incident Code:</strong> ${code}</div>
      <div><strong>Reporter:</strong> ${myIncident.reporter_name} (${myIncident.reporter_phone})</div>
      <div><strong>Category:</strong> ${res.category}</div>
      <div><strong>Needs:</strong> ${selectedNeeds.join(", ")}</div>
      <div><strong>AI Urgency Rating:</strong> Level ${res.severity_level || 4.5} / 5</div>
    `;
  }

  document.getElementById('trackBtnModal').onclick = () => {
    window.location.href = `/track?id=${code}`;
  };

  document.getElementById('resultModal').classList.remove('hidden');

  setTimeout(() => {
    window.location.href = `/track?id=${code}`;
  }, 2200);
}

function showOfflineModal() {
  document.getElementById('modalTitle').innerText = "Saved Offline";
  document.getElementById('modalSub').innerText = "Stored safely on your phone. Will upload automatically when network returns.";
  document.getElementById('modalDetails').innerHTML = `
    <div><strong>Status:</strong> QUEUED LOCALLY</div>
    <div><strong>Category:</strong> ${selectedCategory}</div>
    <div><strong>Needs:</strong> ${selectedNeeds.join(", ")}</div>
  `;

  document.getElementById('trackBtnModal').onclick = () => {
    window.location.href = `/track`;
  };

  document.getElementById('resultModal').classList.remove('hidden');
}

function showFakeWarningModal(res) {
  const modal = document.getElementById('fakeWarningModal');
  const reasonText = document.getElementById('fakeReasonText');
  const closeBtn = document.getElementById('closeFakeModalBtn');
  const editBtn = document.getElementById('editReportBtn');

  if (reasonText) {
    reasonText.innerText = res.fake_reason || res.message || "Detected non-disaster, test, or prank keywords.";
  }

  if (modal) modal.classList.remove('hidden');

  if (closeBtn) {
    closeBtn.onclick = () => {
      if (modal) modal.classList.add('hidden');
    };
  }

  if (editBtn) {
    editBtn.onclick = () => {
      if (modal) modal.classList.add('hidden');
      const desc = document.getElementById('description');
      if (desc) {
        desc.focus();
        desc.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };
  }
}

function closeModal() {
  document.getElementById('resultModal').classList.add('hidden');
}
