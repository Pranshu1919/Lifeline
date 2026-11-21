# LifeLine: Smart Disaster Response & Resource Allocation System

LifeLine is an enterprise-grade AI-powered disaster management platform designed for sub-second emergency intake, multi-modal crisis triage, offline PWA resilience, and real-time resource allocation.

---

## 🌟 Architecture & Key Features

* 🌐 **Unified Enterprise Web Server (`PORT: 8000`)**:
  * **Citizen Disaster Reporting Portal (`/`)**: High-contrast Light Mode emergency reporting, multi-photo/video camera capture, high-accuracy GPS, and instant AI triage.
  * **Citizen Rescue Tracker (`/track`)**: Public tracking portal displaying live assigned vehicle distance, route map, and ETA.
  * **Authority Command Center (`/admin`)**: Passkey-protected tactical operations center (`Badge: COMMANDER-01` or `admin`, `Passkey: lifeline@2026`) with live WebSocket incidents feed and interactive heatmaps.
  * **Emergency Dispatch Optimizer (`/incident`)**: Automated Haversine nearest-depot station locator and MILP vehicle allocation engine.
* 🤖 **Multi-Modal AI & Computer Vision Microservice (`PORT: 5000`)**:
  * **CrisisMMD NLP Triage**: 8-class humanitarian urgency classifier (84.05% Accuracy, F1: 0.8361).
  * **PyTorch MobileNetV3 Image Authenticity Model**: Detects real vs. fake/off-topic photos (79.86% Accuracy).
  * **PyTorch MobileNetV3 Visual Damage Model**: Scores structural damage severity (Severe, Mild, Little/None).
  * **SciPy MILP Resource Dispatch Engine**: Sub-10ms global mathematically optimal vehicle-to-incident allocation.
* 📡 **Zero-Network Offline PWA**: Local IndexedDB queueing with auto-sync when network returns.
* 💾 **Shared SQLite Enterprise Database**: Real-time bi-directional data flow between citizen distress reports and official authority response.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Node.js**: v18+
* **Python**: v3.9+

---

### 2. Install Dependencies

#### Node.js Backend Dependencies:
```bash
npm install
```

#### Python AI/ML Microservice Dependencies:
```bash
pip install -r requirements.txt
```

---

### 3. Initialize SQLite Database
Initialize the database tables and seed emergency stations, rescue vehicles, and shelters:
```bash
node db_setup.js
```

---

### 4. Running the Microservices

#### Step A: Start Python ML Microservice (Port 5000)
```bash
python ml_service.py
```

#### Step B: Start Unified Enterprise Server (Port 8000)
```bash
node server.js
```

---

## 🌐 Accessing the Platform

* 🌐 **Citizen Reporting Portal**: [http://localhost:8000/](http://localhost:8000/)
* 📍 **Citizen Rescue Tracker**: [http://localhost:8000/track](http://localhost:8000/track)
* 🛡️ **Authority Command Center**: [http://localhost:8000/admin](http://localhost:8000/admin) *(Passkey: `lifeline@2026`)*
* 📍 **Incident Dispatch**: [http://localhost:8000/incident](http://localhost:8000/incident)

---

## ☁️ Cloud Deployment

LifeLine is fully containerized with a production [`Dockerfile`](./Dockerfile) and pre-configured for 1-click cloud deployment on Render.com or Railway.
Refer to [**DEPLOYMENT_GUIDE.md**](./DEPLOYMENT_GUIDE.md) for complete cloud setup instructions.

---

## 👥 Project Team & Credits

* **Vijay Katiyar** (2300270130205) – ML Engineer (NLP Triage, Urgency Scoring & Vision Models)
* **Priyanshu Kushwaha** (2300270130136) – ML & Optimization Engineer (Spatial Distance & MILP Solver)
* **Pranshu** (2300270130129) – Full-Stack Developer (Web App, GIS Maps, Express & WebSocket Backend)
* **Project Guide**: Dr. Sunil Kumar (Professor, Department of Computer Science & Engineering, AKGEC)
