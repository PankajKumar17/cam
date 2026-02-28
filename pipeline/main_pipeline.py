"""
Intelli-Credit — Main Pipeline
================================
Connects all three person's modules into one end-to-end flow.
Run this to process a borrower application from start to finish.
"""

import pandas as pd
from dotenv import load_dotenv
load_dotenv()


def run_pipeline(company_name: str, data_path: str = None):
    """
    Full end-to-end pipeline for one borrower company.
    Returns a complete credit decision with CAM.
    """

    print(f"\n{'='*60}")
    print(f"INTELLI-CREDIT PIPELINE")
    print(f"Company: {company_name}")
    print(f"{'='*60}")

    results = {}

    # ── PERSON 1: ML CORE ─────────────────────────────────────────────────
    print("\n[LAYER 1] Financial Forensics...")
    # from modules.person1_ml_core.forensics import run_forensics
    # results["forensics"] = run_forensics(company_name, data_path)

    print("[LAYER 2] ML Credit Scoring...")
    # from modules.person1_ml_core.credit_scorer import run_scoring
    # results["scoring"] = run_scoring(company_name, data_path)

    # ── PERSON 2: ALTERNATIVE DATA ────────────────────────────────────────
    print("[LAYER 3] Network Risk...")
    # from modules.person2_alt_data.network_graph import run_network_analysis
    # results["network"] = run_network_analysis(company_name)

    print("[LAYER 4] Satellite + GST...")
    # from modules.person2_alt_data.satellite_module import run_satellite
    # results["satellite"] = run_satellite(company_name)

    print("[LAYER 5] Stress Testing...")
    # from modules.person2_alt_data.stress_test import run_stress_test
    # results["stress"] = run_stress_test(company_name, results["scoring"])

    # ── PERSON 3: LLM + CAM ───────────────────────────────────────────────
    print("[LAYER 6] Research Agent...")
    # from modules.person3_llm_cam.research_agent import run_research
    # results["research"] = run_research(company_name)

    print("[LAYER 7] Adversarial CAM Generation...")
    # from modules.person3_llm_cam.cam_generator import generate_cam
    # results["cam"] = generate_cam(company_name, results)

    print(f"\n✅ Pipeline complete for {company_name}")
    return results


if __name__ == "__main__":
    run_pipeline("Sunrise Textile Mills", "data/synthetic/demo_sunrise_textile.csv")
