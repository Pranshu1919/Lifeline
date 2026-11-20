# 🌐 LifeLine Disaster Response System — Cloud Deployment Guide

This guide explains how to deploy the **LifeLine Multi-Modal Disaster Management System** online so that it can be accessed anywhere in the world using **one single public URL**.

---

## 📌 Architectural Overview: Single Link Architecture

With a single deployed link (e.g., `https://lifeline-disaster-response.onrender.com`), both portals operate securely and concurrently on the same backend and database:

| Public URL Path | Target Audience | Access Protection | Functionality |
| :--- | :--- | :--- | :--- |
| **`/`** | **General Citizens** | Public (No login) | Emergency SOS reporting, multi-photo/video upload, geolocation, and automatic AI triage. |
| **`/track`** | **General Citizens** | Public (Incident ID lookup) | Real-time rescue tracker showing assigned vehicle distance, ETA, and progress steps. |
| **`/admin`** | **Disaster Authorities Only** | **Encrypted Passkey Gate** (`lifeline@2026`) | Live tactical incident feed, heatmaps, resource analytics, and one-click dispatch triggers. |
| **`/incident`** | **Rescue Commanders** | Authorized Session | Nearest emergency station locator (Haversine formula), MILP vehicle dispatch, and live status updates. |
| **`/ws`** | **WebSocket Engine** | Full-duplex Socket | Real-time bi-directional synchronization between Citizen reports and Authority screens. |

---

## 🚀 Option 1: Render.com (Recommended Free PaaS Deployment)

Render allows you to host Docker containers for free directly linked to your GitHub repository.

### Step 1: Push Your Code to GitHub
Ensure the latest code is on GitHub repository `https://github.com/Pranshu1919/Lifeline.git` on branch `main`.

### Step 2: Sign In to Render
1. Visit [render.com](https://render.com) and create a free account or sign in with your GitHub account.

### Step 3: Create a New Web Service
1. In the Render Dashboard, click **New +** and select **Web Service**.
2. Select **Build and deploy from a Git repository**.
3. Connect your GitHub account and choose `Pranshu1919/Lifeline`.
4. Configure the service settings:
   - **Name**: `lifeline-disaster-response` (or any custom name)
   - **Region**: `Singapore` or `Frankfurt` (choose the closest to your location)
   - **Branch**: `main`
   - **Runtime**: `Docker` (Render will automatically detect our `Dockerfile`)
   - **Instance Type**: `Free`
5. Under **Environment Variables**, verify or add:
   - `PORT`: `8000`
   - `NODE_ENV`: `production`
   - `ML_HOST`: `127.0.0.1`
   - `ML_PORT`: `5000`
6. Click **Deploy Web Service**.

### Step 4: Access Your Live System
Render will build the Docker image, initialize the SQLite schema, start the Python ML microservice, and launch the Node.js server.
Your live public link will be generated:
- **Citizen Portal**: `https://lifeline-disaster-response.onrender.com/`
- **Citizen Tracker**: `https://lifeline-disaster-response.onrender.com/track`
- **Authority Command Center**: `https://lifeline-disaster-response.onrender.com/admin`
  - *Badge ID*: `COMMANDER-01` or `admin`
  - *Passkey*: `lifeline@2026`

---

## ⚡ Option 2: Railway.app (Fast 1-Click Deployment)

Railway provides 500 hours / $5 free trial credits with fast builds and persistent disk support.

### Steps:
1. Visit [railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select `Pranshu1919/Lifeline`.
4. Railway will detect the `Dockerfile` and start building automatically.
5. In **Settings** $\rightarrow$ **Networking**, click **Generate Domain**.
6. Railway will give you a live domain like `https://lifeline-production.up.railway.app`.

---

## 🌐 Option 3: Instant Live Demo via Cloudflare Tunnel (Zero-Cloud Setup, 30 Seconds)

If you want to immediately showcase the project right now from your laptop to anyone's phone or desktop anywhere in the world without creating cloud accounts:

1. In PowerShell, run:
   ```powershell
   npx cloudflared tunnel --url http://localhost:8000
   ```
2. Cloudflare will output a public HTTPS URL (e.g., `https://random-words-1234.trycloudflare.com`).
3. Anyone in the world can open that link on their mobile phone or PC to test the citizen portal or admin command center in real-time.

---

## 🔒 Security & Data Integrity Features

1. **Role-Based Isolation**:
   - The Citizen Portal (`/`) contains zero navigation or visual links to the Command Center.
   - The Authority Command Center (`/admin`) is blocked by an encrypted modal barrier. Access is rejected without valid credentials.
2. **Shared Enterprise Database**:
   - SQLite `lifeline_enterprise.db` is shared across all processes.
   - When a citizen files an emergency report from their smartphone, the Node.js backend processes it, invokes the Python ML microservice on localhost:5000 for CrisisMMD triage, stores it in SQLite, and pushes a real-time WebSocket broadcast to all active `/admin` screens within milliseconds.
3. **Nearest-Station Resource Dispatch**:
   - Rescue dispatches calculate real Haversine distances to Police, Fire, and Medical stations, ensuring vehicles are dispatched from the closest depot.
