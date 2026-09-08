import os, json, math, datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from scipy.optimize import milp, LinearConstraint, Bounds
import numpy as np

# Ensure directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(
    title="LifeLine: Full-Stack Smart Disaster Response System",
    description="Unified AI, GIS, and Resource Optimization Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Persistence File Paths
INCIDENTS_FILE = os.path.join(BASE_DIR, "incidents_db.json")
UNITS_FILE = os.path.join(BASE_DIR, "units_db.json")
SHELTERS_FILE = os.path.join(BASE_DIR, "shelters_db.json")

# Initial Default Data
DEFAULT_UNITS = [
    {"unit_id": "AMBULANCE-01", "type": "Ambulance", "latitude": 28.6800, "longitude": 77.4950, "capacity": 2, "status": "AVAILABLE", "speed": 35},
    {"unit_id": "RESCUE-BOAT-01", "type": "Rescue Boat", "latitude": 28.6710, "longitude": 77.5100, "capacity": 4, "status": "AVAILABLE", "speed": 20},
    {"unit_id": "FIRE-ENGINE-01", "type": "Fire Engine", "latitude": 28.6900, "longitude": 77.4800, "capacity": 6, "status": "AVAILABLE", "speed": 40}
]

DEFAULT_SHELTERS = [
    {"shelter_id": "SHELTER-01", "name": "AKGEC Community Shelter", "latitude": 28.6760, "longitude": 77.5010, "capacity": 150, "occupied": 42},
    {"shelter_id": "SHELTER-02", "name": "Raj Nagar Relief Hospital", "latitude": 28.6880, "longitude": 77.4480, "capacity": 200, "occupied": 95}
]

def load_data(file_path, default_value):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

incidents_db = load_data(INCIDENTS_FILE, [
    {
        "incident_id": "INC-0001",
        "reporter_name": "Sample Reporter",
        "description": "Flash flood water reaching 2nd floor near main market, 3 people trapped needing boat evacuation",
        "category": "Flood",
        "severity": 4.5,
        "latitude": 28.6752,
        "longitude": 77.5020,
        "image_url": None,
        "status": "QUEUED",
        "assigned_unit": None,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
])
units_db = load_data(UNITS_FILE, DEFAULT_UNITS)
shelters_db = load_data(SHELTERS_FILE, DEFAULT_SHELTERS)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# Haversine Distance Helper
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- ROUTES ---

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/admin")
def admin_page():
    return RedirectResponse(url="/static/admin.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 1. Citizen Incident Reporting (Supports Text + File Upload)
@app.post("/api/incidents/report")
async def report_incident_full(
    reporter_name: Optional[str] = Form("Anonymous"),
    reporter_phone: Optional[str] = Form(""),
    description: str = Form(...),
    category: Optional[str] = Form("General"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    file: Optional[UploadFile] = File(None)
):
    image_url = None
    if file:
        file_filename = f"{int(datetime.datetime.utcnow().timestamp())}_{file.filename}"
        file_path = os.path.join(UPLOADS_DIR, file_filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        image_url = f"/uploads/{file_filename}"

    # Natural Language Triage Rule Processing
    text_lower = description.lower()
    inferred_cat = category
    if "flood" in text_lower or "water" in text_lower or "submerged" in text_lower:
        inferred_cat = "Flood"
    elif "fire" in text_lower or "smoke" in text_lower or "blaze" in text_lower:
        inferred_cat = "Fire"
    elif "landslide" in text_lower or "mud" in text_lower:
        inferred_cat = "Landslide"
    elif "earthquake" in text_lower or "rubble" in text_lower or "collapse" in text_lower:
        inferred_cat = "Earthquake"
    elif "medical" in text_lower or "blood" in text_lower or "injury" in text_lower:
        inferred_cat = "Medical"

    # Severity Scoring Engine
    severity = 3.0
    if any(k in text_lower for k in ["trapped", "dying", "critical", "heavy", "fire", "submerged"]):
        severity = 4.5
    elif any(k in text_lower for k in ["minor", "waterlogging", "small"]):
        severity = 2.0

    # Spatial-Temporal Deduplication Check (100m radius)
    is_duplicate = False
    matched_id = None
    for inc in incidents_db:
        dist_km = haversine(latitude, longitude, inc["latitude"], inc["longitude"])
        if dist_km <= 0.100: # 100 meters
            is_duplicate = True
            matched_id = inc["incident_id"]
            inc["severity"] = min(5.0, inc["severity"] + 0.5)
            save_data(INCIDENTS_FILE, incidents_db)
            break

    if is_duplicate:
        await manager.broadcast({"event": "INCIDENT_UPDATED", "incident_id": matched_id})
        return {
            "status": "success",
            "incident_id": matched_id,
            "category": inferred_cat,
            "severity_level": 5.0,
            "is_duplicate": True,
            "message": "Merged with nearby existing incident report."
        }

    inc_id = f"INC-{len(incidents_db) + 1:04d}"
    new_inc = {
        "incident_id": inc_id,
        "reporter_name": reporter_name,
        "reporter_phone": reporter_phone,
        "description": description,
        "category": inferred_cat,
        "severity": severity,
        "latitude": latitude,
        "longitude": longitude,
        "image_url": image_url,
        "status": "QUEUED",
        "assigned_unit": None,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    incidents_db.append(new_inc)
    save_data(INCIDENTS_FILE, incidents_db)
    
    await manager.broadcast({"event": "INCIDENT_ADDED", "data": new_inc})

    return {
        "status": "success",
        "incident_id": inc_id,
        "category": inferred_cat,
        "severity_level": severity,
        "is_duplicate": False,
        "message": "Incident report logged and categorized by LifeLine AI."
    }

@app.get("/api/incidents")
def get_incidents():
    return {"incidents": incidents_db}

@app.get("/api/units")
def get_units():
    return {"units": units_db}

@app.get("/api/shelters")
def get_shelters():
    return {"shelters": shelters_db}

@app.get("/api/stats")
def get_stats():
    total = len(incidents_db)
    critical = sum(1 for i in incidents_db if i["severity"] >= 4.0)
    avail_units = sum(1 for u in units_db if u["status"] == "AVAILABLE")
    return {
        "total_incidents": total,
        "critical_incidents": critical,
        "available_units": avail_units,
        "active_shelters": len(shelters_db),
        "avg_response_time": 21.0
    }

# MILP Resource Dispatch Optimization Engine
class IncidentOpt(BaseModel):
    incident_id: str
    latitude: float
    longitude: float
    composite_severity: float

class UnitOpt(BaseModel):
    unit_id: str
    type: str
    latitude: float
    longitude: float
    capacity: int = 4
    avg_speed_kmh: float = 30.0

class OptRequest(BaseModel):
    unassigned_incidents: List[IncidentOpt]
    available_units: List[UnitOpt]

@app.post("/api/ml/optimize-dispatch")
async def optimize_dispatch_api(req: OptRequest):
    unassigned = [i for i in incidents_db if i["status"] != "DISPATCHED"]
    avail_units = [u for u in units_db if u["status"] == "AVAILABLE"]

    if not unassigned or not avail_units:
        return {"dispatch_plan": [], "message": "No unassigned incidents or available units."}

    n_inc = len(unassigned)
    n_units = len(avail_units)

    cost_vector = []
    for u_idx, u in enumerate(avail_units):
        for k_idx, k in enumerate(unassigned):
            dist_km = haversine(u["latitude"], u["longitude"], k["latitude"], k["longitude"])
            travel_time_mins = (dist_km / u.get("speed", 30.0)) * 60.0
            weighted_cost = travel_time_mins / max(0.1, k["severity"])
            cost_vector.append(weighted_cost)

    c = np.array(cost_vector)
    n_vars = len(c)
    integrality = np.ones(n_vars)

    A_rows = []
    b_upper = []
    b_lower = []

    # Constraint: Each unit assigned to at most 1 incident
    for u_idx in range(n_units):
        row = np.zeros(n_vars)
        for k_idx in range(n_inc):
            row[u_idx * n_inc + k_idx] = 1.0
        A_rows.append(row)
        b_lower.append(0.0)
        b_upper.append(1.0)

    constraints = LinearConstraint(np.array(A_rows), b_lower, b_upper)
    bounds = Bounds(0, 1)

    res = milp(c=c, integrality=integrality, constraints=constraints, bounds=bounds)

    dispatch_plan = []
    if res.success:
        x_sol = res.x
        for u_idx in range(n_units):
            for k_idx in range(n_inc):
                if x_sol[u_idx * n_inc + k_idx] > 0.5:
                    u = avail_units[u_idx]
                    k = unassigned[k_idx]
                    dist_km = haversine(u["latitude"], u["longitude"], k["latitude"], k["longitude"])
                    travel_time_mins = round((dist_km / u.get("speed", 30.0)) * 60.0, 1)

                    # Update internal DB
                    for inc in incidents_db:
                        if inc["incident_id"] == k["incident_id"]:
                            inc["status"] = "DISPATCHED"
                            inc["assigned_unit"] = u["unit_id"]

                    for unit in units_db:
                        if unit["unit_id"] == u["unit_id"]:
                            unit["status"] = "DISPATCHED"

                    dispatch_plan.append({
                        "unit_id": u["unit_id"],
                        "incident_id": k["incident_id"],
                        "estimated_travel_time_minutes": travel_time_mins,
                        "xai_explanation": f"{u['unit_id']} dispatched to {k['incident_id']}: Travel time {travel_time_mins} mins, severity Level {k['severity']} prioritized."
                    })

        save_data(INCIDENTS_FILE, incidents_db)
        save_data(UNITS_FILE, units_db)
        await manager.broadcast({"event": "OPTIMIZATION_COMPLETED", "plan": dispatch_plan})

    return {"dispatch_plan": dispatch_plan}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
