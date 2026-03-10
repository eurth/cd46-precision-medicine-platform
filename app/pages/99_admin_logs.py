"""
Admin - Visitor Analytics (GitHub Gist backend)
Password-gated, hidden from sidebar.
URL: /admin_logs
"""
import io, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

_FILENAME = "cd46_visitor_log.csv"
_API_BASE = "https://api.github.com/gists"

# ---- Password gate ----------------------------------------------------------
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    st.title("Admin Access")
    pw = st.text_input("Password", type="password", key="admin_pw")
    if st.button("Unlock", key="btn_unlock"):
        if pw == st.secrets.get("admin", {}).get("password", ""):
            st.session_state.admin_authed = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()

# ---- Header -----------------------------------------------------------------
st.title("Visitor Analytics")
st.caption("CD46 Platform - GitHub Gist log")

c1, c2, c3 = st.columns([1, 1, 8])
with c1:
    if st.button("Refresh", key="btn_refresh"):
        st.rerun()
with c2:
    if st.button("Logout", key="btn_logout"):
        st.session_state.admin_authed = False
        st.rerun()

st.divider()

# ---- Secrets check ----------------------------------------------------------
token   = st.secrets.get("github_gist", {}).get("token", "")
gist_id = st.secrets.get("github_gist", {}).get("gist_id", "")
if not token or not gist_id:
    st.error("github_gist secrets not set in Streamlit Cloud.")
    st.stop()

# ---- Fetch Gist -------------------------------------------------------------
hdrs = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
try:
    resp = requests.get(f"{_API_BASE}/{gist_id}", headers=hdrs, timeout=15)
    resp.raise_for_status()
    raw = resp.json()["files"][_FILENAME]["content"]
except Exception as e:
    st.error(f"Could not read Gist: {e}")
    st.stop()

# ---- Parse ------------------------------------------------------------------
try:
    df = pd.read_csv(io.StringIO(raw))
except Exception as e:
    st.error(f"CSV parse error: {e}")
    st.code(raw[:500])
    st.stop()

# Ensure all expected columns exist
for col in ["Timestamp","Session_ID","Page","Browser","OS","IP"]:
    if col not in df.columns:
        df[col] = ""

df = df[df["Page"].notna() & (df["Page"] != "")]

if df.empty:
    st.info("No visits logged yet.")
    with st.expander("Diagnostics - Test Write", expanded=True):
        if st.button("Write test row to Gist", key="btn_test"):
            try:
                current = raw
                if current and not current.endswith("\n"):
                    current += "\n"
                buf = io.StringIO()
                import csv as _csv
                _csv.writer(buf).writerow(["2026-01-01 00:00:00","TESTID","TestPage","Chrome","Windows","1.2.3.4"])
                pr = requests.patch(
                    f"{_API_BASE}/{gist_id}",
                    json={"files": {_FILENAME: {"content": current + buf.getvalue()}}},
                    headers=hdrs, timeout=15,
                )
                if pr.status_code in (200,201):
                    st.success("Write OK - click Refresh.")
                else:
                    st.error(f"HTTP {pr.status_code}: {pr.text[:300]}")
            except Exception as ex:
                st.error(str(ex))
        st.markdown("**Raw Gist content:**")
        st.code(raw[:1000])
    st.stop()

df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df["Date"] = df["Timestamp"].dt.date
df["Hour"] = df["Timestamp"].dt.hour

# ---- Metrics ----------------------------------------------------------------
total  = len(df)
sess   = df["Session_ID"].nunique()
pages  = df["Page"].nunique()
top    = df["Page"].value_counts().index[0]
last   = df["Timestamp"].max()
last_s = last.strftime("%Y-%m-%d %H:%M") if pd.notna(last) else "—"

m1,m2,m3,m4 = st.columns(4)
m1.metric("Total Views",     f"{total:,}")
m2.metric("Unique Sessions", f"{sess:,}")
m3.metric("Pages Visited",   f"{pages:,}")
m4.metric("Top Page",        top[:22] + ("..." if len(top)>22 else ""))
st.caption(f"Last visit: **{last_s} UTC**  |  Stored in private GitHub Gist")

st.divider()

# ---- Filters ----------------------------------------------------------------
with st.expander("Filters", expanded=False):
    fa, fb, fc = st.columns(3)
    with fa:
        vd = df["Date"].dropna()
        if not vd.empty:
            dr = st.date_input("Date range", value=(vd.min(), vd.max()),
                               min_value=vd.min(), max_value=vd.max(), key="dr")
        else:
            dr = ()
    with fb:
        sp = st.selectbox("Page",    ["All"]+sorted(df["Page"].dropna().unique().tolist()), key="sp")
    with fc:
        sb = st.selectbox("Browser", ["All"]+sorted(df["Browser"].dropna().unique().tolist()), key="sb")

fdf = df.copy()
if len(dr)==2:
    fdf = fdf[(fdf["Date"]>=dr[0])&(fdf["Date"]<=dr[1])]
if sp != "All":
    fdf = fdf[fdf["Page"]==sp]
if sb != "All":
    fdf = fdf[fdf["Browser"]==sb]
st.caption(f"Showing {len(fdf):,} of {total:,} records")

# ---- Charts -----------------------------------------------------------------
st.subheader("Traffic Overview")
ca, cb = st.columns(2)
with ca:
    d = fdf.groupby("Date").size().reset_index(name="Views")
    st.plotly_chart(px.bar(d, x="Date", y="Views", title="Daily Views",
                   color_discrete_sequence=["#38bdf8"]).update_layout(
                   paper_bgcolor="#0f172a",plot_bgcolor="#0f172a",font_color="#e2e8f0",
                   margin=dict(l=10,r=10,t=40,b=10)), use_container_width=True)
with cb:
    pv = fdf["Page"].value_counts().reset_index()
    pv.columns = ["Page","Views"]
    st.plotly_chart(px.bar(pv.head(12), x="Views", y="Page", orientation="h",
                   title="Top Pages", color_discrete_sequence=["#818cf8"]).update_layout(
                   paper_bgcolor="#0f172a",plot_bgcolor="#0f172a",font_color="#e2e8f0",
                   yaxis={"categoryorder":"total ascending"},
                   margin=dict(l=10,r=10,t=40,b=10)), use_container_width=True)

cc, cd = st.columns(2)
with cc:
    bv = fdf["Browser"].value_counts().reset_index()
    bv.columns=["Browser","Count"]
    st.plotly_chart(px.pie(bv, names="Browser", values="Count", title="Browsers",
                   color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4).update_layout(
                   paper_bgcolor="#0f172a",font_color="#e2e8f0",
                   margin=dict(l=10,r=10,t=40,b=10)), use_container_width=True)
with cd:
    ov = fdf["OS"].value_counts().reset_index()
    ov.columns=["OS","Count"]
    st.plotly_chart(px.bar(ov, x="Count", y="OS", orientation="h", title="OS",
                   color_discrete_sequence=["#f59e0b"]).update_layout(
                   paper_bgcolor="#0f172a",plot_bgcolor="#0f172a",font_color="#e2e8f0",
                   yaxis={"categoryorder":"total ascending"},
                   margin=dict(l=10,r=10,t=40,b=10)), use_container_width=True)

hv = fdf.groupby("Hour").size().reset_index(name="Views")
st.plotly_chart(px.bar(hv, x="Hour", y="Views", title="Activity by Hour (UTC)",
               color_discrete_sequence=["#e879f9"]).update_layout(
               paper_bgcolor="#0f172a",plot_bgcolor="#0f172a",font_color="#e2e8f0",
               xaxis=dict(tickmode="linear",dtick=2),
               margin=dict(l=10,r=10,t=40,b=10)), use_container_width=True)

# ---- Table ------------------------------------------------------------------
st.divider()
st.subheader("Session Log")
cols = [c for c in ["Timestamp","Session_ID","Page","Browser","OS","IP"] if c in fdf.columns]
disp = fdf[cols].sort_values("Timestamp", ascending=False).reset_index(drop=True)
st.dataframe(disp, use_container_width=True, height=380)
st.download_button("Download CSV", disp.to_csv(index=False).encode(),
                   "cd46_visitor_log.csv", "text/csv", key="btn_dl")
