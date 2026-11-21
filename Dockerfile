# LifeLine Production Container: Unified Node.js + Python ML Architecture
FROM node:20-bookworm-slim

# Install Python 3, pip, and essential C/C++ build tools for native SQLite compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Node.js dependencies and compile sqlite3 natively from source
COPY package*.json ./
RUN npm install --omit=dev --build-from-source

# 2. Install Python dependencies (CPU-optimized PyTorch to minimize image size)
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --break-system-packages \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# 3. Copy project files, pre-trained models, and assets
COPY . .

# 4. Set executable permissions for start script
RUN chmod +x start.sh

# 5. Environment configuration
ENV PORT=8000
ENV ML_HOST=127.0.0.1
ENV ML_PORT=5000
ENV NODE_ENV=production

# 6. Expose the public web port
EXPOSE 8000

# 7. Start both services
CMD ["./start.sh"]
