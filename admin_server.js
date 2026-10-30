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

app.get('/api/incidents/:code', (req, res) => {
  const code = req.params.code;
  fetchIncidentEnriched(code, true, (err, payload) => {
    if (err || !payload) return res.status(404).json({ error: 'Incident not found' });
    res.json(payload);
  });
});

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

      const distKm = Math.round(haversine(u.latitude, u.longitude, inc.latitude, inc.longitude) * 100) / 100;
      const timeMins = Math.round(((distKm / (u.speed_kmh || 35.0)) * 60.0) * 10) / 10;
      const rationale = `Manual Commander Override: Dispatched from home station "${u.station_name || 'Station'}" (${distKm} km away). Estimated transit time: ${timeMins} mins with on-board supplies: ${u.supplies_payload || 'Standard'}.`;

      db.run(`UPDATE incidents SET status = 'DISPATCHED', assigned_unit_code = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_code = ?`, [unit_code, incident_code], (err) => {
        db.run(`UPDATE units SET status = 'DISPATCHED', last_dispatch_at = CURRENT_TIMESTAMP WHERE unit_code = ?`, [unit_code], (err) => {
          db.run(`INSERT INTO dispatches (incident_code, unit_code, station_code, station_name, distance_km, travel_time_minutes, supplies_dispatched, xai_rationale) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
            [incident_code, unit_code, u.station_code, u.station_name, distKm, timeMins, u.supplies_payload, rationale], (err) => {
            
            broadcastWS({ event: 'MANUAL_DISPATCH', incident_code, unit_code });
            notifyCitizenServer();

            res.json({
              status: 'success',
              incident_code,
              unit_code,
              station_name: u.station_name,
              distance_km: distKm,
              travel_time_minutes: timeMins,
              supplies_dispatched: u.supplies_payload,
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
          let bestDist = 0;
          for (let u of availableUnits) {
            if (assignedUnitIds.has(u.unit_code)) continue;
            const distKm = haversine(u.latitude, u.longitude, inc.latitude, inc.longitude);
            const timeMins = (distKm / (u.speed_kmh || 35.0)) * 60.0;
            if (timeMins < minTime) {
              minTime = timeMins;
              bestUnit = u;
              bestDist = distKm;
            }
          }

          if (bestUnit) {
            assignedUnitIds.add(bestUnit.unit_code);
            const rDist = Math.round(bestDist * 100) / 100;
            const rTime = Math.round(minTime * 10) / 10;
            dispatchPlan.push({
              unit_code: bestUnit.unit_code,
              incident_code: inc.incident_code,
              station_code: bestUnit.station_code,
              station_name: bestUnit.station_name,
              distance_km: rDist,
              travel_time_minutes: rTime,
              supplies_payload: bestUnit.supplies_payload,
              xai_rationale: `Dispatched from nearest station '${bestUnit.station_name}' (${rDist} km away). Fastest transit arrival: ${rTime} mins with on-board supplies: ${bestUnit.supplies_payload}.`
            });
          }
        }
      }

      for (let item of dispatchPlan) {
        db.run(`UPDATE incidents SET status = 'DISPATCHED', assigned_unit_code = ? WHERE incident_code = ?`, [item.unit_code, item.incident_code]);
        db.run(`UPDATE units SET status = 'DISPATCHED', last_dispatch_at = CURRENT_TIMESTAMP WHERE unit_code = ?`, [item.unit_code]);
        db.run(`INSERT INTO dispatches (incident_code, unit_code, station_code, station_name, distance_km, travel_time_minutes, supplies_dispatched, xai_rationale) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
          [item.incident_code, item.unit_code, item.station_code, item.station_name, item.distance_km, item.travel_time_minutes, item.supplies_payload, item.xai_rationale]);
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
