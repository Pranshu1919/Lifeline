# LifeLine: Smart Disaster Response & Resource Allocation System

LifeLine is an enterprise-grade AI-powered disaster management platform designed for sub-second emergency intake, multi-modal crisis triage, offline PWA resilience, and real-time resource allocation.

---

## 🌟 Architecture & Key Features

* 🌐 **Dual Independent Portals**:
  * **Citizen Disaster Reporting Portal (`http://localhost:8000`)**: Emergency reporting, camera photo/video capture, high-accuracy GPS, and citizen rescue tracker (`/track`).
  * **Authority Command Center (`http://localhost:8001`)**: Real-time severity dashboard (`/`), incident detail view (`/incident`), and human commander manual resource allocation override.
* 🤖 **Multi-Modal AI & Computer Vision Microservice (`http://127.0.0.1:5000`)**:
  * **CrisisMMD NLP Triage**: 8-class humanitarian urgency classifier (81.09% Accuracy).
  * **PyTorch MobileNetV3 Image Authenticity Model**: Detects real vs. fake/off-topic photos (80.87% Validation Accuracy).
  * **PyTorch MobileNetV3 Visual Damage Model**: Scores structural damage severity ($0.20 \to 0.95$).
  * **SciPy MILP Resource Dispatch Engine**: Sub-50ms optimal vehicle-to-incident allocation.
* 📡 **Zero-Network Offline PWA**: Local IndexedDB queueing with auto-sync when network returns.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Node.js**: v16+
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
Initialize the database tables and seed rescue vehicles and shelters:
```bash
node db_setup.js
```

---

### 4. Running the Microservices

#### Step A: Start Python ML Microservice (Port 5000)
```bash
python ml_service.py
```

#### Step B: Start Citizen Disaster Reporting Portal (Port 8000)
```bash
node citizen_server.js
```

#### Step C: Start Authority Command Center (Port 8001)
```bash
node admin_server.js
```

---

## 🌐 Accessing the Platform

* 🌐 **Citizen Reporting Portal**: [http://localhost:8000/](http://localhost:8000/)
* 📍 **Citizen Rescue Tracker**: [http://localhost:8000/track](http://localhost:8000/track)
* 🛡️ **Authority Command Center**: [http://localhost:8001/](http://localhost:8001/)
* 📍 **Authority Rescue Tracker**: [http://localhost:8001/track](http://localhost:8001/track)

---

## 🧠 Training Machine Learning Models (Optional)

To re-train the models on the CrisisMMD v2.0 dataset:

1. **Train NLP Text Classification Pipeline**:
   ```bash
   python train_crisismmd_model.py
   ```
2. **Train PyTorch Vision Models**:
   ```bash
   python train_crisismmd_vision.py
   ```

---

## 👥 Project Team & Credits

* **Vijay Katiyar** (2300270130205) – ML Engineer 1 (NLP, Deduplication, Urgency Rating)
* **Priyanshu Kushwaha** (2300270130136) – ML Engineer 2 (Computer Vision, Spatial Optimization)
* **Pranshu** (2300270130129) – Full-Stack Developer (Web App, GIS Maps, Express Backend)
* **Guide**: Dr. Suneel Kumar (Professor, Dept. of IT, Ajay Kumar Garg Engineering College, Ghaziabad)
