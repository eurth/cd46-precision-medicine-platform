"""
Admin — Visitor Analytics
Password-gated. NOT shown in the sidebar.
Access directly: https://cd46-precision-medicine-platform.streamlit.app/Admin_Logs
                 http://localhost:850X/Admin_Logs
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

_LOG_FILE   = Path("/tmp/cd46_visitor_log.csv")
_DEBUG_FILE = Path("/tmp/cd46_tracker_debug.txt")

# ── Password gate ─────────────────────────────────────────────────────────────
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    st.markdown(
        "<h2 style='color:#38bdf8; margin-bottom:4px;'>🔒 Admin Access</h2>"
        "<p style='color:#64748b;'>Visitor analytics — authorised access only.</p>",
        unsafe_allow_html=True,
    )
    pw = st.text_input("Password", type="password", key="admin_pw_input")
    if st.button("Unlock", type="primary"):
        correct = st.secrets.get("admin", {}).get("password", "")
        if pw and pw == correct:
            st.session_state.admin_authed = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# ── Header + controls ─────────────────────────────────────────────────────────
st.markdown(
    "<h2 style='color:#38bdf8; margin-bottom:0;'>📊 Visitor Analytics</h2>"
    "<p style='color:#64748b; margin-top:4px;'>CD46 Platform — live access log</p>",
    unsafe_allow_html=True,
)

col_r, col_l, _ = st.columns([1, 1, 8])
with col_r:
    if st.button("🔄 Refresh"):
        st.rerun()
with col_l:
    if st.button("🚪 Logout"):
        st.session_state.admin_authed = False
        st.rerun()

st.markdown("---")

# ── Load CSV ──────────────────────────────────────────────────────────────────
if not _LOG_FILE.exists():
    st.info(
        "**No visits logged yet.**\n\n"
        "The log file is created automatically when the first visitor arrives. "
        "Note: `/tmp/` resets on server restarts — download the CSV regularly to archive."
    )
    st.caption(f"Log path: `{_LOG_FILE}`")

    # ── Debug panel ───────────────────────────────────────────────────────
    with st.expander("🔧 Diagnostics (debug)", expanded=True):
        if st.button("✅ Run Test Write"):
            try:
                import csv as _csv
                with open(_LOG_FILE, "w", newline="", encoding="utf-8") as f:
                    w = _csv.writer(f)
                    w.writerow(["Timestamp", "Session_ID", "Page", "Browser", "OS"])
                    w.writerow(["TEST", "TESTID", "AdminTest", "Chrome", "Windows"])
                st.success(f"Write succeeded → `{_LOG_FILE}` created. Refresh the page.")
            except Exception as e:
                st.error(f"Write FAILED: {e}")

        if _DEBUG_FILE.exists():
            st.markdown("**Tracker error log** (`/tmp/cd46_tracker_debug.txt`):")
            st.code(_DEBUG_FILE.read_text(encoding="utf-8")[-3000:])
        else:
            st.caption("No tracker errors logged yet (debug file doesn't exist either).")

    st.stop()

df = pd.read_csv(_LOG_FILE)
if df.empty:
    st.info("Log file exists but is empty — no visits recorded yet.")
    st.stop()

df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df["Date"] = df["Timestamp"].dt.date
df["Hour"] = df["Timestamp"].dt.hour

# ── KPI metrics ───────────────────────────────────────────────────────────────
total_views    = len(df)
unique_sess    = df["Session_ID"].nunique()
unique_ips     = df["IP"].nunique()
unique_country = df["Country"].replace("", pd.NA).dropna().nunique()
top_page       = df["Page"].value_counts().index[0] if total_views else "–"
last_seen      = df["Timestamp"].max()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📄 Total Page Views", f"{total_views:,}")
c2.metric("👥 Unique Sessions",  f"{unique_sess:,}")
c3.metric("🌐 Unique IPs",       f"{unique_ips:,}")
c4.metric("🗺️ Countries",        f"{unique_country:,}")
c5.metric("🔥 Top Page",         top_page[:18] + ("…" if len(top_page) > 18 else ""))

st.caption(
    f"Last visit: **{last_seen.strftime('%Y-%m-%d %H:%M')} UTC**  |  "
    f"Log size: **{total_views:,} rows**  |  "
    f"⚠️ On Streamlit Cloud this file resets on redeploy — download CSV to archive."
)

st.markdown("---")

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔎 Filters", expanded=True):
    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        min_d = df["Date"].min()
        max_d = df["Date"].max()
        date_range = st.date_input(
            "Date range", value=(min_d, max_d),
            min_value=min_d, max_value=max_d, key="admin_date",
        )

    with fc2:
        pages = ["All"] + sorted(df["Page"].dropna().unique().tolist())
        sel_page = st.selectbox("Page", pages, key="admin_page")

    with fc3:
        countries_avail = df["Country"].replace("", pd.NA).dropna().unique().tolist()
        countries = ["All"] + sorted(countries_avail)
        sel_country = st.selectbox("Country", countries, key="admin_country")

# Apply filters
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["Date"] >= date_range[0]) & (fdf["Date"] <= date_range[1])]
if sel_page != "All":
    fdf = fdf[fdf["Page"] == sel_page]
if sel_country != "All":
    fdf = fdf[fdf["Country"] == sel_country]

st.caption(f"Showing **{len(fdf):,}** of **{total_views:,}** records after filters.")

# ── Charts row 1: daily views + top pages ─────────────────────────────────────
st.subheader("📈 Traffic Overview")
col_a, col_b = st.columns(2)

with col_a:
    daily = fdf.groupby("Date").size().reset_index(name="Views")
    fig = px.bar(daily, x="Date", y="Views", title="Daily Page Views",
                 color_discrete_sequence=["#38bdf8"])
    fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                      font_color="#e2e8f0", margin=dict(l=10, r=10, t=40, b=10),
                      xaxis_title="", yaxis_title="Views")
    st.plotly_chart(fig, width="stretch")

with col_b:
    page_vc = fdf["Page"].value_counts().reset_index()
    page_vc.columns = ["Page", "Views"]
    fig2 = px.bar(page_vc.head(12), x="Views", y="Page", orientation="h",
                  title="Top Pages", color_discrete_sequence=["#818cf8"])
    fig2.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                       font_color="#e2e8f0",
                       yaxis={"categoryorder": "total ascending"},
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig2, width="stretch")

# ── Charts row 2: countries + browsers ────────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    country_data = fdf["Country"].replace("", pd.NA).dropna()
    if not country_data.empty:
        cvc = country_data.value_counts().reset_index()
        cvc.columns = ["Country", "Visits"]
        fig3 = px.bar(cvc.head(12), x="Visits", y="Country", orientation="h",
                      title="Visitors by Country",
                      color_discrete_sequence=["#34d399"])
        fig3.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                           font_color="#e2e8f0",
                           yaxis={"categoryorder": "total ascending"},
                           margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig3, width="stretch")
    else:
        st.info("No geo data yet — IP lookup runs on first real visitor.")

with col_d:
    bvc = fdf["Browser"].value_counts().reset_index()
    bvc.columns = ["Browser", "Count"]
    fig4 = px.pie(bvc, names="Browser", values="Count", title="Browser Breakdown",
                  color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
    fig4.update_layout(paper_bgcolor="#0f172a", font_color="#e2e8f0",
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig4, width="stretch")

# ── Charts row 3: OS + hour of day ────────────────────────────────────────────
col_e, col_f = st.columns(2)

with col_e:
    osvc = fdf["OS"].value_counts().reset_index()
    osvc.columns = ["OS", "Count"]
    fig5 = px.bar(osvc, x="Count", y="OS", orientation="h",
                  title="Operating System",
                  color_discrete_sequence=["#f59e0b"])
    fig5.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                       font_color="#e2e8f0",
                       yaxis={"categoryorder": "total ascending"},
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig5, width="stretch")

with col_f:
    hourly = fdf.groupby("Hour").size().reset_index(name="Views")
    fig6 = px.bar(hourly, x="Hour", y="Views", title="Activity by Hour (UTC)",
                  color_discrete_sequence=["#e879f9"])
    fig6.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                       font_color="#e2e8f0",
                       xaxis=dict(tickmode="linear", dtick=2),
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig6, width="stretch")

# ── Session detail table ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Session Log")
import pandas as pd

# ---------------------------------------------------------------------------
# Password gate — must pass before any data is shown
# ---------------------------------------------------------------------------
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    st.markdown(
        "<h2 style='color:#38bdf8;'>🔒 Admin Access</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Visitor logs & analytics — authorised access only.")
    pw = st.text_input("Password", type="password", key="admin_pw_input")
    if st.button("Unlock", type="primary"):
        correct = st.secrets.get("admin", {}).get("password", "")
        if pw and pw == correct:
            st.session_state.admin_authed = True
            st.rerun()
show_cols = [c for c in ["Timestamp", "Session_ID", "Page", "IP", "Country", "City", "Browser", "OS"] if c in fdf.columns]
display_df = (
    fdf[show_cols]
    .sort_values("Timestamp", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(display_df, use_container_width=True, height=380)

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    data=csv_bytes,
    file_name="cd46_visitor_log.csv",
    mime="text/csv",
)


st.markdown(
    "<h2 style='color:#38bdf8;'>🔒 Visitor Logs — Admin View</h2>",
    unsafe_allow_html=True,
)

col_refresh, col_logout, _ = st.columns([1, 1, 8])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()
with col_logout:
    if st.button("🚪 Logout"):
        st.session_state.admin_authed = False
        st.rerun()

st.markdown("---")


@st.cache_data(ttl=60, show_spinner="Loading visitor data…")
def _load_sessions() -> list[dict]:
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
    return ws.get_all_records()


# Check if GCP is configured at all before attempting connection
if "gcp_service_account" not in st.secrets:
    st.info(
        "**Google Sheets not configured yet.**\n\n"
        "Visitor tracking will appear here once you add `[gcp_service_account]` "
        "and `[google_sheets]` to your Streamlit Secrets.\n\n"
        "See `.streamlit/secrets.toml.template` for setup instructions."
    )
    st.stop()

try:
    rows = _load_sessions()
except Exception as e:
    st.error(f"Could not connect to Google Sheets: {e}")
    st.stop()

if not rows:
    st.info("No visits have been logged yet.  "
            "Check that your secrets are configured and the app has received a visitor.")
    st.stop()

df = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Page Views", len(df))
c2.metric(
    "Unique Sessions",
    df["Session ID"].nunique() if "Session ID" in df.columns else "–",
)
c3.metric(
    "Countries",
    df["Country"].nunique() if "Country" in df.columns else "–",
)
c4.metric(
    "Unique Pages Visited",
    df["Page"].nunique() if "Page" in df.columns else "–",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
col_a, col_b, col_c = st.columns(3)

with col_a:
    if "Page" in df.columns:
        page_filter = st.multiselect("Filter by Page", sorted(df["Page"].dropna().unique()))
        if page_filter:
            df = df[df["Page"].isin(page_filter)]

with col_b:
    if "Country" in df.columns:
        country_filter = st.multiselect("Filter by Country", sorted(df["Country"].dropna().unique()))
        if country_filter:
            df = df[df["Country"].isin(country_filter)]

with col_c:
    if "Browser" in df.columns:
        browser_filter = st.multiselect("Filter by Browser", sorted(df["Browser"].dropna().unique()))
        if browser_filter:
            df = df[df["Browser"].isin(browser_filter)]

# Sort newest first
if "Timestamp" in df.columns:
    df = df.sort_values("Timestamp", ascending=False)

# ---------------------------------------------------------------------------
# Data table
# ---------------------------------------------------------------------------
st.subheader(f"Session Log ({len(df):,} rows)")
st.dataframe(df, use_container_width=True, height=500)

csv = df.to_csv(index=False)
st.download_button(
    "⬇️ Download CSV",
    data=csv,
    file_name="visitor_logs.csv",
    mime="text/csv",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Quick charts
# ---------------------------------------------------------------------------
if len(df) >= 2:
    import plotly.express as px

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        if "Page" in df.columns:
            page_counts = df["Page"].value_counts().reset_index()
            page_counts.columns = ["Page", "Views"]
            fig = px.bar(
                page_counts,
                x="Views", y="Page",
                orientation="h",
                title="Page Views",
                color_discrete_sequence=["#38bdf8"],
            )
            fig.update_layout(
                paper_bgcolor="#0f172a",
                plot_bgcolor="#0f172a",
                font_color="#e2e8f0",
                yaxis={"categoryorder": "total ascending"},
                margin={"l": 10, "r": 10, "t": 40, "b": 10},
            )
            st.plotly_chart(fig, width="stretch")

    with col_chart2:
        if "Country" in df.columns:
            country_counts = df["Country"].value_counts().reset_index()
            country_counts.columns = ["Country", "Visits"]
            fig2 = px.bar(
                country_counts.head(15),
                x="Visits", y="Country",
                orientation="h",
                title="Top Countries",
                color_discrete_sequence=["#818cf8"],
            )
            fig2.update_layout(
                paper_bgcolor="#0f172a",
                plot_bgcolor="#0f172a",
                font_color="#e2e8f0",
                yaxis={"categoryorder": "total ascending"},
                margin={"l": 10, "r": 10, "t": 40, "b": 10},
            )
            st.plotly_chart(fig2, width="stretch")
