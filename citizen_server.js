const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const http = require('http');
const WebSocket = require('ws');
const multer = require('multer');
const sqlite3 = require('sqlite3').verbose();
const httpNative = require('http');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = 8000;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Directories
const STATIC_DIR = path.join(__dirname, 'static');
const UPLOADS_DIR = path.join(__dirname, 'uploads');
const DB_PATH = path.join(__dirname, 'lifeline_enterprise.db');

if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

app.use('/static', express.static(STATIC_DIR));
app.use('/uploads', express.static(UPLOADS_DIR));

// Configure Multer for Multiple File Uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});
const upload = multer({ storage: storage });

// Shared Database Connection with WAL Mode
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) console.error('Database connection error:', err);
  else {
    console.log('🟢 Citizen Server connected to SQLite DB:', DB_PATH);
    db.run('PRAGMA journal_mode = WAL;');
    db.run('PRAGMA busy_timeout = 5000;');
  }
});

function callMLMicroservice(endpoint, payload) {
  return new Promise((resolve) => {
    const dataString = JSON.stringify(payload);
    const options = {
      hostname: '127.0.0.1',
      port: 5000,
      path: endpoint,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(dataString)
      }
    };

    const req = httpNative.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); } catch (e) { resolve(null); }
      });
    });

    req.on('error', () => resolve(null));
    req.write(dataString);
    req.end();
  });
}

function notifyAdminServer() {
  const req = httpNative.request({
    hostname: '127.0.0.1',
    port: 8001,
    path: '/api/internal/notify-update',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, () => {});
  req.on('error', () => {});
  req.write(JSON.stringify({ event: 'REFRESH' }));
  req.end();
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

// Proximity-First Nearest-Station & Capability-Matching Dispatch Engine
function findBestStationUnit(incident, availableUnits) {
  let bestUnit = null;
  let minEffTime = Infinity;
  let bestDist = 0;
  let bestTime = 0;

  for (const u of availableUnits) {
    const distKm = haversine(u.latitude, u.longitude, incident.latitude, incident.longitude);
    const speed = u.speed_kmh || 35.0;
    const timeMins = (distKm / speed) * 60.0;

    let capScore = 1.0;
    const textCorpus = `${incident.category || ''} ${incident.description || ''} ${incident.demands || ''} ${incident.needs || ''}`.toLowerCase();
    const capCorpus = `${u.capabilities || ''} ${u.type || ''}`.toLowerCase();

    if (/flood|water|drown|submerged|river|overflow|boat/.test(textCorpus) && /boat|flood|water|evacuation/.test(capCorpus)) capScore += 5.0;
    if (/fire|flame|smoke|burn|explosion|blaze/.test(textCorpus) && /fire|foam|tender|engine|extinguisher/.test(capCorpus)) capScore += 5.0;
    if (/medical|injured|casualty|bleeding|heart|oxygen|doctor|hospital|ambulance|wound|trauma/.test(textCorpus) && /ambulance|medic|trauma|als|oxygen|paramedic/.test(capCorpus)) capScore += 5.0;
    if (/earthquake|collapse|debris|rubble|trapped|building|structure/.test(textCorpus) && /ndrf|search|extrication|cutter|radar/.test(capCorpus)) capScore += 5.0;
    if (/food|water|ration|starv|hunger|blanket|shelter|relief/.test(textCorpus) && /relief|truck|supplies|food|purification/.test(capCorpus)) capScore += 5.0;

    const effTime = timeMins / capScore;
    if (effTime < minEffTime) {
      minEffTime = effTime;
      bestUnit = u;
      bestDist = distKm;
      bestTime = timeMins;
    }
  }
  return { bestUnit, bestDist, bestTime };
}

function broadcastWS(data) {
  const msg = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(msg);
    }
  });
}

// Internal Notification Endpoint from Admin Server (Port 8001)
app.post('/api/internal/notify-update', (req, res) => {
  broadcastWS({ event: 'REFRESH_DISPATCH' });
  res.json({ ok: true });
});

// Routes for Citizen Public Portal (Port 8000)
app.get('/', (req, res) => res.sendFile(path.join(STATIC_DIR, 'index.html')));
app.get('/track', (req, res) => res.sendFile(path.join(STATIC_DIR, 'track.html')));

// Citizen Emergency Reporting API Endpoint
app.post('/api/incidents/report', upload.array('files', 20), async (req, res) => {
  try {
    const { reporter_name, reporter_phone, description, demands, category, needs, latitude, longitude } = req.body;
    const trimmedName = (reporter_name || '').trim();
    const trimmedPhone = (reporter_phone || '').trim();

    if (!trimmedName || !trimmedPhone) {
      return res.status(400).json({
        status: 'error',
        message: 'Contact details (Full Name and Phone Number) are required to report an emergency.'
      });
    }

    const lat = parseFloat(latitude) || 28.6752;
    const lng = parseFloat(longitude) || 77.5020;
    
    let imagePaths = [];
    let videoPaths = [];

    if (req.files && req.files.length > 0) {
      req.files.forEach(f => {
        const ext = path.extname(f.originalname).toLowerCase();
        const url = `/uploads/${f.filename}`;
        if (['.webm', '.mp4', '.avi', '.mov', '.mkv', '.3gp', '.ogg'].includes(ext)) {
          videoPaths.push(url);
        } else {
          imagePaths.push(url);
        }
      });
    }

    const imageUrl = imagePaths.length > 0 ? imagePaths.join(',') : null;
    const videoUrl = videoPaths.length > 0 ? videoPaths.join(',') : null;

    let firstImgPath = null;
    if (req.files && req.files.length > 0 && imagePaths.length > 0) {
      firstImgPath = req.files.find(f => !['.webm', '.mp4', '.avi', '.mov', '.mkv', '.3gp', '.ogg'].includes(path.extname(f.originalname).toLowerCase()))?.path;
    }

    // Multi-Modal AI Gatekeeper: Validate Authenticity (Fake / Prank vs Genuine Disaster)
    let verifyRes = await callMLMicroservice('/predict/verify', {
      text: description,
      image_path: firstImgPath || null,
      category: category,
      needs: needs
    });

    // If ML model flags report as fake, prank, or non-disaster bullshit: BLOCK IT!
    if (verifyRes && verifyRes.is_fake) {
      console.warn(`🚨 [AI Gatekeeper BLOCKED] Fake report from "${trimmedName}" (${trimmedPhone}): ${verifyRes.fake_reason}`);
      return res.status(403).json({
        status: 'rejected_fake',
        is_fake: true,
        title: 'Emergency Alert Flagged as Fake / Prank',
        fake_reason: verifyRes.fake_reason || 'Identified as a false alarm or non-disaster submission.',
        warning_message: verifyRes.warning_message || 'PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. False emergency calls waste critical life-saving rescue vehicles, jeopardize real victims\' lives, and are subject to legal penalties under the Disaster Management Act.',
        message: 'Report rejected by LifeLine Multi-Modal AI Authenticity Gatekeeper.'
      });
    }

    let inferredCat = (verifyRes && verifyRes.category && verifyRes.category !== 'General Disaster Alert') ? verifyRes.category : (category || 'General Disaster Alert');
    let textSev = verifyRes ? verifyRes.text_severity : 3.5;
    let visualSev = verifyRes ? verifyRes.visual_severity : 0.0;
    let compositeSev = verifyRes ? verifyRes.composite_severity : 3.5;

    db.all(`SELECT * FROM incidents WHERE status != 'RESOLVED'`, [], async (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });

      let isDuplicate = false;
      let matchedCode = null;

      for (let inc of rows) {
        const distKm = haversine(lat, lng, inc.latitude, inc.longitude);
        if (distKm <= 0.100) {
          isDuplicate = true;
          matchedCode = inc.incident_code;
          const newCount = inc.confirmations_count + 1;
          const newSev = Math.min(5.0, inc.composite_severity + 0.3);
          const combinedImgs = [inc.image_url, imageUrl].filter(Boolean).join(',');
          const combinedVids = [inc.video_url, videoUrl].filter(Boolean).join(',');
          db.run(
            `UPDATE incidents SET confirmations_count = ?, composite_severity = ?, image_url = ?, video_url = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_code = ?`,
            [newCount, newSev, combinedImgs || null, combinedVids || null, matchedCode]
          );
          break;
        }
      }

      if (isDuplicate) {
        broadcastWS({ event: 'INCIDENT_UPDATED', incident_code: matchedCode });
        notifyAdminServer();
        return res.json({
          status: 'success',
          incident_code: matchedCode,
          category: inferredCat,
          composite_severity: 5.0,
          is_duplicate: true,
          message: 'Report merged with existing nearby disaster incident.'
        });
      }

      db.get(`SELECT COUNT(*) as cnt FROM incidents`, [], (err, countRow) => {
        const count = (countRow ? countRow.cnt : 0) + 1;
        const incCode = `INC-2026-${String(count).padStart(4, '0')}`;

        db.run(
          `INSERT INTO incidents (incident_code, reporter_name, reporter_phone, description, demands, category, needs, text_severity, visual_severity, composite_severity, latitude, longitude, image_url, video_url, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [incCode, trimmedName, trimmedPhone, description, demands || '', inferredCat, needs || '', textSev, visualSev, compositeSev, lat, lng, imageUrl, videoUrl, 'QUEUED'],
          function (err) {
            if (err) return res.status(500).json({ error: err.message });

            const newInc = {
              incident_id: incCode,
              incident_code: incCode,
              reporter_name: trimmedName,
              reporter_phone: trimmedPhone,
              description,
              demands: demands || '',
              category: inferredCat,
              needs: needs || '',
              severity: Math.round(compositeSev * 10) / 10,
              latitude: lat,
              longitude: lng,
              image_url: imageUrl,
              video_url: videoUrl,
              status: 'QUEUED'
            };

            // Automated Nearest-Station Resource Allocation Engine
            db.all(`SELECT * FROM units WHERE status = 'AVAILABLE'`, [], async (err, availUnits) => {
              let chosenUnit = null;
              let chosenDist = 0;
              let chosenTime = 0;
              let chosenStationCode = null;
              let chosenStationName = null;
              let chosenSupplies = null;
              let rationale = '';

              if (availUnits && availUnits.length > 0) {
                // Call ML solver for optimization
                try {
                  const optRes = await callMLMicroservice('/optimize/dispatch', {
                    incidents: [{
                      incident_code: incCode,
                      category: inferredCat,
                      description: description,
                      demands: demands || '',
                      needs: needs || '',
                      composite_severity: compositeSev,
                      latitude: lat,
                      longitude: lng
                    }],
                    units: availUnits
                  });

                  if (optRes && optRes.dispatch_plan && optRes.dispatch_plan.length > 0) {
                    const plan = optRes.dispatch_plan[0];
                    const matchUnit = availUnits.find(u => u.unit_code === plan.unit_code);
                    if (matchUnit) {
                      chosenUnit = matchUnit;
                      chosenDist = plan.distance_km;
                      chosenTime = plan.travel_time_minutes;
                      chosenStationCode = plan.station_code || matchUnit.station_code;
                      chosenStationName = plan.station_name || matchUnit.station_name;
                      chosenSupplies = plan.supplies_payload || matchUnit.supplies_payload;
                      rationale = plan.xai_rationale;
                    }
                  }
                } catch (e) {}

                // Greedy fallback if ML solver was offline or skipped
                if (!chosenUnit) {
                  const greedy = findBestStationUnit(
                    { category: inferredCat, description, demands, needs, latitude: lat, longitude: lng },
                    availUnits
                  );
                  if (greedy.bestUnit) {
                    chosenUnit = greedy.bestUnit;
                    chosenDist = Math.round(greedy.bestDist * 100) / 100;
                    chosenTime = Math.round(greedy.bestTime * 10) / 10;
                    chosenStationCode = chosenUnit.station_code;
                    chosenStationName = chosenUnit.station_name;
                    chosenSupplies = chosenUnit.supplies_payload;
                    rationale = `Dispatched from nearest station '${chosenStationName}' (${chosenDist} km away). Reaching location in estimated fastest travel time of ${chosenTime} mins with on-board supplies: ${chosenSupplies}.`;
                  }
                }
              }

              if (chosenUnit) {
                db.run(
                  `UPDATE incidents SET status = 'DISPATCHED', assigned_unit_code = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_code = ?`,
                  [chosenUnit.unit_code, incCode]
                );
                db.run(
                  `UPDATE units SET status = 'DISPATCHED', last_dispatch_at = CURRENT_TIMESTAMP WHERE unit_code = ?`,
                  [chosenUnit.unit_code]
                );
                db.run(
                  `INSERT INTO dispatches (incident_code, unit_code, station_code, station_name, distance_km, travel_time_minutes, supplies_dispatched, xai_rationale)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
                  [incCode, chosenUnit.unit_code, chosenStationCode, chosenStationName, chosenDist, chosenTime, chosenSupplies, rationale]
                );

                broadcastWS({
                  event: 'DISPATCH_ALLOCATED',
                  incident_code: incCode,
                  unit_code: chosenUnit.unit_code,
                  station_code: chosenStationCode,
                  station_name: chosenStationName,
                  distance_km: chosenDist,
                  travel_time_minutes: chosenTime,
                  supplies_dispatched: chosenSupplies,
                  rationale
                });
                notifyAdminServer();

                return res.json({
                  status: 'success',
                  incident_code: incCode,
                  category: inferredCat,
                  severity_level: Math.round(compositeSev * 10) / 10,
                  is_duplicate: false,
                  is_dispatched: true,
                  assigned_unit: chosenUnit.unit_code,
                  unit_type: chosenUnit.type,
                  station_code: chosenStationCode,
                  station_name: chosenStationName,
                  distance_km: chosenDist,
                  travel_time_minutes: chosenTime,
                  supplies_dispatched: chosenSupplies,
                  message: `Disaster verified. Nearest rescue station "${chosenStationName}" has immediately dispatched ${chosenUnit.type} (${chosenUnit.unit_code}) with essential life-saving supplies (${chosenDist} km away). ETA: ${chosenTime} mins.`
                });
              } else {
                broadcastWS({ event: 'INCIDENT_ADDED', data: newInc });
                notifyAdminServer();

                return res.json({
                  status: 'success',
                  incident_code: incCode,
                  category: inferredCat,
                  severity_level: Math.round(compositeSev * 10) / 10,
                  is_duplicate: false,
                  is_dispatched: false,
                  message: 'Incident report verified and logged. All emergency units currently engaged; queued for next returning response team.'
                });
              }
            });
          }
        );
      });
    });

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Helper to fully enrich incident with assigned unit, dispatch log, and station details
function fetchIncidentEnriched(codeOrQuery, isCode, callback) {
  let sql;
  let params;

  if (isCode) {
    sql = `SELECT * FROM incidents WHERE incident_code = ?`;
    params = [codeOrQuery];
  } else {
    const rawClean = codeOrQuery.trim();
    const digitsOnly = rawClean.replace(/\D/g, '');
    const searchTail = digitsOnly.length >= 7 ? digitsOnly.slice(-10) : digitsOnly;

    sql = `
      SELECT * FROM incidents 
      WHERE incident_code = ? 
         OR reporter_phone = ? 
         OR reporter_phone LIKE ?
         OR REPLACE(REPLACE(REPLACE(reporter_phone, ' ', ''), '-', ''), '+', '') LIKE ?
      ORDER BY id DESC LIMIT 1
    `;
    params = [rawClean, rawClean, `%${rawClean}%`, `%${searchTail || rawClean}%`];
  }

  db.get(sql, params, (err, inc) => {
    if (err || !inc) return callback(err || new Error('Not found'), null);

    if (inc.assigned_unit_code) {
      db.get(`SELECT * FROM units WHERE unit_code = ?`, [inc.assigned_unit_code], (err, unit) => {
        db.get(`SELECT * FROM dispatches WHERE incident_code = ? ORDER BY id DESC LIMIT 1`, [inc.incident_code], (err, disp) => {
          const stCode = (disp && disp.station_code) || (unit && unit.station_code);
          if (stCode) {
            db.get(`SELECT * FROM emergency_stations WHERE station_code = ?`, [stCode], (err, station) => {
              callback(null, { incident: inc, assigned_unit: unit || null, dispatch: disp || null, station: station || null });
            });
          } else {
            callback(null, { incident: inc, assigned_unit: unit || null, dispatch: disp || null, station: null });
          }
        });
      });
    } else {
      callback(null, { incident: inc, assigned_unit: null, dispatch: null, station: null });
    }
  });
}

// Lookup Incident by Individual's Phone Number or Incident Code
app.get('/api/incidents/lookup', (req, res) => {
  const query = (req.query.query || req.query.phone || req.query.code || '').trim();
  if (!query) return res.status(400).json({ error: 'Search query (phone or incident code) is required.' });

  fetchIncidentEnriched(query, false, (err, payload) => {
    if (err || !payload) {
      return res.status(404).json({ error: 'No matching disaster report found for the provided details.' });
    }
    res.json(payload);
  });
});

// Single Incident Details for Citizen Tracking
app.get('/api/incidents/:code', (req, res) => {
  const code = req.params.code;
  fetchIncidentEnriched(code, true, (err, payload) => {
    if (err || !payload) return res.status(404).json({ error: 'Incident not found' });
    res.json(payload);
  });
});

// All Incidents List
app.get('/api/incidents', (req, res) => {
  db.all(`SELECT * FROM incidents ORDER BY composite_severity DESC, id DESC`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    const formatted = (rows || []).map(r => ({
      incident_id: r.incident_code,
      incident_code: r.incident_code,
      reporter_name: r.reporter_name,
      reporter_phone: r.reporter_phone,
      description: r.description,
      demands: r.demands,
      category: r.category,
      needs: r.needs,
      severity: r.composite_severity,
      latitude: r.latitude,
      longitude: r.longitude,
      image_url: r.image_url,
      video_url: r.video_url,
      status: r.status,
      assigned_unit: r.assigned_unit_code,
      timestamp: r.created_at
    }));
    res.json({ incidents: formatted });
  });
});

// All Active Emergency Stations and Attached Fleets
app.get('/api/stations', (req, res) => {
  db.all(`SELECT * FROM emergency_stations WHERE status = 'ACTIVE'`, [], (err, stations) => {
    if (err) return res.status(500).json({ error: err.message });
    db.all(`SELECT * FROM units`, [], (err, units) => {
      const enriched = (stations || []).map(st => ({
        ...st,
        fleet: (units || []).filter(u => u.station_code === st.station_code)
      }));
      res.json({ stations: enriched });
    });
  });
});

// All Response Units
app.get('/api/units', (req, res) => {
  db.all(`SELECT * FROM units`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ units: rows || [] });
  });
});

// All Active Shelters
app.get('/api/shelters', (req, res) => {
  db.all(`SELECT * FROM shelters`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ shelters: rows || [] });
  });
});

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ event: 'CONNECTED', message: 'Citizen Portal Active' }));
});

server.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🌐 CITIZEN DISASTER WEBSITE running on http://localhost:${PORT}/`);
  console.log(`📍 Citizen Live Rescue Tracker: http://localhost:${PORT}/track`);
  console.log(`====================================================`);
});
