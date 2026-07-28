"""
Create a Neo4j Aura Free instance via Aura API and print URI + password once.

Requires in .env (from Aura Console → Account details → API credentials):
  AURA_CLIENT_ID
  AURA_CLIENT_SECRET
  AURA_TENANT_ID   # optional — defaults to first tenant / EurthTech project

Usage:
  python scripts/create_aura_instance.py
  python scripts/create_aura_instance.py --update-env   # write NEO4J_* into .env
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

API = "https://api.neo4j.io/v1"
OAUTH = "https://api.neo4j.io/oauth/token"
# Fallback tenant — create script prefers GET /tenants (first project)
DEFAULT_TENANT = "2a7764af-08bb-4fcc-aeab-396b2e27aa1a"


def get_token(client_id: str, client_secret: str) -> str:
    r = requests.post(
        OAUTH,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def list_tenants(token: str) -> list[dict]:
    r = requests.get(
        f"{API}/tenants",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def list_instances(token: str, tenant_id: str | None = None) -> list[dict]:
    params = {"tenantId": tenant_id} if tenant_id else {}
    r = requests.get(
        f"{API}/instances",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params=params,
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def create_free(token: str, tenant_id: str, name: str = "oncobridge-cd46") -> dict:
    # Free tier: type free-db, fixed 1GB — memory is required by current Aura API
    body = {
        "name": name,
        "type": "free-db",
        "tenant_id": tenant_id,
        "region": "europe-west1",
        "cloud_provider": "gcp",
        "version": "5",
        "memory": "1GB",
    }
    r = requests.post(
        f"{API}/instances",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=120,
    )
    if r.status_code >= 400:
        # Retry common Free-region variants
        print(f"Create failed ({r.status_code}): {r.text[:500]}")
        for region, cloud in (
            ("us-central1", "gcp"),
            ("us-east-1", "aws"),
            ("eastus", "azure"),
        ):
            body["region"] = region
            body["cloud_provider"] = cloud
            r = requests.post(
                f"{API}/instances",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=120,
            )
            if r.status_code < 400:
                break
            print(f"  retry {cloud}/{region} → {r.status_code}: {r.text[:300]}")
        r.raise_for_status()
    return r.json().get("data", r.json())


def wait_running(token: str, instance_id: str, timeout_s: int = 600) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        r = requests.get(
            f"{API}/instances/{instance_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json().get("data", r.json())
        status = data.get("status", "")
        print(f"  status={status}")
        if status.lower() == "running":
            return data
        time.sleep(15)
    raise TimeoutError(f"Instance {instance_id} not running within {timeout_s}s")


def write_env(uri: str, password: str, username: str = "neo4j") -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        env_path.write_text("", encoding="utf-8")
    set_key(str(env_path), "NEO4J_URI", uri)
    set_key(str(env_path), "NEO4J_USERNAME", username)
    set_key(str(env_path), "NEO4J_PASSWORD", password)
    print(f"Wrote NEO4J_* to {env_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-env", action="store_true")
    parser.add_argument("--name", default="oncobridge-cd46")
    args = parser.parse_args()

    client_id = os.getenv("AURA_CLIENT_ID", "").strip()
    client_secret = os.getenv("AURA_CLIENT_SECRET", "").strip()
    tenant_id = os.getenv("AURA_TENANT_ID", DEFAULT_TENANT).strip()

    if not client_id or not client_secret:
        print(
            "Missing AURA_CLIENT_ID / AURA_CLIENT_SECRET in .env\n"
            "Create them: Aura Console → profile → Account details → API credentials → Create\n"
            "Then re-run: python scripts/create_aura_instance.py --update-env"
        )
        return 2

    print("Fetching Aura bearer token...")
    token = get_token(client_id, client_secret)
    tenants = list_tenants(token)
    print(f"Tenants: {json.dumps([{k: t.get(k) for k in ('id', 'name')} for t in tenants], indent=2)}")
    if tenant_id not in {t.get("id") for t in tenants} and tenants:
        tenant_id = tenants[0]["id"]
        print(f"Using first tenant: {tenant_id}")

    existing = list_instances(token, tenant_id)
    free = [i for i in existing if (i.get("type") or "").startswith("free") or i.get("name") == args.name]
    if existing:
        print(f"Existing instances ({len(existing)}):")
        for i in existing:
            print(f"  {i.get('id')} name={i.get('name')} status={i.get('status')} "
                  f"conn={i.get('connection_url')}")

    if free and free[0].get("connection_url"):
        print("Free/named instance already exists — not creating another.")
        print("Set NEO4J_PASSWORD manually if you still have it (Aura does not re-show it).")
        data = free[0]
        uri = data.get("connection_url")
        if args.update_env and uri:
            print("Skipping password write (unknown). Update NEO4J_URI only if needed.")
        return 0

    print(f"Creating Aura Free instance '{args.name}' on tenant {tenant_id}...")
    created = create_free(token, tenant_id, name=args.name)
    print(json.dumps({k: created.get(k) for k in created if k != "password"}, indent=2, default=str))
    password = created.get("password")
    instance_id = created.get("id")
    uri = created.get("connection_url")
    if not instance_id:
        print("Unexpected create response:", created)
        return 1

    print("Waiting until running...")
    data = wait_running(token, instance_id)
    uri = data.get("connection_url") or uri
    # Aura Free often returns instance-id as username (not "neo4j")
    username = (
        data.get("username")
        or created.get("username")
        or "neo4j"
    )
    print(f"READY uri={uri} username={username}")
    if password:
        print("PASSWORD (save now — shown only once):", password)
    else:
        print("WARNING: API did not return password — check create response / console.")

    if args.update_env and uri and password:
        write_env(uri, password, username)
    elif args.update_env:
        print("--update-env skipped: missing uri or password")
    return 0


if __name__ == "__main__":
    sys.exit(main())
