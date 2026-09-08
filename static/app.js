// LifeLine High-Accuracy Emergency Intake & Multiple Media Engine
let map, marker;
let selectedCategory = "Flood";
let selectedNeeds = ["Boat Evacuation"];
let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let capturedBlob = null;
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

function initCameraControls() {
  const openCamBtn = document.getElementById('openCamBtn');
  const snapPhotoBtn = document.getElementById('snapPhotoBtn');
  const recordVideoBtn = document.getElementById('recordVideoBtn');
  const stopRecordBtn = document.getElementById('stopRecordBtn');
  const cameraVideo = document.getElementById('cameraVideo');
  const cameraPlaceholder = document.getElementById('cameraPlaceholder');

  openCamBtn.addEventListener('click', async () => {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      cameraVideo.srcObject = mediaStream;
      cameraVideo.classList.remove('hidden');
      cameraPlaceholder.classList.add('hidden');
      snapPhotoBtn.classList.remove('hidden');
      recordVideoBtn.classList.remove('hidden');
      openCamBtn.classList.add('hidden');
    } catch (err) {
      alert("Camera access error: " + err.message + "\nYou can use file upload below.");
    }
  });

  // Take Photo
  snapPhotoBtn.addEventListener('click', () => {
    const canvas = document.getElementById('photoCanvas');
    canvas.width = cameraVideo.videoWidth || 640;
    canvas.height = cameraVideo.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      capturedBlob = new File([blob], `live_photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
      showCapturedPreview(URL.createObjectURL(blob), 'image');
    }, 'image/jpeg', 0.9);
  });

  // Record Video
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
      capturedBlob = new File([blob], `live_video_${Date.now()}.webm`, { type: 'video/webm' });
      showCapturedPreview(URL.createObjectURL(blob), 'video');
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

  document.getElementById('clearMediaBtn').addEventListener('click', () => {
    capturedBlob = null;
    document.getElementById('capturedPreview').classList.add('hidden');
  });
}

function showCapturedPreview(url, type) {
  const container = document.getElementById('capturedPreview');
  const img = document.getElementById('capturedImg');
  const vid = document.getElementById('capturedVid');
  const title = document.getElementById('mediaTitle');

  container.classList.remove('hidden');
  if (type === 'image') {
    img.src = url;
    img.classList.remove('hidden');
    vid.classList.add('hidden');
    title.innerText = "Live Photo Captured";
  } else {
    vid.src = url;
    vid.classList.remove('hidden');
    img.classList.add('hidden');
    title.innerText = "Live Video Recorded";
  }
}

function initFormSubmit() {
  const form = document.getElementById('incidentForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;

    const fileInput = document.getElementById('imageInput');
    const attachedFiles = [];

    if (capturedBlob) attachedFiles.push(capturedBlob);
    if (fileInput.files && fileInput.files.length > 0) {
      for (let i = 0; i < fileInput.files.length; i++) {
        attachedFiles.push(fileInput.files[i]);
      }
    }

    const reportData = {
      reporter_name: document.getElementById('reporter_name')?.value || "Anonymous",
      reporter_phone: document.getElementById('reporter_phone')?.value || "",
      description: document.getElementById('description').value,
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
      capturedBlob = null;
      document.getElementById('capturedPreview').classList.add('hidden');
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
      if (response.ok) {
        showOnlineModal(res);
        form.reset();
        capturedBlob = null;
        document.getElementById('capturedPreview').classList.add('hidden');
      } else {
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

function showOnlineModal(res) {
  const code = res.incident_code || res.incident_id || "INC-2026-0001";
  document.getElementById('modalTitle').innerText = "Emergency Alert Sent";
  document.getElementById('modalSub').innerText = "Incident code " + code + ". Opening live rescue tracking dashboard...";
  document.getElementById('modalDetails').innerHTML = `
    <div><strong>Incident Code:</strong> ${code}</div>
    <div><strong>Category:</strong> ${res.category}</div>
    <div><strong>Needs:</strong> ${selectedNeeds.join(", ")}</div>
    <div><strong>AI Urgency Rating:</strong> Level ${res.severity_level || 4.5} / 5</div>
  `;

  document.getElementById('trackBtnModal').onclick = () => {
    window.location.href = `/track?id=${code}`;
  };

  document.getElementById('resultModal').classList.remove('hidden');

  setTimeout(() => {
    window.location.href = `/track?id=${code}`;
  }, 1500);
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

function closeModal() {
  document.getElementById('resultModal').classList.add('hidden');
}
