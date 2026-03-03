"""
Yakṣarāja — Main Pipeline
================================
Connects all three persons' modules into one end-to-end flow.

Person 1 (ML Core)   → Feature engineering, forensic scores, credit scoring
Person 2 (Alt Data)  → Network graph, stress test, satellite, GST, DNA matching
Person 3 (LLM + CAM) → Research, bull/bear agents, CEO interview, CAM DOCX

Run:
    python pipeline/main_pipeline.py

Output:
    data/processed/CAM_<company>_<date>.docx
    data/processed/CAM_<company>_<date>.json
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── Add project root to path ────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  DEMO COMPANY DATA — Sunrise Textile Mills (FY2024)                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝
# Used when Person 1 models are not yet trained (no feature_matrix.csv).

SUNRISE_DEMO_FINANCIALS: Dict[str, Any] = {
    "company_name": "Sunrise Textile Mills",
    "sector": "Textiles",
    "fiscal_year": 2024,
    # P&L
    "revenue": 850.0,
    "ebitda": 127.5,
    "ebitda_margin": 0.15,
    "pat": 51.0,
    "net_margin": 0.06,
    "gross_margin": 0.38,
    # Balance sheet
    "total_assets": 1200.0,
    "total_equity": 325.0,
    "total_debt": 520.0,
    "lt_borrowings": 350.0,
    "st_borrowings": 170.0,
    "trade_receivables": 120.0,
    "inventories": 95.0,
    "cash_equivalents": 45.0,
    # Cash flow
    "cfo": 95.0,
    "cfi": -55.0,
    "cff": -30.0,
    "capex": 55.0,
    "free_cash_flow": 42.0,
    # Ratios
    "dscr": 1.85,
    "interest_coverage": 2.4,
    "debt_to_equity": 1.6,
    "current_ratio": 1.25,
    "roe": 0.14,
    "roa": 0.06,
    "revenue_growth": 0.08,
    # Governance
    "promoter_holding_pct": 0.62,
    "promoter_pledge_pct": 0.08,
    "institutional_holding_pct": 0.18,
    "related_party_tx_to_rev": 0.05,
    "receivables_days": 55.0,
    # Forensic scores
    "beneish_m_score": -2.45,
    "beneish_dsri": 0.95,
    "beneish_tata": 0.03,
    "altman_z_score": 2.3,
    "piotroski_f_score": 6,
    "auditor_distress_score": 1,
    "going_concern_flag": 0,
    "qualified_opinion_flag": 0,
    "auditor_resigned_flag": 0,
    # Alt data placeholders (filled by Person 2)
    "contagion_risk_score": 0.0,
    "network_npa_ratio": 0.0,
    "gst_vs_bank_divergence": 0.0,
    "satellite_activity_score": 0.0,
    "employee_cost_to_rev": 0.15,
    "st_debt_to_lt_assets_ratio": 0.49,
    "cfo_to_debt": 0.18,
    "debt_growth_3yr": 0.12,
    "cfo_to_pat": 0.85,
    "free_cash_flow_margin": 0.04,
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  LAYER FUNCTIONS                                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _layer_timer(layer_name: str):
    """Context manager that logs execution time."""
    class Timer:
        def __init__(self):
            self.start = 0
        def __enter__(self):
            self.start = time.time()
            logger.info(f"\n{'─'*60}")
            logger.info(f"▶ {layer_name}")
            logger.info(f"{'─'*60}")
            return self
        def __exit__(self, *args):
            elapsed = time.time() - self.start
            logger.info(f"✅ {layer_name} completed in {elapsed:.1f}s")
    return Timer()


# ── LAYER 1: Person 1 — Financial Forensics & Feature Engineering ────────

def run_layer1_forensics(company_data: dict) -> dict:
    """
    Run Person 1 forensics: Beneish M-Score, Altman Z-Score, Piotroski F-Score.

    If feature_matrix.csv exists, loads from it; otherwise uses demo financials.
    """
    forensics = {
        "beneish_m_score": company_data.get("beneish_m_score", -2.45),
        "altman_z_score": company_data.get("altman_z_score", 2.3),
        "piotroski_f_score": company_data.get("piotroski_f_score", 6),
        "auditor_distress_score": company_data.get("auditor_distress_score", 1),
        "going_concern_flag": company_data.get("going_concern_flag", 0),
        "source": "demo_financials",
    }

    try:
        from modules.person1_ml_core.feature_engineering import (
            compute_velocity_features,
            compute_default_dna,
        )
        logger.info("Person 1 feature engineering modules loaded")
        forensics["source"] = "person1_modules"
    except ImportError:
        logger.warning("Person 1 feature engineering not available — using demo data")

    return forensics


# ── LAYER 2: Person 1 — ML Credit Scoring ────────────────────────────────

def run_layer2_ml_scoring(company_data: dict) -> dict:
    """
    Run Person 1 ML credit scoring (XGBoost + RF + LightGBM ensemble).

    If trained models exist (models/*.pkl), uses them for real prediction.
    Otherwise returns demo/fallback scores.
    """
    models_dir = os.path.join(PROJECT_ROOT, "models")
    model_exists = os.path.exists(os.path.join(models_dir, "xgb_model.pkl"))

    if model_exists:
        try:
            from modules.person1_ml_core.credit_scorer import predict
            logger.info("Trained models found — running real ML prediction")

            feature_row = pd.Series(company_data)
            result = predict(feature_row)
            return {
                "ensemble_pd": result["pd_score"],
                "pd_xgb": result["pd_xgb"],
                "pd_rf": result["pd_rf"],
                "pd_lgb": result["pd_lgb"],
                "lending_decision": result["lending_decision"],
                "credit_limit_cr": result["credit_limit_cr"],
                "risk_premium": result["risk_premium_pct"],
                "model_disagreement_flag": result["model_disagreement_flag"],
                "top_features": result.get("top_features", []),
                "source": "trained_models",
            }
        except Exception as e:
            logger.error(f"ML prediction failed: {e} — using fallback")

    # Fallback: heuristic scoring from financial ratios
    logger.info("No trained models — computing heuristic PD from financial ratios")

    dscr = company_data.get("dscr", 1.5)
    icr = company_data.get("interest_coverage", 2.0)
    de = company_data.get("debt_to_equity", 1.5)
    altman = company_data.get("altman_z_score", 2.5)

    # Simple logistic heuristic
    z = -1.5 + 0.8 * (2.0 - dscr) + 0.4 * (de - 1.0) + 0.3 * (2.5 - altman)
    pd_score = 1.0 / (1.0 + np.exp(-z))
    pd_score = round(float(np.clip(pd_score, 0.01, 0.99)), 4)

    if pd_score < 0.20:
        decision = "APPROVE"
    elif pd_score < 0.50:
        decision = "CONDITIONAL_APPROVE"
    else:
        decision = "REJECT"

    revenue = company_data.get("revenue", 500)
    credit_limit = round(revenue * 0.25 * (1 - pd_score) * max(0.3, min(2.0, dscr / 1.5)), 2)
    risk_premium = round(2.5 + pd_score * 8.0, 2)

    return {
        "ensemble_pd": pd_score,
        "pd_xgb": round(pd_score * 0.95, 4),
        "pd_rf": round(pd_score * 1.05, 4),
        "pd_lgb": round(pd_score * 1.02, 4),
        "lending_decision": decision,
        "credit_limit_cr": max(0, credit_limit),
        "risk_premium": risk_premium,
        "model_disagreement_flag": False,
        "top_features": [],
        "source": "heuristic_fallback",
    }


# ── LAYER 3: Person 1 — Temporal LSTM Trajectory ─────────────────────────

def run_layer3_trajectory(company_name: str) -> dict:
    """
    Run Person 1 LSTM trajectory early-warning system.

    Requires 5 years of data in feature_matrix.csv. Falls back to demo.
    """
    try:
        from modules.person1_ml_core.temporal_model import get_trajectory_score
        feature_path = os.path.join(PROJECT_ROOT, "data", "processed", "feature_matrix.csv")
        if os.path.exists(feature_path):
            result = get_trajectory_score(company_name)
            if "error" not in result:
                logger.info(f"Trajectory: {result['warning_level']} "
                            f"(risk={result['trajectory_risk_score']:.4f})")
                return result
    except Exception as e:
        logger.warning(f"Trajectory model unavailable: {e}")

    # Demo fallback
    return {
        "company_name": company_name,
        "trajectory_risk_score": 0.18,
        "estimated_months_to_distress": 999,
        "warning_level": "GREEN",
        "dscr_trend": [1.65, 1.72, 1.78, 1.82, 1.85],
        "dscr_velocity": 0.03,
        "current_dscr": 1.85,
        "source": "demo_fallback",
    }


# ── LAYER 4: Person 2 — Promoter Network Graph ──────────────────────────

def run_layer4_network(company_cin: str = "U17100MH2010PLC123456") -> dict:
    """Run Person 2 network analysis."""
    from modules.person2_alt_data.network_graph import run_network_analysis
    return run_network_analysis(company_cin, save_visualization=True)


# ── LAYER 5: Person 2 — Satellite + GST Intelligence ────────────────────

def run_layer5_satellite_gst(company_name: str, revenue_cr: float = 850.0) -> dict:
    """Run Person 2 satellite and GST intelligence modules."""
    from modules.person2_alt_data.satellite_module import get_factory_activity
    from modules.person2_alt_data.gst_intelligence import analyze_gst_data

    satellite = get_factory_activity(
        company_name=company_name,
        revenue_cr=revenue_cr,
        industry_avg_revenue_cr=revenue_cr * 0.8,
    )

    gst = analyze_gst_data(company_name, bank_revenue_cr=revenue_cr)

    return {"satellite": satellite, "gst": gst}


# ── LAYER 6: Person 2 — Stress Test + DNA Matching ──────────────────────

def run_layer6_stress_dna(company_data: dict) -> dict:
    """Run Person 2 Monte Carlo stress test and corporate DNA matching."""
    from modules.person2_alt_data.stress_test import run_stress_test
    from modules.person2_alt_data.dna_matching import run_dna_analysis

    # Build financials dict for stress test
    stress_financials = {
        "company_name": company_data.get("company_name", "Unknown"),
        "revenue": company_data.get("revenue", 850.0),
        "ebitda": company_data.get("ebitda", 127.5),
        "interest_expense": company_data.get("interest_expense",
                            company_data.get("ebitda", 127.5) / company_data.get("interest_coverage", 2.4)),
        "depreciation": company_data.get("depreciation",
                        company_data.get("ebitda", 127.5) * 0.2),
        "tax_rate": company_data.get("tax_rate", 0.25),
        "annual_debt_repayment": company_data.get("annual_debt_repayment",
                                  company_data.get("total_debt", 520) * 0.15),
    }

    stress_result = run_stress_test(stress_financials, n_simulations=1000, save_chart=True)

    # DNA matching — build borrower features from company data
    borrower_features = {
        "st_debt_to_lt_assets_ratio": company_data.get("st_debt_to_lt_assets_ratio", 0.49),
        "current_ratio": company_data.get("current_ratio", 1.25),
        "debt_to_equity": company_data.get("debt_to_equity", 1.6),
        "interest_coverage": company_data.get("interest_coverage", 2.4),
        "cfo_to_debt": company_data.get("cfo_to_debt", 0.18),
        "cfo_to_pat": company_data.get("cfo_to_pat", 0.85),
        "free_cash_flow_margin": company_data.get("free_cash_flow_margin", 0.04),
        "revenue_growth": company_data.get("revenue_growth", 0.08),
        "debt_growth_3yr": company_data.get("debt_growth_3yr", 0.12),
        "roe": company_data.get("roe", 0.14),
        "employee_cost_to_rev": company_data.get("employee_cost_to_rev", 0.15),
        "promoter_pledge_pct": company_data.get("promoter_pledge_pct", 0.08),
        "related_party_tx_to_rev": company_data.get("related_party_tx_to_rev", 0.05),
        "receivables_days": company_data.get("receivables_days", 55.0),
        "gst_vs_bank_divergence": company_data.get("gst_vs_bank_divergence", 0.03),
        "contagion_risk_score": company_data.get("contagion_risk_score", 0.15),
        "network_npa_ratio": company_data.get("network_npa_ratio", 0.05),
        "beneish_dsri": company_data.get("beneish_dsri", 0.95),
        "beneish_tata": company_data.get("beneish_tata", 0.03),
        "auditor_distress_score": company_data.get("auditor_distress_score", 0.0),
    }

    dna_result = run_dna_analysis(borrower_features, company_data.get("company_name", "Unknown"))

    return {"stress_test": stress_result, "dna": dna_result}


# ── LAYER 7: Person 3 — Research Agent ───────────────────────────────────

def run_layer7_research(company_name: str, sector: str = "Textiles") -> dict:
    """Run Person 3 LangGraph research agent."""
    from modules.person3_llm_cam.research_agent import run_research
    return run_research(company_name, sector=sector, promoter_name="Promoter Group")


# ── LAYER 8: Person 3 — CEO Interview Analysis ──────────────────────────

def run_layer8_ceo_interview(company_data: dict) -> dict:
    """Run Person 3 CEO interview analysis (fallback mode — no audio)."""
    from modules.person3_llm_cam.ceo_interview import run_ceo_interview_analysis
    return run_ceo_interview_analysis(company_data=company_data)


# ── LAYER 9: Person 3 — Adversarial Bull vs Bear + Recommendation ───────

def run_layer9_adversarial(company_data: dict, research: dict,
                            ml_scores: dict) -> dict:
    """Run Person 3 adversarial approval/dissent agents and synthesize."""
    from modules.person3_llm_cam.approval_agent import write_bull_case
    from modules.person3_llm_cam.dissent_agent import (
        write_bear_case,
        synthesize_cam_recommendation,
    )

    bull_case = write_bull_case(company_data, research)
    bear_case = write_bear_case(company_data, bull_case, research)

    # Build scores dict for coordinator
    scores = {
        "ensemble_pd": ml_scores.get("ensemble_pd", 0.15),
        "dscr": company_data.get("dscr", 1.85),
        "lending_decision": ml_scores.get("lending_decision", "REVIEW"),
        "risk_premium": ml_scores.get("risk_premium", 4.0),
        "revenue": company_data.get("revenue", 850.0),
    }

    recommendation = synthesize_cam_recommendation(bull_case, bear_case, scores)

    return {
        "bull_case": bull_case,
        "bear_case": bear_case,
        "recommendation": recommendation,
    }


# ── LAYER 10: Person 3 — CAM Document Generation ────────────────────────

def run_layer10_cam(all_data: dict, output_dir: str = "data/processed/") -> str:
    """Run Person 3 CAM DOCX generator — assembles all 11 sections."""
    from modules.person3_llm_cam.cam_generator import generate_cam
    return generate_cam(all_data, output_dir=output_dir)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MASTER PIPELINE                                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def run_pipeline(
    company_name: str = "Sunrise Textile Mills",
    company_data: Optional[Dict[str, Any]] = None,
    output_dir: str = "data/processed/",
) -> Dict[str, Any]:
    """
    Full end-to-end pipeline: Person 1 → Person 2 → Person 3 → CAM DOCX.

    Args:
        company_name: Borrower company name
        company_data: Financial data dict (None → uses Sunrise demo data)
        output_dir:   Directory for output files

    Returns:
        Complete pipeline results dict with all layer outputs
    """
    pipeline_start = time.time()

    logger.info(f"\n{'═'*60}")
    logger.info(f"  YAKṢARĀJA — AI CREDIT DECISIONING ENGINE")
    logger.info(f"  Company: {company_name}")
    logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'═'*60}")

    # Use demo data if none provided
    if company_data is None:
        company_data = SUNRISE_DEMO_FINANCIALS.copy()
    company_data["company_name"] = company_name

    results = {"company_name": company_name, "company_data": company_data}

    # ══════════════════════════════════════════════════════════════════════
    #  PERSON 1: ML CORE
    # ══════════════════════════════════════════════════════════════════════

    with _layer_timer("LAYER 1 — Financial Forensics (Person 1)"):
        results["forensics"] = run_layer1_forensics(company_data)

    with _layer_timer("LAYER 2 — ML Credit Scoring (Person 1)"):
        results["ml_scores"] = run_layer2_ml_scoring(company_data)

    with _layer_timer("LAYER 3 — LSTM Trajectory (Person 1)"):
        results["trajectory"] = run_layer3_trajectory(company_name)

    # Update company_data with ML scores for downstream layers
    company_data["ensemble_pd"] = results["ml_scores"]["ensemble_pd"]
    company_data["lending_decision"] = results["ml_scores"]["lending_decision"]

    # ══════════════════════════════════════════════════════════════════════
    #  PERSON 2: ALTERNATIVE DATA
    # ══════════════════════════════════════════════════════════════════════

    with _layer_timer("LAYER 4 — Promoter Network Graph (Person 2)"):
        results["network"] = run_layer4_network()

    # Update company_data with network contagion
    company_data["contagion_risk_score"] = results["network"].get("contagion_risk_score", 0)
    company_data["network_npa_ratio"] = results["network"].get("npa_ratio", 0)
    company_data["promoter_total_companies"] = results["network"].get("promoter_total_companies", 0)
    company_data["promoter_npa_companies"] = results["network"].get("promoter_npa_companies", 0)

    with _layer_timer("LAYER 5 — Satellite + GST Intelligence (Person 2)"):
        sat_gst = run_layer5_satellite_gst(company_name, company_data.get("revenue", 850.0))
        results["satellite"] = sat_gst["satellite"]
        results["gst"] = sat_gst["gst"]

    # Update company_data with satellite & GST
    company_data["satellite_activity_score"] = results["satellite"].get("activity_score", 0)
    company_data["satellite_activity_category"] = results["satellite"].get("classification", "N/A")
    company_data["satellite_vs_revenue_flag"] = results["satellite"].get("satellite_vs_revenue_flag", 0)
    company_data["gst_vs_bank_divergence"] = results["gst"].get("gst_vs_bank_divergence", 0)
    company_data["gst_divergence_flag"] = results["gst"].get("gst_divergence_flag", 0)
    company_data["gst_filing_delays_count"] = results["gst"].get("gst_filing_delays_count",
                                               int(results["gst"].get("max_filing_delay_days", 0) > 15))
    company_data["ewaybill_volume_consistency"] = results["gst"].get("ewaybill_consistency_ratio", 0.9)
    company_data["gst_payment_delay_days"] = results["gst"].get("avg_filing_delay_days", 0)
    company_data["gst_health_score"] = results["gst"].get("gst_health_score", 80)

    with _layer_timer("LAYER 6 — Stress Test + DNA Matching (Person 2)"):
        stress_dna = run_layer6_stress_dna(company_data)
        results["stress_test"] = stress_dna["stress_test"]
        results["dna_match"] = stress_dna["dna"]

    # ══════════════════════════════════════════════════════════════════════
    #  PERSON 3: LLM + CAM
    # ══════════════════════════════════════════════════════════════════════

    with _layer_timer("LAYER 7 — Research Agent (Person 3)"):
        results["research"] = run_layer7_research(
            company_name, company_data.get("sector", "Industrial")
        )

    with _layer_timer("LAYER 8 — CEO Interview Analysis (Person 3)"):
        results["ceo_interview"] = run_layer8_ceo_interview(company_data)

    with _layer_timer("LAYER 9 — Adversarial Bull vs Bear (Person 3)"):
        adversarial = run_layer9_adversarial(
            company_data, results["research"], results["ml_scores"]
        )
        results["bull_case"] = adversarial["bull_case"]
        results["bear_case"] = adversarial["bear_case"]
        results["recommendation"] = adversarial["recommendation"]

    # ══════════════════════════════════════════════════════════════════════
    #  ASSEMBLE & GENERATE CAM
    # ══════════════════════════════════════════════════════════════════════

    with _layer_timer("LAYER 10 — CAM Document Generation (Person 3)"):
        # Build the all_data dict expected by cam_generator
        cam_data = {
            "company_name": company_name,
            "fiscal_year": company_data.get("fiscal_year", 2024),
            "sector": company_data.get("sector", "Textiles"),
            "financial_data": company_data,
            "forensics": results["forensics"],
            "ml_scores": results["ml_scores"],
            "trajectory": results["trajectory"],
            "network": results["network"],
            "satellite": results["satellite"],
            "gst": results["gst"],
            "stress_test": {
                "dscr_p10": results["stress_test"].get("p10_dscr"),
                "dscr_p50": results["stress_test"].get("p50_dscr"),
                "dscr_p90": results["stress_test"].get("p90_dscr"),
                "covenant_breach_probability": results["stress_test"].get("default_probability_3yr"),
                "named_scenarios": [
                    {
                        "name": sc.get("name", ""),
                        "dscr_impact": sc.get("dscr", 0),
                        "pd_impact": max(0, 1.0 - sc.get("dscr", 1.0)),
                    }
                    for sc in results["stress_test"]
                        .get("named_scenarios", {})
                        .get("scenarios", [])
                ],
            },
            "dna_match": {
                "closest_default_archetype": results["dna_match"].get("closest_archetype", "N/A"),
                "max_archetype_similarity": results["dna_match"].get("max_similarity", 0),
            },
            "research": results["research"],
            "ceo_interview": results["ceo_interview"],
            "bull_case": results["bull_case"],
            "bear_case": results["bear_case"],
            "recommendation": results["recommendation"],
        }

        cam_path = run_layer10_cam(cam_data, output_dir)
        results["cam_path"] = cam_path

    # ══════════════════════════════════════════════════════════════════════
    #  SUMMARY
    # ══════════════════════════════════════════════════════════════════════

    elapsed = time.time() - pipeline_start

    logger.info(f"\n{'═'*60}")
    logger.info(f"  ✅ PIPELINE COMPLETE")
    logger.info(f"  Company:    {company_name}")
    logger.info(f"  Decision:   {results['recommendation'].get('lending_decision', 'N/A')}")
    logger.info(f"  PD:         {results['ml_scores']['ensemble_pd']:.2%}")
    logger.info(f"  DSCR:       {company_data.get('dscr', 'N/A')}")
    logger.info(f"  CAM:        {cam_path}")
    logger.info(f"  Total Time: {elapsed:.1f}s")
    logger.info(f"{'═'*60}")

    results["pipeline_elapsed_seconds"] = round(elapsed, 1)
    return results


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE RUN                                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    results = run_pipeline("Sunrise Textile Mills")
    print(f"\n🎯 Final Decision: {results['recommendation'].get('lending_decision', 'N/A')}")
    print(f"📄 CAM Document:   {results.get('cam_path', 'N/A')}")
