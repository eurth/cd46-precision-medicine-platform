"""Page 3 — Survival Outcomes: forest plot, Cox PH, KM interpretation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.theme import plotly_layout, apply_plotly_layout
from components.targets import get_active_symbol, list_symbols, render_stub_gate
from components.ui_kit import export_research_pack, filter_bar, page_header, section_tabs, research_table

if render_stub_gate(module="Survival Outcomes"):
    st.stop()

_GENE = get_active_symbol()

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
_BG     = "#FFFFFF"
_LINE   = "#E2E8F0"
_INDIGO = "#2563EB"
_ROSE   = "#F472B6"
_GREEN  = "#34D399"
_AMBER  = "#FBBF24"
_SLATE  = "#94A3B8"
_MID    = "#94A3B8"
_TEXT   = "#64748B"
_LIGHT  = "#1E293B"
_RED    = "#F87171"

# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------
@st.cache_data
def load_survival(symbol: str):
    p = Path(f"data/processed/{symbol.lower()}_survival_results.csv")
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df = df.copy()
    df["gene_symbol"] = symbol
    return df


@st.cache_data
def load_survival_multi(symbols: tuple[str, ...]) -> pd.DataFrame:
    frames = []
    for sym in symbols:
        df = load_survival(sym)
        if df is not None and not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# Interactive filters — defaults to active research target
_all_syms = list_symbols()
_default_genes = [_GENE] if _GENE in _all_syms else _all_syms[:1]
with filter_bar("Gene & endpoint filters"):
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        _selected_genes = st.multiselect(
            "Gene markers",
            options=_all_syms,
            default=_default_genes,
            key="surv_genes",
            help="Load Cox/log-rank results for one or more registry genes.",
        )
    with fc2:
        _endpoint_opts = ["All", "OS", "PFI", "DSS", "DFI"]
        _endpoint = st.selectbox("Endpoint", _endpoint_opts, index=0, key="surv_endpoint")
    with fc3:
        st.caption("Filters apply to all tabs below.")

if not _selected_genes:
    _selected_genes = [_GENE]

survival_df = load_survival_multi(tuple(_selected_genes))
_primary_gene = _selected_genes[0] if len(_selected_genes) == 1 else _GENE

# ---------------------------------------------------------------------------
# Prepare sub-frames: Cox rows and log-rank rows
# ---------------------------------------------------------------------------
if survival_df is not None and not survival_df.empty:
    if _endpoint != "All" and "endpoint" in survival_df.columns:
        survival_df = survival_df[
            survival_df["endpoint"].astype(str).str.upper() == _endpoint
        ]
    _cancers = sorted(survival_df["cancer_type"].dropna().unique().tolist())
    _sel_cancers = st.multiselect(
        "Cancers",
        options=_cancers,
        default=_cancers,
        key="surv_cancers",
    )
    if _sel_cancers:
        survival_df = survival_df[survival_df["cancer_type"].isin(_sel_cancers)]

    cox_df  = survival_df[survival_df["hazard_ratio"].notna()].copy()
    logr_df = survival_df[survival_df["log_rank_p"].notna() & survival_df["n_high"].notna()].copy()

    n_cancers = int(cox_df["cancer_type"].nunique()) if not cox_df.empty else 0
    n_sig     = int((cox_df["p_value"] < 0.05).sum()) if not cox_df.empty else 0
    top_pos   = cox_df[cox_df["hazard_ratio"] > 1].nsmallest(1, "p_value") if not cox_df.empty else cox_df
    top_neg   = cox_df[cox_df["hazard_ratio"] < 1].nsmallest(1, "p_value") if not cox_df.empty else cox_df
    top_pos_txt = (
        f"{top_pos.iloc[0]['cancer_type']} HR={top_pos.iloc[0]['hazard_ratio']:.2f}"
        if len(top_pos) > 0 else "—"
    )
    top_neg_txt = (
        f"{top_neg.iloc[0]['cancer_type']} HR={top_neg.iloc[0]['hazard_ratio']:.2f}"
        if len(top_neg) > 0 else "—"
    )
    _GENE_LABEL = ",".join(_selected_genes) if len(_selected_genes) > 1 else _primary_gene
else:
    cox_df = logr_df = pd.DataFrame()
    n_cancers, n_sig = 0, 0
    top_pos_txt, top_neg_txt = "—", "—"
    _GENE_LABEL = _primary_gene
    st.warning(
        f"No survival CSV for: {', '.join(_selected_genes)}. "
        f"Expected `data/processed/{{gene}}_survival_results.csv`."
    )

# Use label in hero (keep _GENE for CD46 vignette branches)
_DISPLAY = _GENE_LABEL

# ---------------------------------------------------------------------------
# Page hero
# ---------------------------------------------------------------------------
page_header(
        icon="📈",
        module_name="Survival Outcomes",
        purpose=(
            f"Cox proportional hazard analysis · TCGA · "
            f"{_DISPLAY}-High vs {_DISPLAY}-Low · Forest plot + significance table"
        ),
        kpi_chips=[
            ("Cancers Tested", str(n_cancers)),
            ("Significant (p<0.05)", str(n_sig)),
            ("Strongest Positive", top_pos_txt),
            ("Strongest Inverse", top_neg_txt),
        ],
        source_badges=["TCGA"],
    )

try:
    from components.tooltip_generator import render_entity_popover
    render_entity_popover(_DISPLAY.split(",")[0].strip(), label=f"🧬 {_DISPLAY.split(',')[0].strip()} structure")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
_SURV_TABS = [
    "Forest Plot — All Cancers",
    "Significance Table & KM Context",
    "Cancer Explorer",
]
_active_surv = section_tabs(_SURV_TABS, key="surv_outcomes_tabs")

# ── Tab 1 : Forest Plot ──────────────────────────────────────────────────────
if _active_surv == _SURV_TABS[0]:
    st.markdown(f"#### Cox PH Forest Plot — {_DISPLAY}-High vs {_DISPLAY}-Low")
    st.caption(
        f"Hazard ratio > 1 → high expression predicts worse survival.  "
        "Error bars = 95% CI.  Stars = p < 0.05.  "
        "Dashed line = HR 1.0 (null hypothesis)."
    )

    ep_col, _ = st.columns([1, 3])
    fp_ep = ep_col.radio("Endpoint", ["OS", "PFI"], horizontal=True, key="fp_ep")

    if cox_df.empty:
        st.info(
            "No Cox rows for the current gene/cancer/endpoint filters. "
            "Adjust filters above or ensure `*_survival_results.csv` exists."
        )
    else:
        fp_data = cox_df[cox_df["endpoint"] == fp_ep].sort_values("hazard_ratio")

        fig_fp = go.Figure()

        for i, (_, row) in enumerate(fp_data.iterrows()):
            hr   = row["hazard_ratio"]
            lo   = row.get("hr_lower_95", hr)
            hi   = row.get("hr_upper_95", hr)
            pv   = row.get("p_value", 1.0)
            is_sig = (not pd.isna(pv)) and (pv < 0.05)
            col  = (_RED if (is_sig and hr > 1) else
                    _GREEN if (is_sig and hr < 1) else _SLATE)
            label = (
                f"{row.get('gene_symbol', _DISPLAY)} · {row['cancer_type']}"
                if len(_selected_genes) > 1
                else row["cancer_type"]
            )
            if is_sig:
                label = f"{label} ★"

            # CI line
            fig_fp.add_shape(
                type="line",
                x0=lo, x1=hi, y0=i, y1=i,
                line=dict(color=col, width=2),
            )
            # HR dot
            fig_fp.add_trace(go.Scatter(
                x=[hr], y=[i],
                mode="markers",
                marker=dict(color=col, size=10, symbol="square"),
                showlegend=False,
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    f"HR: {hr:.3f}<br>"
                    f"95% CI: {lo:.3f}–{hi:.3f}<br>"
                    f"p-value: {pv:.4f}<extra></extra>"
                ),
            ))

        fig_fp.add_vline(x=1.0, line_dash="dash", line_color=_MID, line_width=1.5)

        y_labels = []
        for _, row in fp_data.iterrows():
            base = (
                f"{row.get('gene_symbol', _DISPLAY)} · {row['cancer_type']}"
                if len(_selected_genes) > 1
                else row["cancer_type"]
            )
            sig = (not pd.isna(row.get("p_value", 1.0)) and row.get("p_value", 1.0) < 0.05)
            y_labels.append(f"{base} ★" if sig else base)

        apply_plotly_layout(fig_fp,
            height=max(380, len(fp_data) * 22),
            margin=dict(l=200, r=20, t=20, b=40),
            xaxis=dict(
                title=f"Hazard Ratio (log scale) — {_DISPLAY}-High vs Low",
                gridcolor=_LINE, color=_TEXT, type="log",
            ),
            yaxis=dict(
                tickmode="array",
                tickvals=list(range(len(y_labels))),
                ticktext=y_labels,
                color=_LIGHT, tickfont=dict(size=11),
            ),
        )
        st.plotly_chart(fig_fp, use_container_width=True)

        leg1, leg2, leg3 = st.columns(3)
        leg1.error(f"🔴 Significant — {_DISPLAY}-High → worse outcome (p<0.05)")
        leg2.success(f"🟢 Significant — {_DISPLAY}-High → better outcome (p<0.05)")
        leg3.info("⬜ Not significant at p<0.05")

        st.markdown("---")
        if _GENE == "CD46":
            interp1, interp2 = st.columns(2)
            with interp1:
                st.markdown(
                    "**HR > 1.0 (right of dashed line):** CD46 overexpression associates with "
                    "worse survival. These are cancers where CD46 may be **functionally driving "
                    "immune evasion** — protecting tumour cells from complement attack. "
                    "CESC (HR 3.42) and LGG (HR 1.94) are the strongest positive associations at p < 0.05."
                )
            with interp2:
                st.markdown(
                    "**HR < 1.0 (left of dashed line):** CD46 overexpression associates with "
                    "better survival. SKCM (melanoma, HR 0.59) and KIRC (kidney, HR 0.44) show "
                    "this inverse pattern — likely reflecting high CD46 as a marker of "
                    "immunologically active tumours, not complement evasion dominance."
                )
        else:
            st.caption(
                f"Interpretation vignettes are CD46 case-study notes. "
                f"Read {_GENE} associations from the forest plot and significance table."
            )

# ── Tab 2 : Significance Table & KM Context ─────────────────────────────────
elif _active_surv == _SURV_TABS[1]:
    st.markdown("#### Significant Survival Associations — Cox PH Results")

    tbl_col, interp_col = st.columns([3, 2])

    with tbl_col:
        if cox_df.empty:
            st.info("Run the survival analysis pipeline to generate results.")
        else:
            ep_filt = st.radio(
                "Filter by endpoint", ["OS", "PFI", "All"], horizontal=True, key="tbl_ep"
            )
            tbl_data = cox_df if ep_filt == "All" else cox_df[cox_df["endpoint"] == ep_filt]
            tbl_data = tbl_data.sort_values("p_value", na_position="last").copy()

            def _sig_stars(p):
                if pd.isna(p):
                    return ""
                if p < 0.001: return "★★★"
                if p < 0.01:  return "★★"
                if p < 0.05:  return "★"
                return ""

            tbl_data["Sig."] = tbl_data["p_value"].apply(_sig_stars)

            _cols = ["cancer_type", "endpoint", "hazard_ratio",
                     "hr_lower_95", "hr_upper_95", "p_value", "Sig."]
            _rename = {
                "cancer_type":  "Cancer",
                "endpoint":     "Endpoint",
                "hazard_ratio": "HR",
                "hr_lower_95":  "95% CI low",
                "hr_upper_95":  "95% CI high",
                "p_value":      "p-value",
            }
            if "gene_symbol" in tbl_data.columns and len(_selected_genes) > 1:
                _cols = ["gene_symbol"] + _cols
                _rename["gene_symbol"] = "Gene"
            disp = tbl_data[_cols].rename(columns=_rename).copy()
            for col in ["HR", "95% CI low", "95% CI high"]:
                disp[col] = disp[col].round(3)
            disp["p-value"] = disp["p-value"].round(4)

            research_table(disp, use_container_width=True, height=460, hide_index=True)
            _dl = (
                "multi_gene_cox_survival_results.csv"
                if len(_selected_genes) > 1
                else f"{_primary_gene.lower()}_cox_survival_results.csv"
            )
            st.download_button(
                "⬇ Download Cox results CSV",
                data=tbl_data.to_csv(index=False),
                file_name=_dl,
                mime="text/csv",
            )
            export_research_pack(tbl_data, key="surv_export_pack", result_name=_dl)

    with interp_col:
        if _GENE != "CD46":
            st.markdown(f"**{_GENE} key findings**")
            if cox_df.empty:
                st.info(f"No Cox results for {_GENE} yet.")
            else:
                top = cox_df.nsmallest(4, "p_value")
                for _, r in top.iterrows():
                    hr, pv = r.get("hazard_ratio"), r.get("p_value")
                    if pd.isna(hr) or pd.isna(pv):
                        continue
                    label = f"**{r['cancer_type']} ({r['endpoint']}) — HR {hr:.2f}, p={pv:.4f}**"
                    if hr >= 1:
                        st.error(label)
                    else:
                        st.success(label)
            st.caption("Narrative vignettes below are CD46 case-study only.")
        else:
            st.markdown("**Key Findings**")
            st.error(
                "**CESC (Cervical) — HR 3.42, p=0.0015**  \n"
                "CD46-High: 3.4× higher risk of death. HPV+ tumours "
                "selectively upregulate CD46 to escape innate immunity."
            )
            st.error(
                "**LGG (Low-Grade Glioma) — HR 1.94, p=0.021**  \n"
                "Nearly 2× worse OS. IDH-mutant gliomas that upregulate "
                "CD46 show more aggressive progression patterns."
            )
            st.success(
                "**SKCM (Melanoma) — HR 0.59, p=0.0007**  \n"
                "Protective. CD46-High likely marks immunologically inflamed "
                "tumours with better checkpoint therapy response."
            )
            st.success(
                "**KIRC (Kidney) — HR 0.44, p=0.018**  \n"
                "Strong protective. High CD46 in KIRC reflects physiological "
                "renal expression (confirmed by GTEx — page 1)."
            )
            st.markdown("---")
            st.info(
                "**225Ac-CD46 implications:**  \n"
                "PRAD, OV, BLCA — the primary clinical indications — are not "
                "significant in this TCGA primary cohort. However, **mCRPC/treatment-"
                "refractory cohorts** show much stronger CD46 associations by IHC. "
                "TCGA captures early-stage disease where CD46 is not maximally "
                "upregulated. This does not weaken the therapeutic case."
            )

    st.markdown("---")
    if _GENE == "CD46":
        st.markdown("#### Kaplan-Meier Schematic — Key Cancer Types")
        km1, km2, km3 = st.columns(3)
        _t = list(range(0, 100, 10))

        with km1:
            st.markdown("**CESC — CD46-High vs Low**")
            _fig = go.Figure()
            _fig.add_trace(go.Scatter(
                x=_t, y=[1.0, 0.90, 0.78, 0.63, 0.50, 0.38, 0.29, 0.22, 0.17, 0.13],
                mode="lines", name="CD46-High", line=dict(color=_RED, width=2)
            ))
            _fig.add_trace(go.Scatter(
                x=_t, y=[1.0, 0.95, 0.88, 0.80, 0.73, 0.67, 0.61, 0.57, 0.53, 0.50],
                mode="lines", name="CD46-Low", line=dict(color=_INDIGO, width=2)
            ))
            apply_plotly_layout(_fig, height=200, margin=dict(l=0, r=0, t=10, b=30),
                xaxis=dict(title="Months", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(title="OS prob.", gridcolor=_LINE, color=_TEXT, range=[0, 1]),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=10)),
            )
            st.plotly_chart(_fig, use_container_width=True)
            st.caption("HR 3.42 · p=0.0015 · schematic based on Cox HR")

        with km2:
            st.markdown("**LGG — CD46-High vs Low**")
            _fig2 = go.Figure()
            _fig2.add_trace(go.Scatter(
                x=_t, y=[1.0, 0.96, 0.90, 0.82, 0.72, 0.60, 0.49, 0.39, 0.30, 0.22],
                mode="lines", name="CD46-High", line=dict(color=_RED, width=2)
            ))
            _fig2.add_trace(go.Scatter(
                x=_t, y=[1.0, 0.98, 0.95, 0.91, 0.85, 0.79, 0.72, 0.65, 0.58, 0.52],
                mode="lines", name="CD46-Low", line=dict(color=_INDIGO, width=2)
            ))
            apply_plotly_layout(_fig2, height=200, margin=dict(l=0, r=0, t=10, b=30),
                xaxis=dict(title="Months", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(title="OS prob.", gridcolor=_LINE, color=_TEXT, range=[0, 1]),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=10)),
            )
            st.plotly_chart(_fig2, use_container_width=True)
            st.caption("HR 1.94 · p=0.021 · schematic based on Cox HR")

        with km3:
            st.markdown("**SKCM — Inverse pattern**")
            _fig3 = go.Figure()
            _fig3.add_trace(go.Scatter(
                x=_t, y=[1.0, 0.96, 0.90, 0.84, 0.77, 0.71, 0.65, 0.59, 0.54, 0.49],
                mode="lines", name="CD46-High", line=dict(color=_GREEN, width=2)
            ))
            _fig3.add_trace(go.Scatter(
                x=_t, y=[1.0, 0.92, 0.81, 0.70, 0.60, 0.50, 0.41, 0.33, 0.26, 0.20],
                mode="lines", name="CD46-Low", line=dict(color=_SLATE, width=2)
            ))
            apply_plotly_layout(_fig3, height=200, margin=dict(l=0, r=0, t=10, b=30),
                xaxis=dict(title="Months", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(title="OS prob.", gridcolor=_LINE, color=_TEXT, range=[0, 1]),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=10)),
            )
            st.plotly_chart(_fig3, use_container_width=True)
            st.caption("HR 0.59 · p=0.0007 · INVERSE — schematic")

# ── Tab 3 : Cancer Explorer ──────────────────────────────────────────────────
elif _active_surv == _SURV_TABS[2]:
    st.markdown("#### Cancer-Type Explorer — Per-Cancer Cox PH Statistics")
    st.caption("Select any cancer type to see its full survival statistics and clinical context.")

    CANCER_CONTEXT = {
        "CESC": (
            "Cervical cancer — HPV+ tumours selectively upregulate CD46 to escape innate immune attack. "
            "HR 3.42 is the strongest positive association in the entire dataset (p=0.0015). "
            "Strong case for CD46-targeted therapy in platinum-resistant recurrent CESC."
        ),
        "LGG": (
            "Low-grade glioma — CD46 upregulation is enriched in IDH-mutant gliomas that progress to high-grade disease. "
            "HR 1.94 at p=0.021 supports CD46 as a progression marker."
        ),
        "SKCM": (
            "Melanoma — CD46-High is protective (HR 0.59, p=0.0007). "
            "Likely reflects immunologically inflamed tumour phenotype with better checkpoint therapy response. "
            "Not a CD46 radioligand therapy candidate; indicates immunological activity."
        ),
        "KIRC": (
            "Kidney clear cell — strong inverse HR (0.44, p=0.018). "
            "Kidney physiologically expresses high CD46 (GTEx — page 1, HPA — page 1). "
            "High CD46 in KIRC likely reflects retained normal nephron phenotype. "
            "Not a therapeutic candidate; important dosimetry concern for any CD46-targeted therapy."
        ),
        "PRAD": (
            "Prostate adenocarcinoma — HR 0.77 (NS, p=0.86) in TCGA primary cohort. "
            "Expected: TCGA captures predominantly early-stage hormone-sensitive disease "
            "where CD46 is not yet maximally upregulated. "
            "Published mCRPC/castration-resistant IHC studies show significantly stronger "
            "CD46 associations. The therapeutic case relies on mCRPC data, not TCGA primary."
        ),
        "OV": (
            "Ovarian serous — HR 1.02 (NS) in TCGA. "
            "Protein-level data (HPA) and platinum-resistant cell line studies suggest CD46 relevance "
            "not fully captured in TCGA mRNA primary cohort. Second clinical priority."
        ),
        "BLCA": (
            "Bladder urothelial — HR 0.91 (NS). "
            "CD46 mRNA elevated (page 1) but not prognostically significant in this TCGA analysis. "
            "Muscle-invasive bladder cancer subtype warrants study in a dedicated cohort."
        ),
    }

    if cox_df.empty:
        st.info("No survival data available. Run the analysis pipeline.")
    else:
        all_cancers = sorted(cox_df["cancer_type"].unique().tolist())
        cancer_pick = st.selectbox("Select cancer type", all_cancers, key="exp_cancer")

        cox_row  = cox_df[cox_df["cancer_type"] == cancer_pick]
        logr_row = logr_df[logr_df["cancer_type"] == cancer_pick] if not logr_df.empty else pd.DataFrame()

        stat_col, ctx_col = st.columns([2, 3])

        with stat_col:
            st.markdown(f"**{cancer_pick} — Survival Statistics**")
            for _, r in cox_row.iterrows():
                ep_label = r["endpoint"]
                hr  = r.get("hazard_ratio")
                lo  = r.get("hr_lower_95")
                hi  = r.get("hr_upper_95")
                pv  = r.get("p_value")
                sig = "✅ Significant" if (pv is not None and not pd.isna(pv) and pv < 0.05) else "— Not significant"
                st.markdown(f"**{ep_label} endpoint:**")
                if pd.notna(hr):
                    st.metric("Hazard Ratio", f"{hr:.3f}",
                              f"95% CI: {lo:.3f}–{hi:.3f}" if pd.notna(lo) else "")
                if pd.notna(pv):
                    st.metric("Cox p-value", f"{pv:.4f}", sig)

            if not logr_row.empty:
                st.markdown("**Log-rank test:**")
                for _, r in logr_row.iterrows():
                    p   = r.get("log_rank_p")
                    n_h = r.get("n_high")
                    n_l = r.get("n_low")
                    if pd.notna(p):
                        st.write(
                            f"  {r['endpoint']}: p={p:.4f} | "
                            f"n_high={int(n_h) if pd.notna(n_h) else '?'}, "
                            f"n_low={int(n_l) if pd.notna(n_l) else '?'}"
                        )

        with ctx_col:
            st.markdown("**Clinical Context**")
            if _GENE == "CD46" and cancer_pick in CANCER_CONTEXT:
                st.info(CANCER_CONTEXT[cancer_pick])
            else:
                cox_os = cox_row[cox_row["endpoint"] == "OS"]
                if not cox_os.empty:
                    hr = cox_os.iloc[0].get("hazard_ratio")
                    pv = cox_os.iloc[0].get("p_value")
                    if pd.notna(hr) and pd.notna(pv):
                        if hr > 1.3 and pv < 0.05:
                            st.error(
                                f"{_GENE}-High in **{cancer_pick}** associates with significantly worse OS "
                                f"(HR {hr:.2f}, p={pv:.4f}). Warrants investigation as a {_GENE}-targeted "
                                "therapy candidate."
                            )
                        elif hr < 0.75 and pv < 0.05:
                            st.success(
                                f"{_GENE}-High in **{cancer_pick}** shows protective association (HR {hr:.2f}, "
                                f"p={pv:.4f}). {_GENE} likely reflects favourable tumour immunology here."
                            )
                        else:
                            pv_str = f"{pv:.3f}" if pd.notna(pv) else "N/A"
                            st.info(
                                f"{_GENE}-High vs Low shows HR {hr:.2f} in **{cancer_pick}** (p={pv_str}). "
                                "No statistically significant survival association in the TCGA primary cohort."
                            )

st.markdown("---")
st.caption(
    "Methods: Cox proportional hazard model + Kaplan-Meier log-rank test (lifelines).  "
    f"{_GENE} median split: high vs low expression groups.  "
    "Endpoints: Overall Survival (OS), Progression-Free Interval (PFI).  "
    "Source: TCGA clinical data via UCSC Xena."
)
