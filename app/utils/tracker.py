"""
Visitor tracking - logs page visits to a private GitHub Gist.
Columns: Timestamp | Session_ID | Page | Browser | OS | IP | Country | City

The Gist write runs in a background thread so it never slows down page loads.

Streamlit Cloud Secrets required:
  [github_gist]
  token   = "ghp_..."
  gist_id = "..."
"""
import csv
import datetime
import io
import ipaddress
import threading
import uuid

import requests
import streamlit as st

_FILENAME = "cd46_visitor_log.csv"
_API_BASE = "https://api.github.com/gists"


def _parse_ua(ua: str) -> tuple:
    browser, os_name = "Unknown", "Unknown"
    u = ua.lower()
    if "edg/" in u or "edga/" in u:   browser = "Edge"
    elif "opr/" in u:                  browser = "Opera"
    elif "chrome/" in u:               browser = "Chrome"
    elif "firefox/" in u:              browser = "Firefox"
    elif "safari/" in u:               browser = "Safari"
    if   "iphone"  in u:              os_name = "iOS"
    elif "ipad"    in u:              os_name = "iOS"
    elif "android" in u:              os_name = "Android"
    elif "windows" in u:              os_name = "Windows"
    elif "macintosh" in u:            os_name = "macOS"
    elif "linux"   in u:              os_name = "Linux"
    return browser, os_name


def _is_public_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def _get_public_ip(headers: dict) -> str:
    """Extracts the public IP from standard proxy headers, ignoring internal IPs."""
    candidates = []
    
    # Case-insensitive header search
    for key, val in headers.items():
        k = key.lower()
        if k in ("x-forwarded-for", "x-real-ip", "true-client-ip", "cf-connecting-ip"):
            candidates.extend([x.strip() for x in val.split(",")])

    # Find the first truly public IP
    for ip in candidates:
        if ip and _is_public_ip(ip):
            return ip
            
    # Fallback to the last candidate if all are private
    return candidates[-1] if candidates else "Unknown"


def _write_to_gist(token: str, gist_id: str, ts: str, session_id: str, page_name: str, browser: str, os_name: str, ip: str) -> None:
    """Runs in background thread. Does GeoIP lookup, reads Gist, appends row, writes back."""
    try:
        # 1. GeoIP Lookup (takes ~100ms, free, no auth)
        country, city = "Unknown", "Unknown"
        if ip and ip != "Unknown" and _is_public_ip(ip):
            try:
                geo_resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    if geo_data.get("status") == "success":
                        country = geo_data.get("country", "Unknown")
                        city = geo_data.get("city", "Unknown")
            except Exception:
                pass

        row = [ts, session_id, page_name, browser, os_name, ip, country, city]

        # 2. Update Gist
        hdrs = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        r = requests.get(f"{_API_BASE}/{gist_id}", headers=hdrs, timeout=15)
        if r.status_code != 200:
            return
        gist_files = r.json().get("files", {})
        if _FILENAME not in gist_files:
            return
        
        current = gist_files[_FILENAME]["content"]
        if current and not current.endswith("\n"):
            current += "\n"
            
        buf = io.StringIO()
        csv.writer(buf).writerow(row)
        new_content = current + buf.getvalue()
        
        requests.patch(
            f"{_API_BASE}/{gist_id}",
            json={"files": {_FILENAME: {"content": new_content}}},
            headers=hdrs,
            timeout=15,
        )
    except Exception:
        pass


def log_page_visit(page_name: str) -> None:
    """Call once per page. Fires a background thread - never blocks."""
    try:
        flag = f"_tracked_{page_name}"
        if st.session_state.get(flag):
            return
        st.session_state[flag] = True

        cfg = st.secrets.get("github_gist", {})
        token   = cfg.get("token", "")
        gist_id = cfg.get("gist_id", "")
        if not token or not gist_id:
            return

        if "_session_id" not in st.session_state:
            st.session_state["_session_id"] = uuid.uuid4().hex[:8].upper()
        session_id = st.session_state["_session_id"]

        try:
            hdrs_ctx = dict(st.context.headers)
            # Find User-Agent case-insensitively
            ua = ""
            for k, v in hdrs_ctx.items():
                if k.lower() == "user-agent":
                    ua = v
                    break
            ip = _get_public_ip(hdrs_ctx)
        except Exception:
            ua, ip = "", "Unknown"

        browser, os_name = _parse_ua(ua)
        ts  = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Pass kwargs to thread to avoid passing a mutable list
        t = threading.Thread(
            target=_write_to_gist, 
            args=(token, gist_id, ts, session_id, page_name, browser, os_name, ip), 
            daemon=True
        )
        t.start()

    except Exception:
        pass
