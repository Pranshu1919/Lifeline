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

  // 2. Emergency Response Stations Table
  db.run(`
    CREATE TABLE IF NOT EXISTS emergency_stations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      station_code TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      station_type TEXT NOT NULL,
      address TEXT NOT NULL,
      contact_number TEXT NOT NULL,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      stockpile_supplies TEXT NOT NULL,
      status TEXT DEFAULT 'ACTIVE'
    )
  `);

  // 3. Units Table (Assigned to Home Stations with On-Board Supplies)
  db.run(`
    CREATE TABLE IF NOT EXISTS units (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      unit_code TEXT UNIQUE NOT NULL,
      station_code TEXT NOT NULL,
      station_name TEXT NOT NULL,
      type TEXT NOT NULL,
      capabilities TEXT NOT NULL,
      supplies_payload TEXT NOT NULL,
      capacity INTEGER NOT NULL,
      speed_kmh REAL DEFAULT 35.0,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      status TEXT DEFAULT 'AVAILABLE',
      last_dispatch_at DATETIME
    )
  `);

  // 4. Shelters Table
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

  // 5. Dispatches Log Table (Audits origin station, distance, fastest time, and supplies)
  db.run(`
    CREATE TABLE IF NOT EXISTS dispatches (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      incident_code TEXT NOT NULL,
      unit_code TEXT NOT NULL,
      station_code TEXT,
      station_name TEXT,
      distance_km REAL,
      travel_time_minutes REAL NOT NULL,
      supplies_dispatched TEXT,
      xai_rationale TEXT NOT NULL,
      dispatched_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Seed Emergency Stations
  const stmtStation = db.prepare(`
    INSERT INTO emergency_stations (station_code, name, station_type, address, contact_number, latitude, longitude, stockpile_supplies, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  stmtStation.run(
    'STATION-FIRE-01',
    'Ghaziabad Central Fire & Disaster Rescue Station',
    'Fire & Hazmat Rescue',
    'GT Road, Sector 1, Industrial Area, Ghaziabad',
    '+91 120-2734101',
    28.6792,
    77.4975,
    '24x Heavy Foam Cannons, 12x Hydraulic Cutters, 6x Thermal Imaging Sensors, 8x Telescopic Rescue Ladders, 100x Fire Retardant Suits',
    'ACTIVE'
  );

  stmtStation.run(
    'STATION-MED-01',
    'District Emergency Trauma & Medical Care Depot',
    'Trauma & Emergency Medical Services',
    'Hindon Hospital Road, Near District MMG Hospital, Ghaziabad',
    '+91 120-2825102',
    28.6710,
    77.5080,
    '50x Medical Oxygen Cylinders, 25x Portable Ventilators, 40x AED Defibrillators, 200x Critical Trauma Packs, 150x Burn Dressing Kits',
    'ACTIVE'
  );

  stmtStation.run(
    'STATION-BOAT-01',
    'Hindon River Flood Rescue & Evacuation Base',
    'Water & Flood Evacuation Depot',
    'Hindon River Barrage Post, Riverfront Bypass, Ghaziabad',
    '+91 120-2863103',
    28.6730,
    77.5180,
    '15x Motorized Inflatable Rescue Boats, 150x Certified Lifejackets, 40x Diving & Snorkel Kits, 30x Ring Buoys, Water Submersible Pumps',
    'ACTIVE'
  );

  stmtStation.run(
    'STATION-NDRF-01',
    '8th Battalion NDRF Regional Disaster Rescue Depot',
    'Urban Search & Structural Collapse Extrication',
    'Govindpuram NDRF Complex, Hapur Road, Ghaziabad',
    '+91 120-2782104',
    28.6870,
    77.4850,
    'Life Detector Ground Radar, Acoustic Listening Sensors, Concrete Chippers & Diamond Cutters, High-Tensile Rescue Winches, Canine Units',
    'ACTIVE'
  );

  stmtStation.run(
    'STATION-SUPPLY-01',
    'Central Disaster Relief Logistics & Supplies Hub',
    'Relief Supplies & Humanitarian Aid',
    'Raj Nagar Extension Warehousing Logistics Hub, Meerut Bypass Road',
    '+91 120-2981105',
    28.6830,
    77.4620,
    '5000x Potable Drinking Water Pouches, 2000x Ready-to-Eat Emergency Food Rations, 500x Thermal Blankets, 100x Family Tent Kits',
    'ACTIVE'
  );

  stmtStation.run(
    'STATION-RAPID-01',
    'Rapid Disaster Quick-Response Station',
    'First-Response Recon & Quick Medic Unit',
    'RDC Raj Nagar Flyover Junction, Ghaziabad',
    '+91 120-2804106',
    28.6650,
    77.5250,
    '20x First-Response Medic Bags, High-Intensity Floodlights, Satellite Radios, Portable Stretchers, Emergency Triaging Tags',
    'ACTIVE'
  );

  stmtStation.finalize();

  // Seed Units (Attached to Stations with specialized capability tags and supplies payloads)
  const stmtUnit = db.prepare(`
    INSERT INTO units (unit_code, station_code, station_name, type, capabilities, supplies_payload, capacity, speed_kmh, latitude, longitude, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // Ambulance 1 at District Trauma Depot
  stmtUnit.run(
    'AMBULANCE-01',
    'STATION-MED-01',
    'District Emergency Trauma & Medical Care Depot',
    'Advanced Life Support (ALS) Ambulance',
    'medical,trauma,cardiac,respiratory,critical,first-aid,injuries,hospital',
    'Portable ICU Ventilator, 4x Medical Oxygen Cylinders, AED Defibrillator, Trauma Hemostatic Bandages, Burn Dressing Kits, 2x Patient Stretchers',
    3,
    50.0,
    28.6710,
    77.5080,
    'AVAILABLE'
  );

  // Rapid Medic Ambulance at Rapid Response Station
  stmtUnit.run(
    'AMBULANCE-02',
    'STATION-RAPID-01',
    'Rapid Disaster Quick-Response Station',
    'Rapid Paramedic First-Response Ambulance',
    'medical,first-aid,triaging,injuries,bleeding,unconscious',
    '2x Oxygen Cylinders, 4x Emergency First Aid Trauma Bags, Cervical Neck Braces, IV Fluid Packs, Splints, Pulse Oximeters',
    2,
    55.0,
    28.6650,
    77.5250,
    'AVAILABLE'
  );

  // Fire Engine 1 at Fire Station
  stmtUnit.run(
    'FIRE-ENGINE-01',
    'STATION-FIRE-01',
    'Ghaziabad Central Fire & Disaster Rescue Station',
    'Heavy Rescue Fire Tender & Foam Extinguisher',
    'fire,burns,smoke,flames,explosion,chemical,blaze,trapped',
    '12x High-Pressure Foam Cannons, Thermal Imaging Camera, 2x Hydraulic Cutters, 15m Telescopic Rescue Ladder, SCBA Breathing Apparatuses',
    6,
    40.0,
    28.6792,
    77.4975,
    'AVAILABLE'
  );

  // Fire Engine 2 at Fire Station
  stmtUnit.run(
    'FIRE-ENGINE-02',
    'STATION-FIRE-01',
    'Ghaziabad Central Fire & Disaster Rescue Station',
    'Rapid Water Bowsers & Fire Suppression Unit',
    'fire,flames,smoke,hazard,factory,transformer',
    '3000L High-Pressure Water Cannon, Chemical Fire Extinguishers, Heavy Rescue Axes, Fire Blankets, Smoke Exhaust Blowers',
    4,
    42.0,
    28.6792,
    77.4975,
    'AVAILABLE'
  );

  // Rescue Boat 1 at Hindon Flood Base (Currently Dispatched to INC-2026-0001)
  stmtUnit.run(
    'RESCUE-BOAT-01',
    'STATION-BOAT-01',
    'Hindon River Flood Rescue & Evacuation Base',
    'Motorized Flood Rescue Boat',
    'flood,water,drowning,submerged,overflow,river,waterlogging,boat,evacuation',
    '8x Inflatable Lifejackets, 2x Ring Buoys, Diver Retrieval Winch, 1x Emergency Inflatable Raft, First Aid Trauma Pack, High-Power Searchlight',
    8,
    25.0,
    28.6730,
    77.5180,
    'DISPATCHED'
  );

  // Rescue Boat 2 at Hindon Flood Base (Available for new flood alerts)
  stmtUnit.run(
    'RESCUE-BOAT-02',
    'STATION-BOAT-01',
    'Hindon River Flood Rescue & Evacuation Base',
    'Deep-Water Rapid Evacuation Zodiac Boat',
    'flood,water,rain,submerged,marooned,drowning,evacuation',
    '10x Certified PFD Lifejackets, 2x Deep-Water Retrieval Poles, Floating Stretcher, Emergency Food Rations, Signaling Flares',
    10,
    28.0,
    28.6730,
    77.5180,
    'AVAILABLE'
  );

  // NDRF Unit at NDRF Depot
  stmtUnit.run(
    'NDRF-UNIT-01',
    'STATION-NDRF-01',
    '8th Battalion NDRF Regional Disaster Rescue Depot',
    'NDRF Heavy Structural Extrication & Urban Search Unit',
    'earthquake,collapse,building,debris,rubble,trapped,structural,search,disaster',
    'Acoustic Life Locator Radar, Hydraulic Concrete Cutters, Heavy Winches, Telescopic Shoring Props, 4x Rigid Basket Stretchers',
    8,
    38.0,
    28.6870,
    77.4850,
    'AVAILABLE'
  );

  // Relief Logistics Truck 1 at Supply Hub
  stmtUnit.run(
    'RELIEF-TRUCK-01',
    'STATION-SUPPLY-01',
    'Central Disaster Relief Logistics & Supplies Hub',
    'Emergency Food, Water & Medical Relief Carrier',
    'food,water,ration,hunger,supplies,blanket,starvation,shelter,relief,kits',
    '600x Sealed Drinking Water Bottles, 250x High-Calorie Food Ration Kits, 60x Thermal Blankets, 15x Family Tents, Water Purification Drops',
    12,
    35.0,
    28.6830,
    77.4620,
    'AVAILABLE'
  );

  // Relief Logistics Truck 2 at Supply Hub
  stmtUnit.run(
    'RELIEF-TRUCK-02',
    'STATION-SUPPLY-01',
    'Central Disaster Relief Logistics & Supplies Hub',
    'Mobile Water Purification & Sanitation Unit',
    'water,drinking,sanitation,relief,cholera,hygiene,clean',
    'RO Mobile Water Filtration System (1000L/hr), 500x Collapsible Jerry Cans, Oral Rehydration Salts, Chlorine Tablets, Emergency Disinfectants',
    6,
    35.0,
    28.6830,
    77.4620,
    'AVAILABLE'
  );

  stmtUnit.finalize();

  // Seed Shelters
  const stmtShelter = db.prepare(`
    INSERT INTO shelters (shelter_code, name, latitude, longitude, total_capacity, occupied_beds, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  stmtShelter.run('SHELTER-01', 'AKGEC Central Relief Camp', 28.6760, 77.5010, 250, 65, 'ACTIVE');
  stmtShelter.run('SHELTER-02', 'Raj Nagar Disaster Medical Ward', 28.6880, 77.4480, 180, 110, 'ACTIVE');
  stmtShelter.finalize();

  // Seed Initial Dispatches & Incidents for demo
  const stmtInc = db.prepare(`
    INSERT INTO incidents (incident_code, reporter_name, reporter_phone, description, demands, category, needs, text_severity, visual_severity, composite_severity, latitude, longitude, status, assigned_unit_code)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  stmtInc.run(
    'INC-2026-0001',
    'Vijay Katiyar',
    '+91 9876543210',
    'Severe flash flood water reaching 2nd floor near main market, 5 people stranded on terrace',
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
  stmtInc.finalize();

  // Seed corresponding dispatch audit for INC-2026-0001
  const stmtDisp = db.prepare(`
    INSERT INTO dispatches (incident_code, unit_code, station_code, station_name, distance_km, travel_time_minutes, supplies_dispatched, xai_rationale)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  stmtDisp.run(
    'INC-2026-0001',
    'RESCUE-BOAT-01',
    'STATION-BOAT-01',
    'Hindon River Flood Rescue & Evacuation Base',
    1.6,
    3.8,
    '8x Inflatable Lifejackets, 2x Ring Buoys, Diver Retrieval Winch, 1x Emergency Inflatable Raft, First Aid Trauma Pack, High-Power Searchlight',
    'Dispatched from nearest station "Hindon River Flood Rescue & Evacuation Base" (1.6 km away). Reaching location in estimated fastest travel time of 3.8 mins with flood rescue equipment.'
  );
  stmtDisp.finalize();

  console.log('✅ LifeLine Enterprise Database built successfully with Emergency Stations, Specialized Vehicles, and On-Board Supplies Network!');
});

db.close();
