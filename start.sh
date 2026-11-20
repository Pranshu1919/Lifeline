#!/bin/bash
set -e

echo "===================================================="
echo "🚀 [LifeLine] Initializing SQLite Enterprise Database..."
echo "===================================================="
node db_setup.js

echo "===================================================="
echo "🤖 [LifeLine] Starting Python ML Microservice (Port 5000)..."
echo "===================================================="
python3 ml_service.py &
ML_PID=$!

# Wait briefly for PyTorch and NLP models to serialize into memory
sleep 4

echo "===================================================="
echo "🌐 [LifeLine] Starting Unified Node.js Server on port ${PORT:-8000}..."
echo "📍 Citizen Portal:       http://0.0.0.0:${PORT:-8000}/"
echo "📍 Citizen Tracker:      http://0.0.0.0:${PORT:-8000}/track"
echo "📍 Command Center:       http://0.0.0.0:${PORT:-8000}/admin"
echo "📍 Incident Dispatch:    http://0.0.0.0:${PORT:-8000}/incident"
echo "===================================================="
exec node server.js
