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

const PORT = process.env.PORT || 8000;

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

// Configure Multer for Multiple File Uploads (Photos + Videos)
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});
const upload = multer({ storage: storage });

// Database Connection
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) console.error('Database connection error:', err);
  else console.log('Node.js Server connected to SQLite DB:', DB_PATH);
});

// Helper for HTTP Post requests to Python ML Microservice
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

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371.0;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function broadcastWS(data) {
  const msg = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(msg);
    }
  });
}

// Routes
app.get('/', (req, res) => res.sendFile(path.join(STATIC_DIR, 'index.html')));
app.get('/track', (req, res) => res.sendFile(path.join(STATIC_DIR, 'track.html')));
app.get('/admin', (req, res) => res.sendFile(path.join(STATIC_DIR, 'admin.html')));
app.get('/admin-incident', (req, res) => res.sendFile(path.join(STATIC_DIR, 'admin-incident.html')));

// Citizen Emergency Intake API Endpoint (Supports Multiple Photos & Videos)
app.post('/api/incidents/report', upload.array('files', 10), async (req, res) => {
  try {
    const { reporter_name, reporter_phone, description, demands, category, needs, latitude, longitude } = req.body;
    const lat = parseFloat(latitude) || 28.6752;
    const lng = parseFloat(longitude) || 77.5020;
    
    let imagePaths = [];
    let videoPaths = [];

    if (req.files && req.files.length > 0) {
      req.files.forEach(f => {
        const ext = path.extname(f.originalname).toLowerCase();
        const url = `/uploads/${f.filename}`;
        if (['.webm', '.mp4', '.avi', '.mov', '.mkv'].includes(ext)) {
          videoPaths.push(url);
        } else {
          imagePaths.push(url);
        }
      });
    }

    const imageUrl = imagePaths.length > 0 ? imagePaths.join(',') : null;
    const videoUrl = videoPaths.length > 0 ? videoPaths.join(',') : null;

    // Call ML NLP Microservice (CrisisMMD Model)
    let nlpRes = await callMLMicroservice('/predict/text', { text: description });
    let inferredCat = category || (nlpRes ? nlpRes.category : 'General Disaster Alert');
    let textSev = nlpRes ? nlpRes.text_severity : 3.5;

    // Call ML CV Microservice if photo attached
    let visualSev = 0.0;
    if (req.files && req.files.length > 0 && imagePaths.length > 0) {
      let firstImgPath = req.files.find(f => !['.webm', '.mp4', '.avi', '.mov', '.mkv'].includes(path.extname(f.originalname).toLowerCase()))?.path;
      if (firstImgPath) {
        let cvRes = await callMLMicroservice('/predict/image', { image_path: firstImgPath });
        if (cvRes) visualSev = cvRes.visual_severity;
      }
    }

    let compositeSev = (textSev * 0.6) + (visualSev * 0.4);
    if (visualSev === 0.0) compositeSev = textSev;

    // Spatial Deduplication (100 meter radius)
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
          db.run(
            `UPDATE incidents SET confirmations_count = ?, composite_severity = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_code = ?`,
            [newCount, newSev, matchedCode]
          );
          break;
        }
      }

      if (isDuplicate) {
        broadcastWS({ event: 'INCIDENT_UPDATED', incident_code: matchedCode });
        return res.json({
          status: 'success',
          incident_code: matchedCode,
          category: inferredCat,
          composite_severity: 5.0,
          is_duplicate: true,
          message: 'Report merged with existing nearby disaster incident.'
        });
      }

      // Insert New Incident to SQLite DB
      db.get(`SELECT COUNT(*) as cnt FROM incidents`, [], (err, countRow) => {
        const count = (countRow ? countRow.cnt : 0) + 1;
        const incCode = `INC-2026-${String(count).padStart(4, '0')}`;

        db.run(
          `INSERT INTO incidents (incident_code, reporter_name, reporter_phone, description, demands, category, needs, text_severity, visual_severity, composite_severity, latitude, longitude, image_url, video_url, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [incCode, reporter_name || 'Anonymous', reporter_phone || '', description, demands || '', inferredCat, needs || '', textSev, visualSev, compositeSev, lat, lng, imageUrl, videoUrl, 'QUEUED'],
          function (err) {
            if (err) return res.status(500).json({ error: err.message });

            const newInc = {
              incident_id: incCode,
              incident_code: incCode,
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

            broadcastWS({ event: 'INCIDENT_ADDED', data: newInc });

            res.json({
              status: 'success',
              incident_code: incCode,
              category: inferredCat,
              severity_level: Math.round(compositeSev * 10) / 10,
              is_duplicate: false,
              message: 'Incident report logged in database and analyzed by ML pipeline.'
            });
          }
        );
      });
    });

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Single Incident Details Endpoint
app.get('/api/incidents/:code', (req, res) => {
  const code = req.params.code;
  db.get(`SELECT * FROM incidents WHERE incident_code = ?`, [code], (err, inc) => {
    if (err || !inc) return res.status(404).json({ error: 'Incident not found' });

    if (inc.assigned_unit_code) {
      db.get(`SELECT * FROM units WHERE unit_code = ?`, [inc.assigned_unit_code], (err, unit) => {
        res.json({ incident: inc, assigned_unit: unit || null });
      });
    } else {
      res.json({ incident: inc, assigned_unit: null });
    }
  });
});

// Get Incidents Ordered Strictly By Severity (Highest to Lowest)
app.get('/api/incidents', (req, res) => {
  db.all(`SELECT * FROM incidents ORDER BY composite_severity DESC, id DESC`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    const formatted = rows.map(r => ({
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

app.get('/api/units', (req, res) => {
  db.all(`SELECT * FROM units`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ units: rows });
  });
});

app.get('/api/shelters', (req, res) => {
  db.all(`SELECT * FROM shelters`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ shelters: rows });
  });
});

app.get('/api/stats', (req, res) => {
  db.get(`SELECT COUNT(*) as total, SUM(CASE WHEN composite_severity >= 4.0 THEN 1 ELSE 0 END) as critical FROM incidents`, [], (err, incRow) => {
    db.get(`SELECT COUNT(*) as avail FROM units WHERE status = 'AVAILABLE'`, [], (err, unitRow) => {
      db.get(`SELECT COUNT(*) as shelters FROM shelters`, [], (err, shelterRow) => {
        res.json({
          total_incidents: incRow ? incRow.total : 0,
          critical_incidents: incRow ? (incRow.critical || 0) : 0,
          available_units: unitRow ? unitRow.avail : 0,
          active_shelters: shelterRow ? shelterRow.shelters : 0,
          avg_response_time: 21.0
        });
      });
    });
  });
});

// Human Commander Manual Resource Assignment & Re-Assignment Override Endpoint
app.post('/api/incidents/assign-manual', (req, res) => {
  const { incident_code, unit_code } = req.body;
  if (!incident_code || !unit_code) {
    return res.status(400).json({ error: 'Missing incident_code or unit_code' });
  }

  db.get(`SELECT * FROM incidents WHERE incident_code = ?`, [incident_code], (err, inc) => {
    if (err || !inc) return res.status(404).json({ error: 'Incident not found' });
    db.get(`SELECT * FROM units WHERE unit_code = ?`, [unit_code], (err, u) => {
      if (err || !u) return res.status(404).json({ error: 'Unit not found' });

      const distKm = haversine(u.latitude, u.longitude, inc.latitude, inc.longitude);
      const timeMins = Math.round(((distKm / (u.speed_kmh || 30.0)) * 60.0) * 10) / 10;
      const rationale = `Human Commander Manual Override: Unit ${u.unit_code} assigned to incident ${inc.incident_code} (Est. ${timeMins} mins travel time).`;

      db.run(`UPDATE incidents SET status = 'DISPATCHED', assigned_unit_code = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_code = ?`, [unit_code, incident_code]);
      db.run(`UPDATE units SET status = 'DISPATCHED', last_dispatch_at = CURRENT_TIMESTAMP WHERE unit_code = ?`, [unit_code]);
      db.run(`INSERT INTO dispatches (incident_code, unit_code, travel_time_minutes, xai_rationale) VALUES (?, ?, ?, ?)`, [incident_code, unit_code, timeMins, rationale]);

      broadcastWS({ event: 'MANUAL_DISPATCH', incident_code, unit_code });

      res.json({
        status: 'success',
        incident_code,
        unit_code,
        travel_time_minutes: timeMins,
        rationale
      });
    });
  });
});

// Automated AI MILP Resource Optimization Solver Endpoint
app.post('/api/ml/optimize-dispatch', (req, res) => {
  db.all(`SELECT * FROM incidents WHERE status != 'DISPATCHED'`, [], (err, unassigned) => {
    if (err) return res.status(500).json({ error: err.message });
    db.all(`SELECT * FROM units WHERE status = 'AVAILABLE'`, [], async (err, availableUnits) => {
      if (err) return res.status(500).json({ error: err.message });

      if (unassigned.length === 0 || availableUnits.length === 0) {
        return res.json({ dispatch_plan: [], message: 'No unassigned incidents or available units.' });
      }

      let optRes = await callMLMicroservice('/optimize/dispatch', {
        incidents: unassigned,
        units: availableUnits
      });

      let dispatchPlan = optRes ? optRes.dispatch_plan : [];

      if (!dispatchPlan || dispatchPlan.length === 0) {
        unassigned.sort((a, b) => b.composite_severity - a.composite_severity);
        const assignedUnitIds = new Set();
        dispatchPlan = [];

        for (let inc of unassigned) {
          let bestUnit = null;
          let minTime = Infinity;
          for (let u of availableUnits) {
            if (assignedUnitIds.has(u.unit_code)) continue;
            const distKm = haversine(u.latitude, u.longitude, inc.latitude, inc.longitude);
            const timeMins = (distKm / (u.speed_kmh || 30.0)) * 60.0;
            if (timeMins < minTime) {
              minTime = timeMins;
              bestUnit = u;
            }
          }

          if (bestUnit) {
            assignedUnitIds.add(bestUnit.unit_code);
            dispatchPlan.push({
              unit_code: bestUnit.unit_code,
              incident_code: inc.incident_code,
              travel_time_minutes: Math.round(minTime * 10) / 10,
              xai_rationale: `Unit ${bestUnit.unit_code} assigned: Shortest travel time of ${Math.round(minTime * 10) / 10} mins to priority incident (Severity ${inc.composite_severity.toFixed(1)}).`
            });
          }
        }
      }

      for (let item of dispatchPlan) {
        db.run(`UPDATE incidents SET status = 'DISPATCHED', assigned_unit_code = ? WHERE incident_code = ?`, [item.unit_code, item.incident_code]);
        db.run(`UPDATE units SET status = 'DISPATCHED', last_dispatch_at = CURRENT_TIMESTAMP WHERE unit_code = ?`, [item.unit_code]);
        db.run(`INSERT INTO dispatches (incident_code, unit_code, travel_time_minutes, xai_rationale) VALUES (?, ?, ?, ?)`, [item.incident_code, item.unit_code, item.travel_time_minutes, item.xai_rationale]);
      }

      broadcastWS({ event: 'OPTIMIZATION_COMPLETED', plan: dispatchPlan });
      res.json({ dispatch_plan: dispatchPlan });
    });
  });
});

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ event: 'CONNECTED', message: 'LifeLine Server Active' }));
});

server.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🚀 LifeLine Server running on port ${PORT}`);
  console.log(`🌐 Public Website Homepage: http://localhost:${PORT}/`);
  console.log(`📍 Citizen Live Tracker:    http://localhost:${PORT}/track`);
  console.log(`🛡️ Official Command Center: http://localhost:${PORT}/admin`);
  console.log(`====================================================`);
});
