FROM python:3.13-slim

WORKDIR /app

# System dependencies — gcc needed for some Python native extensions (scipy, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverages Docker layer cache)
COPY requirements-docker.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --timeout 300 -r requirements-docker.txt \
    && pip cache purge \
    && find /usr/local/lib/python3.13 -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

# Copy application code
COPY . .

# Create data directories — will be overlaid by Coolify volume mount at runtime
RUN mkdir -p data/processed data/raw data/genie data/logs

# Port 8504 — next free port in EurthTech service registry (8503 = PondWatch)
EXPOSE 8504

CMD ["python", "-m", "streamlit", "run", "app/streamlit_app.py", \
     "--server.port", "8504", \
     "--server.address", "0.0.0.0", \
     "--server.headless", "true", \
     "--server.fileWatcherType", "none"]
