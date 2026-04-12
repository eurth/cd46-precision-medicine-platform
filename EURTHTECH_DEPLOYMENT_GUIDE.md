# EurthTech — Coolify Deployment Guide

> **Purpose:** A reusable, step-by-step playbook for deploying any Python/web service from a private GitHub repository to the EurthTech Coolify server as a subdomain of `eurthtech.com`. Written from live deployment experience with PondWatch.

---

## Table of Contents

1. [Infrastructure Overview](#1-infrastructure-overview)
2. [Prerequisites Checklist](#2-prerequisites-checklist)
3. [Repository Setup](#3-repository-setup)
4. [Dockerfile Requirements](#4-dockerfile-requirements)
5. [Coolify Application Setup](#5-coolify-application-setup)
6. [DNS Configuration (Wix)](#6-dns-configuration-wix)
7. [SSL / HTTPS](#7-ssl--https)
8. [Environment Variables & Secrets](#8-environment-variables--secrets)
9. [Persistent Storage (Volumes)](#9-persistent-storage-volumes)
10. [Auto-Deploy on Push](#10-auto-deploy-on-push)
11. [First-Boot / Database Seeding](#11-first-boot--database-seeding)
12. [Deployment Verification](#12-deployment-verification)
13. [Troubleshooting](#13-troubleshooting)
14. [SSH Quick Reference](#14-ssh-quick-reference)
15. [Service Registry](#15-service-registry)

---

## 1. Infrastructure Overview

| Component | Details |
|-----------|---------|
| **Server** | Linode VPS — `172.236.176.222` |
| **OS** | Ubuntu 22.04 LTS |
| **Docker** | 29.4.x (managed by Coolify) |
| **Coolify** | v4.0.0-beta.472 — self-hosted PaaS |
| **Coolify UI** | `http://172.236.176.222:8000` |
| **Reverse proxy** | Traefik (bundled with Coolify, auto-manages routing + TLS) |
| **DNS provider** | Wix (eurthtech.com domain) |
| **SSL** | Let's Encrypt via Traefik — free, auto-renewed |
| **SSH user** | `eurth` |
| **SSH key** | `C:\Users\GuestUser\.ssh\eurthtech_key` (passphrase-protected) |
| **SSH alias** | `eurthtech` (configured in `~/.ssh/config`) |

### How it fits together

```
GitHub repo (main branch)
        │  push
        ▼
  Coolify detects push via GitHub App webhook
        │  build
        ▼
  Docker image built on server from Dockerfile
        │  run
        ▼
  Container on Docker network
        │  port (e.g., 8503)
        ▼
  Traefik reverse proxy  ←── Let's Encrypt SSL
        │  HTTPS
        ▼
  yourservice.eurthtech.com
```

---

## 2. Prerequisites Checklist

Before starting a new service deployment, verify all of these are in place:

- [ ] **GitHub App connected to Coolify** — already done for `eurth` org/user. New repos under the same account are automatically accessible. If you add a new GitHub organisation, re-authorise under Coolify → Settings → Source → GitHub App.
- [ ] **SSH config entry** — `eurthtech` alias exists in `~/.ssh/config` (see [§14](#14-ssh-quick-reference)).
- [ ] **Sudoers rule** — `eurth` has passwordless sudo: `/etc/sudoers.d/90-coolify` already deployed.
- [ ] **Traefik on ports 80 + 443** — confirm with `ssh eurthtech "sudo ss -tlnp | grep -E '80|443'"`.
- [ ] **DNS A record** — subdomain pointing to `172.236.176.222` must be added before Let's Encrypt can issue a cert.

---

## 3. Repository Setup

### 3.1 Required files at repo root

| File | Purpose |
|------|---------|
| `Dockerfile` | Build instructions — **required** |
| `.dockerignore` | Exclude `.git`, `__pycache__`, `.env`, large artefacts |
| `coolify.env.example` | Document every env var the service needs (safe to commit) |
| `README.md` | High-level description + quick-start |

### 3.2 `.dockerignore` template

```dockerignore
.git
.gitignore
__pycache__
*.pyc
*.pyo
.env
.env.*
!coolify.env.example
data/
*.duckdb
*.db
.vscode/
tests/
docs/
*.md
*.docx
*.pptx
```

> **Why exclude `data/`?** Runtime data lives on a Docker volume mounted at deploy time. Never bake DB files or generated data into the image — they bloat it and get wiped on each rebuild anyway.

### 3.3 `coolify.env.example` template

Create this file and document every secret/config the app needs. Operators paste real values directly into the Coolify UI — they never commit a filled-in `.env`.

```dotenv
# ── External API Credentials ──────────────────────────────────────────────────
SOME_API_KEY=your-key-here
SOME_API_SECRET=your-secret-here

# ── App Config ────────────────────────────────────────────────────────────────
APP_PORT=8000
ENVIRONMENT=production
```

---

## 4. Dockerfile Requirements

### 4.1 Minimal working Dockerfile (Python / Streamlit pattern)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (GDAL, gcc, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgdal-dev gdal-bin gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create runtime directories (will be overlay by volume mount)
RUN mkdir -p data/

EXPOSE 8503

CMD ["python", "-m", "streamlit", "run", "dashboard/app.py", \
     "--server.port", "8503", \
     "--server.address", "0.0.0.0", \
     "--server.headless", "true", \
     "--server.fileWatcherType", "none"]
```

### 4.2 Dockerfile rules

| Rule | Reason |
|------|--------|
| Always `--server.address 0.0.0.0` (Streamlit) | Container IP alone won't be reachable from Traefik |
| Always `--server.headless true` (Streamlit) | Prevents "open browser" prompts that stall startup |
| `EXPOSE` must match Coolify port field | Traefik routes to this port |
| `RUN mkdir -p data/` before volume mount | Docker will still mount the volume; this is belt-and-braces |
| System deps before Python deps | Avoids broken pip installs for native extensions |
| `rm -rf /var/lib/apt/lists/*` after apt | Keeps image lean |

### 4.3 Non-Streamlit services

For FastAPI/Flask/Node services, swap the `CMD` accordingly:

```dockerfile
# FastAPI example
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Node example
CMD ["node", "server.js"]
```

---

## 5. Coolify Application Setup

### 5.1 Create a new Application

1. Open Coolify: `http://172.236.176.222:8000`
2. Navigate to your **Project** (or create a new one: `+ New Project`)
3. Click **+ New Resource** → **Application**
4. Source: **GitHub** → select the repository → select branch `main`

### 5.2 Build Configuration

| Field | Value |
|-------|-------|
| **Build Pack** | `Dockerfile` |
| **Dockerfile path** | `Dockerfile` (default) |
| **Build context** | `/` (repo root) |
| **Port** | Match your `EXPOSE` value (e.g., `8503`) |

> If you leave Build Pack as "Nixpacks", Coolify will try to auto-detect — this often fails for complex Python apps with native deps. Always set it explicitly to `Dockerfile`.

### 5.3 Domain

Set the domain under **Domains** tab:

```
https://yourservice.eurthtech.com
```

Use `https://` from the start — Coolify + Traefik will handle cert issuance automatically once the A record is in place.

### 5.4 Environment Variables

Navigate to **Environment Variables** tab. Add each key-value pair from `coolify.env.example`. Mark sensitive values as **Secret** (they will be masked in logs).

> **Do not paste the entire `.env` file.** Add each variable individually so they are stored securely in Coolify's vault, not as plaintext files.

### 5.5 Volumes (Persistent Storage)

Navigate to **Storages** tab → **+ Add Volume**:

| Field | Value |
|-------|-------|
| **Source path (host)** | `/data/yourservice-data` |
| **Destination path (container)** | `/app/data` |

This ensures the database, uploaded files, and any generated artefacts survive container rebuilds and redeploys.

**First-time note:** Create the host directory before the first deploy:

```bash
ssh eurthtech "sudo mkdir -p /data/yourservice-data && sudo chown -R 1000:1000 /data/yourservice-data"
```

### 5.6 Save and Deploy

1. Click **Save** on each settings page
2. Click **Deploy** (or just push to `main` if auto-deploy is already configured)
3. Watch the **Deployments** tab for build logs

---

## 6. DNS Configuration (Wix)

1. Log in to **Wix** → Domains → Manage `eurthtech.com`
2. Go to **DNS Records**
3. Add an **A Record**:

| Field | Value |
|-------|-------|
| **Type** | `A` |
| **Host / Subdomain** | `yourservice` |
| **Points to** | `172.236.176.222` |
| **TTL** | `1 hour` (or lowest available) |

4. Save

> **Propagation time:** Usually 1–10 minutes on Wix. Let's Encrypt cert issuance requires the A record to resolve correctly before it will succeed. If the first deploy fails on TLS, wait 5 minutes and redeploy.

### Verify DNS resolution

```powershell
# From local machine (PowerShell)
Resolve-DnsName yourservice.eurthtech.com
# Should return: 172.236.176.222

# Or
nslookup yourservice.eurthtech.com 8.8.8.8
```

---

## 7. SSL / HTTPS

Coolify + Traefik handle TLS automatically via Let's Encrypt. To enable:

1. In Coolify application → **Configuration** tab
2. Set domain to `https://yourservice.eurthtech.com` (must include `https://`)
3. Enable the **Let's Encrypt** toggle
4. Click **Save** → **Redeploy**

Traefik will:
- Obtain a cert from Let's Encrypt (ACME HTTP-01 challenge on port 80)
- Auto-renew before expiry
- Force HTTP → HTTPS redirect on all incoming requests

### Verify TLS is live

```bash
# From server
ssh eurthtech "sudo ss -tlnp | grep 443"
# Should show Traefik on 0.0.0.0:443

# From local machine
curl -I https://yourservice.eurthtech.com
# Should return HTTP/2 200
```

---

## 8. Environment Variables & Secrets

### The two-file pattern

| File | Committed? | Purpose |
|------|-----------|---------|
| `.env` | **NO** — in `.gitignore` | Local development only |
| `coolify.env.example` | **YES** | Documents all required variables (no real values) |

### How the app reads env vars

In Python, use `os.getenv()` with safe defaults:

```python
import os

API_KEY = os.getenv("MY_API_KEY", "")
DEBUG   = os.getenv("DEBUG", "false").lower() == "true"
```

Never hardcode credentials. Never call `os.environ["KEY"]` without a fallback unless the key is truly mandatory at startup (in which case fail fast with a clear error message).

### Adding secrets to Coolify

1. Coolify → Application → **Environment Variables**
2. Click **+ Add Variable**
3. Enter `KEY` and `VALUE`
4. Toggle **Is Secret** to mask the value in build logs
5. **Save** → redeploy is required for new env vars to take effect

> Variables set in Coolify are injected at container runtime as real OS environment variables — no `.env` file is written to disk on the server.

---

## 9. Persistent Storage (Volumes)

### When to use volumes

Use a volume mount for any data that must survive a redeploy:

- Databases (DuckDB, SQLite)
- User-uploaded files
- Generated reports / caches
- ML model weights downloaded at runtime

### Volume naming convention

```
/data/{service-name}-data   →   /app/data
```

Examples:
- `/data/pondwatch-data` → `/app/data`
- `/data/cropwatch-data` → `/app/data`
- `/data/floodwatch-data` → `/app/data`

### Pre-create host directories

```bash
ssh eurthtech "sudo mkdir -p /data/{service-name}-data"
```

Coolify will create the directory if it doesn't exist, but explicit pre-creation avoids permission issues on first boot.

### Viewing volume contents

```bash
ssh eurthtech "sudo ls -lah /data/{service-name}-data/"
```

### Wiping volume data (reset to fresh state)

```bash
# WARNING: destructive — deletes all persisted data
ssh eurthtech "sudo rm -rf /data/{service-name}-data/*"
```

---

## 10. Auto-Deploy on Push

Coolify uses a **GitHub App webhook** to detect pushes. After initial setup:

- Every `git push origin main` triggers an automatic build and redeploy
- Typical build time: **2–4 minutes** for a Python app with native deps
- Check progress: Coolify UI → Application → **Deployments** tab

### Deploy manually

If auto-deploy doesn't trigger (e.g., webhook missed):

1. Coolify UI → Application → click **Deploy** button, or
2. `ssh eurthtech "sudo docker ps"` — verify the container is running

### Rollback to previous version

Coolify keeps a deploy history. Click any previous deployment entry → **Rollback**.

---

## 11. First-Boot / Database Seeding

For services that use a database, the volume starts **empty** on first deploy. The app must seed it gracefully.

### Recommended pattern: `seed_cloud.py`

Create a `seed_cloud.py` at repo root with an `ensure_db()` function:

```python
"""seed_cloud.py — Bootstrap DB on first container start."""
import subprocess
import sys
from pathlib import Path

_DB_PATH = Path(__file__).parent / "data" / "myapp.duckdb"
_SEED_SCRIPT = Path(__file__).parent / "seed_data.py"
_MIN_BYTES = 100_000  # < 100 KB → treat as missing/corrupt


def ensure_db() -> None:
    """Seed the database if it is absent, too small, or has empty tables."""
    if _DB_PATH.exists() and _DB_PATH.stat().st_size >= _MIN_BYTES:
        try:
            import duckdb
            con = duckdb.connect(str(_DB_PATH))
            count = con.execute("SELECT COUNT(*) FROM my_main_table").fetchone()[0]
            con.close()
            if count > 0:
                return  # DB is healthy
        except Exception:
            pass  # Table missing or corrupt — fall through

    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(_SEED_SCRIPT)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Seeding failed:\n{result.stderr or result.stdout}")
```

Call `ensure_db()` at the top of your Streamlit `app.py` entry point:

```python
from seed_cloud import ensure_db
ensure_db()
```

### Why file-size check alone is insufficient

An empty/schema-only DB file can be ≥ 100 KB. Always follow up with a row-count query on a key table to confirm data actually exists.

---

## 12. Deployment Verification

After each deploy, run this checklist:

```bash
# 1. Container is running
ssh eurthtech "sudo docker ps | grep yourservice"

# 2. App logs look healthy (no Python tracebacks)
ssh eurthtech "sudo docker logs \$(sudo docker ps -qf name=yourservice) --tail 50"

# 3. DNS resolves correctly
nslookup yourservice.eurthtech.com 8.8.8.8

# 4. HTTPS responds
curl -I https://yourservice.eurthtech.com

# 5. App loads in browser (hard-refresh: Ctrl+Shift+R)
# Navigate to https://yourservice.eurthtech.com
```

---

## 13. Troubleshooting

### Build fails: package install error

Check build logs in Coolify. Common fixes:

| Symptom | Fix |
|---------|-----|
| `gcc: not found` | Add `gcc g++` to `apt-get install` in Dockerfile |
| `gdal-config: not found` | Add `libgdal-dev gdal-bin` to Dockerfile |
| `pip install` timeout | Add `--timeout 120` to pip install line |
| `requirements.txt not found` | Ensure file is at repo root and not in `.dockerignore` |

### App starts but shows blank page

```bash
ssh eurthtech "sudo docker logs \$(sudo docker ps -qf name=yourservice) --tail 100"
```

Common causes:
- Missing env var → add it in Coolify → redeploy
- DB seeding failed → check `seed_data.py` imports
- Port mismatch → verify `EXPOSE` in Dockerfile matches Coolify port field

### HTTPS certificate not issued

- Confirm A record resolves to `172.236.176.222`
- Confirm Traefik is listening on port 443: `ssh eurthtech "sudo ss -tlnp | grep 443"`
- In Coolify: ensure domain starts with `https://` and Let's Encrypt toggle is **on**
- After DNS propagation, click **Redeploy** — Traefik will retry ACME challenge

### 0 rows / empty data on first boot

- Volume was empty on first start
- `ensure_db()` check failed silently
- SSH in and check: `ssh eurthtech "sudo ls -lah /data/{service-name}-data/"`
- Manually trigger seed: `ssh eurthtech "sudo docker exec -it CONTAINER_ID python seed_data.py"`

### Port conflict

```bash
ssh eurthtech "sudo ss -tlnp | grep PORT_NUMBER"
# If occupied, change the port in Dockerfile EXPOSE + Coolify port field
```

### Auto-deploy not triggering

Check GitHub → repo Settings → Webhooks → recent deliveries. If the webhook URL shows Coolify's IP, confirm port 8000 is reachable:
```bash
# From GitHub's servers, they POST to http://172.236.176.222:8000/...
# Port 8000 must be open on the server firewall
ssh eurthtech "sudo ufw status"
```

---

## 14. SSH Quick Reference

### `~/.ssh/config` entry (already configured)

```sshconfig
Host eurthtech
    HostName 172.236.176.222
    User eurth
    IdentityFile C:/Users/GuestUser/.ssh/eurthtech_key
    ServerAliveInterval 60
```

### Common SSH commands

```bash
# Connect interactively
ssh eurthtech

# Check all running containers
ssh eurthtech "sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Tail logs for a service
ssh eurthtech "sudo docker logs \$(sudo docker ps -qf name=PARTIAL_NAME) --tail 100 -f"

# Exec into a running container
ssh eurthtech "sudo docker exec -it CONTAINER_ID bash"

# Check disk space
ssh eurthtech "df -h"

# Check server RAM
ssh eurthtech "free -h"

# Check all open ports
ssh eurthtech "sudo ss -tlnp"

# Restart a container (force redeploy from Coolify instead when possible)
ssh eurthtech "sudo docker restart CONTAINER_ID"
```

---

## 15. Service Registry

Track all deployed services here so there are no port conflicts or subdomain clashes.

| Service | Subdomain | Internal Port | Volume | Status |
|---------|-----------|--------------|--------|--------|
| **PondWatch** | `pondwatch.eurthtech.com` | `8503` | `/data/pondwatch-data` | ✅ LIVE |
| **OncoBridge Intelligence** | `oncobridge.eurthtech.com` | `8504` | `/data/oncobridge-data` | 🔧 DEPLOY READY |
| *(next service)* | `*.eurthtech.com` | `8505+` | `/data/*-data` | — |

### Port assignment rule

Start new services at port `8504` and increment by 1 for each additional service. Ports `80`, `443`, `8000`, `8080`, and `8503` are taken.

---

## Appendix A: Deployment Checklist (copy-paste for each new service)

```
## Deployment Checklist — {Service Name}

### Repository
- [ ] Dockerfile at repo root
- [ ] .dockerignore created
- [ ] coolify.env.example documenting all secrets
- [ ] Port chosen and confirmed free (see service registry)

### Coolify
- [ ] New application created
- [ ] Build pack set to Dockerfile
- [ ] Port set to match EXPOSE
- [ ] Domain set to https://{name}.eurthtech.com
- [ ] Let's Encrypt toggle ON
- [ ] Environment variables added (mark sensitive ones as Secret)
- [ ] Volume configured: /data/{name}-data → /app/data

### DNS (Wix)
- [ ] A record: {name} → 172.236.176.222
- [ ] Verified with nslookup

### First Deploy
- [ ] Click Deploy, watch build logs
- [ ] Confirm container is running (docker ps)
- [ ] HTTPS cert issued (curl -I https://{name}.eurthtech.com)
- [ ] App loads in browser, data seeded correctly
- [ ] Update service registry table above
```

---

## Appendix B: File Structure Convention

For consistency across EurthTech services, follow this project layout:

```
myservice/
├── Dockerfile
├── .dockerignore
├── .gitignore              # includes .env, data/, __pycache__/
├── coolify.env.example     # documents all required env vars
├── requirements.txt
├── README.md
│
├── dashboard/              # Streamlit UI (or api/ for FastAPI, etc.)
│   └── app.py              # entry point
│
├── pipeline/               # data ingestion / processing
├── analytics/              # scoring / analytics
├── tests/
├── docs/
│
├── seed_data.py            # seeds demo/initial data
├── seed_cloud.py           # ensure_db() for first-boot seeding
├── run_pipeline.py         # production pipeline entry point
├── run_analytics.py        # analytics/scoring entry point
│
└── data/                   # .gitignored — mounted as Docker volume
    └── myservice.duckdb
```

---

*Last updated: April 2026 — based on live PondWatch deployment at `https://pondwatch.eurthtech.com`*
