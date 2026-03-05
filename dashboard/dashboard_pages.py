"""
Intelli-Credit — Dashboard Pages (Finexy Theme)
================================================
Renders fully themed HTML/CSS dashboard content.
Uses st.html() for all visual layout, st.plotly_chart() for charts,
st.download_button() and st.button() only where functional interactivity needed.

Theme: Finexy fintech — orange #E8470A + white #FFFFFF + near-black #1A1A1A
Fonts: DM Sans (UI) + DM Serif Display (hero numbers)
"""

import os
import json
import time
import math
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go

# ════════════════════════════════════════════════════════════════════
#  COLOR TOKENS
# ════════════════════════════════════════════════════════════════════

BG_PAGE       = "#F4F5F7"
BG_CARD       = "#FFFFFF"
BG_ROW_ALT    = "#FAFAFA"

ORANGE        = "#E8470A"
ORANGE_LIGHT  = "#FF6B35"
ORANGE_PALE   = "#FFF7F4"
ORANGE_BG     = "#FFF0EB"

TEXT_PRIMARY   = "#1A1A1A"
TEXT_SECONDARY = "#6B7280"
TEXT_MUTED     = "#9CA3AF"

BORDER         = "#E5E7EB"
DIVIDER        = "#F3F4F6"

SUCCESS        = "#10B981"
SUCCESS_BG     = "#ECFDF5"
WARNING        = "#F59E0B"
WARNING_BG     = "#FFFBEB"
DANGER         = "#EF4444"
DANGER_BG      = "#FEF2F2"
INFO           = "#3B82F6"
INFO_BG        = "#EFF6FF"

DARK           = "#1A1A1A"
DARK_HOVER     = "#2D2D2D"

DECISION_COLORS = {
    "APPROVE": SUCCESS,
    "CONDITIONAL_APPROVE": WARNING,
    "REJECT": DANGER,
    "REVIEW": TEXT_MUTED,
}

RISK_MAP = {"GREEN": SUCCESS, "AMBER": WARNING, "RED": DANGER, "LOW": SUCCESS, "MEDIUM": WARNING, "HIGH": DANGER}


# ════════════════════════════════════════════════════════════════════
#  INLINE SVG ICONS
# ════════════════════════════════════════════════════════════════════

_IC = {
    "grid": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
    "chart": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "shield": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "download": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "check": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "alert": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "trending_up": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "trending_down": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>',
    "network": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
    "robot": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>',
    "search": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "file": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "activity": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "lock": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "target": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "zap": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "dollar": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "percent": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>',
    "clipboard": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>',
}


# ════════════════════════════════════════════════════════════════════
#  DASHBOARD GLOBAL CSS
# ════════════════════════════════════════════════════════════════════

DASHBOARD_CSS = """
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ── Page reset ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #F4F5F7 !important;
    color: #1A1A1A !important;
}
[data-testid="stAppViewContainer"] {
    background: #F4F5F7 !important;
    background-image: none !important;
}
.main .block-container {
    padding: 24px 32px !important;
    max-width: 1280px !important;
}
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }

h1,h2,h3,h4,h5,h6 { color: #1A1A1A !important; font-family: 'DM Sans', sans-serif !important; }
p, span, label, li, td, th { font-family: 'DM Sans', sans-serif !important; }

/* ── Tabs (styled as pill navigation) ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 14px !important;
    padding: 4px !important;
    margin-bottom: 28px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7280 !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border: none !important;
    font-family: 'DM Sans', sans-serif !important;
    height: auto !important;
    white-space: nowrap !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #1A1A1A !important;
    background: #F9FAFB !important;
}
.stTabs [aria-selected="true"] {
    color: white !important;
    background: #1A1A1A !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Plotly chart containers ── */
[data-testid="stPlotlyChart"] {
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 16px !important;
    padding: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #E8470A 0%, #FF6B35 100%) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; min-height: 44px !important;
    font-weight: 600 !important; font-size: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 4px 16px rgba(232,71,10,.3) !important;
    transition: all .2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(232,71,10,.4) !important;
}
.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
    background: white !important; color: #1A1A1A !important;
    border: 1.5px solid #D1D5DB !important; border-radius: 12px !important;
    min-height: 44px !important; font-weight: 600 !important;
    font-size: 14px !important; font-family: 'DM Sans', sans-serif !important;
    transition: all .15s ease !important;
}
.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {
    border-color: #E8470A !important; color: #E8470A !important;
    background: #FFF7F4 !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
    background: #1A1A1A !important; color: white !important;
    border: none !important; border-radius: 12px !important;
    min-height: 44px !important; font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all .15s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #2D2D2D !important;
}

/* ── Metrics (remove default Streamlit styling) ── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 16px !important;
    padding: 20px 24px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetric"] label { color: #9CA3AF !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #1A1A1A !important; font-size: 24px !important; font-weight: 700 !important; }
[data-testid="stMetric"] [data-testid="stMetricDelta"] { font-size: 13px !important; }

/* ── DataFrames ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }

/* ── Progress bar ── */
.stProgress > div > div { background: linear-gradient(90deg, #E8470A, #FF6B35) !important; }

/* ── Alerts ── */
.stAlert { border-radius: 12px !important; }

/* ── Expander ──*/
.streamlit-expanderHeader { font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; }
</style>
"""


# ════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════

def _g(data: dict, *keys, default="N/A"):
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


def _decision_color(d: str) -> str:
    return DECISION_COLORS.get(str(d).upper(), TEXT_MUTED)


def _risk_level(value, good, warn, higher_is_better=True) -> str:
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "GREY"
    if higher_is_better:
        return "GREEN" if v >= good else ("AMBER" if v >= warn else "RED")
    else:
        return "GREEN" if v <= good else ("AMBER" if v <= warn else "RED")


def _risk_color(level: str) -> str:
    return RISK_MAP.get(level, TEXT_MUTED)


def _risk_bg(level: str) -> str:
    colors = {"GREEN": SUCCESS_BG, "AMBER": WARNING_BG, "RED": DANGER_BG}
    return colors.get(level, "#F9FAFB")


# ════════════════════════════════════════════════════════════════════
#  COMPONENT BUILDERS (return HTML strings)
# ════════════════════════════════════════════════════════════════════

def _navbar_html(company_name: str, decision: str = "") -> str:
    dec_color = _decision_color(decision) if decision else ORANGE
    decision_pill = ""
    if company_name and company_name != "N/A":
        decision_pill = f"""
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="height:24px;width:1px;background:#E5E7EB;"></div>
          <span style="background:#FFF7F4;color:#E8470A;font-size:13px;font-weight:500;
                       padding:6px 14px;border-radius:999px;border:1px solid rgba(232,71,10,0.15);">
            {company_name}
          </span>
          <span style="background:{dec_color}15;color:{dec_color};font-size:11px;font-weight:600;
                       padding:4px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:.5px;">
            {decision if decision else 'PROCESSING'}
          </span>
        </div>
        """
    return f"""
    <nav style="background:white;border-bottom:1px solid #F3F4F6;margin:-24px -32px 24px -32px;
                padding:0 32px;position:sticky;top:0;z-index:100;">
      <div style="height:64px;display:flex;align-items:center;gap:16px;font-family:'DM Sans',sans-serif;">
        <div style="width:36px;height:36px;border-radius:50%;
                    background:linear-gradient(135deg,#E8470A,#FF6B35);
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-weight:700;font-size:14px;flex-shrink:0;">IC</div>
        <span style="font-weight:600;font-size:18px;color:#1A1A1A;">Intelli-Credit</span>
        {decision_pill}
      </div>
    </nav>
    """


def _metric_card_html(label: str, value: str, subtitle: str = "",
                      variant: str = "white", icon_svg: str = "") -> str:
    """variant: 'white' | 'orange' | 'dark'"""
    if variant == "orange":
        bg = "linear-gradient(135deg, #E8470A 0%, #FF6B35 100%)"
        txt = "white"
        sub = "rgba(255,255,255,0.75)"
        lbl = "rgba(255,255,255,0.8)"
        shadow = "0 4px 16px rgba(232,71,10,0.35)"
        border = "none"
        icon_color = "rgba(255,255,255,0.85)"
    elif variant == "dark":
        bg = "#1A1A1A"
        txt = "white"
        sub = "#9CA3AF"
        lbl = "#9CA3AF"
        shadow = "0 4px 16px rgba(0,0,0,0.2)"
        border = "none"
        icon_color = "rgba(255,255,255,0.6)"
    else:
        bg = "white"
        txt = "#1A1A1A"
        sub = "#9CA3AF"
        lbl = "#9CA3AF"
        shadow = "0 1px 4px rgba(0,0,0,0.06), 0 2px 12px rgba(0,0,0,0.06)"
        border = "1px solid #E5E7EB"
        icon_color = "#E8470A"

    icon_html = f'<span style="font-size:20px;color:{icon_color};display:flex;position:absolute;top:24px;right:24px;">{icon_svg}</span>' if icon_svg else ""

    return f"""
    <div style="background:{bg};border-radius:20px;padding:24px 28px;border:{border};
                box-shadow:{shadow};position:relative;font-family:'DM Sans',sans-serif;">
      {icon_html}
      <p style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;
                color:{lbl};margin:0 0 8px 0;">{label}</p>
      <p style="font-size:32px;font-weight:700;color:{txt};margin:0;line-height:1.2;">{value}</p>
      <p style="font-size:12px;color:{sub};margin:6px 0 0 0;">{subtitle}</p>
    </div>
    """


def _signal_card_html(name: str, detail: str, level: str = "GREEN") -> str:
    color = _risk_color(level)
    bg = _risk_bg(level)
    return f"""
    <div style="background:white;border:1px solid #E5E7EB;border-left:4px solid {color};
                border-radius:14px;padding:16px 18px;margin-bottom:10px;
                font-family:'DM Sans',sans-serif;transition:transform .15s ease,box-shadow .2s ease;"
         onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 16px rgba(0,0,0,0.08)'"
         onmouseout="this.style.transform='none';this.style.boxShadow='none'">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <span style="font-size:12px;font-weight:600;color:#6B7280;">{name}</span>
        <span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;
                     background:{bg};color:{color};">{level}</span>
      </div>
      <p style="margin:0;font-size:13px;font-weight:500;color:#1A1A1A;">{detail}</p>
    </div>
    """


def _table_html(headers: list, rows: list, col_align: list = None) -> str:
    """Build a styled HTML table. rows is list of lists."""
    if not col_align:
        col_align = ["left"] * len(headers)
    hdr = "".join(
        f'<th style="background:#F9FAFB;padding:12px 16px;font-size:12px;font-weight:600;'
        f'color:#9CA3AF;text-transform:uppercase;letter-spacing:.5px;text-align:{col_align[i]};'
        f'border-bottom:1px solid #E5E7EB;">{h}</th>'
        for i, h in enumerate(headers)
    )
    body = ""
    for ri, row in enumerate(rows):
        bg = "#FAFAFA" if ri % 2 == 1 else "white"
        cells = ""
        for ci, cell in enumerate(row):
            cells += f'<td style="padding:12px 16px;font-size:14px;color:#1A1A1A;text-align:{col_align[ci]};border-bottom:1px solid #F3F4F6;">{cell}</td>'
        body += f'<tr style="background:{bg};transition:background .1s ease;" onmouseover="this.style.background=\'#FFF7F4\'" onmouseout="this.style.background=\'{bg}\'">{cells}</tr>'
    return f"""
    <table style="width:100%;border-collapse:separate;border-spacing:0;border-radius:16px;
                  overflow:hidden;background:white;border:1px solid #E5E7EB;
                  font-family:'DM Sans',sans-serif;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <thead><tr>{hdr}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    """


def _section_header_html(title: str, subtitle: str = "") -> str:
    sub = f'<p style="font-size:14px;color:#6B7280;margin:4px 0 0 0;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin:32px 0 16px 0;font-family:'DM Sans',sans-serif;">
      <h2 style="font-size:22px;font-weight:600;color:#1A1A1A;margin:0;">{title}</h2>
      {sub}
    </div>
    """


def _badge_html(text: str, color: str, bg: str) -> str:
    return f'<span style="display:inline-block;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;background:{bg};color:{color};">{text}</span>'


def _card_wrap(html_inside: str, pad: str = "24px 28px") -> str:
    return f"""
    <div style="background:white;border:1px solid #E5E7EB;border-radius:20px;padding:{pad};
                box-shadow:0 1px 4px rgba(0,0,0,0.06),0 2px 12px rgba(0,0,0,0.06);
                font-family:'DM Sans',sans-serif;margin-bottom:16px;">
      {html_inside}
    </div>
    """


# ════════════════════════════════════════════════════════════════════
#  PLOTLY THEME HELPER — Light mode
# ════════════════════════════════════════════════════════════════════

def _plotly_layout(**kw):
    """Merge Finexy light-theme defaults with caller overrides."""
    defaults = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        font=dict(family="DM Sans", color=TEXT_PRIMARY, size=13),
        margin=dict(t=30, b=50, l=50, r=30),
        xaxis=dict(gridcolor=DIVIDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=DIVIDER, zerolinecolor=BORDER),
    )
    defaults.update(kw)
    return defaults


# ════════════════════════════════════════════════════════════════════
#  PAGE  — OVERVIEW (Credit Decision + Signals + Gauges)
# ════════════════════════════════════════════════════════════════════

def render_overview(data: dict):
    rec = _g(data, "recommendation", default={})
    ml = _g(data, "ml_scores", default={})
    fin = _g(data, "financial_data", default={})
    company = _g(data, "company_name")

    # Greeting
    now = datetime.now()
    greeting = "Good morning" if now.hour < 12 else ("Good afternoon" if now.hour < 17 else "Good evening")
    st.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <div style="font-family:'DM Sans',sans-serif;margin-bottom:12px;">
      <h1 style="font-family:'DM Serif Display',serif;font-size:32px;font-weight:700;color:#1A1A1A;margin:0;">
        {greeting}, Analyst</h1>
      <p style="font-size:15px;color:#9CA3AF;margin:6px 0 0 0;">
        {company} analysis is ready &middot; {now.strftime('%d %B %Y')}</p>
    </div>
    """)

    # Row 1 — 4 Metric Cards
    decision = _g(rec, "lending_decision", default="REVIEW")
    ensemble_pd = _g(ml, "ensemble_pd", default=0)
    limit = _g(rec, "recommended_limit_cr", default="N/A")
    rate = _g(rec, "recommended_rate_pct", default="N/A")
    premium = _g(ml, "risk_premium", default="N/A")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.html(_metric_card_html(
            "Lending Decision", decision,
            f"Ensemble PD: {_pct(ensemble_pd)}",
            variant="dark", icon_svg=_IC["shield"]))
    with c2:
        st.html(_metric_card_html(
            "PD Score", _pct(ensemble_pd),
            "Probability of Default",
            variant="orange", icon_svg=_IC["target"]))
    with c3:
        st.html(_metric_card_html(
            "Credit Limit", f"₹{_fmt(limit)} Cr" if limit != "N/A" else "N/A",
            "Revenue × (1 – PD) factor",
            icon_svg=_IC["dollar"]))
    with c4:
        st.html(_metric_card_html(
            "Interest Rate", f"{_fmt(rate)}%" if rate != "N/A" else "N/A",
            f"Base + {_fmt(premium)}% risk premium",
            icon_svg=_IC["percent"]))

    # Row 2 — signal overview
    st.html(_section_header_html("Risk Signal Overview", "All AI-computed innovation signals"))

    dscr = _g(fin, "dscr", default=0)
    m_score = _g(fin, "beneish_m_score", default=-3)
    z_score = _g(fin, "altman_z_score", default=3)
    months = _g(fin, "months_to_dscr_danger", default=120)
    mq = _g(data, "ceo_interview", "management_quality_score", default=50)
    breach_prob = _g(data, "stress_test", "covenant_breach_probability", default=0)
    dna_sim = _g(data, "dna_match", "max_archetype_similarity", default=0)
    sat_score = _g(fin, "satellite_activity_score", default=50)
    sat_cat = _g(fin, "satellite_activity_category", default="N/A")
    contagion = _g(fin, "contagion_risk_score", default=0)
    deflection = _g(data, "ceo_interview", "key_scores", "ceo_deflection_score", default=0)

    signals = [
        ("Forensics: Beneish", f"M-Score {_fmt(m_score)} — {'SUSPICIOUS' if float(m_score) > -2.22 else 'CLEAN'}", "RED" if float(m_score) > -2.22 else "GREEN"),
        ("DSCR Trajectory", f"DSCR {_fmt(dscr)} | Danger in {int(float(months))}mo", "RED" if float(months) < 18 else ("AMBER" if float(months) < 36 else "GREEN")),
        ("ML Ensemble", f"PD {_pct(ensemble_pd)} | Spread: {_fmt(_g(ml, 'model_disagreement'))}", "RED" if float(ensemble_pd) > 0.4 else ("AMBER" if float(ensemble_pd) > 0.2 else "GREEN")),
        ("Bull–Bear Debate", f"Decision: {decision}", "GREEN" if "APPROVE" in str(decision) and "REJECT" not in str(decision) else ("RED" if "REJECT" in str(decision) else "AMBER")),
        ("Default DNA Match", f"Similarity: {_fmt(dna_sim)} — {_g(data, 'dna_match', 'closest_default_archetype')}", "RED" if float(dna_sim) > 0.5 else ("AMBER" if float(dna_sim) > 0.3 else "GREEN")),
        ("Network Contagion", f"Score: {_fmt(contagion, '.2f')}", "RED" if float(contagion) > 0.5 else ("AMBER" if float(contagion) > 0.25 else "GREEN")),
        ("Satellite Verification", f"Score: {_fmt(sat_score, '.0f')}/100 — {sat_cat}", "RED" if float(sat_score) < 40 else ("AMBER" if float(sat_score) < 65 else "GREEN")),
        ("Monte Carlo Stress", f"Breach Prob: {_pct(breach_prob)} | P10: {_fmt(_g(data, 'stress_test', 'dscr_p10'))}", "RED" if float(breach_prob) > 0.3 else ("AMBER" if float(breach_prob) > 0.1 else "GREEN")),
        ("Web Research", f"Sentiment: {_fmt(_g(data, 'research', 'research_sentiment_score'))} | {_g(data, 'research', 'industry_outlook')}", "GREEN" if _g(data, 'research', 'industry_outlook') == "POSITIVE" else "AMBER"),
        ("CEO Interview", f"MQ: {_fmt(mq, '.0f')}/100 | Deflection: {_fmt(deflection)}", "RED" if float(deflection) > 0.4 else ("AMBER" if float(deflection) > 0.25 else "GREEN")),
        ("CAM Generator", "Document ready", "GREEN"),
    ]

    # Build 3-column signal grid
    cols = st.columns(3)
    for i, (name, detail, level) in enumerate(signals):
        with cols[i % 3]:
            st.html(_signal_card_html(name, detail, level))

    # Row 3 — model gauges
    st.html(_section_header_html("Model Consensus", "Individual PD estimates from ensemble members"))

    g1, g2, g3, g4 = st.columns(4)
    gauge_cfg = [
        (g1, "XGBoost", float(_g(ml, "xgb_pd", default=0)), "#E8470A"),
        (g2, "Random Forest", float(_g(ml, "rf_pd", default=0)), "#3B82F6"),
        (g3, "LightGBM", float(_g(ml, "lgb_pd", default=0)), "#6366F1"),
        (g4, "Ensemble", float(_g(ml, "ensemble_pd", default=0)), "#1A1A1A"),
    ]
    for col, label, val, color in gauge_cfg:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val * 100,
            number={"suffix": "%", "font": {"size": 22, "color": TEXT_PRIMARY}},
            title={"text": label, "font": {"size": 12, "color": TEXT_SECONDARY}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"color": TEXT_MUTED, "size": 10}},
                "bar": {"color": color, "thickness": 0.7},
                "bgcolor": "#F3F4F6",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 20], "color": SUCCESS_BG},
                    {"range": [20, 40], "color": WARNING_BG},
                    {"range": [40, 100], "color": DANGER_BG},
                ],
                "threshold": {"line": {"color": DANGER, "width": 3}, "thickness": 0.8, "value": 50},
            },
        ))
        fig.update_layout(height=200, margin=dict(t=50, b=10, l=30, r=30),
                          paper_bgcolor="rgba(0,0,0,0)", font={"color": TEXT_PRIMARY})
        with col:
            st.plotly_chart(fig, use_container_width=True)

    # Disagreement
    disagree = _g(ml, "model_disagreement_flag", default=False)
    if disagree:
        st.html(f'<div style="background:{DANGER_BG};border:1px solid {DANGER}20;border-left:3px solid {DANGER};padding:14px 20px;border-radius:12px;font-family:DM Sans,sans-serif;margin-top:8px;"><span style="font-weight:600;color:{DANGER};">Model Disagreement Detected</span> — PD estimates diverge significantly. Manual review recommended.</div>')
    else:
        st.html(f'<div style="background:{SUCCESS_BG};border:1px solid {SUCCESS}20;border-left:3px solid {SUCCESS};padding:14px 20px;border-radius:12px;font-family:DM Sans,sans-serif;margin-top:8px;"><span style="font-weight:600;color:{SUCCESS};">Models in Consensus</span> — PD spread within acceptable range ({_fmt(_g(ml, "model_disagreement"))})</div>')


# ════════════════════════════════════════════════════════════════════
#  PAGE  — DEEP DIVE
# ════════════════════════════════════════════════════════════════════

def render_deep_dive(data: dict):
    fin = _g(data, "financial_data", default={})
    company = _g(data, "company_name")

    st.html(_section_header_html("Deep Dive Analysis", f"Visual breakdown for {company}"))

    # Sub-tabs for deep dive sections
    t_fin, t_net, t_stress, t_debate = st.tabs([
        "Financial Analysis", "Network Graph", "Stress Testing", "Bull vs Bear"
    ])

    # ── Financial Analysis Tab ──────────────────────────────
    with t_fin:
        st.html(_section_header_html("Key Financial Ratios"))

        ratio_metrics = [
            ("DSCR", _fmt(_g(fin, "dscr")), _risk_level(_g(fin, "dscr", default=0), 1.5, 1.0)),
            ("Interest Coverage", _fmt(_g(fin, "interest_coverage")), _risk_level(_g(fin, "interest_coverage", default=0), 2.0, 1.3)),
            ("Debt / Equity", _fmt(_g(fin, "debt_to_equity")), _risk_level(_g(fin, "debt_to_equity", default=0), 1.5, 2.5, False)),
            ("Current Ratio", _fmt(_g(fin, "current_ratio")), _risk_level(_g(fin, "current_ratio", default=0), 1.2, 0.8)),
            ("ROE", _pct(_g(fin, "roe")), _risk_level(_g(fin, "roe", default=0), 0.12, 0.05)),
            ("ROA", _pct(_g(fin, "roa")), _risk_level(_g(fin, "roa", default=0), 0.05, 0.02)),
            ("EBITDA Margin", _pct(_g(fin, "ebitda_margin")), _risk_level(_g(fin, "ebitda_margin", default=0), 0.12, 0.06)),
            ("Net Margin", _pct(_g(fin, "net_margin")), _risk_level(_g(fin, "net_margin", default=0), 0.04, 0.01)),
        ]
        rows = []
        for metric, val, level in ratio_metrics:
            c = _risk_color(level)
            bg = _risk_bg(level)
            badge = f'<span style="display:inline-block;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;background:{bg};color:{c};">{level}</span>'
            rows.append([metric, val, badge])

        st.html(_table_html(["Metric", "Value", "Assessment"], rows, ["left", "right", "center"]))

        # DSCR Trajectory + Beneish gauge
        st.html(_section_header_html("DSCR Trajectory"))
        col_a, col_b = st.columns(2)

        with col_a:
            traj = _g(data, "trajectory", default={})
            fy = _g(traj, "fiscal_years", default=[2020, 2021, 2022, 2023, 2024])
            dscr_hist = _g(traj, "dscr_history", default=[1.5]*5)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=fy, y=dscr_hist, mode="lines+markers", name="DSCR",
                line=dict(color=ORANGE, width=3),
                marker=dict(size=10, color=ORANGE),
            ))
            fig.add_hline(y=1.0, line_dash="dash", line_color=DANGER, annotation_text="Danger (1.0x)",
                          annotation_font_color=TEXT_SECONDARY)
            fig.add_hline(y=1.5, line_dash="dot", line_color=WARNING, annotation_text="Watch (1.5x)",
                          annotation_font_color=TEXT_SECONDARY)
            fig.update_layout(**_plotly_layout(height=350, xaxis_title="Fiscal Year", yaxis_title="DSCR"))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            m_val = float(_g(fin, "beneish_m_score", default=-2.5))
            fig_b = go.Figure(go.Indicator(
                mode="number+gauge",
                value=m_val,
                title={"text": "Beneish M-Score", "font": {"size": 14, "color": TEXT_SECONDARY}},
                number={"font": {"size": 28, "color": TEXT_PRIMARY}},
                gauge={
                    "axis": {"range": [-5, 0], "tickfont": {"color": TEXT_MUTED}},
                    "bar": {"color": DANGER if m_val > -2.22 else SUCCESS},
                    "bgcolor": "#F3F4F6",
                    "threshold": {"line": {"color": DANGER, "width": 3}, "thickness": 0.8, "value": -2.22},
                    "steps": [
                        {"range": [-5, -2.22], "color": SUCCESS_BG},
                        {"range": [-2.22, 0], "color": DANGER_BG},
                    ],
                },
            ))
            fig_b.update_layout(height=350, margin=dict(t=80, b=30, l=30, r=30),
                                paper_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_PRIMARY))
            st.plotly_chart(fig_b, use_container_width=True)

        # Financial summary metrics
        st.html(_section_header_html("Financial Summary"))
        summary_rows = [
            [f"₹{_fmt(_g(fin, 'revenue'))} Cr", f"₹{_fmt(_g(fin, 'ebitda'))} Cr",
             f"₹{_fmt(_g(fin, 'free_cash_flow'))} Cr", f"₹{_fmt(_g(fin, 'total_debt'))} Cr"],
        ]
        st.html(_table_html(["Revenue", "EBITDA", "Free Cash Flow", "Total Debt"],
                            summary_rows, ["center"]*4))

    # ── Network Graph Tab ───────────────────────────────────
    with t_net:
        st.html(_section_header_html("Promoter Network & Contagion Risk"))

        network = _g(data, "network", default={})
        nodes = _g(network, "network_nodes", default=[])
        edges = _g(network, "network_edges", default=[])
        cont = float(_g(network, "contagion_risk_score", default=0))
        level = "RED" if cont > 0.5 else ("AMBER" if cont > 0.25 else "GREEN")
        st.html(_signal_card_html("Contagion Risk Score", f"{_fmt(cont, '.2f')} — {'HIGH' if cont > 0.5 else ('MEDIUM' if cont > 0.25 else 'LOW')}", level))

        if nodes:
            n = len(nodes)
            pos = {}
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / n
                pos[node["id"]] = (math.cos(angle), math.sin(angle))
            edge_x, edge_y = [], []
            for edge in edges:
                x0, y0 = pos.get(edge["from"], (0, 0))
                x1, y1 = pos.get(edge["to"], (0, 0))
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            fig_net = go.Figure()
            fig_net.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                                         line=dict(width=2, color=BORDER), hoverinfo="none"))
            node_colors = {"target": ORANGE, "promoter": WARNING, "related": INFO, "peer": "#60A5FA"}
            for nd in nodes:
                x, y = pos[nd["id"]]
                ntype = nd.get("type", "related")
                color = DANGER if nd.get("npa") else node_colors.get(ntype, TEXT_MUTED)
                fig_net.add_trace(go.Scatter(
                    x=[x], y=[y], mode="markers+text",
                    marker=dict(size=30 if ntype == "target" else 20, color=color,
                                line=dict(width=2, color="rgba(0,0,0,0.1)")),
                    text=[nd["id"]], textposition="top center",
                    textfont=dict(size=11, color=TEXT_PRIMARY),
                    hovertext=f"{nd['id']} ({ntype})", hoverinfo="text", showlegend=False,
                ))
            fig_net.update_layout(**_plotly_layout(
                height=450, showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ))
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.html(_card_wrap('<p style="text-align:center;color:#9CA3AF;padding:40px 0;">No network data available.</p>'))

        # Network stats
        st.html(_section_header_html("Promoter Network Stats"))
        net_rows = [[
            str(_g(fin, "promoter_total_companies", default="N/A")),
            str(_g(fin, "promoter_npa_companies", default="N/A")),
            str(_g(fin, "promoter_struck_off_companies", default="N/A")),
            str(_g(fin, "din_disqualified_count", default="N/A")),
        ]]
        st.html(_table_html(["Promoter Companies", "NPA Companies", "Struck-Off", "DIN Disqualified"],
                            net_rows, ["center"]*4))

    # ── Stress Testing Tab ──────────────────────────────────
    with t_stress:
        st.html(_section_header_html("Monte Carlo Stress Testing", "10,000 DSCR trajectory simulations"))

        stress = _g(data, "stress_test", default={})
        sim_data = _g(stress, "dscr_simulated", default=[])

        if sim_data and isinstance(sim_data, list):
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=sim_data, nbinsx=30, name="Simulated DSCR",
                marker_color=ORANGE, opacity=0.85,
            ))
            fig_hist.add_vline(x=1.0, line_dash="dash", line_color=DANGER,
                               annotation_text="Breach (1.0x)", annotation_font_color=TEXT_SECONDARY)
            p50 = float(_g(stress, "dscr_p50", default=1.5))
            fig_hist.add_vline(x=p50, line_dash="dot", line_color=SUCCESS,
                               annotation_text=f"P50: {p50:.2f}", annotation_font_color=TEXT_SECONDARY)
            fig_hist.update_layout(**_plotly_layout(
                height=400, xaxis_title="Simulated DSCR", yaxis_title="Frequency", showlegend=False))
            st.plotly_chart(fig_hist, use_container_width=True)

        # Percentile cards
        p_cols = st.columns(4)
        with p_cols[0]:
            st.html(_metric_card_html("P10 (Severe)", _fmt(_g(stress, "dscr_p10"))))
        with p_cols[1]:
            st.html(_metric_card_html("P50 (Base)", _fmt(_g(stress, "dscr_p50"))))
        with p_cols[2]:
            st.html(_metric_card_html("P90 (Optimistic)", _fmt(_g(stress, "dscr_p90"))))
        with p_cols[3]:
            bp = _g(stress, "covenant_breach_probability", default=0)
            st.html(_metric_card_html("Breach Probability", _pct(bp),
                    variant="orange" if float(bp) > 0.15 else "white"))

        # Named scenarios
        scenarios = _g(stress, "named_scenarios", default=[])
        if scenarios:
            st.html(_section_header_html("Named Stress Scenarios"))
            sc_rows = []
            for sc in scenarios:
                dscr_v = float(sc.get("dscr_impact", 1.0))
                pd_v = float(sc.get("pd_impact", 0))
                c = DANGER if dscr_v < 1.0 else (WARNING if dscr_v < 1.2 else SUCCESS)
                badge = f'<span style="font-weight:700;color:{c};">{dscr_v:.2f}x</span>'
                sc_rows.append([sc.get("name", ""), badge, f"{pd_v*100:.1f}%"])
            st.html(_table_html(["Scenario", "DSCR Under Stress", "PD Impact"], sc_rows, ["left", "center", "center"]))

            # Bar chart
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Bar(
                x=[s.get("name","") for s in scenarios],
                y=[s.get("dscr_impact",1) for s in scenarios],
                marker_color=[DANGER if s.get("dscr_impact",1)<1 else (WARNING if s.get("dscr_impact",1)<1.2 else SUCCESS) for s in scenarios],
                text=[f"{s.get('dscr_impact',1):.2f}x" for s in scenarios],
                textposition="outside",
            ))
            fig_sc.add_hline(y=1.0, line_dash="dash", line_color=DANGER)
            fig_sc.update_layout(**_plotly_layout(height=350, xaxis_title="Scenario", yaxis_title="DSCR"))
            st.plotly_chart(fig_sc, use_container_width=True)

    # ── Bull vs Bear Tab ────────────────────────────────────
    with t_debate:
        st.html(_section_header_html("Adversarial Credit Committee Debate",
                "Two independent AI agents debated this loan"))

        bc, be = st.columns(2)
        with bc:
            bull = str(_g(data, "bull_case", default="Not available"))
            bull_html = _debate_text_to_html(bull)
            st.html(f"""
            <div style="font-family:'DM Sans',sans-serif;">
              <div style="background:linear-gradient(135deg,{SUCCESS},#059669);color:white;padding:14px 20px;
                          border-radius:16px 16px 0 0;font-size:15px;font-weight:700;text-align:center;
                          text-transform:uppercase;letter-spacing:.5px;">
                {_IC['check']} &nbsp; BULL CASE — Approval Agent
              </div>
              <div style="background:white;border:1px solid #E5E7EB;border-top:none;padding:20px;
                          border-radius:0 0 16px 16px;font-size:13.5px;line-height:1.7;color:#6B7280;
                          max-height:500px;overflow-y:auto;">
                {bull_html}
              </div>
            </div>
            """)
        with be:
            bear = str(_g(data, "bear_case", default="Not available"))
            bear_html = _debate_text_to_html(bear)
            st.html(f"""
            <div style="font-family:'DM Sans',sans-serif;">
              <div style="background:linear-gradient(135deg,{DANGER},#DC2626);color:white;padding:14px 20px;
                          border-radius:16px 16px 0 0;font-size:15px;font-weight:700;text-align:center;
                          text-transform:uppercase;letter-spacing:.5px;">
                {_IC['alert']} &nbsp; BEAR CASE — Dissent Agent
              </div>
              <div style="background:white;border:1px solid #E5E7EB;border-top:none;padding:20px;
                          border-radius:0 0 16px 16px;font-size:13.5px;line-height:1.7;color:#6B7280;
                          max-height:500px;overflow-y:auto;">
                {bear_html}
              </div>
            </div>
            """)

        # Final verdict
        rec = _g(data, "recommendation", default={})
        decision = _g(rec, "lending_decision", default="REVIEW")
        dc = _decision_color(decision)
        st.html(f"""
        <div style="background:white;border:1px solid #E5E7EB;border-left:5px solid {dc};
                    padding:24px;border-radius:0 16px 16px 0;margin:24px 0;
                    font-family:'DM Sans',sans-serif;">
          <h3 style="color:{dc};margin:0 0 8px 0;font-size:18px;font-weight:700;">FINAL VERDICT: {decision}</h3>
          <p style="margin:0;font-size:14px;line-height:1.7;color:#6B7280;">
            {_g(rec, 'final_rationale', default='N/A')}</p>
        </div>
        """)

        # Conditions
        conditions = _g(rec, "key_conditions", default=[])
        if conditions:
            st.html(_section_header_html("Lending Conditions & Covenants"))
            cond_html = ""
            for i, cond in enumerate(conditions, 1):
                cond_html += f"""
                <div style="border-left:3px solid #E8470A;padding:12px 16px;margin-bottom:8px;
                            background:#FFF7F4;border-radius:0 10px 10px 0;">
                  <span style="font-size:14px;color:#374151;"><strong>{i}.</strong> {cond}</span>
                </div>
                """
            st.html(f'<div style="font-family:DM Sans,sans-serif;">{cond_html}</div>')


def _debate_text_to_html(text: str) -> str:
    lines = text.split("\n")
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            out.append("<br>")
        elif line.startswith("## "):
            out.append(f"<h4 style='margin:14px 0 6px 0;font-size:14px;font-weight:600;color:#1A1A1A;'>{line[3:]}</h4>")
        elif line.startswith("- ") or line.startswith("• "):
            out.append(f"<div style='margin:2px 0 2px 12px;'>{line}</div>")
        else:
            out.append(f"<div>{line}</div>")
    return "\n".join(out)


# ════════════════════════════════════════════════════════════════════
#  PAGE  — REPORTS & DOWNLOAD
# ════════════════════════════════════════════════════════════════════

def render_reports(data: dict, cam_path: str = None):
    rec = _g(data, "recommendation", default={})
    ml = _g(data, "ml_scores", default={})
    fin = _g(data, "financial_data", default={})
    ceo = _g(data, "ceo_interview", default={})
    company = _g(data, "company_name")

    decision = _g(rec, "lending_decision", default="REVIEW")
    dc = _decision_color(decision)
    limit = _g(rec, "recommended_limit_cr", default="N/A")
    rate = _g(rec, "recommended_rate_pct", default="N/A")

    # Decision summary card (dark)
    st.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <div style="background:#1A1A1A;border-radius:20px;padding:32px;font-family:'DM Sans',sans-serif;
                box-shadow:0 4px 16px rgba(0,0,0,0.25);margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:24px;">
        <div>
          <p style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;
                    color:#E8470A;margin:0 0 12px 0;">Final Lending Decision</p>
          <p style="font-size:36px;font-weight:700;color:white;margin:0;">{decision}</p>
          <p style="font-size:16px;color:#9CA3AF;margin:8px 0 0 0;">
            ₹{_fmt(limit)} Cr at {_fmt(rate)}% with {len(_g(rec, 'key_conditions', default=[]))} conditions</p>
        </div>
      </div>
    </div>
    """)

    # Download buttons + Score summary
    dl_col, score_col = st.columns([3, 2])

    with dl_col:
        st.html(_section_header_html("Download Reports"))

        # CAM download
        st.html(_card_wrap(f"""
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:48px;height:48px;border-radius:14px;background:#FFF0EB;color:#E8470A;
                      display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;">
            {_IC['file']}</div>
          <div>
            <h3 style="margin:0;font-size:16px;font-weight:600;color:#1A1A1A;">Credit Appraisal Memorandum</h3>
            <p style="margin:4px 0 0 0;font-size:13px;color:#9CA3AF;">
              Professional DOCX with all 11 innovation outputs, financial analysis, and adversarial debate.</p>
          </div>
        </div>
        """))

        gen_col, dl_btn_col = st.columns(2)
        with gen_col:
            generate_btn = st.button("Generate Full CAM Report", type="primary", use_container_width=True, key="gen_cam")
        with dl_btn_col:
            if cam_path and os.path.exists(cam_path):
                with open(cam_path, "rb") as f:
                    st.download_button(
                        "Download DOCX", data=f,
                        file_name=os.path.basename(cam_path),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

        if generate_btn:
            _generate_cam(data, cam_path)

        # JSON download
        json_summary = {
            "company_name": company,
            "generated_at": datetime.now().isoformat(),
            "lending_decision": _g(rec, "lending_decision"),
            "credit_limit_cr": _g(rec, "recommended_limit_cr"),
            "interest_rate_pct": _g(rec, "recommended_rate_pct"),
            "ensemble_pd": _g(ml, "ensemble_pd"),
            "dscr": _g(fin, "dscr"),
            "beneish_m_score": _g(fin, "beneish_m_score"),
        }
        st.download_button(
            "Download Scores JSON",
            data=json.dumps(json_summary, indent=2),
            file_name=f"scores_{str(company).replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with score_col:
        st.html(_section_header_html("Score Summary"))

        summary_items = [
            ("Lending Decision", _g(rec, "lending_decision")),
            ("Credit Limit", f"₹{_fmt(_g(rec, 'recommended_limit_cr'))} Cr"),
            ("Interest Rate", f"{_fmt(_g(rec, 'recommended_rate_pct'))}%"),
            ("Ensemble PD", _pct(_g(ml, "ensemble_pd"))),
            ("DSCR", _fmt(_g(fin, "dscr"))),
            ("D/E Ratio", _fmt(_g(fin, "debt_to_equity"))),
            ("Beneish M-Score", _fmt(_g(fin, "beneish_m_score"))),
            ("Altman Z-Score", _fmt(_g(fin, "altman_z_score"))),
            ("Contagion Risk", _fmt(_g(fin, "contagion_risk_score"))),
            ("Satellite Score", _fmt(_g(fin, "satellite_activity_score"), ".0f")),
            ("MQ Score", _fmt(_g(ceo, "management_quality_score"), ".0f")),
        ]
        rows_html = ""
        for label, val in summary_items:
            rows_html += f"""
            <div style="display:flex;justify-content:space-between;padding:10px 0;
                        border-bottom:1px solid #F3F4F6;">
              <span style="font-size:14px;color:#6B7280;font-weight:500;">{label}</span>
              <span style="font-size:14px;color:#1A1A1A;font-weight:600;">{val}</span>
            </div>
            """
        st.html(_card_wrap(rows_html, pad="20px 24px"))


def _generate_cam(data: dict, cam_path: str = None):
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
            for i, section in enumerate(sections):
                progress.progress((i + 1) / len(sections), text=f"Generating: {section}...")
                time.sleep(0.3)
            import sys, os
            PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            output_dir = os.path.join(PROJECT_ROOT, "data", "processed")
            new_path = generate_cam(data, output_dir=output_dir)
            if new_path and os.path.exists(new_path):
                st.session_state.cam_path = new_path
                progress.progress(1.0, text="CAM generated!")
                st.rerun()
            else:
                st.error("CAM generation failed — check logs.")
        except ImportError:
            st.error("python-docx not installed. Run: pip install python-docx")
        except Exception as e:
            st.error(f"Error generating CAM: {e}")
