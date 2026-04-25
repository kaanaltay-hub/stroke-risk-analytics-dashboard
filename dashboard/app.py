"""
Stroke Risk Analytics Dashboard
================================
Executive-style Streamlit dashboard for exploring demographic and clinical
risk patterns associated with stroke incidence.

Run from project root:
    streamlit run dashboard/app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Stroke Risk Analytics Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    "bg": "#F8FAFC",
    "card": "#FFFFFF",
    "dark": "#1F2937",
    "primary": "#2563EB",
    "accent": "#14B8A6",
    "risk": "#EF4444",
    "warn": "#F59E0B",
    "gray": "#64748B",
    "border": "#E5E7EB",
    "muted": "#94A3B8",
}

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {COLORS['bg']}; }}
        .block-container {{
            padding-top: 1.15rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }}

        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid {COLORS['border']};
        }}

        #MainMenu, footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{ background: transparent; }}

        .dash-header {{
            background: linear-gradient(135deg, #1F2937 0%, #2563EB 100%);
            padding: 1.25rem 1.7rem;
            border-radius: 14px;
            color: white;
            margin-bottom: 1.0rem;
            box-shadow: 0 8px 24px rgba(31, 41, 55, 0.10);
        }}
        .dash-header h1 {{
            margin: 0;
            font-size: 1.65rem;
            font-weight: 750;
            letter-spacing: -0.02em;
        }}
        .dash-header p {{
            margin: 0.28rem 0 0 0;
            opacity: 0.88;
            font-size: 0.92rem;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {COLORS['card']};
            border-radius: 12px !important;
            border: 1px solid {COLORS['border']} !important;
            padding: 0.55rem 0.85rem !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            transition: box-shadow 0.15s ease;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
        }}

        .kpi-label {{
            color: {COLORS['gray']};
            font-size: 0.70rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 750;
            margin: 0.05rem 0 0.18rem 0;
        }}
        .kpi-value {{
            color: {COLORS['dark']};
            font-size: 1.65rem;
            font-weight: 760;
            line-height: 1.05;
            margin: 0;
        }}
        .kpi-value.risk {{ color: {COLORS['risk']}; }}
        .kpi-sub {{
            color: {COLORS['muted']};
            font-size: 0.73rem;
            margin: 0.22rem 0 0.05rem 0;
        }}

        .chart-title {{
            color: {COLORS['dark']};
            font-size: 0.95rem;
            font-weight: 750;
            margin: 0.1rem 0 0.08rem 0;
        }}
        .chart-sub {{
            color: {COLORS['gray']};
            font-size: 0.78rem;
            margin: 0 0 0.4rem 0;
        }}

        .section-h {{
            color: {COLORS['dark']};
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            font-weight: 800;
            margin: 0.95rem 0 0.55rem 0;
            border-bottom: 2px solid {COLORS['border']};
            padding-bottom: 0.35rem;
        }}

        .insight-card {{
            background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
            border-left: 4px solid {COLORS['accent']};
            border-radius: 12px;
            padding: 1.0rem 1.2rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }}
        .insight-card h3 {{
            margin: 0 0 0.55rem 0;
            color: {COLORS['dark']};
            font-size: 0.98rem;
            font-weight: 760;
        }}
        .insight-card ul {{
            margin: 0;
            padding-left: 1.1rem;
            color: {COLORS['dark']};
            line-height: 1.55;
            font-size: 0.86rem;
        }}
        .insight-card li {{ margin-bottom: 0.26rem; }}
        .insight-card li b {{ color: {COLORS['risk']}; }}

        .mini-note {{
            color: {COLORS['gray']};
            font-size: 0.78rem;
            line-height: 1.45;
        }}

        div[data-testid="stTabs"] button {{
            font-weight: 700;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading & preparation
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load and prepare the analytical dataset."""
    here = Path(__file__).parent
    candidates = [
        here.parent / "data" / "raw" / "healthcare-dataset-stroke-data.csv",
        here / "data" / "raw" / "healthcare-dataset-stroke-data.csv",
        Path("data/raw/healthcare-dataset-stroke-data.csv"),
        Path("healthcare-dataset-stroke-data.csv"),
    ]
    csv_path = next((p for p in candidates if p.exists()), None)
    if csv_path is None:
        st.error(
            "Could not find healthcare-dataset-stroke-data.csv. "
            "Place it under data/raw/."
        )
        st.stop()

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()
    df = df[df["gender"] != "Other"].copy()

    df["bmi_missing"] = df["bmi"].isna()
    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    df["age_group"] = pd.cut(
        df["age"],
        bins=[0, 18, 30, 45, 60, 75, 90],
        labels=["0-18", "19-30", "31-45", "46-60", "61-75", "76-90"],
        include_lowest=True,
    )
    df["bmi_category"] = pd.cut(
        df["bmi"],
        bins=[0, 18.5, 25, 30, 100],
        labels=["Underweight", "Normal", "Overweight", "Obese"],
        include_lowest=True,
    )
    df["glucose_category"] = pd.cut(
        df["avg_glucose_level"],
        bins=[0, 100, 125, 1000],
        labels=["Normal", "Pre-diabetic", "Diabetic range"],
        include_lowest=True,
    )
    df["risk_factors"] = (
        df["hypertension"]
        + df["heart_disease"]
        + (df["avg_glucose_level"] > 125).astype(int)
        + (df["bmi"] > 30).astype(int)
        + (df["smoking_status"] == "smokes").astype(int)
    )
    return df


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def style_fig(fig: go.Figure, height: int = 280) -> go.Figure:
    """Apply consistent visual styling to Plotly figures."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        plot_bgcolor=COLORS["card"],
        paper_bgcolor=COLORS["card"],
        font=dict(family="Inter, system-ui, sans-serif", color=COLORS["dark"], size=11),
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor=COLORS["border"]),
        xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def card_title(title: str, subtitle: str = "") -> None:
    sub = f'<p class="chart-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<p class="chart-title">{title}</p>{sub}', unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str, value_class: str = "") -> None:
    cls = f' class="kpi-value {value_class}"' if value_class else ' class="kpi-value"'
    st.markdown(
        f'<p class="kpi-label">{label}</p>'
        f'<p{cls}>{value}</p>'
        f'<p class="kpi-sub">{sub}</p>',
        unsafe_allow_html=True,
    )


def stroke_rate_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    out = df.groupby(col, observed=True)["stroke"].agg(["mean", "count"]).reset_index()
    out["rate"] = out["mean"] * 100
    return out


def safe_ratio(a: float, b: float) -> float:
    return a / b if b and b > 0 else 0.0


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="dash-header">
        <h1>🩺 Stroke Risk Analytics Dashboard</h1>
        <p>Executive view of demographic and clinical stroke-risk patterns — focused on prevention, segmentation and decision support.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
df_full = load_data()

with st.sidebar:
    st.markdown("### 🎛️ Filters")
    st.caption("Refine the patient cohort shown in the dashboard.")
    st.markdown("---")

    gender_opts = sorted(df_full["gender"].dropna().unique().tolist())
    sel_gender = st.multiselect("Gender", gender_opts, default=gender_opts)

    age_opts = [str(x) for x in df_full["age_group"].cat.categories]
    sel_age = st.multiselect("Age group", age_opts, default=age_opts)

    smoking_opts = sorted(df_full["smoking_status"].dropna().unique().tolist())
    sel_smoking = st.multiselect("Smoking status", smoking_opts, default=smoking_opts)

    sel_ht = st.radio("Hypertension", ["All", "Yes", "No"], horizontal=True)
    sel_hd = st.radio("Heart disease", ["All", "Yes", "No"], horizontal=True)

    st.markdown("---")
    if st.button("Reset filters", width="stretch"):
        st.rerun()
    st.caption(f"Total records in dataset: **{len(df_full):,}**")

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
df = df_full.copy()
if sel_gender:
    df = df[df["gender"].isin(sel_gender)]
if sel_age:
    df = df[df["age_group"].astype(str).isin(sel_age)]
if sel_smoking:
    df = df[df["smoking_status"].isin(sel_smoking)]
if sel_ht == "Yes":
    df = df[df["hypertension"] == 1]
elif sel_ht == "No":
    df = df[df["hypertension"] == 0]
if sel_hd == "Yes":
    df = df[df["heart_disease"] == 1]
elif sel_hd == "No":
    df = df[df["heart_disease"] == 0]

if df.empty:
    st.warning("No patients match the current filter combination. Loosen the filters to see results.")
    st.stop()

# ---------------------------------------------------------------------------
# Dynamic metrics
# ---------------------------------------------------------------------------
total = len(df)
strokes = int(df["stroke"].sum())
stroke_rate = strokes / total * 100
avg_age = df["age"].mean()
avg_glu = df["avg_glucose_level"].mean()

# Dynamic rate comparisons for text
ht_rates = stroke_rate_by(df, "hypertension")
hd_rates = stroke_rate_by(df, "heart_disease")
ht_no = float(ht_rates.loc[ht_rates["hypertension"] == 0, "rate"].iloc[0]) if (ht_rates["hypertension"] == 0).any() else 0
ht_yes = float(ht_rates.loc[ht_rates["hypertension"] == 1, "rate"].iloc[0]) if (ht_rates["hypertension"] == 1).any() else 0
hd_no = float(hd_rates.loc[hd_rates["heart_disease"] == 0, "rate"].iloc[0]) if (hd_rates["heart_disease"] == 0).any() else 0
hd_yes = float(hd_rates.loc[hd_rates["heart_disease"] == 1, "rate"].iloc[0]) if (hd_rates["heart_disease"] == 1).any() else 0
ht_rr = safe_ratio(ht_yes, ht_no)
hd_rr = safe_ratio(hd_yes, hd_no)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    with st.container(border=True):
        kpi("Total patients", f"{total:,}", f"{total / len(df_full) * 100:.1f}% of dataset")
with k2:
    with st.container(border=True):
        kpi("Stroke cases", f"{strokes:,}", "Observed events", "risk")
with k3:
    with st.container(border=True):
        kpi("Stroke rate", f"{stroke_rate:.2f}%", "Current cohort", "risk")
with k4:
    with st.container(border=True):
        kpi("Avg age", f"{avg_age:.1f}", "years")
with k5:
    with st.container(border=True):
        kpi("Avg glucose", f"{avg_glu:.1f}", "mg/dL")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_exec, tab_deep, tab_dist = st.tabs([
    "Executive Overview",
    "Clinical Deep Dive",
    "Distributions & Correlations",
])

# ---------------------------------------------------------------------------
# TAB 1 — Executive Overview
# ---------------------------------------------------------------------------
with tab_exec:
    st.markdown('<div class="section-h">Executive Risk Overview</div>', unsafe_allow_html=True)

    top_left, top_right = st.columns([1.55, 1.05])

    with top_left:
        with st.container(border=True):
            card_title("Stroke rate by age group", "Aging is the strongest visible risk signal in this cohort.")
            by_age = stroke_rate_by(df, "age_group")
            color_seq = [COLORS["primary"], COLORS["primary"], COLORS["primary"], COLORS["accent"], COLORS["warn"], COLORS["risk"]]
            fig = go.Figure()
            fig.add_bar(
                x=by_age["age_group"].astype(str),
                y=by_age["rate"],
                marker_color=color_seq[: len(by_age)],
                text=[f"{v:.1f}%" for v in by_age["rate"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Stroke rate: %{y:.2f}%<br>Patients: %{customdata}<extra></extra>",
                customdata=by_age["count"],
            )
            fig.update_yaxes(title="Stroke rate (%)")
            fig.update_xaxes(title="")
            max_y = max(by_age["rate"].max() * 1.25, 1)
            fig.update_yaxes(range=[0, max_y])
            style_fig(fig, height=285)
            st.plotly_chart(fig, width="stretch", key="exec_age")

    with top_right:
        with st.container(border=True):
            card_title("Risk segments", "Stroke rate by number of stacked risk factors.")
            rf = df.groupby("risk_factors")["stroke"].agg(["mean", "count"]).reset_index()
            rf = rf[rf["count"] >= 5].copy()
            rf["rate"] = rf["mean"] * 100
            rf["risk_factors"] = rf["risk_factors"].astype(int)
            grad = [COLORS["gray"], COLORS["primary"], COLORS["accent"], COLORS["warn"], COLORS["risk"], COLORS["risk"]]
            fig = go.Figure()
            fig.add_bar(
                x=rf["risk_factors"].astype(str),
                y=rf["rate"],
                marker_color=[grad[min(int(v), 5)] for v in rf["risk_factors"]],
                text=[f"{v:.1f}%" for v in rf["rate"]],
                textposition="outside",
                customdata=rf["count"],
                hovertemplate="<b>%{x} risk factors</b><br>Stroke rate: %{y:.2f}%<br>Patients: %{customdata}<extra></extra>",
            )
            fig.update_xaxes(title="Number of risk factors")
            fig.update_yaxes(title="Stroke rate (%)", range=[0, max(rf["rate"].max() * 1.25, 1) if len(rf) else 1])
            style_fig(fig, height=285)
            st.plotly_chart(fig, width="stretch", key="exec_risk_segments")

    mid1, mid2, mid3 = st.columns([1, 1, 1.25])

    with mid1:
        with st.container(border=True):
            card_title("Hypertension", f"Observed rate ratio: {ht_rr:.1f}× vs. non-hypertensive patients." if ht_rr else "Observed stroke-rate comparison.")
            rates = ht_rates.sort_values("hypertension")
            fig = go.Figure()
            fig.add_bar(
                x=["No", "Yes"],
                y=rates["rate"],
                marker_color=[COLORS["gray"], COLORS["risk"]],
                text=[f"{v:.1f}%" for v in rates["rate"]],
                textposition="outside",
            )
            fig.update_yaxes(title="Stroke rate (%)", range=[0, max(rates["rate"].max() * 1.25, 1)])
            style_fig(fig, height=235)
            st.plotly_chart(fig, width="stretch", key="exec_ht")

    with mid2:
        with st.container(border=True):
            card_title("Heart disease", f"Observed rate ratio: {hd_rr:.1f}× vs. patients without heart disease." if hd_rr else "Observed stroke-rate comparison.")
            rates = hd_rates.sort_values("heart_disease")
            fig = go.Figure()
            fig.add_bar(
                x=["No", "Yes"],
                y=rates["rate"],
                marker_color=[COLORS["gray"], COLORS["risk"]],
                text=[f"{v:.1f}%" for v in rates["rate"]],
                textposition="outside",
            )
            fig.update_yaxes(title="Stroke rate (%)", range=[0, max(rates["rate"].max() * 1.25, 1)])
            style_fig(fig, height=235)
            st.plotly_chart(fig, width="stretch", key="exec_hd")

    with mid3:
        high_risk_seg = df[df["risk_factors"] >= 2]
        high_risk_rate = high_risk_seg["stroke"].mean() * 100 if len(high_risk_seg) else 0.0
        top_age_rate = by_age["rate"].max() if len(by_age) else 0
        top_age_group = str(by_age.loc[by_age["rate"].idxmax(), "age_group"]) if len(by_age) else "N/A"
        st.markdown(
            f"""
            <div class="insight-card">
                <h3>💡 Key findings from the current cohort</h3>
                <ul>
                    <li>The highest observed age-group stroke rate is in <b>{top_age_group}</b> with <b>{top_age_rate:.1f}%</b>.</li>
                    <li>Hypertension and heart disease are both linked with visibly higher observed stroke rates.</li>
                    <li>Patients with <b>2+ stacked risk factors</b> show a stroke rate of <b>{high_risk_rate:.1f}%</b>.</li>
                    <li>These findings are associative and should support screening prioritization, not causal diagnosis.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# TAB 2 — Clinical Deep Dive
# ---------------------------------------------------------------------------
with tab_deep:
    st.markdown('<div class="section-h">Clinical & Lifestyle Deep Dive</div>', unsafe_allow_html=True)

    d1, d2 = st.columns(2)

    with d1:
        with st.container(border=True):
            card_title("Stroke rate by smoking status", "Interpret carefully: smoking categories may reflect age and data-quality effects.")
            rates = stroke_rate_by(df, "smoking_status").sort_values("rate")
            fig = go.Figure()
            fig.add_bar(
                x=rates["rate"],
                y=rates["smoking_status"],
                orientation="h",
                marker_color=COLORS["primary"],
                text=[f"{v:.1f}%" for v in rates["rate"]],
                textposition="outside",
                customdata=rates["count"],
                hovertemplate="<b>%{y}</b><br>Stroke rate: %{x:.2f}%<br>Patients: %{customdata}<extra></extra>",
            )
            fig.update_xaxes(title="Stroke rate (%)", range=[0, max(rates["rate"].max() * 1.25, 1)])
            style_fig(fig, height=330)
            st.plotly_chart(fig, width="stretch", key="deep_smoking")

    with d2:
        with st.container(border=True):
            card_title("Stroke rate by glucose category", "Higher glucose ranges show elevated observed stroke rates.")
            rates = stroke_rate_by(df, "glucose_category")
            fig = go.Figure()
            fig.add_bar(
                x=rates["glucose_category"].astype(str),
                y=rates["rate"],
                marker_color=[COLORS["accent"], COLORS["warn"], COLORS["risk"]][: len(rates)],
                text=[f"{v:.1f}%" for v in rates["rate"]],
                textposition="outside",
                customdata=rates["count"],
                hovertemplate="<b>%{x}</b><br>Stroke rate: %{y:.2f}%<br>Patients: %{customdata}<extra></extra>",
            )
            fig.update_yaxes(title="Stroke rate (%)", range=[0, max(rates["rate"].max() * 1.25, 1)])
            style_fig(fig, height=330)
            st.plotly_chart(fig, width="stretch", key="deep_glucose")

    d3, d4 = st.columns(2)

    with d3:
        with st.container(border=True):
            card_title("Stroke rate by BMI category", "BMI alone is weaker than age and clinical history in this dataset.")
            rates = stroke_rate_by(df, "bmi_category")
            fig = go.Figure()
            fig.add_bar(
                x=rates["bmi_category"].astype(str),
                y=rates["rate"],
                marker_color=COLORS["accent"],
                text=[f"{v:.1f}%" for v in rates["rate"]],
                textposition="outside",
                customdata=rates["count"],
                hovertemplate="<b>%{x}</b><br>Stroke rate: %{y:.2f}%<br>Patients: %{customdata}<extra></extra>",
            )
            fig.update_yaxes(title="Stroke rate (%)", range=[0, max(rates["rate"].max() * 1.25, 1)])
            style_fig(fig, height=315)
            st.plotly_chart(fig, width="stretch", key="deep_bmi_cat")

    with d4:
        with st.container(border=True):
            card_title("Risk-factor definition", "The stacked segment combines five interpretable risk indicators.")
            st.markdown(
                """
                <div class="mini-note">
                <b>Risk factors counted:</b><br>
                1. Hypertension<br>
                2. Heart disease<br>
                3. Average glucose level &gt; 125 mg/dL<br>
                4. BMI &gt; 30<br>
                5. Current smoking status<br><br>
                This score is not a medical diagnosis. It is a simple analytical segmentation used to summarize risk concentration in the dataset.
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# TAB 3 — Distributions & Correlations
# ---------------------------------------------------------------------------
with tab_dist:
    st.markdown('<div class="section-h">Distributions & Correlations</div>', unsafe_allow_html=True)

    c6, c7, c8 = st.columns(3)

    with c6:
        with st.container(border=True):
            card_title("BMI distribution by stroke status", "Density overlay of stroke vs. non-stroke patients.")
            fig = go.Figure()
            for v, label, color in [(0, "No stroke", COLORS["gray"]), (1, "Stroke", COLORS["risk"] )]:
                sub = df[df["stroke"] == v]
                if len(sub):
                    fig.add_trace(go.Histogram(
                        x=sub["bmi"],
                        name=label,
                        marker_color=color,
                        opacity=0.65,
                        nbinsx=35,
                        histnorm="probability density",
                    ))
            fig.update_layout(barmode="overlay")
            fig.update_xaxes(title="BMI", range=[10, 60])
            fig.update_yaxes(title="Density")
            style_fig(fig, height=350)
            st.plotly_chart(fig, width="stretch", key="dist_bmi")

    with c7:
        with st.container(border=True):
            card_title("Age vs. average glucose", "Stroke cases are highlighted in red.")
            fig = go.Figure()
            no = df[df["stroke"] == 0]
            yes = df[df["stroke"] == 1]
            if len(no):
                fig.add_trace(go.Scatter(
                    x=no["age"],
                    y=no["avg_glucose_level"],
                    mode="markers",
                    name="No stroke",
                    marker=dict(color=COLORS["gray"], size=4, opacity=0.35),
                ))
            if len(yes):
                fig.add_trace(go.Scatter(
                    x=yes["age"],
                    y=yes["avg_glucose_level"],
                    mode="markers",
                    name="Stroke",
                    marker=dict(color=COLORS["risk"], size=6, opacity=0.85, line=dict(width=0.5, color="white")),
                ))
            fig.add_hline(
                y=125,
                line_dash="dash",
                line_color=COLORS["dark"],
                opacity=0.4,
                annotation_text="Glucose threshold",
                annotation_position="top left",
            )
            fig.update_xaxes(title="Age (years)")
            fig.update_yaxes(title="Glucose (mg/dL)")
            style_fig(fig, height=350)
            st.plotly_chart(fig, width="stretch", key="dist_age_glucose")

    with c8:
        with st.container(border=True):
            card_title("Correlation heatmap", "Technical view of pairwise linear relationships.")
            cols = ["age", "avg_glucose_level", "bmi", "hypertension", "heart_disease", "stroke"]
            labels = ["Age", "Glucose", "BMI", "HT", "HD", "Stroke"]
            corr = df[cols].corr().values
            fig = go.Figure(data=go.Heatmap(
                z=corr,
                x=labels,
                y=labels,
                colorscale=[[0, COLORS["primary"]], [0.5, "#FFFFFF"], [1, COLORS["risk"]]],
                zmid=0,
                zmin=-0.5,
                zmax=0.5,
                text=[[f"{v:.2f}" for v in row] for row in corr],
                texttemplate="%{text}",
                textfont={"size": 11, "color": COLORS["dark"]},
                showscale=True,
                colorbar=dict(thickness=10, len=0.7),
            ))
            style_fig(fig, height=350)
            st.plotly_chart(fig, width="stretch", key="dist_corr")

    st.markdown(
        f"""
        <div style='color:{COLORS['gray']}; font-size:0.82rem; margin-top:0.7rem;'>
            Note: Correlations and distributions are exploratory. They do not prove causality and should be interpreted together with domain knowledge and the full notebook analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div style='text-align:center; color:{COLORS['muted']}; font-size:0.76rem; margin-top: 1.25rem;'>
        Source: Stroke Prediction Dataset · Findings are associative, not causal · See <code>notebooks/stroke_risk_analysis.ipynb</code> for the full hypothesis-driven analysis.
    </div>
    """,
    unsafe_allow_html=True,
)
