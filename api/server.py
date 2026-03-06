"""
Yakṣarāja — FastAPI Backend
============================
Wraps the existing pipeline modules and serves JSON to the React frontend.
"""

import os
import sys
import json
import uuid
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response as RawResponse
import json as _json


class UTF8JSONResponse(JSONResponse):
    """JSONResponse that keeps emoji intact (ensure_ascii=False)."""
    def render(self, content) -> bytes:
        return _json.dumps(content, ensure_ascii=False, allow_nan=False, default=str).encode("utf-8")

# ── Project path setup ──────────────────────────────────────────────────
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from pipeline.main_pipeline import run_pipeline, SUNRISE_DEMO_FINANCIALS
from pipeline.excel_parser import parse_screener_excel

import logging
logging.getLogger("uvicorn").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

# ── App ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Yakṣarāja API", version="1.0.0", default_response_class=UTF8JSONResponse)

_allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
if _frontend_url:
    _allowed_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for analysis results (single-user hackathon demo)
_store: dict = {}

_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def _persist_analysis(analysis_id: str, data: dict) -> None:
    """Save analysis data to disk so it survives server restarts."""
    try:
        os.makedirs(_STORE_DIR, exist_ok=True)
        path = os.path.join(_STORE_DIR, f"analysis_{analysis_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception:
        pass


def _load_persisted_stores() -> None:
    """On startup, reload any previously saved analyses into _store."""
    try:
        if not os.path.isdir(_STORE_DIR):
            return
        for fname in os.listdir(_STORE_DIR):
            if fname.startswith("analysis_") and fname.endswith(".json"):
                aid = fname[len("analysis_"):-len(".json")]
                path = os.path.join(_STORE_DIR, fname)
                with open(path, "r", encoding="utf-8") as f:
                    _store[aid] = json.load(f)
    except Exception:
        pass


_load_persisted_stores()


# ── Helpers ─────────────────────────────────────────────────────────────

def _safe(val, default="N/A"):
    return val if val is not None else default


def _load_demo_data() -> dict:
    """Pre-computed demo data for Sunrise Textile Mills (no API calls)."""
    return {
        "company_name": "Sunrise Textile Mills",
        "fiscal_year": 2024,
        "sector": "Textiles",
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
            "label": 0,
        },
        "ml_scores": {
            "ensemble_pd": 0.12, "xgb_pd": 0.11, "rf_pd": 0.14, "lgb_pd": 0.13,
            "lending_decision": "CONDITIONAL_APPROVE",
            "risk_premium": 3.5,
            "model_disagreement": 0.03,
            "model_disagreement_flag": False,
        },
        "trajectory": {
            "dscr_trend": "STABLE",
            "months_to_danger": 36,
            "dscr_3yr_slope": 0.03,
            "dscr_history": [1.55, 1.62, 1.70, 1.78, 1.85],
            "fiscal_years": [2020, 2021, 2022, 2023, 2024],
        },
        "forensics": {
            "beneish_m_score": -2.45, "beneish_flag": "CLEAN",
            "altman_z_score": 2.3, "altman_zone": "GREY",
            "piotroski_f_score": 6, "piotroski_strength": "MODERATE",
        },
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
        "satellite": {
            "activity_score": 82.5,
            "activity_category": "ACTIVE",
            "vs_revenue_flag": 0,
        },
        "dna_match": {
            "closest_default_archetype": "None (Healthy)",
            "max_archetype_similarity": 0.18,
        },
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
            "research_sources": ["Economic Times", "Business Standard", "CRISIL Textiles Report"],
            "used_fallback": False,
        },
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


def _adapt_pipeline_results(results: dict) -> dict:
    """Reshape run_pipeline() output to the dashboard-expected format."""

    company_data = results.get("company_data", {})
    ml_scores = results.get("ml_scores", {})
    stress_raw = results.get("stress_test", {})
    trajectory = results.get("trajectory", {})
    network_raw = results.get("network", {})
    dna_raw = results.get("dna_match", {})
    ceo_raw = results.get("ceo_interview", {})

    xgb = ml_scores.get("pd_xgb", ml_scores.get("xgb_pd"))
    rf  = ml_scores.get("pd_rf",  ml_scores.get("rf_pd"))
    ml_adapted = {
        "ensemble_pd": ml_scores.get("ensemble_pd"),
        "xgb_pd": xgb,
        "rf_pd": rf,
        "lgb_pd": ml_scores.get("pd_lgb", ml_scores.get("lgb_pd")),
        "lending_decision": ml_scores.get("lending_decision", "REVIEW"),
        "risk_premium": ml_scores.get("risk_premium"),
        "credit_limit_cr": ml_scores.get("credit_limit_cr"),
        "model_disagreement": abs(xgb - rf) if xgb is not None and rf is not None else None,
        "model_disagreement_flag": ml_scores.get("model_disagreement_flag", False),
    }

    # stress_test returns "simulated_dscrs" (numpy ndarray) — convert to plain list
    _sim = stress_raw.get("simulated_dscrs",
           stress_raw.get("dscr_simulated",
           stress_raw.get("all_dscr", [])))
    try:
        dscr_simulated = [round(float(v), 4) for v in _sim]
    except (TypeError, ValueError):
        dscr_simulated = []
    named_scenarios_raw = stress_raw.get("named_scenarios", {})
    if isinstance(named_scenarios_raw, dict):
        scenarios = named_scenarios_raw.get("scenarios", [])
    else:
        scenarios = named_scenarios_raw if isinstance(named_scenarios_raw, list) else []

    stress_adapted = {
        "dscr_p10": stress_raw.get("p10_dscr", stress_raw.get("dscr_p10")),
        "dscr_p50": stress_raw.get("p50_dscr", stress_raw.get("dscr_p50")),
        "dscr_p90": stress_raw.get("p90_dscr", stress_raw.get("dscr_p90")),
        "covenant_breach_probability": stress_raw.get(
            "default_probability_3yr",
            stress_raw.get("covenant_breach_probability")
        ),
        "dscr_simulated": dscr_simulated if dscr_simulated else [],
        "named_scenarios": [
            {
                "name": sc.get("name", ""),
                "dscr_impact": sc.get("dscr", sc.get("dscr_impact", 1.0)),
                "pd_impact": sc.get("pd_impact", max(0, 1.0 - sc.get("dscr", 1.0))),
            }
            for sc in scenarios
        ],
    }

    # dscr_trend can be either a list (old fallback) or a string like "GREEN"
    _raw_dscr_trend = trajectory.get("dscr_trend")
    _dscr_hist = (
        (_raw_dscr_trend if isinstance(_raw_dscr_trend, list) else [])
        or trajectory.get("dscr_history", [])
        or company_data.get("dscr_history", [])
    )
    _fy_list = (
        trajectory.get("fiscal_years")
        or company_data.get("fiscal_years", [])
    )
    traj_adapted = {
        "dscr_trend": trajectory.get("warning_level", "STABLE") if not isinstance(_raw_dscr_trend, list) else "STABLE",
        "months_to_danger": trajectory.get("estimated_months_to_distress"),
        "dscr_3yr_slope": trajectory.get("dscr_velocity"),
        "dscr_history": _dscr_hist,
        "fiscal_years": _fy_list,
    }

    nodes = network_raw.get("network_nodes", [])
    edges = network_raw.get("network_edges", [])

    # De-duplicate and filter out "Unknown" placeholder nodes
    seen_ids = set()
    clean_nodes = []
    for n in nodes:
        nid = n.get("id", "")
        if nid and nid != "Unknown" and nid not in seen_ids:
            seen_ids.add(nid)
            clean_nodes.append(n)
    valid_ids = seen_ids
    clean_edges = [e for e in edges
                   if e.get("from") in valid_ids and e.get("to") in valid_ids]
    nodes, edges = clean_nodes, clean_edges

    if not nodes:
        company_name = results.get("company_name", "Company")
        nodes = [{"id": company_name, "type": "target", "npa": False}]
        for d in network_raw.get("directors", []):
            name = d if isinstance(d, str) else d.get("name", "Unknown")
            if name != "Unknown":
                nodes.append({"id": name, "type": "promoter", "npa": False})
        for c in network_raw.get("related_companies", []):
            cname = c if isinstance(c, str) else c.get("name", c.get("company_name", "Unknown"))
            if cname != "Unknown":
                is_npa = c.get("is_npa", False) if isinstance(c, dict) else False
                nodes.append({"id": cname, "type": "related", "npa": is_npa})
        edges = [{"from": n["id"], "to": company_name} for n in nodes[1:]]

    network_adapted = {
        "contagion_risk_score": network_raw.get("contagion_risk_score", 0),
        "network_nodes": nodes,
        "network_edges": edges,
    }

    dna_adapted = {
        "closest_default_archetype": dna_raw.get(
            "closest_archetype", dna_raw.get("closest_default_archetype", "N/A")),
        "max_archetype_similarity": dna_raw.get(
            "max_similarity", dna_raw.get("max_archetype_similarity", 0)),
    }

    return {
        "company_name": results.get("company_name", "Unknown"),
        "fiscal_year": company_data.get("fiscal_year", 2024),
        "sector": company_data.get("sector", "Industrial"),
        "financial_data": company_data,
        "ml_scores": ml_adapted,
        "trajectory": traj_adapted,
        "forensics": results.get("forensics", {}),
        "network": network_adapted,
        "stress_test": stress_adapted,
        "satellite": results.get("satellite", {}),
        "gst": results.get("gst", {}),
        "mca_legal": results.get("mca_legal", {}),
        "bank_analysis": results.get("bank_analysis", {}),
        "pdf_analysis": results.get("pdf_analysis"),
        "qualitative_notes": company_data.get("qualitative_notes"),
        "dna_match": dna_adapted,
        "research": results.get("research", {}),
        "ceo_interview": ceo_raw,
        "bull_case": results.get("bull_case", "Not available"),
        "bear_case": results.get("bear_case", "Not available"),
        "recommendation": results.get("recommendation", {}),
        "cam_path": results.get("cam_path"),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/demo")
async def load_demo():
    """Load pre-computed Sunrise Textile Mills demo data."""
    data = _load_demo_data()
    analysis_id = str(uuid.uuid4())[:8]
    _store[analysis_id] = data
    _persist_analysis(analysis_id, data)
    return {"analysis_id": analysis_id, "data": data}


@app.post("/api/analyse")
async def analyse(
    company_name: str = Form(...),
    file: UploadFile = File(...),
    ceo_audio: Optional[UploadFile] = File(None),
    ceo_transcript: Optional[str] = Form(None),
    pdf_files: Optional[List[UploadFile]] = File(None),
    qualitative_notes: Optional[str] = Form(None),
):
    """Upload financials (and optionally CEO interview audio/transcript + PDF documents) then run the pipeline."""
    allowed_ext = {".xlsx", ".xls", ".csv"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    allowed_audio_ext = {".mp3", ".wav", ".mp4", ".m4a", ".ogg", ".flac"}
    if ceo_audio and ceo_audio.filename:
        audio_ext = os.path.splitext(ceo_audio.filename)[1].lower()
        if audio_ext not in allowed_audio_ext:
            raise HTTPException(400, f"Unsupported audio type: {audio_ext}. Use mp3/wav/mp4")

    if pdf_files:
        for pf in pdf_files:
            if pf and pf.filename:
                if not pf.filename.lower().endswith(".pdf"):
                    raise HTTPException(400, f"PDF upload '{pf.filename}' is not a .pdf file")

    # Save uploads to temp dir
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    ceo_audio_path = None
    saved_pdf_paths: List[str] = []
    try:
        with open(tmp_path, "wb") as f:
            content = await file.read()
            if len(content) > 200 * 1024 * 1024:  # 200MB limit
                raise HTTPException(413, "File too large (max 200MB)")
            f.write(content)

        # Save CEO audio if provided
        if ceo_audio and ceo_audio.filename:
            ceo_tmp_path = os.path.join(tmp_dir, ceo_audio.filename)
            audio_content = await ceo_audio.read()
            if len(audio_content) > 500 * 1024 * 1024:  # 500MB limit for audio
                raise HTTPException(413, "Audio file too large (max 500MB)")
            with open(ceo_tmp_path, "wb") as f:
                f.write(audio_content)
            ceo_audio_path = ceo_tmp_path

        # Save PDF documents if provided
        if pdf_files:
            for pf in pdf_files:
                if pf and pf.filename:
                    pdf_tmp_path = os.path.join(tmp_dir, pf.filename)
                    pdf_content = await pf.read()
                    if len(pdf_content) > 100 * 1024 * 1024:  # 100MB per PDF
                        raise HTTPException(413, f"PDF '{pf.filename}' too large (max 100MB)")
                    with open(pdf_tmp_path, "wb") as f:
                        f.write(pdf_content)
                    saved_pdf_paths.append(pdf_tmp_path)

        # Parse the uploaded financials
        company_data = parse_screener_excel(tmp_path, company_name=company_name)

        # Run the full pipeline
        raw_results = run_pipeline(
            company_name=company_name,
            company_data=company_data,
            output_dir=os.path.join(PROJECT_ROOT, "data", "processed"),
            ceo_audio_path=ceo_audio_path,
            ceo_transcript=ceo_transcript or None,
            pdf_paths=saved_pdf_paths or None,
            qualitative_notes=qualitative_notes or None,
        )

        # Adapt to dashboard format
        data = _adapt_pipeline_results(raw_results)
        analysis_id = str(uuid.uuid4())[:8]
        _store[analysis_id] = data
        _persist_analysis(analysis_id, data)

        return {"analysis_id": analysis_id, "data": data}

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Retrieve a previously computed analysis."""
    if analysis_id not in _store:
        raise HTTPException(404, "Analysis not found")
    return {"data": _store[analysis_id]}


@app.get("/api/cam/{analysis_id}")
async def download_cam(analysis_id: str):
    """Download the generated CAM DOCX for an analysis."""
    if analysis_id not in _store:
        raise HTTPException(404, "Analysis not found")
    cam_path = _store[analysis_id].get("cam_path")
    if not cam_path or not os.path.exists(cam_path):
        raise HTTPException(404, "CAM document not generated")
    return FileResponse(
        cam_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(cam_path),
    )
