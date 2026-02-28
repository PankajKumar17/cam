"""
Intelli-Credit — GST Filing Intelligence Module (Person 2)
===========================================================
GST data is filed to the government — harder to fake than a P&L.
We compare GST-declared revenue vs bank-declared revenue to detect
revenue inflation fraud.

Features:
  - Synthetic GST data generator (healthy vs distressed companies)
  - GST vs Bank revenue divergence analysis
  - Filing delay scoring (last 12 months)
  - E-way bill consistency check
  - Fraud risk classification (HIGH / MEDIUM / LOW)

Author: Person 2
Module: modules/person2_alt_data/gst_intelligence.py
"""

import os
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd

from loguru import logger


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

RANDOM_SEED = 42

# GST filing months (last 12)
GST_RETURN_TYPES = ["GSTR-1", "GSTR-3B"]

# Divergence thresholds
DIVERGENCE_HIGH   = 0.40   # > 40% = HIGH fraud risk
DIVERGENCE_MEDIUM = 0.20   # 20-40% = MEDIUM
# < 20% = LOW

# Filing delay thresholds (days)
FILING_DELAY_HIGH   = 30   # > 30 days avg = HIGH risk
FILING_DELAY_MEDIUM = 15   # 15-30 = MEDIUM

# ── Demo companies ──────────────────────────────────────────────────────
DEMO_COMPANIES: Dict[str, Dict[str, Any]] = {
    "Sunrise Textile Mills": {
        "gstin": "27AABCU9603R1ZX",
        "bank_revenue_cr": 1250.0,
        "health": "good",       # GST revenue ≈ bank revenue
        "sector": "Textiles",
        "filing_discipline": "good",
    },
    "TechFab Industries": {
        "gstin": "27AAHCT4568P1Z2",
        "bank_revenue_cr": 620.0,
        "health": "good",
        "sector": "Textiles",
        "filing_discipline": "good",
    },
    "Gujarat Spinners Ltd": {
        "gstin": "24AAECG7834M1ZP",
        "bank_revenue_cr": 85.0,
        "health": "distressed",  # GST revenue << bank revenue
        "sector": "Textiles",
        "filing_discipline": "poor",
    },
    "Kumar Holdings Pvt Ltd": {
        "gstin": "27AABCK1234R1Z5",
        "bank_revenue_cr": 50.0,
        "health": "distressed",
        "sector": "Financial Services",
        "filing_discipline": "poor",
    },
    "Sunrise Exports Ltd": {
        "gstin": "27AABCS5678R1Z8",
        "bank_revenue_cr": 180.0,
        "health": "moderate",
        "sector": "Textiles",
        "filing_discipline": "moderate",
    },
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SYNTHETIC GST DATA GENERATOR                                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _generate_gstin(company_name: str) -> str:
    """Generate a deterministic fake GSTIN from company name."""
    h = hashlib.md5(company_name.encode()).hexdigest().upper()
    state_code = random.choice(["27", "24", "29", "33", "09", "07", "06"])
    return f"{state_code}{h[:5]}{h[5:9]}R1Z{h[9]}"


def generate_gst_filings(
    company_name: str,
    bank_revenue_cr: float,
    health: str = "good",
    filing_discipline: str = "good",
    n_months: int = 12,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate synthetic monthly GST filing data for a company.

    For healthy companies:
      Monthly GST revenue ≈ bank revenue / 12 (within ±5%)

    For distressed companies:
      Monthly GST revenue = bank revenue / 12 × random(0.55, 0.85)
      This simulates companies inflating revenue reported to banks
      while filing lower (actual) revenue with GST authorities.

    Args:
        company_name:      Company name
        bank_revenue_cr:   Annual revenue reported to bank (₹ Cr)
        health:            "good" | "moderate" | "distressed"
        filing_discipline: "good" | "moderate" | "poor"
        n_months:          Number of months of GST data (default 12)
        seed:              Random seed

    Returns:
        DataFrame with monthly GST filing records:
          month, return_type, bank_monthly_rev, gst_declared_rev,
          filing_due_date, filing_actual_date, delay_days,
          ewaybill_value, ewaybill_count
    """
    rng = np.random.default_rng(seed + hash(company_name) % 10000)
    random.seed(seed + hash(company_name) % 10000)

    monthly_bank_rev = bank_revenue_cr / 12.0

    records = []
    today = datetime.now()

    for m in range(n_months):
        month_date = today - timedelta(days=30 * (n_months - m))
        month_str = month_date.strftime("%Y-%m")

        # ── GST declared revenue ────────────────────────────────────
        if health == "good":
            # Within ±5% of bank revenue
            gst_factor = rng.uniform(0.95, 1.05)
        elif health == "moderate":
            # 10-20% lower than bank revenue
            gst_factor = rng.uniform(0.80, 0.92)
        else:  # distressed
            # 15-45% lower — significant inflation to banks
            gst_factor = rng.uniform(0.55, 0.85)

        gst_rev = monthly_bank_rev * gst_factor

        # ── Filing delay ────────────────────────────────────────────
        # Due date: 20th of next month for GSTR-3B
        due_date = (month_date.replace(day=1) + timedelta(days=50)).replace(day=20)

        if filing_discipline == "good":
            delay = max(0, int(rng.normal(2, 3)))     # 0-5 days
        elif filing_discipline == "moderate":
            delay = max(0, int(rng.normal(12, 8)))     # 5-20 days
        else:  # poor
            delay = max(0, int(rng.normal(35, 15)))    # 20-50+ days

        actual_date = due_date + timedelta(days=delay)

        # ── E-way bill data ─────────────────────────────────────────
        # E-way bill value should track GST revenue for manufacturers
        if health == "good":
            ewb_factor = rng.uniform(0.90, 1.10)
        elif health == "moderate":
            ewb_factor = rng.uniform(0.75, 0.95)
        else:
            ewb_factor = rng.uniform(0.50, 0.80)

        ewaybill_value = gst_rev * ewb_factor
        # ~20-40 e-way bills per crore for manufacturing
        ewaybill_count = max(1, int(ewaybill_value * rng.uniform(20, 40)))

        for return_type in GST_RETURN_TYPES:
            records.append({
                "month": month_str,
                "return_type": return_type,
                "bank_monthly_rev_cr": round(monthly_bank_rev, 4),
                "gst_declared_rev_cr": round(gst_rev, 4),
                "filing_due_date": due_date.strftime("%Y-%m-%d"),
                "filing_actual_date": actual_date.strftime("%Y-%m-%d"),
                "delay_days": delay,
                "ewaybill_value_cr": round(ewaybill_value, 4),
                "ewaybill_count": ewaybill_count,
            })

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} GST filing records for {company_name}")
    return df


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  GST ANALYSIS ENGINE                                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _compute_divergence(
    bank_revenue_cr: float,
    gst_revenue_cr: float,
) -> Tuple[float, int]:
    """
    Compute GST vs bank revenue divergence.

    divergence = (bank_revenue - gst_revenue) / gst_revenue

    A positive divergence means bank-declared revenue exceeds GST-declared
    revenue — the borrower may be inflating revenue to secure larger loans.

    Returns:
        (divergence_ratio, flag)
        flag = 1 if divergence > 20%
    """
    if gst_revenue_cr <= 0:
        return (0.0, 0)
    divergence = (bank_revenue_cr - gst_revenue_cr) / gst_revenue_cr
    flag = 1 if divergence > DIVERGENCE_MEDIUM else 0
    return (round(divergence, 4), flag)


def _compute_filing_delay_score(filings_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute average filing delay across last 12 months of GST filings.

    Args:
        filings_df: DataFrame from generate_gst_filings()

    Returns:
        Dict with delay metrics
    """
    # Use GSTR-3B filings only (more relevant for revenue matching)
    gstr3b = filings_df[filings_df["return_type"] == "GSTR-3B"]
    delays = gstr3b["delay_days"].values

    avg_delay = float(np.mean(delays)) if len(delays) > 0 else 0.0
    max_delay = float(np.max(delays)) if len(delays) > 0 else 0.0
    on_time_pct = float(np.mean(delays <= 5)) * 100 if len(delays) > 0 else 100.0
    late_count = int(np.sum(delays > 15))

    # Score: 100 = perfect, 0 = terrible
    # Deduct 3 points per average day of delay, capped at 0
    delay_score = max(0.0, 100.0 - avg_delay * 3.0)

    # Risk level
    if avg_delay > FILING_DELAY_HIGH:
        delay_risk = "HIGH"
    elif avg_delay > FILING_DELAY_MEDIUM:
        delay_risk = "MEDIUM"
    else:
        delay_risk = "LOW"

    return {
        "avg_filing_delay_days": round(avg_delay, 1),
        "max_filing_delay_days": round(max_delay, 1),
        "on_time_filing_pct": round(on_time_pct, 1),
        "late_filing_count": late_count,
        "filing_delay_score": round(delay_score, 2),
        "filing_delay_risk": delay_risk,
    }


def _compute_ewaybill_consistency(filings_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if e-way bill implied revenue is consistent with GST declared revenue.

    For manufacturers, goods movement (e-way bills) should closely track
    the GST-declared revenue. A large gap means either under-reporting
    shipments or over-reporting revenue.

    ewaybill_consistency = ewaybill_implied_revenue / gst_declared_revenue

    Returns:
        Dict with e-way bill consistency metrics
    """
    gstr3b = filings_df[filings_df["return_type"] == "GSTR-3B"]

    total_gst_rev = gstr3b["gst_declared_rev_cr"].sum()
    total_ewb_value = gstr3b["ewaybill_value_cr"].sum()
    total_ewb_count = int(gstr3b["ewaybill_count"].sum())

    if total_gst_rev > 0:
        consistency_ratio = total_ewb_value / total_gst_rev
    else:
        consistency_ratio = 1.0

    # Flag if e-way bill value diverges > 25% from GST revenue
    ewb_flag = 1 if abs(consistency_ratio - 1.0) > 0.25 else 0

    return {
        "total_ewaybill_value_cr": round(total_ewb_value, 2),
        "total_ewaybill_count": total_ewb_count,
        "ewaybill_consistency_ratio": round(consistency_ratio, 4),
        "ewaybill_divergence_flag": ewb_flag,
    }


def _classify_fraud_risk(divergence: float) -> str:
    """
    Classify fraud risk based on GST vs bank divergence.

    HIGH:   divergence > 40%
    MEDIUM: divergence 20-40%
    LOW:    divergence < 20%
    """
    if divergence > DIVERGENCE_HIGH:
        return "HIGH"
    elif divergence > DIVERGENCE_MEDIUM:
        return "MEDIUM"
    else:
        return "LOW"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HIGH-LEVEL ENTRY POINT                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def analyze_gst_data(
    company_name: str = "Sunrise Textile Mills",
    bank_revenue_cr: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Complete GST intelligence analysis for a borrower company.

    Pipeline:
      1. Generate / retrieve synthetic GST filing data
      2. Compute GST vs bank revenue divergence
      3. Score filing discipline (delay analysis)
      4. Check e-way bill consistency
      5. Classify overall fraud risk

    Args:
        company_name:    Name of the borrower company
        bank_revenue_cr: Annual revenue reported to bank (₹ Cr).
                         If None, uses demo company data.

    Returns:
        Comprehensive analysis dict:
        {
            "company_name":               str,
            "gstin":                      str,
            "bank_revenue_cr":            float,
            "gst_annual_revenue_cr":      float,
            "gst_vs_bank_divergence":     float,
            "gst_divergence_flag":        0 | 1,
            "fraud_risk_level":           "HIGH" | "MEDIUM" | "LOW",
            # Filing discipline
            "avg_filing_delay_days":      float,
            "max_filing_delay_days":      float,
            "on_time_filing_pct":         float,
            "filing_delay_score":         float (0-100),
            "filing_delay_risk":          str,
            # E-way bill
            "ewaybill_consistency_ratio": float,
            "ewaybill_divergence_flag":   0 | 1,
            # Monthly detail
            "monthly_filings":            pd.DataFrame,
            # Composite GST health
            "gst_health_score":           float (0-100),
        }
    """
    logger.info(f"{'='*60}")
    logger.info(f"GST INTELLIGENCE ANALYSIS — {company_name}")
    logger.info(f"{'='*60}")

    # ── Resolve company data ─────────────────────────────────────────────
    demo = DEMO_COMPANIES.get(company_name)
    if demo:
        gstin = demo["gstin"]
        if bank_revenue_cr is None:
            bank_revenue_cr = demo["bank_revenue_cr"]
        health = demo["health"]
        filing_discipline = demo["filing_discipline"]
        sector = demo["sector"]
    else:
        gstin = _generate_gstin(company_name)
        if bank_revenue_cr is None:
            bank_revenue_cr = 500.0   # Default
        health = "good"               # Assume good if unknown
        filing_discipline = "good"
        sector = "Unknown"

    logger.info(f"GSTIN: {gstin} | Bank Revenue: ₹{bank_revenue_cr:.1f} Cr")

    # ── Step 1: Generate GST filings ─────────────────────────────────────
    filings_df = generate_gst_filings(
        company_name, bank_revenue_cr, health, filing_discipline,
    )

    # ── Step 2: Revenue divergence ───────────────────────────────────────
    # Annualize GST revenue from monthly filings
    gstr3b = filings_df[filings_df["return_type"] == "GSTR-3B"]
    gst_annual_rev = gstr3b["gst_declared_rev_cr"].sum()

    divergence, div_flag = _compute_divergence(bank_revenue_cr, gst_annual_rev)
    fraud_risk = _classify_fraud_risk(divergence)

    logger.info(f"GST Annual Revenue: ₹{gst_annual_rev:.2f} Cr")
    logger.info(f"Divergence: {divergence:.2%} | Flag: {div_flag} | Risk: {fraud_risk}")

    # ── Step 3: Filing delay analysis ────────────────────────────────────
    delay_metrics = _compute_filing_delay_score(filings_df)
    logger.info(f"Avg Filing Delay: {delay_metrics['avg_filing_delay_days']:.1f} days "
                f"| Risk: {delay_metrics['filing_delay_risk']}")

    # ── Step 4: E-way bill consistency ───────────────────────────────────
    ewb_metrics = _compute_ewaybill_consistency(filings_df)
    logger.info(f"E-way Bill Consistency: {ewb_metrics['ewaybill_consistency_ratio']:.4f} "
                f"| Flag: {ewb_metrics['ewaybill_divergence_flag']}")

    # ── Step 5: Composite GST health score ───────────────────────────────
    # Weighted combination: divergence (40%) + filing discipline (30%) + ewb (30%)
    div_score = max(0, 100 - abs(divergence) * 200)   # 0% div → 100, 50% → 0
    ewb_score = max(0, 100 - abs(ewb_metrics["ewaybill_consistency_ratio"] - 1.0) * 200)
    gst_health_score = round(
        0.40 * div_score +
        0.30 * delay_metrics["filing_delay_score"] +
        0.30 * ewb_score,
        2,
    )
    gst_health_score = min(100.0, max(0.0, gst_health_score))

    # ── Assemble result ──────────────────────────────────────────────────
    result = {
        "company_name":               company_name,
        "gstin":                      gstin,
        "sector":                     sector,
        "bank_revenue_cr":            bank_revenue_cr,
        "gst_annual_revenue_cr":      round(gst_annual_rev, 2),
        "gst_vs_bank_divergence":     divergence,
        "gst_divergence_flag":        div_flag,
        "fraud_risk_level":           fraud_risk,
    }
    result.update(delay_metrics)
    result.update(ewb_metrics)
    result["monthly_filings"] = filings_df
    result["gst_health_score"] = gst_health_score

    logger.info(f"{'='*60}")
    logger.info(f"GST ANALYSIS COMPLETE — {company_name}")
    logger.info(f"  Divergence:     {divergence:.2%} → {fraud_risk}")
    logger.info(f"  Filing Score:   {delay_metrics['filing_delay_score']:.1f}/100")
    logger.info(f"  EWB Ratio:      {ewb_metrics['ewaybill_consistency_ratio']:.4f}")
    logger.info(f"  GST Health:     {gst_health_score:.2f}/100")
    logger.info(f"{'='*60}")

    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GST INTELLIGENCE — Standalone Test")
    print("=" * 60)

    # ── Test 1: Healthy company ──────────────────────────────────────────
    print("\n[1] Sunrise Textile Mills (expected: LOW fraud risk)")
    r1 = analyze_gst_data("Sunrise Textile Mills")
    print(f"   Bank Revenue:  ₹{r1['bank_revenue_cr']:.1f} Cr")
    print(f"   GST Revenue:   ₹{r1['gst_annual_revenue_cr']:.1f} Cr")
    print(f"   Divergence:    {r1['gst_vs_bank_divergence']:.2%}")
    print(f"   Fraud Risk:    {r1['fraud_risk_level']}")
    print(f"   Filing Delay:  {r1['avg_filing_delay_days']:.1f} days")
    print(f"   EWB Ratio:     {r1['ewaybill_consistency_ratio']:.4f}")
    print(f"   GST Health:    {r1['gst_health_score']:.2f}/100")

    # ── Test 2: Distressed company ───────────────────────────────────────
    print("\n[2] Gujarat Spinners Ltd (expected: HIGH fraud risk)")
    r2 = analyze_gst_data("Gujarat Spinners Ltd")
    print(f"   Bank Revenue:  ₹{r2['bank_revenue_cr']:.1f} Cr")
    print(f"   GST Revenue:   ₹{r2['gst_annual_revenue_cr']:.1f} Cr")
    print(f"   Divergence:    {r2['gst_vs_bank_divergence']:.2%}")
    print(f"   Fraud Risk:    {r2['fraud_risk_level']}")
    print(f"   Filing Delay:  {r2['avg_filing_delay_days']:.1f} days")
    print(f"   GST Health:    {r2['gst_health_score']:.2f}/100")

    # ── Test 3: Unknown company ──────────────────────────────────────────
    print("\n[3] Random Corp (unknown company, default healthy)")
    r3 = analyze_gst_data("Random Corp", bank_revenue_cr=300.0)
    print(f"   Divergence:    {r3['gst_vs_bank_divergence']:.2%}")
    print(f"   Fraud Risk:    {r3['fraud_risk_level']}")
    print(f"   GST Health:    {r3['gst_health_score']:.2f}/100")

    print("\n" + "=" * 60)
    print("✅ GST intelligence test complete!")
    print("=" * 60)
