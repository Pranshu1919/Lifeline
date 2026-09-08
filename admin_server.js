const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const http = require('http');
const WebSocket = require('ws');
const sqlite3 = require('sqlite3').verbose();
const httpNative = require('http');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = 8001;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Directories
const STATIC_DIR = path.join(__dirname, 'static');
const UPLOADS_DIR = path.join(__dirname, 'uploads');
const DB_PATH = path.join(__dirname, 'lifeline_enterprise.db');

app.use('/static', express.static(STATIC_DIR));
app.use('/uploads', express.static(UPLOADS_DIR));

// Shared Database Connection with WAL Mode
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) console.error('Database connection error:', err);
  else {
    console.log('🛡️ Command Center Server connected to SQLite DB:', DB_PATH);
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

function notifyCitizenServer() {
  const req = httpNative.request({
    hostname: '127.0.0.1',
    port: 8000,
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

function broadcastWS(data) {
  const msg = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(msg);
    }
  });
}

// Internal Notification Endpoint from Citizen Server (Port 8000)
app.post('/api/internal/notify-update', (req, res) => {
  broadcastWS({ event: 'REFRESH_INCIDENTS' });
  res.json({ ok: true });
});

// Routes for Authority Command Center Website (Port 8001)
app.get('/', (req, res) => res.sendFile(path.join(STATIC_DIR, 'admin.html')));
app.get('/incident', (req, res) => res.sendFile(path.join(STATIC_DIR, 'admin-incident.html')));
app.get('/track', (req, res) => res.sendFile(path.join(STATIC_DIR, 'track.html')));

// API Endpoints for Authority Resource Allocation & Tracking
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

      db.run(`UPDATE incidents SET status = 'DISPATCHED', assigned_unit_code = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_code = ?`, [unit_code, incident_code], (err) => {
        db.run(`UPDATE units SET status = 'DISPATCHED', last_dispatch_at = CURRENT_TIMESTAMP WHERE unit_code = ?`, [unit_code], (err) => {
          db.run(`INSERT INTO dispatches (incident_code, unit_code, travel_time_minutes, xai_rationale) VALUES (?, ?, ?, ?)`, [incident_code, unit_code, timeMins, rationale], (err) => {
            
            broadcastWS({ event: 'MANUAL_DISPATCH', incident_code, unit_code });
            notifyCitizenServer();

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
      notifyCitizenServer();

      res.json({ dispatch_plan: dispatchPlan });
    });
  });
});

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ event: 'CONNECTED', message: 'Command Center Active' }));
});

server.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🛡️ AUTHORITY COMMAND CENTER WEBSITE running on http://localhost:${PORT}/`);
  console.log(`📍 Incident Resource Allocation Manager: http://localhost:${PORT}/incident`);
  console.log(`📍 Live Rescue Tracking Portal: http://localhost:${PORT}/track`);
  console.log(`====================================================`);
});
