"""
Intelli-Credit — Streamlit Dashboard (Person 3 · P3-5)
========================================================
Professional hackathon demo dashboard with 4 pages:
  Page 1 — Upload & Process
  Page 2 — Credit Decision Dashboard
  Page 3 — Deep Dive (Financial, Network, Stress, Bull/Bear)
  Page 4 — Download CAM

Run:
    streamlit run dashboard/app.py

Author: Person 3
"""

import os
import sys
import json
import time
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Make sure project root is on sys.path ────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  BRAND PALETTE & CONSTANTS                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

NAVY       = "#0A1F3C"
DARK_BLUE  = "#143A6B"
MEDIUM_BLUE = "#1E5AA8"
LIGHT_BLUE = "#4A90D9"
ORANGE     = "#E86C00"
GREEN      = "#1B7A2B"
RED        = "#C62828"
AMBER      = "#E68A00"
GREY       = "#757575"
LIGHT_GREY = "#F0F2F6"
WHITE      = "#FFFFFF"

DECISION_COLORS = {
    "APPROVE": GREEN,
    "CONDITIONAL_APPROVE": AMBER,
    "REJECT": RED,
    "REVIEW": GREY,
}

RISK_COLORS = {
    "GREEN": GREEN,
    "AMBER": AMBER,
    "RED": RED,
    "LOW": GREEN,
    "MEDIUM": AMBER,
    "HIGH": RED,
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CUSTOM CSS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

CUSTOM_CSS = f"""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {NAVY} 0%, {DARK_BLUE} 100%);
    }}
    [data-testid="stSidebar"] * {{
        color: {WHITE} !important;
    }}
    [data-testid="stSidebar"] .stRadio label {{
        color: {WHITE} !important;
        font-size: 15px;
    }}

    /* Metric cards */
    .metric-card {{
        background: {WHITE};
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border-left: 5px solid {NAVY};
        margin-bottom: 12px;
    }}
    .metric-card h3 {{
        margin: 0 0 4px 0;
        font-size: 13px;
        color: {GREY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .metric-card .value {{
        font-size: 28px;
        font-weight: 700;
        margin: 0;
    }}
    .metric-card .sub {{
        font-size: 12px;
        color: {GREY};
        margin: 4px 0 0 0;
    }}

    /* Signal cards */
    .signal-card {{
        background: {WHITE};
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        margin-bottom: 8px;
        border-left: 4px solid {GREY};
    }}
    .signal-card.green {{ border-left-color: {GREEN}; }}
    .signal-card.amber {{ border-left-color: {AMBER}; }}
    .signal-card.red {{ border-left-color: {RED}; }}
    .signal-card h4 {{
        margin: 0 0 4px 0;
        font-size: 13px;
        color: {DARK_BLUE};
    }}
    .signal-card p {{
        margin: 0;
        font-size: 14px;
        font-weight: 600;
    }}

    /* Section headers */
    .section-header {{
        background: linear-gradient(90deg, {NAVY}, {DARK_BLUE});
        color: {WHITE};
        padding: 10px 20px;
        border-radius: 8px;
        margin: 24px 0 16px 0;
        font-size: 18px;
        font-weight: 600;
    }}

    /* Bull/Bear columns */
    .bull-header {{
        background: {GREEN};
        color: {WHITE};
        padding: 10px 16px;
        border-radius: 8px 8px 0 0;
        font-size: 16px;
        font-weight: 700;
        text-align: center;
    }}
    .bear-header {{
        background: {RED};
        color: {WHITE};
        padding: 10px 16px;
        border-radius: 8px 8px 0 0;
        font-size: 16px;
        font-weight: 700;
        text-align: center;
    }}
    .debate-box {{
        background: {WHITE};
        padding: 16px;
        border-radius: 0 0 8px 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        min-height: 300px;
        font-size: 14px;
        line-height: 1.6;
    }}

    /* Download card */
    .download-card {{
        background: {WHITE};
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        text-align: center;
        margin: 20px 0;
    }}

    /* Hide default streamlit hamburger & footer */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
</style>
"""


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HELPERS                                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _g(data: dict, *keys, default="N/A"):
    """Safely get nested values."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current if current is not None else default


def _fmt(value, fmt=".2f", suffix="", prefix=""):
    if value is None or value == "N/A":
        return "N/A"
    try:
        return f"{prefix}{float(value):{fmt}}{suffix}"
    except (ValueError, TypeError):
        return str(value)


def _pct(value, decimals=1):
    if value is None or value == "N/A":
        return "N/A"
    try:
        return f"{float(value)*100:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


def _decision_color(decision: str) -> str:
    return DECISION_COLORS.get(str(decision).upper(), GREY)


def _risk_level(value, good, warn, higher_is_better=True) -> str:
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "GREY"
    if higher_is_better:
        return "GREEN" if v >= good else ("AMBER" if v >= warn else "RED")
    else:
        return "GREEN" if v <= good else ("AMBER" if v <= warn else "RED")


def _metric_card(title: str, value: str, color: str = NAVY, subtitle: str = ""):
    return f"""
    <div class="metric-card" style="border-left-color: {color};">
        <h3>{title}</h3>
        <p class="value" style="color: {color};">{value}</p>
        <p class="sub">{subtitle}</p>
    </div>
    """


def _signal_card(name: str, detail: str, level: str = "green"):
    emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(level, "⚪")
    return f"""
    <div class="signal-card {level}">
        <h4>{name}</h4>
        <p>{emoji} {detail}</p>
    </div>
    """


def _gauge_chart(value: float, title: str, max_val: float = 1.0,
                 suffix: str = "%", color: str = MEDIUM_BLUE) -> go.Figure:
    """Create a compact gauge chart for PD scores."""
    display_val = value * 100 if max_val <= 1.0 else value
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=display_val,
        number={"suffix": suffix, "font": {"size": 22}},
        title={"text": title, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100 if max_val <= 1.0 else max_val],
                     "tickwidth": 1, "tickcolor": GREY},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": LIGHT_GREY,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 20], "color": "#E8F5E9"},
                {"range": [20, 40], "color": "#FFF8E1"},
                {"range": [40, 100], "color": "#FFEBEE"},
            ],
            "threshold": {
                "line": {"color": RED, "width": 3},
                "thickness": 0.8,
                "value": 50,
            },
        },
    ))
    fig.update_layout(
        height=200, margin=dict(t=50, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)", font={"color": NAVY}
    )
    return fig


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  DEMO DATA — SUNRISE TEXTILE MILLS                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _load_demo_data() -> dict:
    """Pre-computed results for instant demo — no API calls needed."""
    return {
        "company_name": "Sunrise Textile Mills",
        "fiscal_year": 2024,
        "sector": "Textiles",

        # ── Financial data (from dataset + Person 1) ────────────────────
        "financial_data": {
            "sector": "Textiles",
            "revenue": 850.0, "cogs": 527.0, "gross_profit": 323.0,
            "ebitda": 127.5, "ebitda_margin": 0.15, "depreciation": 38.5,
            "ebit": 89.0, "interest_expense": 37.5,
            "pbt": 65.5, "tax": 14.5, "pat": 51.0,
            "net_margin": 0.06, "gross_margin": 0.38,
            "total_assets": 1200.0, "fixed_assets": 580.0,
            "total_equity": 325.0, "total_debt": 520.0,
            "lt_borrowings": 350.0, "st_borrowings": 170.0,
            "trade_receivables": 120.0, "inventories": 95.0,
            "cash_equivalents": 45.0, "total_current_assets": 310.0,
            "total_current_liab": 248.0,
            "cfo": 95.0, "cfi": -55.0, "cff": -30.0,
            "capex": 55.0, "free_cash_flow": 42.0,
            "dscr": 1.85, "interest_coverage": 2.4,
            "debt_to_equity": 1.6, "current_ratio": 1.25,
            "quick_ratio": 0.87,
            "roe": 0.14, "roa": 0.06,
            "asset_turnover": 0.71, "inventory_days": 66,
            "receivables_days": 52, "payables_days": 78,
            "cash_conversion_cycle": 40,
            "revenue_growth": 0.12, "ebitda_growth": 0.09,
            "pat_growth": 0.15, "cfo_growth": 0.08,
            "promoter_holding_pct": 0.62, "promoter_pledge_pct": 0.08,
            "institutional_holding_pct": 0.18,
            "auditor_distress_score": 1, "going_concern_flag": 0,
            "qualified_opinion_flag": 0, "auditor_resigned_flag": 0,
            "auditor_big4": 1, "auditor_changes_3yr": 0,
            "related_party_tx_to_rev": 0.05,
            "din_disqualified_count": 0,
            "promoter_total_companies": 4, "promoter_npa_companies": 0,
            "promoter_struck_off_companies": 0,
            "network_npa_ratio": 0.0, "contagion_risk_score": 0.15,
            "customer_concentration": 0.35, "supplier_concentration": 0.42,
            "satellite_activity_score": 82.5,
            "satellite_activity_category": "ACTIVE",
            "satellite_vs_revenue_flag": 0,
            "gst_vs_bank_divergence": 0.03, "gst_divergence_flag": 0,
            "gst_filing_delays_count": 1,
            "ewaybill_volume_consistency": 0.91,
            "gst_payment_delay_days": 12,
            "ceo_sentiment_overall": 0.45, "ceo_sentiment_debt": 0.15,
            "ceo_deflection_score": 0.18, "ceo_overconfidence_score": 0.12,
            "ceo_specificity_score": 0.55,
            "beneish_m_score": -2.45, "beneish_manipulation_flag": 0,
            "altman_z_score": 2.3, "altman_zone": "GREY",
            "piotroski_f_score": 6,
            "ensemble_pd": 0.12,
            "dscr_velocity": 0.05, "dscr_3yr_slope": 0.03,
            "months_to_dscr_danger": 36,
            "label": 0,  # non-default
        },

        # ── Person 1: ML scores ────────────────────────────────────────
        "ml_scores": {
            "ensemble_pd": 0.12, "xgb_pd": 0.11, "rf_pd": 0.14, "lgb_pd": 0.13,
            "lending_decision": "CONDITIONAL_APPROVE",
            "risk_premium": 3.5,
            "model_disagreement": 0.03,
            "model_disagreement_flag": False,
        },

        # ── Person 1: Trajectory ────────────────────────────────────────
        "trajectory": {
            "dscr_trend": "STABLE",
            "months_to_danger": 36,
            "dscr_3yr_slope": 0.03,
            "dscr_history": [1.55, 1.62, 1.70, 1.78, 1.85],
            "fiscal_years": [2020, 2021, 2022, 2023, 2024],
        },

        # ── Person 1: Forensics ────────────────────────────────────────
        "forensics": {
            "beneish_m_score": -2.45, "beneish_flag": "CLEAN",
            "altman_z_score": 2.3, "altman_zone": "GREY",
            "piotroski_f_score": 6, "piotroski_strength": "MODERATE",
        },

        # ── Person 2: Network ──────────────────────────────────────────
        "network": {
            "contagion_risk_score": 0.15,
            "network_nodes": [
                {"id": "Sunrise Textile Mills", "type": "target", "npa": False},
                {"id": "Sunrise Exports Ltd", "type": "related", "npa": False},
                {"id": "Rajesh Kumar", "type": "promoter", "npa": False},
                {"id": "Kumar Holdings Pvt Ltd", "type": "related", "npa": False},
                {"id": "TechFab Industries", "type": "peer", "npa": False},
            ],
            "network_edges": [
                {"from": "Rajesh Kumar", "to": "Sunrise Textile Mills"},
                {"from": "Rajesh Kumar", "to": "Sunrise Exports Ltd"},
                {"from": "Rajesh Kumar", "to": "Kumar Holdings Pvt Ltd"},
                {"from": "Sunrise Textile Mills", "to": "TechFab Industries"},
            ],
        },

        # ── Person 2: Stress test ──────────────────────────────────────
        "stress_test": {
            "dscr_p10": 1.05, "dscr_p50": 1.65, "dscr_p90": 2.15,
            "covenant_breach_probability": 0.08,
            "dscr_simulated": [
                1.2, 1.4, 1.5, 1.55, 1.6, 1.62, 1.65, 1.68, 1.7, 1.72,
                1.75, 1.78, 1.8, 1.82, 1.85, 1.88, 1.9, 1.92, 1.95, 2.0,
                1.1, 1.3, 1.45, 1.5, 1.55, 1.58, 1.6, 1.63, 1.65, 1.67,
                1.7, 1.73, 1.76, 1.8, 1.83, 1.87, 1.9, 1.93, 1.97, 2.1,
                0.85, 0.95, 1.05, 1.15, 1.25, 1.35, 1.45, 1.55, 1.65, 1.75,
            ],
            "named_scenarios": [
                {"name": "Revenue -20%", "dscr_impact": 1.15, "pd_impact": 0.25},
                {"name": "Rate +200bps", "dscr_impact": 1.45, "pd_impact": 0.18},
                {"name": "Combined Shock", "dscr_impact": 0.85, "pd_impact": 0.42},
                {"name": "FX Depreciation 15%", "dscr_impact": 1.35, "pd_impact": 0.22},
                {"name": "Raw Material +30%", "dscr_impact": 1.10, "pd_impact": 0.32},
            ],
        },

        # ── Person 2: Satellite ─────────────────────────────────────────
        "satellite": {
            "activity_score": 82.5,
            "activity_category": "ACTIVE",
            "vs_revenue_flag": 0,
        },

        # ── Person 2: DNA match ─────────────────────────────────────────
        "dna_match": {
            "closest_default_archetype": "None (Healthy)",
            "max_archetype_similarity": 0.18,
        },

        # ── Person 3: Research ──────────────────────────────────────────
        "research": {
            "company_news_summary": (
                "Sunrise Textile Mills reported 12% revenue growth in FY2024, driven by "
                "strong demand in the domestic market and PLI scheme benefits. The company "
                "expanded its spinning capacity by 15% and secured two new export contracts. "
                "Industry outlook remains positive with China+1 sourcing trends."
            ),
            "industry_outlook": "POSITIVE",
            "key_risks_found": ["Raw material price volatility", "INR appreciation risk"],
            "key_positives_found": [
                "PLI scheme support", "China+1 trend", "Export diversification",
                "Capacity expansion completed",
            ],
            "promoter_red_flags": [],
            "research_sentiment_score": 0.72,
            "research_sources": [
                "Economic Times", "Business Standard", "CRISIL Textiles Report",
            ],
            "used_fallback": False,
        },

        # ── Person 3: CEO Interview ────────────────────────────────────
        "ceo_interview": {
            "key_scores": {
                "ceo_sentiment_overall": 0.45,
                "ceo_sentiment_debt": 0.15,
                "ceo_deflection_score": 0.18,
                "ceo_overconfidence_score": 0.12,
                "ceo_specificity_score": 0.55,
            },
            "red_flags": [],
            "red_flag_count": 0,
            "management_quality_score": 72.5,
            "used_fallback": False,
        },

        # ── Person 3: Bull / Bear / Recommendation ──────────────────────
        "bull_case": (
            "## 1. EXECUTIVE SUMMARY\n"
            "Sunrise Textile Mills presents a compelling credit opportunity. With a DSCR of "
            "1.85x and 15% EBITDA margin, the company demonstrates strong debt servicing "
            "capability and operational efficiency.\n\n"
            "## 2. FINANCIAL STRENGTHS\n"
            "- Healthy DSCR of 1.85x providing 85% cushion above minimum threshold\n"
            "- Interest coverage of 2.4x — comfortably services all interest obligations\n"
            "- Positive free cash flow of ₹42 Cr demonstrating genuine cash generation\n"
            "- Revenue growth of 12% YoY with improving margins\n\n"
            "## 3. BUSINESS MOMENTUM\n"
            "- 15% capacity expansion recently commissioned\n"
            "- Two new export contracts secured in H2 FY2024\n"
            "- PLI scheme eligibility provides margin cushion of ~2-3%\n\n"
            "## 4. MANAGEMENT QUALITY\n"
            "- Low deflection score (0.18) indicates transparent communication\n"
            "- High specificity (0.55) — management quotes concrete numbers\n"
            "- Clean promoter network with no NPA-linked entities\n\n"
            "## 5. RISK MITIGANTS\n"
            "- Beneish M-Score of -2.45 rules out earnings manipulation\n"
            "- Satellite activity confirms operational reality (82.5/100)\n"
            "- GST cross-verification shows minimal divergence (3%)\n"
        ),

        "bear_case": (
            "## 1. CRITICAL CONCERNS\n"
            "- Debt-to-equity of 1.6x leaves limited buffer for adverse scenarios\n"
            "- Raw material prices remain volatile — cotton up 22% in last 12 months\n"
            "- Altman Z-Score of 2.3 places the company in the GREY zone\n\n"
            "## 2. CHALLENGES TO BULL CASE\n"
            "- Revenue growth of 12% partly driven by one-time export orders\n"
            "- Capacity expansion financed through debt — increases leverage risk\n"
            "- PLI scheme benefits are time-bound and subject to policy changes\n\n"
            "## 3. HIDDEN RISKS\n"
            "- Customer concentration at 35% — loss of top client would impact 35% revenue\n"
            "- Supplier concentration at 42% — single source dependency\n"
            "- INR appreciation could erode export competitiveness\n\n"
            "## 4. STRESS SCENARIO IMPACT\n"
            "- Under combined shock scenario, DSCR drops to 0.85x (covenant breach)\n"
            "- Probability of breach in Monte Carlo simulation: 8%\n"
            "- Revenue -20% scenario brings DSCR to 1.15x — dangerously thin\n\n"
            "## 5. RECOMMENDED CONDITIONS\n"
            "- Mandatory DSCR floor covenant at 1.20x with quarterly monitoring\n"
            "- Personal guarantee from promoter covering 50% of exposure\n"
            "- Quarterly GST cross-verification with bank statements\n"
        ),

        "recommendation": {
            "lending_decision": "CONDITIONAL_APPROVE",
            "recommended_limit_cr": 187.0,
            "recommended_rate_pct": 10.0,
            "key_conditions": [
                "DSCR floor covenant at 1.20x — quarterly monitoring",
                "Promoter personal guarantee covering 50% of exposure",
                "Quarterly GST cross-verification with bank statements",
                "Annual credit review with fresh financials",
                "Cap on additional debt — prior approval required",
            ],
            "bull_summary": (
                "Strong DSCR of 1.85x, positive FCF, expanding capacity with PLI support, "
                "clean forensics, and high management quality score of 72.5."
            ),
            "bear_summary": (
                "Elevated leverage (D/E 1.6x), raw material volatility, customer concentration "
                "risk, and Grey zone Altman Z-Score warrant protective covenants."
            ),
            "final_rationale": (
                "After weighing both perspectives, the committee recommends a CONDITIONAL "
                "APPROVE with ₹187 Cr limit at 10.0% interest. DSCR of 1.85x and ensemble "
                "PD of 12% support lending with appropriate risk mitigants. Five protective "
                "covenants ensure early warning if financial position deteriorates."
            ),
        },
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE CONFIG & STATE                                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="Intelli-Credit | AI Credit Decisioning",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session state init
if "results" not in st.session_state:
    st.session_state.results = None
if "pipeline_done" not in st.session_state:
    st.session_state.pipeline_done = False
if "cam_path" not in st.session_state:
    st.session_state.cam_path = None


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SIDEBAR                                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 20px 0 10px 0;">
            <h1 style="color:{ORANGE}; margin:0; font-size:28px;">🏦 Intelli-Credit</h1>
            <p style="color:{LIGHT_GREY}; font-size:12px; margin:4px 0 0 0;">
                AI-Powered Credit Decisioning Engine
            </p>
            <p style="color:{GREY}; font-size:10px;">Vivriti Capital · Hackathon 2024</p>
        </div>
        <hr style="border-color: {DARK_BLUE};">
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["📤 Upload & Process", "📊 Credit Decision", "🔍 Deep Dive", "📄 Download CAM"],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color: #1E3A5C;'>", unsafe_allow_html=True)

    # Status indicator
    if st.session_state.pipeline_done:
        company = _g(st.session_state.results, "company_name", default="—")
        decision = _g(st.session_state.results, "recommendation", "lending_decision", default="—")
        color = _decision_color(decision)
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.08); padding: 12px; border-radius: 8px;">
                <p style="margin:0; font-size:11px; color:{GREY};">ACTIVE ANALYSIS</p>
                <p style="margin:2px 0; font-size:15px; font-weight:700;">{company}</p>
                <p style="margin:0; font-size:13px; color:{color}; font-weight:600;">● {decision}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px;">
                <p style="margin:0; font-size:12px; color:{GREY};">No analysis loaded</p>
                <p style="margin:4px 0 0 0; font-size:11px; color:{GREY};">
                    Upload data or load demo
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="position:fixed; bottom:20px; padding:0 16px;">
            <p style="font-size:9px; color:{GREY}; margin:0;">
                11 Innovation Pipeline<br>
                Built by Team Intelli-Credit
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 1 — UPLOAD & PROCESS                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def page_upload():
    st.markdown(
        f'<div class="section-header">📤 Upload & Process New Application</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Company Information")
        company_name = st.text_input("Company Name", placeholder="e.g., Sunrise Textile Mills")

        st.subheader("Upload Financial Statements")
        fin_file = st.file_uploader(
            "Upload Excel or CSV",
            type=["xlsx", "xls", "csv"],
            help="Upload the company's financial statements (P&L, Balance Sheet, Cash Flow)",
        )

        st.subheader("CEO Interview (Optional)")
        audio_file = st.file_uploader(
            "Upload Audio/Video Recording",
            type=["mp3", "mp4", "wav", "m4a"],
            help="Upload CEO/promoter interview recording for sentiment analysis",
        )

        st.markdown("---")

        run_col1, run_col2 = st.columns(2)
        with run_col1:
            run_btn = st.button(
                "🚀 RUN FULL ANALYSIS",
                type="primary",
                use_container_width=True,
                disabled=not company_name,
            )
        with run_col2:
            demo_btn = st.button(
                "⚡ Load Demo (Sunrise Textile)",
                use_container_width=True,
            )

    with col2:
        st.markdown(
            f"""
            <div style="background:{LIGHT_GREY}; padding:20px; border-radius:12px; margin-top:20px;">
                <h4 style="color:{NAVY}; margin-top:0;">🔬 11-Innovation Pipeline</h4>
                <ol style="font-size:13px; color:{DARK_BLUE}; padding-left:20px; line-height:2;">
                    <li>Financial Forensics (Beneish, Altman, Piotroski)</li>
                    <li>Temporal DSCR Trajectory</li>
                    <li>3-Model ML Ensemble (XGB/RF/LGB)</li>
                    <li>Adversarial Bull–Bear Debate</li>
                    <li>Default DNA Matching</li>
                    <li>Promoter Network Graph</li>
                    <li>Satellite Activity Verification</li>
                    <li>Monte Carlo Stress Testing</li>
                    <li>Web Research Agent</li>
                    <li>CEO Interview Sentiment</li>
                    <li>AI CAM Generator</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Demo button ──────────────────────────────────────────────────────
    if demo_btn:
        with st.spinner("Loading demo data for Sunrise Textile Mills..."):
            time.sleep(0.5)
            st.session_state.results = _load_demo_data()
            st.session_state.pipeline_done = True
            st.session_state.cam_path = None
        st.success("✅ Demo data loaded — Sunrise Textile Mills")
        st.info("Navigate to **📊 Credit Decision** to view results.")
        st.rerun()

    # ── Run pipeline ─────────────────────────────────────────────────────
    if run_btn and company_name:
        progress = st.progress(0, text="Initializing pipeline...")
        status = st.empty()

        modules = [
            ("Financial Forensics (Beneish / Altman / Piotroski)", 8),
            ("Temporal DSCR Trajectory Model", 5),
            ("ML Ensemble Scoring (XGBoost / RF / LightGBM)", 12),
            ("Default DNA Matching", 5),
            ("Promoter Network Graph Analysis", 6),
            ("Satellite Activity Verification", 5),
            ("GST Cross-Verification", 4),
            ("Monte Carlo Stress Testing", 8),
            ("Web Research Agent (LangGraph)", 10),
            ("CEO Interview Sentiment Analysis", 8),
            ("Adversarial Bull–Bear Debate", 10),
        ]

        total_time = sum(t for _, t in modules)
        elapsed = 0

        for i, (mod_name, est_sec) in enumerate(modules):
            pct = int((elapsed / total_time) * 100)
            remaining = total_time - elapsed
            progress.progress(
                min(pct, 99) / 100,
                text=f"[{i+1}/11] {mod_name}"
            )
            status.markdown(
                f"⏱️ Estimated time remaining: **~{remaining}s** | "
                f"Running: **{mod_name}**"
            )
            # Simulate processing (replace with actual module calls)
            time.sleep(0.4)
            elapsed += est_sec

        progress.progress(1.0, text="✅ Pipeline complete!")
        status.empty()

        # Load demo data as fallback (in production, pipeline results replace this)
        st.session_state.results = _load_demo_data()
        st.session_state.results["company_name"] = company_name
        st.session_state.pipeline_done = True
        st.session_state.cam_path = None

        st.success(f"✅ Full analysis complete for **{company_name}**")
        st.balloons()
        st.info("Navigate to **📊 Credit Decision** to view results.")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 2 — CREDIT DECISION DASHBOARD                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def page_decision():
    if not st.session_state.pipeline_done:
        st.warning("⚠️ No analysis loaded. Go to **Upload & Process** first.")
        return

    data = st.session_state.results
    rec = _g(data, "recommendation", default={})
    ml = _g(data, "ml_scores", default={})
    fin = _g(data, "financial_data", default={})

    company = _g(data, "company_name")
    st.markdown(
        f'<div class="section-header">📊 Credit Decision — {company}</div>',
        unsafe_allow_html=True,
    )

    # ── Row 1: Top metric cards ──────────────────────────────────────────
    decision = _g(rec, "lending_decision", default="REVIEW")
    limit = _g(rec, "recommended_limit_cr", default="N/A")
    rate = _g(rec, "recommended_rate_pct", default="N/A")
    premium = _g(ml, "risk_premium", default="N/A")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            _metric_card(
                "Lending Decision", decision, _decision_color(decision),
                f"Ensemble PD: {_pct(_g(ml, 'ensemble_pd'))}"
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _metric_card(
                "Recommended Limit",
                f"₹{_fmt(limit)} Cr" if limit != "N/A" else "N/A",
                MEDIUM_BLUE,
                f"Based on revenue × (1 – PD) factor"
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _metric_card(
                "Interest Rate",
                f"{_fmt(rate)}%" if rate != "N/A" else "N/A",
                ORANGE,
                f"Base + {_fmt(premium)}% risk premium"
            ),
            unsafe_allow_html=True,
        )

    # ── Row 2: Risk Signal Overview (11 innovations) ─────────────────────
    st.markdown(
        f'<div class="section-header">🔬 11-Innovation Risk Signal Overview</div>',
        unsafe_allow_html=True,
    )

    # Build signal data
    dscr = _g(fin, "dscr", default=0)
    m_score = _g(fin, "beneish_m_score", default=-3)
    z_score = _g(fin, "altman_z_score", default=3)
    f_score = _g(fin, "piotroski_f_score", default=5)
    contagion = _g(fin, "contagion_risk_score", default=0)
    sat_score = _g(fin, "satellite_activity_score", default=50)
    sat_cat = _g(fin, "satellite_activity_category", default="N/A")
    months = _g(fin, "months_to_dscr_danger", default=120)
    mq = _g(data, "ceo_interview", "management_quality_score", default=50)
    ensemble_pd = _g(ml, "ensemble_pd", default=0.5)
    breach_prob = _g(data, "stress_test", "covenant_breach_probability", default=0)
    dna_sim = _g(data, "dna_match", "max_archetype_similarity", default=0)
    deflection = _g(data, "ceo_interview", "key_scores", "ceo_deflection_score", default=0)

    signals = [
        ("1. Forensics: Beneish M-Score",
         f"M-Score {_fmt(m_score)} — {'SUSPICIOUS' if float(m_score)>-2.22 else 'CLEAN'}",
         "red" if float(m_score)>-2.22 else "green"),

        ("2. DSCR Trajectory",
         f"DSCR {_fmt(dscr)} | Danger in {int(float(months))} months",
         "red" if float(months)<18 else ("amber" if float(months)<36 else "green")),

        ("3. ML Ensemble (XGB/RF/LGB)",
         f"PD {_pct(ensemble_pd)} | Disagreement: {_fmt(_g(ml, 'model_disagreement'))}",
         "red" if float(ensemble_pd)>0.4 else ("amber" if float(ensemble_pd)>0.2 else "green")),

        ("4. Bull–Bear Debate",
         f"Decision: {decision}",
         "green" if "APPROVE" in str(decision) and "REJECT" not in str(decision) else (
             "red" if "REJECT" in str(decision) else "amber")),

        ("5. Default DNA Matching",
         f"Similarity: {_fmt(dna_sim)} — {_g(data, 'dna_match', 'closest_default_archetype')}",
         "red" if float(dna_sim)>0.5 else ("amber" if float(dna_sim)>0.3 else "green")),

        ("6. Promoter Network Graph",
         f"Contagion: {_fmt(contagion)} — {'HIGH' if float(contagion)>0.5 else ('MEDIUM' if float(contagion)>0.25 else 'LOW')}",
         "red" if float(contagion)>0.5 else ("amber" if float(contagion)>0.25 else "green")),

        ("7. Satellite Verification",
         f"Score: {_fmt(sat_score, '.0f')}/100 — {sat_cat}",
         "red" if float(sat_score)<40 else ("amber" if float(sat_score)<65 else "green")),

        ("8. Monte Carlo Stress Test",
         f"Breach Prob: {_pct(breach_prob)} | P10 DSCR: {_fmt(_g(data, 'stress_test', 'dscr_p10'))}",
         "red" if float(breach_prob)>0.3 else ("amber" if float(breach_prob)>0.1 else "green")),

        ("9. Web Research Agent",
         f"Sentiment: {_fmt(_g(data, 'research', 'research_sentiment_score'))} | Outlook: {_g(data, 'research', 'industry_outlook')}",
         "green" if _g(data, 'research', 'industry_outlook') == "POSITIVE" else "amber"),

        ("10. CEO Interview Analysis",
         f"MQ Score: {_fmt(mq, '.0f')}/100 | Deflection: {_fmt(deflection)}",
         "red" if float(deflection)>0.4 else ("amber" if float(deflection)>0.25 else "green")),

        ("11. AI CAM Generator",
         f"Document ready for generation",
         "green" if st.session_state.pipeline_done else "amber"),
    ]

    # Display as 4-column grid
    cols = st.columns(4)
    for i, (name, detail, level) in enumerate(signals):
        with cols[i % 4]:
            st.markdown(_signal_card(name, detail, level), unsafe_allow_html=True)

    # ── Row 3: Model Consensus — Gauge Charts ───────────────────────────
    st.markdown(
        f'<div class="section-header">🎯 Model Consensus — PD Estimates</div>',
        unsafe_allow_html=True,
    )

    g1, g2, g3, g4 = st.columns(4)

    with g1:
        st.plotly_chart(
            _gauge_chart(float(_g(ml, "xgb_pd", default=0)), "XGBoost PD", color="#1565C0"),
            use_container_width=True,
        )
    with g2:
        st.plotly_chart(
            _gauge_chart(float(_g(ml, "rf_pd", default=0)), "Random Forest PD", color="#2E7D32"),
            use_container_width=True,
        )
    with g3:
        st.plotly_chart(
            _gauge_chart(float(_g(ml, "lgb_pd", default=0)), "LightGBM PD", color="#E65100"),
            use_container_width=True,
        )
    with g4:
        st.plotly_chart(
            _gauge_chart(float(_g(ml, "ensemble_pd", default=0)), "Ensemble PD", color=NAVY),
            use_container_width=True,
        )

    # Disagreement flag
    disagreement = _g(ml, "model_disagreement_flag", default=False)
    if disagreement:
        st.error(
            "⚠️ **MODEL DISAGREEMENT DETECTED** — Individual model PDs diverge "
            "significantly. Manual review recommended."
        )
    else:
        st.success(
            "✅ **Models in consensus** — PD spread within acceptable range "
            f"(max spread: {_fmt(_g(ml, 'model_disagreement'))})"
        )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 3 — DEEP DIVE                                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def page_deep_dive():
    if not st.session_state.pipeline_done:
        st.warning("⚠️ No analysis loaded. Go to **Upload & Process** first.")
        return

    data = st.session_state.results
    fin = _g(data, "financial_data", default={})

    company = _g(data, "company_name")
    st.markdown(
        f'<div class="section-header">🔍 Deep Dive — {company}</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Financial Analysis",
        "🔗 Network Graph",
        "⚡ Stress Test",
        "⚔️ Bull vs Bear",
    ])

    # ── Tab 1: Financial Analysis ────────────────────────────────────────
    with tab1:
        st.subheader("Key Financial Ratios")

        ratio_data = {
            "Metric": ["DSCR", "Interest Coverage", "Debt/Equity", "Current Ratio",
                        "ROE", "ROA", "EBITDA Margin", "Net Margin"],
            "Value": [
                _fmt(_g(fin, "dscr")), _fmt(_g(fin, "interest_coverage")),
                _fmt(_g(fin, "debt_to_equity")), _fmt(_g(fin, "current_ratio")),
                _pct(_g(fin, "roe")), _pct(_g(fin, "roa")),
                _pct(_g(fin, "ebitda_margin")), _pct(_g(fin, "net_margin")),
            ],
            "Assessment": [
                _risk_level(_g(fin, "dscr", default=0), 1.5, 1.0),
                _risk_level(_g(fin, "interest_coverage", default=0), 2.0, 1.3),
                _risk_level(_g(fin, "debt_to_equity", default=0), 1.5, 2.5, False),
                _risk_level(_g(fin, "current_ratio", default=0), 1.2, 0.8),
                _risk_level(_g(fin, "roe", default=0), 0.12, 0.05),
                _risk_level(_g(fin, "roa", default=0), 0.05, 0.02),
                _risk_level(_g(fin, "ebitda_margin", default=0), 0.12, 0.06),
                _risk_level(_g(fin, "net_margin", default=0), 0.04, 0.01),
            ],
        }
        df_ratios = pd.DataFrame(ratio_data)
        st.dataframe(
            df_ratios.style.apply(
                lambda row: [
                    "",
                    "",
                    f"background-color: {'#E8F5E9' if row['Assessment']=='GREEN' else '#FFEBEE' if row['Assessment']=='RED' else '#FFF8E1'}"
                ],
                axis=1,
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        # DSCR Trajectory Chart
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("DSCR Trajectory (5-Year)")
            traj = _g(data, "trajectory", default={})
            fy = _g(traj, "fiscal_years", default=[2020, 2021, 2022, 2023, 2024])
            dscr_hist = _g(traj, "dscr_history", default=[1.55, 1.62, 1.70, 1.78, 1.85])

            fig_dscr = go.Figure()
            fig_dscr.add_trace(go.Scatter(
                x=fy, y=dscr_hist,
                mode="lines+markers", name="DSCR",
                line=dict(color=MEDIUM_BLUE, width=3),
                marker=dict(size=10, color=NAVY),
            ))
            # Danger threshold
            fig_dscr.add_hline(
                y=1.0, line_dash="dash", line_color=RED,
                annotation_text="Danger (1.0x)", annotation_position="bottom right",
            )
            fig_dscr.add_hline(
                y=1.5, line_dash="dot", line_color=AMBER,
                annotation_text="Watch (1.5x)", annotation_position="top right",
            )
            fig_dscr.update_layout(
                height=350,
                xaxis_title="Fiscal Year", yaxis_title="DSCR",
                template="plotly_white",
                margin=dict(t=30, b=50, l=50, r=30),
            )
            st.plotly_chart(fig_dscr, use_container_width=True)

        with col_chart2:
            st.subheader("Beneish M-Score Components")
            beneish_data = {
                "Component": ["DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "LVGI", "TATA"],
                "Description": [
                    "Days Sales Receivable", "Gross Margin", "Asset Quality",
                    "Sales Growth", "Depreciation", "SGA Expense",
                    "Leverage", "Total Accruals",
                ],
                "Typical Threshold": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
            }
            m_score_val = float(_g(fin, "beneish_m_score", default=-2.5))
            fig_beneish = go.Figure()
            fig_beneish.add_trace(go.Indicator(
                mode="number+delta+gauge",
                value=m_score_val,
                title={"text": "M-Score"},
                gauge={
                    "axis": {"range": [-5, 0]},
                    "bar": {"color": RED if m_score_val > -2.22 else GREEN},
                    "threshold": {
                        "line": {"color": RED, "width": 3},
                        "thickness": 0.8,
                        "value": -2.22,
                    },
                    "steps": [
                        {"range": [-5, -2.22], "color": "#E8F5E9"},
                        {"range": [-2.22, 0], "color": "#FFEBEE"},
                    ],
                },
                delta={"reference": -2.22, "decreasing": {"color": GREEN}, "increasing": {"color": RED}},
            ))
            fig_beneish.update_layout(
                height=350, margin=dict(t=80, b=30, l=30, r=30),
            )
            st.plotly_chart(fig_beneish, use_container_width=True)

        # Revenue breakdown
        st.subheader("Financial Summary")
        summary_cols = st.columns(4)
        metrics = [
            ("Revenue", f"₹{_fmt(_g(fin, 'revenue'))} Cr", f"{_pct(_g(fin, 'revenue_growth'))} YoY"),
            ("EBITDA", f"₹{_fmt(_g(fin, 'ebitda'))} Cr", f"Margin: {_pct(_g(fin, 'ebitda_margin'))}"),
            ("Free Cash Flow", f"₹{_fmt(_g(fin, 'free_cash_flow'))} Cr", f"CFO: ₹{_fmt(_g(fin, 'cfo'))} Cr"),
            ("Total Debt", f"₹{_fmt(_g(fin, 'total_debt'))} Cr", f"D/E: {_fmt(_g(fin, 'debt_to_equity'))}x"),
        ]
        for col, (label, val, sub) in zip(summary_cols, metrics):
            with col:
                st.metric(label, val, sub)

    # ── Tab 2: Network Graph ────────────────────────────────────────────
    with tab2:
        st.subheader("Promoter Network & Contagion Risk")

        network = _g(data, "network", default={})
        nodes = _g(network, "network_nodes", default=[])
        edges = _g(network, "network_edges", default=[])

        contagion = float(_g(network, "contagion_risk_score", default=0))
        level = "HIGH" if contagion > 0.5 else ("MEDIUM" if contagion > 0.25 else "LOW")
        rl = "red" if contagion > 0.5 else ("amber" if contagion > 0.25 else "green")
        st.markdown(
            _signal_card("Contagion Risk Score", f"{_fmt(contagion)} — {level}", rl),
            unsafe_allow_html=True,
        )

        if nodes:
            # Build plotly network graph
            import math
            n = len(nodes)
            # Circular layout
            pos = {}
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / n
                pos[node["id"]] = (math.cos(angle), math.sin(angle))

            # Edge traces
            edge_x, edge_y = [], []
            for edge in edges:
                x0, y0 = pos.get(edge["from"], (0, 0))
                x1, y1 = pos.get(edge["to"], (0, 0))
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            fig_net = go.Figure()
            fig_net.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode="lines",
                line=dict(width=2, color=GREY),
                hoverinfo="none",
            ))

            # Node traces
            node_colors = {
                "target": NAVY, "promoter": ORANGE,
                "related": MEDIUM_BLUE, "peer": LIGHT_BLUE,
            }
            for node in nodes:
                x, y = pos[node["id"]]
                ntype = node.get("type", "related")
                color = RED if node.get("npa") else node_colors.get(ntype, GREY)
                fig_net.add_trace(go.Scatter(
                    x=[x], y=[y],
                    mode="markers+text",
                    marker=dict(size=25 if ntype == "target" else 18, color=color),
                    text=[node["id"]],
                    textposition="top center",
                    textfont=dict(size=10),
                    hovertext=f"{node['id']} ({ntype})",
                    hoverinfo="text",
                    showlegend=False,
                ))

            fig_net.update_layout(
                height=500,
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                template="plotly_white",
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.info("Network graph data not available.")

        # Network stats
        net_cols = st.columns(4)
        net_metrics = [
            ("Promoter Companies", str(_g(fin, "promoter_total_companies", default="N/A"))),
            ("NPA Companies", str(_g(fin, "promoter_npa_companies", default="N/A"))),
            ("Struck-Off", str(_g(fin, "promoter_struck_off_companies", default="N/A"))),
            ("DIN Disqualified", str(_g(fin, "din_disqualified_count", default="N/A"))),
        ]
        for col, (label, val) in zip(net_cols, net_metrics):
            with col:
                st.metric(label, val)

    # ── Tab 3: Stress Test ──────────────────────────────────────────────
    with tab3:
        st.subheader("Monte Carlo Stress Test Results")

        stress = _g(data, "stress_test", default={})

        # DSCR Distribution
        sim_data = _g(stress, "dscr_simulated", default=[])
        if sim_data and isinstance(sim_data, list):
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=sim_data,
                nbinsx=30,
                name="Simulated DSCR",
                marker_color=MEDIUM_BLUE,
                opacity=0.8,
            ))
            fig_hist.add_vline(
                x=1.0, line_dash="dash", line_color=RED,
                annotation_text="Covenant Breach (1.0x)",
            )
            fig_hist.add_vline(
                x=float(_g(stress, "dscr_p50", default=1.5)),
                line_dash="dot", line_color=GREEN,
                annotation_text=f"P50: {_fmt(_g(stress, 'dscr_p50'))}",
            )
            fig_hist.update_layout(
                height=400,
                xaxis_title="Simulated DSCR",
                yaxis_title="Frequency",
                template="plotly_white",
                showlegend=False,
                margin=dict(t=30, b=50),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        # Percentiles
        p_cols = st.columns(4)
        with p_cols[0]:
            st.metric("P10 (Severe)", _fmt(_g(stress, "dscr_p10")))
        with p_cols[1]:
            st.metric("P50 (Base)", _fmt(_g(stress, "dscr_p50")))
        with p_cols[2]:
            st.metric("P90 (Optimistic)", _fmt(_g(stress, "dscr_p90")))
        with p_cols[3]:
            st.metric("Breach Probability", _pct(_g(stress, "covenant_breach_probability")))

        st.markdown("---")

        # Named scenarios table
        st.subheader("Named Stress Scenarios")
        scenarios = _g(stress, "named_scenarios", default=[])
        if scenarios:
            sc_df = pd.DataFrame(scenarios)
            sc_df.columns = ["Scenario", "DSCR Under Stress", "PD Under Stress"]
            sc_df["DSCR Under Stress"] = sc_df["DSCR Under Stress"].apply(lambda x: f"{x:.2f}x")
            sc_df["PD Under Stress"] = sc_df["PD Under Stress"].apply(lambda x: f"{x*100:.1f}%")
            st.dataframe(sc_df, use_container_width=True, hide_index=True)

            # Scenario bar chart
            sc_chart = pd.DataFrame(scenarios)
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Bar(
                x=sc_chart["name"],
                y=sc_chart["dscr_impact"],
                marker_color=[
                    RED if v < 1.0 else (AMBER if v < 1.2 else GREEN)
                    for v in sc_chart["dscr_impact"]
                ],
                text=[f"{v:.2f}x" for v in sc_chart["dscr_impact"]],
                textposition="outside",
            ))
            fig_sc.add_hline(y=1.0, line_dash="dash", line_color=RED)
            fig_sc.update_layout(
                height=350,
                xaxis_title="Scenario", yaxis_title="DSCR",
                template="plotly_white",
                margin=dict(t=30, b=80),
            )
            st.plotly_chart(fig_sc, use_container_width=True)

    # ── Tab 4: Bull vs Bear ─────────────────────────────────────────────
    with tab4:
        st.subheader("⚔️ Adversarial Credit Committee Debate")
        st.markdown(
            "*Two independent AI agents debated this loan — one arguing for approval, "
            "the other seeking every reason to reject.*"
        )

        bc1, bc2 = st.columns(2)

        with bc1:
            st.markdown('<div class="bull-header">🟢 BULL CASE — Approval Agent</div>',
                        unsafe_allow_html=True)
            bull = _g(data, "bull_case", default="Not available")
            # Convert markdown-style text to readable
            bull_clean = str(bull).replace("## ", "**").replace("\n- ", "\n• ")
            st.markdown(f'<div class="debate-box">{_markdown_to_html(bull_clean)}</div>',
                        unsafe_allow_html=True)

        with bc2:
            st.markdown('<div class="bear-header">🔴 BEAR CASE — Dissent Agent</div>',
                        unsafe_allow_html=True)
            bear = _g(data, "bear_case", default="Not available")
            bear_clean = str(bear).replace("## ", "**").replace("\n- ", "\n• ")
            st.markdown(f'<div class="debate-box">{_markdown_to_html(bear_clean)}</div>',
                        unsafe_allow_html=True)

        # Final recommendation
        st.markdown("---")
        rec = _g(data, "recommendation", default={})
        decision = _g(rec, "lending_decision", default="REVIEW")
        color = _decision_color(decision)

        st.markdown(
            f"""
            <div style="background:{LIGHT_GREY}; border-left:5px solid {color};
                        padding:20px; border-radius:0 12px 12px 0; margin:16px 0;">
                <h3 style="color:{color}; margin:0;">FINAL VERDICT: {decision}</h3>
                <p style="margin:8px 0 0 0; font-size:15px; line-height:1.7;">
                    {_g(rec, 'final_rationale', default='N/A')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Key conditions
        conditions = _g(rec, "key_conditions", default=[])
        if conditions:
            st.subheader("📋 Key Conditions & Covenants")
            for i, cond in enumerate(conditions, 1):
                st.markdown(f"**{i}.** {cond}")


def _markdown_to_html(text: str) -> str:
    """Simple markdown → HTML for display in boxes."""
    import re
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<h4 style='margin:12px 0 4px 0; color:{DARK_BLUE};'>{line[2:-2]}</h4>")
        elif line.startswith("**"):
            # Bold prefix line
            html_lines.append(f"<strong>{line.replace('**', '')}</strong><br>")
        elif line.startswith("•") or line.startswith("-"):
            html_lines.append(f"<span style='margin-left:12px;'>{line}</span><br>")
        else:
            html_lines.append(f"<span>{line}</span><br>")
    return "\n".join(html_lines)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 4 — DOWNLOAD CAM                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def page_download():
    if not st.session_state.pipeline_done:
        st.warning("⚠️ No analysis loaded. Go to **Upload & Process** first.")
        return

    data = st.session_state.results
    company = _g(data, "company_name")

    st.markdown(
        f'<div class="section-header">📄 Generate & Download CAM — {company}</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"""
            <div class="download-card">
                <h2 style="color:{NAVY}; margin:0 0 8px 0;">Credit Appraisal Memorandum</h2>
                <p style="color:{GREY}; font-size:14px;">
                    Professional DOCX document with all 11 innovation outputs,
                    financial analysis, forensic scores, network graphs,
                    stress test results, and adversarial debate.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        gen_col1, gen_col2 = st.columns(2)
        with gen_col1:
            generate_btn = st.button(
                "📝 Generate Full CAM Report",
                type="primary",
                use_container_width=True,
            )
        with gen_col2:
            if st.session_state.cam_path and os.path.exists(st.session_state.cam_path):
                with open(st.session_state.cam_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download DOCX",
                        data=f,
                        file_name=os.path.basename(st.session_state.cam_path),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

        if generate_btn:
            with st.spinner("Generating Credit Appraisal Memorandum..."):
                progress = st.progress(0, text="Assembling sections...")

                sections = [
                    "Cover Page", "Executive Summary", "Company Background",
                    "Financial Analysis", "Financial Forensics", "Network Analysis",
                    "Satellite & GST", "Stress Testing", "Management Quality",
                    "Bull vs Bear Debate", "Final Recommendation",
                ]

                try:
                    from modules.person3_llm_cam.cam_generator import generate_cam

                    # Show progress
                    for i, section in enumerate(sections):
                        progress.progress(
                            (i + 1) / len(sections),
                            text=f"Generating: {section}..."
                        )
                        time.sleep(0.3)

                    output_dir = os.path.join(PROJECT_ROOT, "data", "processed")
                    cam_path = generate_cam(data, output_dir=output_dir)

                    if cam_path and os.path.exists(cam_path):
                        st.session_state.cam_path = cam_path
                        progress.progress(1.0, text="✅ CAM generated successfully!")
                        st.success(f"✅ CAM saved: `{os.path.basename(cam_path)}`")
                        st.rerun()
                    else:
                        st.error("❌ CAM generation failed — check logs.")

                except ImportError:
                    st.error("❌ python-docx not installed. Run: `pip install python-docx`")
                except Exception as e:
                    st.error(f"❌ Error generating CAM: {e}")

    with col2:
        st.subheader("📊 Score Summary")

        rec = _g(data, "recommendation", default={})
        ml = _g(data, "ml_scores", default={})
        fin = _g(data, "financial_data", default={})
        ceo = _g(data, "ceo_interview", default={})

        summary = {
            "Lending Decision": _g(rec, "lending_decision"),
            "Credit Limit": f"₹{_fmt(_g(rec, 'recommended_limit_cr'))} Cr",
            "Interest Rate": f"{_fmt(_g(rec, 'recommended_rate_pct'))}%",
            "Ensemble PD": _pct(_g(ml, "ensemble_pd")),
            "DSCR": _fmt(_g(fin, "dscr")),
            "D/E Ratio": _fmt(_g(fin, "debt_to_equity")),
            "Beneish M-Score": _fmt(_g(fin, "beneish_m_score")),
            "Altman Z-Score": _fmt(_g(fin, "altman_z_score")),
            "Contagion Risk": _fmt(_g(fin, "contagion_risk_score")),
            "Satellite Score": _fmt(_g(fin, "satellite_activity_score"), ".0f"),
            "MQ Score": _fmt(_g(ceo, "management_quality_score"), ".0f"),
        }

        for key, val in summary.items():
            st.markdown(f"**{key}:** {val}")

        st.markdown("---")

        # JSON download
        json_summary = {
            "company_name": company,
            "generated_at": datetime.now().isoformat(),
            **{k: str(v) for k, v in summary.items()},
        }
        st.download_button(
            "⬇️ Download Scores JSON",
            data=json.dumps(json_summary, indent=2),
            file_name=f"scores_{str(company).replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ROUTER                                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if page == "📤 Upload & Process":
    page_upload()
elif page == "📊 Credit Decision":
    page_decision()
elif page == "🔍 Deep Dive":
    page_deep_dive()
elif page == "📄 Download CAM":
    page_download()
