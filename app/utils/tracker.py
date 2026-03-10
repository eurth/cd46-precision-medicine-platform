"""
Visitor tracking — logs page visits to a private GitHub Gist as CSV.

Columns: Timestamp | Session_ID | Page | Browser | OS

Setup (one-time):
  1. Create a private Gist at https://gist.github.com with a single file
     named  cd46_visitor_log.csv  containing exactly this header line:
       Timestamp,Session_ID,Page,Browser,OS
  2. Create a GitHub PAT at https://github.com/settings/tokens
     with only the  gist  scope (no other permissions needed).
  3. Add to Streamlit Cloud Secrets (Settings → Secrets):
       [github_gist]
       token   = "ghp_xxxxxxxxxxxxxxxxxxxx"
       gist_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

Design:
  - Reads current Gist content, appends one row, writes back (PATCH).
  - Dedupes per page per session — at most one API call per page per user.
  - All exceptions are silently swallowed so the main app never crashes.
  - Falls back gracefully if secrets are not configured yet.
"""

import csv
import datetime
import io
import uuid

import requests
import streamlit as st

_FILENAME = "cd46_visitor_log.csv"
_HEADERS  = ["Timestamp", "Session_ID", "Page", "Browser", "OS"]
_API_BASE = "https://api.github.com/gists"


def _parse_ua(ua: str) -> tuple[str, str]:
    browser, os_name = "Unknown", "Unknown"
    ua_l = ua.lower()
    if "edg/" in ua_l or "edga/" in ua_l:
        browser = "Edge"
    elif "opr/" in ua_l or "opera/" in ua_l:
        browser = "Opera"
    elif "chrome/" in ua_l and "safari" in ua_l:
        browser = "Chrome"
    elif "firefox/" in ua_l:
        browser = "Firefox"
    elif "safari/" in ua_l:
        browser = "Safari"
    if "iphone" in ua_l:
        os_name = "iOS (iPhone)"
    elif "ipad" in ua_l:
        os_name = "iOS (iPad)"
    elif "android" in ua_l:
        os_name = "Android"
    elif "windows" in ua_l:
        os_name = "Windows"
    elif "macintosh" in ua_l or "mac os x" in ua_l:
        os_name = "macOS"
    elif "linux" in ua_l:
        os_name = "Linux"
    return browser, os_name


def _gist_cfg():
    """Return (token, gist_id) from secrets, or ('', '') if not configured."""
    cfg = st.secrets.get("github_gist", {})
    return cfg.get("token", ""), cfg.get("gist_id", "")


def _auth_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


_DEBUG_FILE = "/tmp/cd46_tracker_debug.txt"


def _dbg(msg: str) -> None:
    """Append a timestamped line to the debug file. Best-effort."""
    try:
        with open(_DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")
    except Exception:
        pass


def log_page_visit(page_name: str) -> None:
    """
    Call from streamlit_app.py after st.navigation().
    Dedupes per page per session; never raises.
    """
    try:
        # --- dedupe ---
        flag = f"_tracked_{page_name}"
        if st.session_state.get(flag):
            return
        st.session_state[flag] = True

        token, gist_id = _gist_cfg()
        if not token or not gist_id:
            _dbg("SKIP: github_gist secrets not configured")
            return

        # --- session ID ---
        if "_session_id" not in st.session_state:
            st.session_state["_session_id"] = uuid.uuid4().hex[:8].upper()
        session_id = st.session_state["_session_id"]

        # --- detect browser / OS ---
        try:
            ua = st.context.headers.get("User-Agent", "")
        except Exception:
            ua = ""
        browser, os_name = _parse_ua(ua)

        ts  = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        row = [ts, session_id, page_name, browser, os_name]

        # --- read current Gist content ---
        hdrs = _auth_headers(token)
        resp = requests.get(f"{_API_BASE}/{gist_id}", headers=hdrs, timeout=8)
        if resp.status_code != 200:
            _dbg(f"GET {gist_id} -> HTTP {resp.status_code}: {resp.text[:200]}")
            return
        gist_data = resp.json()
        if _FILENAME not in gist_data.get("files", {}):
            _dbg(f"File '{_FILENAME}' not found in Gist. Files: {list(gist_data.get('files', {}).keys())}")
            return
        current = gist_data["files"][_FILENAME]["content"]

        # --- append new row ---
        if current and not current.endswith("\n"):
            current += "\n"
        out = io.StringIO()
        csv.writer(out).writerow(row)
        new_content = current + out.getvalue()

        # --- write back ---
        patch_resp = requests.patch(
            f"{_API_BASE}/{gist_id}",
            json={"files": {_FILENAME: {"content": new_content}}},
            headers=hdrs,
            timeout=8,
        )
        if patch_resp.status_code not in (200, 201):
            _dbg(f"PATCH -> HTTP {patch_resp.status_code}: {patch_resp.text[:200]}")
        else:
            _dbg(f"OK: logged '{page_name}' for session {session_id}")

    except Exception as exc:
        _dbg(f"EXCEPTION in log_page_visit({page_name!r}): {type(exc).__name__}: {exc}")


import csv
import datetime
import uuid
from pathlib import Path

import requests
import streamlit as st

_LOG_DIR  = Path("/tmp")
_LOG_FILE = _LOG_DIR / "cd46_visitor_log.csv"

_HEADERS = [
    "Timestamp", "Session_ID", "Page", "IP",
    "Country", "City", "Region", "ISP", "Browser", "OS",
]


def _get_ip() -> str:
    headers = st.context.headers
    xff = headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return headers.get("X-Real-Ip", "") or "unknown"


def _get_user_agent() -> str:
    return st.context.headers.get("User-Agent", "unknown")


def _parse_ua(ua: str) -> tuple[str, str]:
    browser, os_name = "Unknown", "Unknown"
    if "Edg/" in ua or "EdgA/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera/" in ua:
        browser = "Opera"
    elif "Chrome/" in ua and "Safari" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua:
        browser = "Safari"
    if "iPhone" in ua:
        os_name = "iOS (iPhone)"
    elif "iPad" in ua:
        os_name = "iOS (iPad)"
    elif "Android" in ua:
        os_name = "Android"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"
    return browser, os_name


@st.cache_data(ttl=3600, show_spinner=False)
def _geo_lookup(ip: str) -> dict:
    if ip in ("unknown", "", "127.0.0.1", "::1"):
        return {}
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=4)
        if r.status_code == 200:
            data = r.json()
            if "error" not in data:
                return data
    except Exception:
        pass
    return {}


def _ensure_log_file() -> None:
    # /tmp/ always exists — just create the CSV header if needed
    if not _LOG_FILE.exists():
        with open(_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(_HEADERS)


def log_page_visit(page_name: str) -> None:
    """
    Call once per page. Safe on Streamlit reruns — dedupes per session.
    Silently skips all errors so the main app is never affected.
    """
    flag = f"_tracked_{page_name}"
    if st.session_state.get(flag):
        return
    st.session_state[flag] = True

    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())[:8].upper()
    session_id = st.session_state["_session_id"]

    try:
        ip      = _get_ip()
        ua      = _get_user_agent()
        browser, os_name = _parse_ua(ua)
        geo     = _geo_lookup(ip)

        row = [
            datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            session_id,
            page_name,
            ip,
            geo.get("country_name", ""),
            geo.get("city", ""),
            geo.get("region", ""),
            geo.get("org", ""),
            browser,
            os_name,
        ]
        _ensure_log_file()
        with open(_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception:
        pass  # Never crash the main app


import datetime
import uuid

import requests
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
    _GSPREAD_OK = True
except ImportError:
    _GSPREAD_OK = False

# Sheet column headers (written on first run if the sheet is empty)
_HEADERS = [
    "Timestamp", "Session ID", "Page", "IP",
    "Country", "City", "Region", "ISP",
    "Latitude", "Longitude", "Browser", "OS", "User Agent",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_ip() -> str:
    headers = st.context.headers
    # Streamlit Cloud sits behind a proxy — real IP is in X-Forwarded-For
    xff = headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return headers.get("X-Real-Ip", "") or "unknown"


def _get_user_agent() -> str:
    return st.context.headers.get("User-Agent", "unknown")


def _parse_ua(ua: str) -> tuple[str, str]:
    """Return (browser, os_name) from a User-Agent string without extra libs."""
    browser = "Unknown"
    os_name = "Unknown"

    # Browser detection (order matters — Edge & Opera share Chrome tokens)
    if "Edg/" in ua or "EdgA/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera/" in ua:
        browser = "Opera"
    elif "Chrome/" in ua and "Safari" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua:
        browser = "Safari"

    # OS detection
    if "iPhone" in ua:
        os_name = "iOS (iPhone)"
    elif "iPad" in ua:
        os_name = "iOS (iPad)"
    elif "Android" in ua:
        os_name = "Android"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"

    return browser, os_name


@st.cache_data(ttl=3600, show_spinner=False)
def _geo_lookup(ip: str) -> dict:
    """Resolve IP → geo dict via ipapi.co. Cached 1 h per IP."""
    if ip in ("unknown", "", "127.0.0.1", "::1"):
        return {}
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=4)
        if r.status_code == 200:
            data = r.json()
            if "error" not in data:
                return data
    except Exception:
        pass
    return {}


def _open_worksheet() -> "gspread.Worksheet":
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    gc = gspread.authorize(creds)
    sh = gc.open(st.secrets["google_sheets"]["sheet_name"])
    ws = sh.worksheet("Sessions")

    # Auto-create headers on first use
    if not ws.cell(1, 1).value:
        ws.insert_row(_HEADERS, index=1)

    return ws


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_page_visit(page_name: str) -> None:
    """
    Call once at the top of each page (or from streamlit_app.py).
    Safe to call on every Streamlit rerun — dedupes per page per session.
    """
    # Prerequisite checks
    if not _GSPREAD_OK:
        return
    if "gcp_service_account" not in st.secrets:
        return  # Not configured (local dev without secrets)

    # Dedupe — only log once per page within a session
    flag = f"_tracked_{page_name}"
    if st.session_state.get(flag):
        return
    st.session_state[flag] = True

    # Assign a short session ID on first page view
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())[:8].upper()
    session_id = st.session_state["_session_id"]

    try:
        ip = _get_ip()
        ua = _get_user_agent()
        browser, os_name = _parse_ua(ua)
        geo = _geo_lookup(ip)

        row = [
            datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            session_id,
            page_name,
            ip,
            geo.get("country_name", ""),
            geo.get("city", ""),
            geo.get("region", ""),
            geo.get("org", ""),          # ISP / organisation
            str(geo.get("latitude", "")),
            str(geo.get("longitude", "")),
            browser,
            os_name,
            ua[:250],
        ]

        ws = _open_worksheet()
        ws.append_row(row, value_input_option="USER_ENTERED")

    except Exception:
        pass  # Silently absorb — tracking must never block the app
