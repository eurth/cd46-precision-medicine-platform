"""
Admin -- Visitor Analytics (GitHub Gist backend)
Password-gated. NOT shown in the sidebar.
Access directly: https://cd46-precision-medicine-platform.streamlit.app/admin_logs
                 http://localhost:850X/admin_logs
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

_FILENAME = "cd46_visitor_log.csv"
_API_BASE = "https://api.github.com/gists"

# -- Password gate ------------------------------------------------------------
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    st.markdown(
        "<h2 style='color:#38bdf8; margin-bottom:4px;'>Lock Admin Access</h2>"
        "<p style='color:#64748b;'>Visitor analytics -- authorised access only.</p>",
        unsafe_allow_html=True,
    )
    pw = st.text_input("Password", type="password", key="admin_pw_input")
    if st.button("Unlock", type="primary", key="btn_unlock"):
        correct = st.secrets.get("admin", {}).get("password", "")
        if pw and pw == correct:
            st.session_state.admin_authed = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# -- Header -------------------------------------------------------------------
st.markdown(
    "<h2 style='color:#38bdf8; margin-bottom:0;'>Visitor Analytics</h2>"
    "<p style='color:#64748b; margin-top:4px;'>CD46 Platform -- GitHub Gist log</p>",
    unsafe_allow_html=True,
)

col_r, col_l, _ = st.columns([1, 1, 8])
with col_r:
    if st.button("Refresh", key="btn_refresh"):
        st.rerun()
with col_l:
    if st.button("Logout", key="btn_logout"):
        st.session_state.admin_authed = False
        st.rerun()

st.markdown("---")

# -- Check secrets ------------------------------------------------------------
token   = st.secrets.get("github_gist", {}).get("token", "")
gist_id = st.secrets.get("github_gist", {}).get("gist_id", "")

if not token or not gist_id:
    st.warning(
        "**GitHub Gist not configured yet.**\n\n"
        "Add the following to Streamlit Cloud Secrets (Settings -> Secrets)."
    )
    with st.expander("Setup Guide", expanded=True):
        st.markdown("""
**Step 1 - Create a private Gist**
1. Go to gist.github.com
2. Filename: `cd46_visitor_log.csv`
3. Content (exactly this one line):
   ```
   Timestamp,Session_ID,Page,Browser,OS
   ```
4. Click **Create secret gist**
5. Copy the Gist ID from the URL

**Step 2 - Create a Personal Access Token**
1. Go to github.com/settings/tokens -> Generate new token (classic)
2. Note: `CD46 Visitor Tracker`
3. Expiration: 1 year
4. Scope: tick only **gist**
5. Generate and copy immediately

**Step 3 - Add to Streamlit Cloud Secrets**
```toml
[github_gist]
token   = "ghp_xxxxxxxxxxxxxxxxxxxx"
gist_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

[admin]
password = "CD46Admin2026!"
```
        """)
    st.stop()

# -- Fetch Gist data ----------------------------------------------------------
hdrs = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}

try:
    resp = requests.get(f"{_API_BASE}/{gist_id}", headers=hdrs, timeout=10)
    resp.raise_for_status()
    raw_csv = resp.json()["files"][_FILENAME]["content"]
except requests.exceptions.HTTPError as e:
    st.error(f"GitHub API error {e.response.status_code}: {e.response.text[:300]}")
    st.stop()
except Exception as e:
    st.error(f"Could not fetch Gist: {e}")
    st.stop()

# -- Parse CSV ----------------------------------------------------------------
try:
    df = pd.read_csv(io.StringIO(raw_csv))
except Exception as e:
    st.error(f"Could not parse CSV from Gist: {e}")
    st.code(raw_csv[:500])
    st.stop()

df = df.dropna(subset=["Page"])
if df.empty:
    st.info("No visits logged yet — log file only contains the header row.")

    # Diagnostics panel
    with st.expander("🔧 Diagnostics", expanded=True):
        st.markdown("**Test write to Gist:**")
        if st.button("✅ Run Test Write", key="btn_test_write"):
            import csv as _csv
            import io as _io
            try:
                # Read current
                r = requests.get(f"{_API_BASE}/{gist_id}", headers=hdrs, timeout=10)
                r.raise_for_status()
                current = r.json()["files"][_FILENAME]["content"]
                if current and not current.endswith("\n"):
                    current += "\n"
                buf = _io.StringIO()
                _csv.writer(buf).writerow(["2026-01-01 00:00:00", "TESTID", "TestPage", "Chrome", "Windows"])
                patch_r = requests.patch(
                    f"{_API_BASE}/{gist_id}",
                    json={"files": {_FILENAME: {"content": current + buf.getvalue()}}},
                    headers=hdrs,
                    timeout=10,
                )
                if patch_r.status_code in (200, 201):
                    st.success("✅ Write succeeded! Click Refresh to see data.")
                else:
                    st.error(f"PATCH failed HTTP {patch_r.status_code}: {patch_r.text[:300]}")
            except Exception as ex:
                st.error(f"Exception: {type(ex).__name__}: {ex}")

        st.markdown("**Tracker debug log** (`/tmp/cd46_tracker_debug.txt`):")
        from pathlib import Path as _Path
        _dbg = _Path("/tmp/cd46_tracker_debug.txt")
        if _dbg.exists():
            st.code(_dbg.read_text(encoding="utf-8")[-3000:])
        else:
            st.caption("Debug file not created yet — tracker hasn't run or has had no errors.")

        st.markdown("**Raw Gist CSV content:**")
        st.code(raw_csv[:1000])

    st.stop()

df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df["Date"]      = df["Timestamp"].dt.date
df["Hour"]      = df["Timestamp"].dt.hour

# -- KPI metrics --------------------------------------------------------------
total_views  = len(df)
unique_sess  = df["Session_ID"].nunique()
unique_pages = df["Page"].nunique()
top_page     = df["Page"].value_counts().index[0] if total_views else "-"
last_seen    = df["Timestamp"].max()
last_seen_str = last_seen.strftime("%Y-%m-%d %H:%M") if pd.notna(last_seen) else "unknown"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Page Views", f"{total_views:,}")
c2.metric("Unique Sessions",  f"{unique_sess:,}")
c3.metric("Pages Visited",    f"{unique_pages:,}")
c4.metric("Top Page",         top_page[:20] + ("..." if len(top_page) > 20 else ""))

st.caption(
    f"Last visit: **{last_seen_str} UTC**  |  "
    f"Log size: **{total_views:,} rows**  |  "
    f"Stored in private GitHub Gist -- persistent across server restarts."
)

st.markdown("---")

# -- Filters ------------------------------------------------------------------
with st.expander("Filters", expanded=True):
    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        valid_dates = df["Date"].dropna()
        if not valid_dates.empty:
            min_d = valid_dates.min()
            max_d = valid_dates.max()
            date_range = st.date_input(
                "Date range", value=(min_d, max_d),
                min_value=min_d, max_value=max_d, key="admin_date",
            )
        else:
            date_range = ()
            st.caption("No valid dates yet.")

    with fc2:
        pages = ["All"] + sorted(df["Page"].dropna().unique().tolist())
        sel_page = st.selectbox("Page", pages, key="admin_page")

    with fc3:
        browsers = ["All"] + sorted(df["Browser"].dropna().unique().tolist())
        sel_browser = st.selectbox("Browser", browsers, key="admin_browser")

fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["Date"] >= date_range[0]) & (fdf["Date"] <= date_range[1])]
if sel_page != "All":
    fdf = fdf[fdf["Page"] == sel_page]
if sel_browser != "All":
    fdf = fdf[fdf["Browser"] == sel_browser]

st.caption(f"Showing **{len(fdf):,}** of **{total_views:,}** records after filters.")

# -- Charts -------------------------------------------------------------------
st.subheader("Traffic Overview")
col_a, col_b = st.columns(2)

with col_a:
    daily = fdf.groupby("Date").size().reset_index(name="Views")
    fig = px.bar(daily, x="Date", y="Views", title="Daily Page Views",
                 color_discrete_sequence=["#38bdf8"])
    fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                      font_color="#e2e8f0", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    page_vc = fdf["Page"].value_counts().reset_index()
    page_vc.columns = ["Page", "Views"]
    fig2 = px.bar(page_vc.head(12), x="Views", y="Page", orientation="h",
                  title="Top Pages", color_discrete_sequence=["#818cf8"])
    fig2.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                       font_color="#e2e8f0",
                       yaxis={"categoryorder": "total ascending"},
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig2, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    bvc = fdf["Browser"].value_counts().reset_index()
    bvc.columns = ["Browser", "Count"]
    fig3 = px.pie(bvc, names="Browser", values="Count", title="Browser Breakdown",
                  color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
    fig3.update_layout(paper_bgcolor="#0f172a", font_color="#e2e8f0",
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    osvc = fdf["OS"].value_counts().reset_index()
    osvc.columns = ["OS", "Count"]
    fig4 = px.bar(osvc, x="Count", y="OS", orientation="h",
                  title="Operating System",
                  color_discrete_sequence=["#f59e0b"])
    fig4.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                       font_color="#e2e8f0",
                       yaxis={"categoryorder": "total ascending"},
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig4, use_container_width=True)

hourly = fdf.groupby("Hour").size().reset_index(name="Views")
fig5 = px.bar(hourly, x="Hour", y="Views", title="Activity by Hour (UTC)",
              color_discrete_sequence=["#e879f9"])
fig5.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                   font_color="#e2e8f0",
                   xaxis=dict(tickmode="linear", dtick=2),
                   margin=dict(l=10, r=10, t=40, b=10))
st.plotly_chart(fig5, use_container_width=True)

# -- Session table ------------------------------------------------------------
st.markdown("---")
st.subheader("Session Log")

show_cols = [c for c in ["Timestamp", "Session_ID", "Page", "Browser", "OS"] if c in fdf.columns]
display_df = (
    fdf[show_cols]
    .sort_values("Timestamp", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(display_df, use_container_width=True, height=380)

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv_bytes,
    file_name="cd46_visitor_log.csv",
    mime="text/csv",
    key="btn_download",
)
