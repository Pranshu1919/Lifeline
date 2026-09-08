const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, 'lifeline_enterprise.db');

if (fs.existsSync(DB_PATH)) {
  try { fs.unlinkSync(DB_PATH); } catch (e) {}
}

const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) console.error('Error connecting to SQLite DB:', err);
  else console.log('Connected to SQLite DB for Enterprise Schema Build:', DB_PATH);
});

db.serialize(() => {
  // 1. Incidents Table
  db.run(`
    CREATE TABLE IF NOT EXISTS incidents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      incident_code TEXT UNIQUE NOT NULL,
      reporter_name TEXT,
      reporter_phone TEXT,
      description TEXT NOT NULL,
      demands TEXT,
      category TEXT NOT NULL,
      needs TEXT,
      text_severity REAL DEFAULT 3.0,
      visual_severity REAL DEFAULT 0.0,
      composite_severity REAL DEFAULT 3.0,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      image_url TEXT,
      video_url TEXT,
      confirmations_count INTEGER DEFAULT 1,
      status TEXT DEFAULT 'QUEUED',
      assigned_unit_code TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 2. Units Table
  db.run(`
    CREATE TABLE IF NOT EXISTS units (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      unit_code TEXT UNIQUE NOT NULL,
      type TEXT NOT NULL,
      capacity INTEGER NOT NULL,
      speed_kmh REAL DEFAULT 30.0,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      status TEXT DEFAULT 'AVAILABLE',
      last_dispatch_at DATETIME
    )
  `);

  // 3. Shelters Table
  db.run(`
    CREATE TABLE IF NOT EXISTS shelters (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      shelter_code TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      total_capacity INTEGER NOT NULL,
      occupied_beds INTEGER DEFAULT 0,
      status TEXT DEFAULT 'ACTIVE'
    )
  `);

  // 4. Dispatches Log Table
  db.run(`
    CREATE TABLE IF NOT EXISTS dispatches (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      incident_code TEXT NOT NULL,
      unit_code TEXT NOT NULL,
      travel_time_minutes REAL NOT NULL,
      xai_rationale TEXT NOT NULL,
      dispatched_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Seed Units
  const stmtUnit = db.prepare(`
    INSERT INTO units (unit_code, type, capacity, speed_kmh, latitude, longitude, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  stmtUnit.run('AMBULANCE-01', 'Ambulance', 2, 40.0, 28.6800, 77.4950, 'AVAILABLE');
  stmtUnit.run('RESCUE-BOAT-01', 'Rescue Boat', 6, 20.0, 28.6710, 77.5100, 'DISPATCHED');
  stmtUnit.run('FIRE-ENGINE-01', 'Fire Engine', 4, 35.0, 28.6900, 77.4800, 'AVAILABLE');
  stmtUnit.run('AMBULANCE-02', 'Rapid Medic Unit', 2, 45.0, 28.6650, 77.5250, 'AVAILABLE');
  stmtUnit.finalize();

  // Seed Shelters
  const stmtShelter = db.prepare(`
    INSERT INTO shelters (shelter_code, name, latitude, longitude, total_capacity, occupied_beds, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  stmtShelter.run('SHELTER-01', 'AKGEC Central Relief Camp', 28.6760, 77.5010, 250, 65, 'ACTIVE');
  stmtShelter.run('SHELTER-02', 'Raj Nagar Disaster Medical Ward', 28.6880, 77.4480, 180, 110, 'ACTIVE');
  stmtShelter.finalize();

  // Seed Initial Incidents with assigned unit for tracking demo
  const stmtInc = db.prepare(`
    INSERT INTO incidents (incident_code, reporter_name, reporter_phone, description, demands, category, needs, text_severity, visual_severity, composite_severity, latitude, longitude, status, assigned_unit_code)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  stmtInc.run(
    'INC-2026-0001',
    'Vijay Katiyar',
    '+91 9876543210',
    'Severe flash flood water reaching 2nd floor near main market',
    'Require 2 inflatable boats, 10 bottles of clean drinking water, insulin for diabetic patient',
    'Flood',
    'Boat Evacuation, Urgent Medical Attention, Food & Water',
    4.5,
    0.90,
    4.7,
    28.6752,
    77.5020,
    'DISPATCHED',
    'RESCUE-BOAT-01'
  );
  stmtInc.run(
    'INC-2026-0002',
    'Rahul Sharma',
    '+91 9811223344',
    'Transformer explosion caused building wall collapse, minor smoke detected',
    'Fire extinguisher, 2 ladders, first aid kits',
    'Fire',
    'Fire Rescue, Search & Rescue',
    3.5,
    0.60,
    3.6,
    28.6890,
    77.5120,
    'QUEUED',
    null
  );
  stmtInc.finalize();

  console.log('Database updated with demands column and tracking demo data!');
});

db.close();
