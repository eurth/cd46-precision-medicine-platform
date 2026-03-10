"""
Visitor tracking - logs page visits to a private GitHub Gist.
Columns: Timestamp | Session_ID | Page | Browser | OS | IP

The Gist write runs in a background thread so it never slows down page loads.

Streamlit Cloud Secrets required:
  [github_gist]
  token   = "ghp_..."
  gist_id = "..."
"""
import csv
import datetime
import io
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


def _write_to_gist(token: str, gist_id: str, row: list) -> None:
    """Runs in background thread. Reads Gist, appends row, writes back."""
    try:
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
            ua  = hdrs_ctx.get("User-Agent", "")
            ip  = (hdrs_ctx.get("X-Forwarded-For", "") or
                   hdrs_ctx.get("X-Real-Ip", "") or "").split(",")[0].strip()
        except Exception:
            ua, ip = "", ""

        browser, os_name = _parse_ua(ua)
        ts  = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        row = [ts, session_id, page_name, browser, os_name, ip]

        t = threading.Thread(target=_write_to_gist, args=(token, gist_id, row), daemon=True)
        t.start()

    except Exception:
        pass
