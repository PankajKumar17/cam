"""
Intelli-Credit — Landing Page
=============================================================
Theme: Finexy-inspired fintech (orange #E8470A + white + near-black)
Fonts: DM Sans · DM Serif Display
Icons: Inline SVGs (no external font dependency)
"""

import os
import time
import tempfile

import streamlit as st

# ── Inline SVG icons (render in any iframe without external CSS) ──
_IC = {
    "chip": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M15 20v2M9 2v2M9 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/></svg>',
    "check": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "chart": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "upload": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "arrow": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    "shield": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
    "search": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>',
    "network": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
    "robot": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>',
    "lock": '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
}


# ════════════════════════════════════════════════════════════════════
#  CSS — injected via st.html() targeting parent Streamlit DOM
# ════════════════════════════════════════════════════════════════════

_STYLE_BLOCK = """
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
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
    padding: 0 !important;
    max-width: 100% !important;
}
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stHeader"]  { background: transparent !important; }
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }

h1,h2,h3,h4,h5,h6 { color: #1A1A1A !important; font-family: 'DM Sans', sans-serif !important; }
p, span, label, li { font-family: 'DM Sans', sans-serif !important; }

/* Upload card container */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border-radius: 24px !important;
    border: none !important;
    box-shadow: 0 8px 40px rgba(0,0,0,0.10) !important;
    padding: 8px 20px !important;
}
/* Text input */
[data-testid="stTextInput"] label {
    font-size: 12px !important; font-weight: 600 !important;
    text-transform: uppercase !important; color: #9CA3AF !important;
    letter-spacing: .5px !important;
}
[data-testid="stTextInput"] input {
    background: #FFFFFF !important; color: #1A1A1A !important;
    border: 1.5px solid #E5E7EB !important; border-radius: 12px !important;
    height: 48px !important; padding: 0 16px !important;
    font-size: 15px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #E8470A !important;
    box-shadow: 0 0 0 3px rgba(232,71,10,.1) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #9CA3AF !important; }

/* File uploader — light theme, bigger drop zone */
[data-testid="stFileUploader"] {
    background: #FAFAFA !important;
    border: 2px dashed #E5E7EB !important;
    border-radius: 16px !important;
    padding: 28px 20px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #E8470A !important; background: #FFF7F4 !important;
}
[data-testid="stFileUploader"] label {
    font-size: 12px !important; font-weight: 600 !important;
    text-transform: uppercase !important; color: #9CA3AF !important;
}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small { color: #6B7280 !important; }

/* Fix file uploader icon — remove dark bg, make orange & bigger */
[data-testid="stFileUploaderDropzoneInput"] > div:first-child,
[data-testid="stFileUploaderDropzone"] > div {
    background: transparent !important;
}
[data-testid="stFileUploader"] svg,
[data-testid="stFileUploaderDropzoneInput"] svg {
    color: #E8470A !important;
    width: 44px !important;
    height: 44px !important;
}
/* Browse files button */
[data-testid="stFileUploader"] section > button,
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
    background: transparent !important; color: #E8470A !important;
    border: 1.5px solid #E8470A !important; font-weight: 600 !important;
    box-shadow: none !important; border-radius: 10px !important;
    min-height: 40px !important;
}
[data-testid="stFileUploader"] section > button:hover,
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover {
    background: #FFF0EB !important;
}

/* Primary button — orange gradient */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #E8470A 0%, #FF6B35 100%) !important;
    color: white !important; border: none !important;
    border-radius: 14px !important; min-height: 48px !important;
    font-weight: 600 !important; font-size: 15px !important;
    box-shadow: 0 4px 16px rgba(232,71,10,.35) !important;
    transition: all .2s ease !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(232,71,10,.45) !important;
}
.stButton > button[kind="primary"]:disabled {
    opacity: .5 !important; transform: none !important; box-shadow: none !important;
}
/* Secondary button — dark */
.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="stBaseButton-secondary"]) {
    background: #1A1A1A !important; color: white !important;
    border: none !important; border-radius: 14px !important;
    min-height: 48px !important; font-weight: 600 !important;
    font-size: 14px !important; transition: all .15s ease !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="stBaseButton-secondary"]):hover {
    background: #2D2D2D !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #E8470A, #FF6B35) !important;
}
</style>
"""


# ════════════════════════════════════════════════════════════════════
#  Pure-HTML blocks rendered via st.html() (no Streamlit sanitiser)
# ════════════════════════════════════════════════════════════════════

_NAVBAR_HTML = """
<nav style="
    position:sticky; top:0; z-index:100;
    background:#FFFFFF; border-bottom:1px solid #F3F4F6;
    backdrop-filter:blur(12px); font-family:'DM Sans',sans-serif;
">
  <div style="max-width:1280px;margin:0 auto;padding:0 40px;height:64px;
              display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:36px;height:36px;border-radius:50%;
                  background:linear-gradient(135deg,#E8470A,#FF6B35);
                  display:flex;align-items:center;justify-content:center;
                  color:white;font-weight:700;font-size:14px;">IC</div>
      <span style="font-weight:600;font-size:18px;color:#1A1A1A;">Intelli-Credit</span>
    </div>
    <div style="display:flex;align-items:center;gap:24px;">
      <a href="#" style="font-size:14px;color:#6B7280;text-decoration:none;">Documentation</a>
      <a href="#" style="font-size:14px;color:#6B7280;text-decoration:none;">About</a>
    </div>
  </div>
</nav>
"""

def _hero_left_html():
    return f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>@keyframes icFU{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}</style>
<div style="padding-top:20px;animation:icFU .5s ease-out;font-family:'DM Sans',sans-serif;">
  <div style="display:inline-flex;align-items:center;gap:8px;
              background:#FFF0EB;color:#E8470A;font-size:11px;font-weight:600;
              text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;
              border-radius:999px;border:1px solid rgba(232,71,10,0.2);margin-bottom:24px;">
    <span style="font-size:16px;line-height:1;display:flex;">{_IC['chip']}</span>
    AI Credit Decisioning Engine
  </div>
  <h1 style="font-family:'DM Serif Display',Georgia,serif;
             font-size:52px;line-height:62px;color:#1A1A1A;margin:0 0 24px 0;font-weight:400;">
    Intelligent Credit<br>Decisions in<br>
    <span style="color:#E8470A;"><em>Minutes.</em></span>
  </h1>
  <p style="font-size:18px;line-height:28px;color:#6B7280;max-width:480px;margin:0 0 32px 0;">
    Upload financial statements, get a complete Credit Appraisal
    Memo powered by 17 AI innovations &mdash; Beneish forensics, satellite
    intelligence, and adversarial LLM agents.
  </p>
  <div style="display:flex;gap:24px;flex-wrap:wrap;">
    <span style="font-size:13px;color:#6B7280;display:flex;align-items:center;gap:6px;">
      <span style="color:#10B981;font-size:16px;display:flex;">{_IC['check']}</span> XGBoost AUC 0.9948</span>
    <span style="font-size:13px;color:#6B7280;display:flex;align-items:center;gap:6px;">
      <span style="color:#10B981;font-size:16px;display:flex;">{_IC['check']}</span> 146 ML Features</span>
    <span style="font-size:13px;color:#6B7280;display:flex;align-items:center;gap:6px;">
      <span style="color:#10B981;font-size:16px;display:flex;">{_IC['check']}</span> Full CAM in &lt; 5 min</span>
  </div>
</div>
"""


def _card_header_html():
    return f"""
<div style="font-family:'DM Sans',sans-serif;">
  <h3 style="font-size:20px;font-weight:600;color:#1A1A1A;margin:0 0 4px 0;display:flex;align-items:center;gap:8px;">
    <span style="color:#E8470A;font-size:22px;display:flex;">{_IC['chart']}</span>Start Your Analysis
  </h3>
  <p style="font-size:13px;color:#9CA3AF;margin:0 0 8px 0;">Enter company name and upload financials</p>
</div>
"""


def _privacy_html():
    return f"""
<p style="text-align:center;font-size:12px;color:#9CA3AF;padding:8px 0 0 0;
          font-family:'DM Sans',sans-serif;display:flex;align-items:center;justify-content:center;gap:5px;">
  <span style="font-size:13px;display:flex;">{_IC['lock']}</span> Files processed locally &middot; never stored
</p>
"""


def _bottom_sections_html():
    return f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<div style="font-family:'DM Sans',sans-serif;">

  <!-- ── How It Works ──────────────────────────────────────── -->
  <div style="padding:80px 0 0;">
    <div style="max-width:1280px;margin:0 auto;padding:0 40px;">
      <h2 style="font-family:'DM Sans',sans-serif;font-size:36px;font-weight:600;color:#1A1A1A;text-align:center;margin:0 0 8px 0;">
        How It Works</h2>
      <p style="font-size:16px;color:#6B7280;text-align:center;margin:0 0 48px 0;">
        From PDF to lending decision in three steps</p>
      <div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:16px;align-items:start;">

        <!-- Step 01 -->
        <div style="background:white;border:1px solid #E5E7EB;border-radius:20px;padding:32px 28px;">
          <p style="font-size:11px;font-weight:700;text-transform:uppercase;color:#E8470A;letter-spacing:2px;margin:0 0 16px 0;">Step 01</p>
          <div style="width:56px;height:56px;border-radius:16px;background:#FFF0EB;color:#E8470A;
                      display:flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:16px;">
            {_IC['upload']}</div>
          <h3 style="font-size:18px;font-weight:600;color:#1A1A1A;margin:0 0 8px 0;">Upload &amp; Name</h3>
          <p style="font-size:14px;color:#6B7280;line-height:1.6;margin:0;">
            Enter the company name and attach financial statements in Excel or CSV format.</p>
        </div>

        <!-- Arrow -->
        <div style="display:flex;align-items:center;justify-content:center;color:#D1D5DB;font-size:24px;padding-top:80px;">
          {_IC['arrow']}</div>

        <!-- Step 02 -->
        <div style="background:white;border:1px solid #E5E7EB;border-radius:20px;padding:32px 28px;">
          <p style="font-size:11px;font-weight:700;text-transform:uppercase;color:#E8470A;letter-spacing:2px;margin:0 0 16px 0;">Step 02</p>
          <div style="width:56px;height:56px;border-radius:16px;background:#FFF0EB;color:#E8470A;
                      display:flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:16px;">
            {_IC['chip']}</div>
          <h3 style="font-size:18px;font-weight:600;color:#1A1A1A;margin:0 0 8px 0;">AI Analyses</h3>
          <p style="font-size:14px;color:#6B7280;line-height:1.6;margin:0;">
            17 innovation modules run in parallel &mdash; forensics, ML ensemble, stress testing, and more.</p>
        </div>

        <!-- Arrow -->
        <div style="display:flex;align-items:center;justify-content:center;color:#D1D5DB;font-size:24px;padding-top:80px;">
          {_IC['arrow']}</div>

        <!-- Step 03 -->
        <div style="background:white;border:1px solid #E5E7EB;border-radius:20px;padding:32px 28px;">
          <p style="font-size:11px;font-weight:700;text-transform:uppercase;color:#E8470A;letter-spacing:2px;margin:0 0 16px 0;">Step 03</p>
          <div style="width:56px;height:56px;border-radius:16px;background:#FFF0EB;color:#E8470A;
                      display:flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:16px;">
            {_IC['shield']}</div>
          <h3 style="font-size:18px;font-weight:600;color:#1A1A1A;margin:0 0 8px 0;">Get Decision</h3>
          <p style="font-size:14px;color:#6B7280;line-height:1.6;margin:0;">
            Full Credit Appraisal Memo with PD score, recommended limit, and interest rate &mdash; in minutes.</p>
        </div>

      </div>
    </div>
  </div>

  <!-- ── Stats Strip ───────────────────────────────────────── -->
  <div style="background:#ECEEF2;padding:48px 0;margin-top:80px;">
    <div style="max-width:1280px;margin:0 auto;padding:0 40px;
                display:grid;grid-template-columns:repeat(4,1fr);">
      <div style="text-align:center;border-right:1px solid #D1D5DB;padding:0 20px;">
        <p style="font-family:'DM Serif Display',serif;font-size:48px;color:#1A1A1A;line-height:1.1;margin:0;">17</p>
        <p style="font-size:13px;font-weight:500;text-transform:uppercase;color:#6B7280;letter-spacing:1.5px;margin:8px 0 0 0;">Innovations</p>
      </div>
      <div style="text-align:center;border-right:1px solid #D1D5DB;padding:0 20px;">
        <p style="font-family:'DM Serif Display',serif;font-size:48px;color:#1A1A1A;line-height:1.1;margin:0;">146</p>
        <p style="font-size:13px;font-weight:500;text-transform:uppercase;color:#6B7280;letter-spacing:1.5px;margin:8px 0 0 0;">ML Features</p>
      </div>
      <div style="text-align:center;border-right:1px solid #D1D5DB;padding:0 20px;">
        <p style="font-family:'DM Serif Display',serif;font-size:48px;color:#1A1A1A;line-height:1.1;margin:0;">0.9961</p>
        <p style="font-size:13px;font-weight:500;text-transform:uppercase;color:#6B7280;letter-spacing:1.5px;margin:8px 0 0 0;">AUC Score</p>
      </div>
      <div style="text-align:center;padding:0 20px;">
        <p style="font-family:'DM Serif Display',serif;font-size:48px;color:#1A1A1A;line-height:1.1;margin:0;">&lt; 5 min</p>
        <p style="font-size:13px;font-weight:500;text-transform:uppercase;color:#6B7280;letter-spacing:1.5px;margin:8px 0 0 0;">Processing</p>
      </div>
    </div>
  </div>

  <!-- ── Features ──────────────────────────────────────────── -->
  <div style="padding:80px 0;">
    <div style="max-width:1280px;margin:0 auto;padding:0 40px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:start;">

        <div>
          <h2 style="font-family:'DM Sans',sans-serif;font-size:36px;font-weight:600;color:#1A1A1A;margin:0 0 16px 0;">
            Built on Academic-Grade ML</h2>
          <p style="font-size:15px;color:#6B7280;line-height:1.7;margin:0 0 24px 0;">
            Our credit decisioning engine combines Beneish M-Score forensic
            analysis with an XGBoost / LightGBM / Random Forest ensemble
            trained on 146 engineered features. The system achieves an AUC
            of 0.9961 on validation data, with adversarial LLM agents
            providing bull-bear debate analysis for every decision.
          </p>
          <p style="font-size:15px;color:#6B7280;line-height:1.7;margin:0 0 24px 0;">
            Monte Carlo stress testing with 10,000 DSCR trajectory simulations,
            satellite imagery verification, GST cross-referencing, and
            corporate DNA matching against historical default cases add layers
            of intelligence no traditional model offers.
          </p>
        </div>

        <div>
          <!-- Feature 1 — tinted -->
          <div style="background:#FFF7F4;border:1px solid rgba(232,71,10,.2);border-left:3px solid #E8470A;
                      border-radius:16px;padding:24px;margin-bottom:16px;display:flex;gap:16px;align-items:flex-start;">
            <div style="width:44px;height:44px;border-radius:12px;background:#FFF0EB;color:#E8470A;
                        display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
              {_IC['search']}</div>
            <div>
              <h4 style="font-size:15px;font-weight:600;color:#1A1A1A;margin:0 0 4px 0;">Beneish M-Score Forensics</h4>
              <p style="font-size:13px;color:#6B7280;margin:0;line-height:1.5;">
                8-factor earnings manipulation detection based on Prof.
                Beneish&rsquo;s academic model. Flags accounting anomalies before they become crises.</p>
            </div>
          </div>
          <!-- Feature 2 -->
          <div style="background:white;border:1px solid #E5E7EB;border-radius:16px;padding:24px;
                      margin-bottom:16px;display:flex;gap:16px;align-items:flex-start;">
            <div style="width:44px;height:44px;border-radius:12px;background:#EFF6FF;color:#3B82F6;
                        display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
              {_IC['network']}</div>
            <div>
              <h4 style="font-size:15px;font-weight:600;color:#1A1A1A;margin:0 0 4px 0;">Network Graph GNN</h4>
              <p style="font-size:13px;color:#6B7280;margin:0;line-height:1.5;">
                Promoter network analysis mapping director interlocks,
                group company contagion risk, and NPA exposure across corporate relationships.</p>
            </div>
          </div>
          <!-- Feature 3 -->
          <div style="background:white;border:1px solid #E5E7EB;border-radius:16px;padding:24px;
                      margin-bottom:16px;display:flex;gap:16px;align-items:flex-start;">
            <div style="width:44px;height:44px;border-radius:12px;background:#EEF2FF;color:#6366F1;
                        display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
              {_IC['robot']}</div>
            <div>
              <h4 style="font-size:15px;font-weight:600;color:#1A1A1A;margin:0 0 4px 0;">Adversarial LLM Agents</h4>
              <p style="font-size:13px;color:#6B7280;margin:0;line-height:1.5;">
                Bull and bear agents independently argue for and against
                lending, with a coordinator synthesising the final recommendation &mdash; removing single-model bias.</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>

  <!-- ── Footer ────────────────────────────────────────────── -->
  <div style="background:#1A1A1A;padding:48px 0 32px;">
    <div style="max-width:1280px;margin:0 auto;padding:0 40px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:32px;">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:36px;height:36px;border-radius:50%;
                      background:linear-gradient(135deg,#E8470A,#FF6B35);
                      display:flex;align-items:center;justify-content:center;
                      color:white;font-weight:700;font-size:14px;font-family:'DM Sans',sans-serif;">IC</div>
          <div>
            <div style="font-size:16px;font-weight:600;color:white;font-family:'DM Sans',sans-serif;">Intelli-Credit</div>
            <p style="font-size:13px;color:#9CA3AF;margin:4px 0 0 0;">AI Credit Decisioning Engine</p>
          </div>
        </div>
        <div style="display:flex;gap:24px;">
          <a href="#" style="font-size:13px;color:#9CA3AF;text-decoration:none;font-family:'DM Sans',sans-serif;">Documentation</a>
          <a href="#" style="font-size:13px;color:#9CA3AF;text-decoration:none;font-family:'DM Sans',sans-serif;">Architecture</a>
          <a href="#" style="font-size:13px;color:#9CA3AF;text-decoration:none;font-family:'DM Sans',sans-serif;">Hackathon</a>
        </div>
      </div>
      <div style="border-top:1px solid #2D2D2D;padding-top:24px;font-size:12px;color:#6B7280;">
        &copy; 2025 Intelli-Credit &middot; Vivriti Capital AI Hackathon
      </div>
    </div>
  </div>

</div>
"""


# ════════════════════════════════════════════════════════════════════
#  Main render function
# ════════════════════════════════════════════════════════════════════

def render_landing(*, load_demo, adapt_results, run_pipeline_fn, parse_excel_fn, project_root):
    """Render the Intelli-Credit landing page."""

    # 1. Inject global CSS overrides (targets parent Streamlit DOM)
    st.html(_STYLE_BLOCK)

    # 2. Navbar (pure HTML — no Streamlit widgets)
    st.html(_NAVBAR_HTML)

    # 3. Hero section — left is pure HTML, right has Streamlit widgets
    hero_left, hero_right = st.columns([55, 45], gap="large")

    with hero_left:
        st.html(_hero_left_html())

    with hero_right:
        with st.container(border=True):
            st.html(_card_header_html())

            company_name = st.text_input(
                "Company Name",
                placeholder="e.g. Sunrise Textile Mills",
                key="landing_company",
            )

            fin_file = st.file_uploader(
                "Financial Statements (Excel / CSV)",
                type=["xlsx", "xls", "csv"],
                key="landing_file",
            )

            btn_left, btn_right = st.columns(2)
            with btn_left:
                run_btn = st.button(
                    "Analyse with AI  \u2192",
                    type="primary",
                    use_container_width=True,
                    disabled=not company_name or fin_file is None,
                    key="landing_analyze",
                )
            with btn_right:
                demo_btn = st.button(
                    "Load Demo",
                    use_container_width=True,
                    key="landing_demo",
                )

            st.html(_privacy_html())

    # 4. Processing placeholder
    proc_area = st.empty()

    # 5. How It Works + Stats + Features + Footer (all pure HTML)
    st.html(_bottom_sections_html())

    # ════════════════════════════════════════════════════════════
    #  Button handlers
    # ════════════════════════════════════════════════════════════

    if demo_btn:
        with st.spinner("Loading demo data\u2026"):
            time.sleep(0.4)
            st.session_state.results = load_demo()
            st.session_state.pipeline_done = True
            st.session_state.cam_path = None
        st.rerun()

    if run_btn and company_name and fin_file:
        with proc_area.container():
            st.html(
                '<div style="background:#FFF7F4;border:1px solid rgba(232,71,10,.2);'
                'border-radius:16px;padding:20px 24px;margin-bottom:16px;font-family:DM Sans,sans-serif;">'
                '<p style="color:#1A1A1A;font-weight:500;margin:0;">'
                f'Analysing <strong>{company_name}</strong>\u2026</p></div>'
            )
            progress = st.progress(0, text="Parsing uploaded file\u2026")

            try:
                tmp_path = os.path.join(tempfile.gettempdir(), fin_file.name)
                with open(tmp_path, "wb") as f:
                    f.write(fin_file.getbuffer())

                company_data = parse_excel_fn(tmp_path, company_name)
                progress.progress(0.10, text="File parsed \u2014 starting pipeline\u2026")

                prefetched = st.session_state.get("prefetched_data", {})
                if prefetched:
                    company_data.update(prefetched)

                output_dir = os.path.join(project_root, "data", "processed")
                os.makedirs(output_dir, exist_ok=True)

                progress.progress(0.15, text="Running 17-innovation pipeline\u2026")
                raw_results = run_pipeline_fn(
                    company_name=company_name,
                    company_data=company_data,
                    output_dir=output_dir,
                )

                progress.progress(0.90, text="Adapting results\u2026")
                adapted = adapt_results(raw_results)

                cam_path = raw_results.get("cam_path")
                if cam_path and os.path.exists(str(cam_path)):
                    adapted["cam_path"] = cam_path
                    st.session_state.cam_path = cam_path
                else:
                    st.session_state.cam_path = None

                st.session_state.results = adapted
                st.session_state.pipeline_done = True

                progress.progress(1.0, text="Analysis complete!")
                time.sleep(0.5)
                st.rerun()

            except Exception as exc:
                progress.progress(1.0, text="Pipeline failed")
                st.error(f"Pipeline error: {exc}")
                import traceback
                st.code(traceback.format_exc(), language="text")
