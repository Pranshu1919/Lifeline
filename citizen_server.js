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

    let nlpRes = await callMLMicroservice('/predict/text', { text: description });
    let inferredCat = category || (nlpRes ? nlpRes.category : 'General Disaster Alert');
    let textSev = nlpRes ? nlpRes.text_severity : 3.5;

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
            notifyAdminServer();

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

// Single Incident Details for Citizen Tracking
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

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ event: 'CONNECTED', message: 'Citizen Portal Active' }));
});

server.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🌐 CITIZEN DISASTER WEBSITE running on http://localhost:${PORT}/`);
  console.log(`📍 Citizen Live Rescue Tracker: http://localhost:${PORT}/track`);
  console.log(`====================================================`);
});
