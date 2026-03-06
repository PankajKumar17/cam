"""
Yakṣarāja — Financial Forensics Module (Person 1)
==================================================
Implements three pillars of accounting fraud detection:

  A. Beneish M-Score (1999) — 8-variable manipulation model
     The only model purpose-built to detect earnings manipulation.
     Threshold: score > -2.22 → Manipulator

  B. Altman Z-Score (1968) — Bankruptcy prediction
     Zone: Z > 2.99 = SAFE, 1.81-2.99 = GREY, < 1.81 = DISTRESS

  C. Piotroski F-Score (2000) — Financial strength signal
     9-point scale: 0-2 = Weak, 3-6 = Moderate, 7-9 = Strong

Indian Context Additions:
  D. Auditor Quality Distress Score — Big4/resignation/going concern flags
  E. Related-party transaction intensity score

Author: Person 1
Module: modules/person1_ml_core/forensics.py
"""

import math
from typing import Dict, Any, Optional, Tuple

from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Beneish (1999) — original regression coefficients
BENEISH_INTERCEPT = -4.84

BENEISH_COEFS = {
    "dsri":  0.920,   # Days Sales Receivable Index    (>1.465 = red flag)
    "gmi":   0.528,   # Gross Margin Index             (<1.0   = improving)
    "aqi":   0.404,   # Asset Quality Index             (>1.254 = red flag)
    "sgi":   0.892,   # Sales Growth Index              (>1.607 = red flag)
    "depi":  0.115,   # Depreciation Index              (>1.0   = red flag)
    "sgai": -0.172,   # SGA Expense Index               (>1.054 = red flag, neg coef)
    "tata":  4.679,   # Total Accruals to Total Assets  (>0.031 = red flag)
    "lvgi":  0.127,   # Leverage Index                  (>1.0   = red flag)
}

BENEISH_THRESHOLDS = {
    "dsri":  1.465,
    "gmi":   1.0,     # < means improving (NOT a flag)
    "aqi":   1.254,
    "sgi":   1.607,
    "depi":  1.0,
    "sgai":  1.054,
    "tata":  0.031,
    "lvgi":  1.0,
}

MANIPULATOR_THRESHOLD = -2.22

# Altman (1968) — Manufacturing firms
ALTMAN_WEIGHTS = {
    "x1": 1.2,   # Working Capital / Total Assets
    "x2": 1.4,   # Retained Earnings / Total Assets
    "x3": 3.3,   # EBIT / Total Assets
    "x4": 0.6,   # Market Value of Equity / Book Value of Debt
    "x5": 1.0,   # Sales / Total Assets
}

ALTMAN_SAFE_ZONE = 2.99
ALTMAN_GREY_ZONE = 1.81

# Piotroski (2000) — 9 binary signals
PIOTROSKI_MAX = 9


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _safe(val: Any, default: float = 0.0) -> float:
    """Return float or default if None / NaN / inf."""
    if val is None:
        return default
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except (TypeError, ValueError):
        return default


def _ratio(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """Safe division with zero-denominator guard."""
    n = _safe(numerator)
    d = _safe(denominator)
    if d == 0.0:
        return default
    return n / d


# ─────────────────────────────────────────────────────────────────────────────
# A.  BENEISH M-SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_beneish_components(
    current: Dict[str, Any],
    prior: Dict[str, Any],
) -> Dict[str, float]:
    """
    Compute all 8 Beneish M-Score indices.

    Parameters
    ----------
    current : dict  — current year financial data
    prior   : dict  — prior year financial data (1 year ago)

    Keys expected (all in ₹ Cr):
        revenue, gross_profit, receivables (trade), total_assets,
        net_block (PPE), depreciation, sga_expense (selling+admin+general),
        ebit, total_debt, ebitda, cfo, pat

    Returns
    -------
    dict with keys: dsri, gmi, aqi, sgi, depi, sgai, tata, lvgi
    """

    # ---- Current year -------------------------------------------------------
    rev_c  = _safe(current.get("revenue"))
    rec_c  = _safe(current.get("trade_receivables", current.get("receivables")))
    gp_c   = _safe(current.get("gross_profit"))
    ta_c   = _safe(current.get("total_assets"), 1.0)
    ppe_c  = _safe(current.get("fixed_assets",  current.get("net_block")))
    dep_c  = _safe(current.get("depreciation"))
    sga_c  = _safe(current.get("sga_expense",   current.get("selling_admin_expense",
                               current.get("employee_cost", 0) +
                               _safe(current.get("other_expenses", 0)))))
    ebit_c = _safe(current.get("ebit", _safe(current.get("ebitda")) - dep_c))
    debt_c = _safe(current.get("total_debt",     current.get("borrowings")))
    cfo_c  = _safe(current.get("cfo"))
    pat_c  = _safe(current.get("pat"))

    # ---- Prior year ---------------------------------------------------------
    rev_p  = _safe(prior.get("revenue"), 1.0)
    rec_p  = _safe(prior.get("trade_receivables", prior.get("receivables")))
    gp_p   = _safe(prior.get("gross_profit"))
    ta_p   = _safe(prior.get("total_assets"), 1.0)
    ppe_p  = _safe(prior.get("fixed_assets",  prior.get("net_block")))
    dep_p  = _safe(prior.get("depreciation"))
    sga_p  = _safe(prior.get("sga_expense",   prior.get("selling_admin_expense",
                               prior.get("employee_cost", 0) +
                               _safe(prior.get("other_expenses", 0)))))
    debt_p = _safe(prior.get("total_debt",     prior.get("borrowings")))

    # ── 1. DSRI: Days Sales Receivable Index ─────────────────────────────────
    #    DSRI = (Receivables_t / Revenue_t) / (Receivables_t-1 / Revenue_t-1)
    dsri = _ratio(
        _ratio(rec_c, rev_c, 0.05),
        _ratio(rec_p, rev_p, 0.05),
        default=1.0,
    )

    # ── 2. GMI: Gross Margin Index ────────────────────────────────────────────
    #    GMI = Gross_Margin_t-1 / Gross_Margin_t
    gm_c = _ratio(gp_c, rev_c, 0.30)
    gm_p = _ratio(gp_p, rev_p, 0.30)
    gmi = _ratio(gm_p, gm_c, default=1.0)

    # ── 3. AQI: Asset Quality Index ───────────────────────────────────────────
    #    AQI = [1 - (CA_t + PPE_t) / TA_t] / [1 - (CA_t-1 + PPE_t-1) / TA_t-1]
    #    Current assets approximation from company data
    ca_c = _safe(current.get("total_current_assets",
                 _safe(current.get("trade_receivables")) +
                 _safe(current.get("inventories")) +
                 _safe(current.get("cash_equivalents"))))
    ca_p = _safe(prior.get("total_current_assets",
                 _safe(prior.get("trade_receivables")) +
                 _safe(prior.get("inventories")) +
                 _safe(prior.get("cash_equivalents"))))

    nqa_c = 1.0 - _ratio(ca_c + ppe_c, ta_c, 0.5)
    nqa_p = 1.0 - _ratio(ca_p + ppe_p, ta_p, 0.5)
    aqi = _ratio(nqa_c, nqa_p, default=1.0)

    # ── 4. SGI: Sales Growth Index ────────────────────────────────────────────
    #    SGI = Revenue_t / Revenue_t-1
    sgi = _ratio(rev_c, rev_p, default=1.0)

    # ── 5. DEPI: Depreciation Index ───────────────────────────────────────────
    #    DEPI = (Dep_t-1 / (Dep_t-1 + PPE_t-1)) / (Dep_t / (Dep_t + PPE_t))
    dep_rate_c = _ratio(dep_c, dep_c + ppe_c, 0.10)
    dep_rate_p = _ratio(dep_p, dep_p + ppe_p, 0.10)
    depi = _ratio(dep_rate_p, dep_rate_c, default=1.0)

    # ── 6. SGAI: SGA Expense Index ────────────────────────────────────────────
    #    SGAI = (SGA_t / Revenue_t) / (SGA_t-1 / Revenue_t-1)
    sgai = _ratio(
        _ratio(sga_c, rev_c, 0.15),
        _ratio(sga_p, rev_p, 0.15),
        default=1.0,
    )

    # ── 7. TATA: Total Accruals to Total Assets ───────────────────────────────
    #    TATA = (Net Income - CFO) / Total Assets
    #    Higher TATA → more income not backed by cash → manipulation risk
    tata = _ratio(pat_c - cfo_c, ta_c, default=0.0)

    # ── 8. LVGI: Leverage Index ───────────────────────────────────────────────
    #    LVGI = (LTD_t + CL_t) / TA_t) / (LTD_t-1 + CL_t-1) / TA_t-1)
    cl_c = _safe(current.get("total_current_liab"))
    cl_p = _safe(prior.get("total_current_liab"))
    lev_c = _ratio(debt_c + cl_c, ta_c, 0.5)
    lev_p = _ratio(debt_p + cl_p, ta_p, 0.5)
    lvgi = _ratio(lev_c, lev_p if lev_p > 0 else lev_c, default=1.0)

    # Clamp unreasonable values (data noise guard)
    def _clamp(v: float, lo: float = 0.1, hi: float = 10.0) -> float:
        return max(lo, min(hi, v))

    return {
        "dsri":  round(_clamp(dsri), 4),
        "gmi":   round(_clamp(gmi),  4),
        "aqi":   round(_clamp(aqi),  4),
        "sgi":   round(_clamp(sgi),  4),
        "depi":  round(_clamp(depi), 4),
        "sgai":  round(_clamp(sgai), 4),
        "tata":  round(max(-0.5, min(0.5, tata)), 4),  # TATA can be negative
        "lvgi":  round(_clamp(lvgi), 4),
    }


def compute_beneish_m_score(
    current: Dict[str, Any],
    prior: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute the full Beneish M-Score and flag individual components.

    Parameters
    ----------
    current, prior : financial dicts (see compute_beneish_components)

    Returns
    -------
    dict:
        m_score          float    — overall M-Score (> -2.22 = manipulator)
        flag             str      — "MANIPULATOR" | "GREY" | "CLEAN"
        components       dict     — all 8 index values
        red_flags        list     — component names that exceeded thresholds
        manipulation_probability  float  0-1
    """
    components = compute_beneish_components(current, prior)

    # Compute M-Score
    m_score = BENEISH_INTERCEPT
    for idx, coef in BENEISH_COEFS.items():
        m_score += coef * components[idx]
    m_score = round(m_score, 4)

    # Flag individual components
    red_flags = []
    for idx, threshold in BENEISH_THRESHOLDS.items():
        val = components[idx]
        if idx == "gmi":
            # For GMI: value > 1 means gross margin deteriorated → red flag
            if val > threshold:
                red_flags.append(f"GMI ({val:.3f} > {threshold})")
        elif idx == "tata":
            if val > threshold:
                red_flags.append(f"TATA ({val:.3f} > {threshold})")
        elif val > threshold:
            flag_map = {
                "dsri": f"DSRI ({val:.3f} > {threshold}) — receivables growing faster than revenue",
                "aqi":  f"AQI  ({val:.3f} > {threshold}) — asset quality deteriorating",
                "sgi":  f"SGI  ({val:.3f} > {threshold}) — high sales growth (may signal channel-stuffing)",
                "depi": f"DEPI ({val:.3f} > {threshold}) — depreciation rate declining",
                "sgai": f"SGAI ({val:.3f} > {threshold}) — overhead growing faster than revenue",
                "lvgi": f"LVGI ({val:.3f} > {threshold}) — leverage increasing",
            }
            if idx in flag_map:
                red_flags.append(flag_map[idx])

    # Classification
    if m_score > MANIPULATOR_THRESHOLD:
        flag = "MANIPULATOR"
    elif m_score > MANIPULATOR_THRESHOLD - 0.5:
        flag = "GREY"
    else:
        flag = "CLEAN"

    # Manipulation probability (logistic transform)
    manipulation_prob = round(1 / (1 + math.exp(-0.9 * (m_score + 2.22))), 4)

    logger.info(
        f"Beneish M-Score: {m_score:.4f} → {flag} "
        f"({len(red_flags)} flags) | prob={manipulation_prob:.1%}"
    )

    return {
        "m_score":                 m_score,
        "flag":                    flag,
        "components":              components,
        "red_flags":               red_flags,
        "manipulation_probability": manipulation_prob,
        # Flattened for easy access by other modules
        "beneish_dsri":  components["dsri"],
        "beneish_gmi":   components["gmi"],
        "beneish_aqi":   components["aqi"],
        "beneish_sgi":   components["sgi"],
        "beneish_depi":  components["depi"],
        "beneish_sgai":  components["sgai"],
        "beneish_tata":  components["tata"],
        "beneish_lvgi":  components["lvgi"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# B.  ALTMAN Z-SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_altman_z_score(financials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute Altman Z-Score for manufacturing companies.

    For private companies (no market cap), uses book value of equity
    in place of market value (Altman 1995 private-firm variant X4').

    Parameters
    ----------
    financials : dict with keys:
        total_assets, total_current_assets, total_current_liab,
        total_equity, retained_earnings (or use total_equity * 0.6),
        ebit, revenue, total_debt (or borrowings)

    Returns
    -------
    dict: z_score, zone, x1..x5, rationale
    """
    ta    = _safe(financials.get("total_assets"), 1.0)
    ca    = _safe(financials.get("total_current_assets",
                  _safe(financials.get("trade_receivables")) +
                  _safe(financials.get("inventories")) +
                  _safe(financials.get("cash_equivalents"))))
    cl    = _safe(financials.get("total_current_liab"))
    eq    = _safe(financials.get("total_equity"))
    # Use retained earnings if available; otherwise estimate as 60% of equity
    re    = _safe(financials.get("retained_earnings", eq * 0.60))
    ebit  = _safe(financials.get("ebit",
                  _safe(financials.get("ebitda")) -
                  _safe(financials.get("depreciation"))))
    rev   = _safe(financials.get("revenue"))
    debt  = _safe(financials.get("total_debt", financials.get("borrowings")))
    debt  = max(debt, 1.0)  # avoid division-by-zero

    # ── X variables ──────────────────────────────────────────────────────────
    x1 = _ratio(ca - cl, ta)              # Working Capital / Total Assets
    x2 = _ratio(re, ta)                   # Retained Earnings / Total Assets
    x3 = _ratio(ebit, ta)                 # EBIT / Total Assets
    x4 = _ratio(eq, debt)                 # Equity / Book Value of Debt (private variant)
    x5 = _ratio(rev, ta)                  # Sales / Total Assets

    z_score = (ALTMAN_WEIGHTS["x1"] * x1 +
               ALTMAN_WEIGHTS["x2"] * x2 +
               ALTMAN_WEIGHTS["x3"] * x3 +
               ALTMAN_WEIGHTS["x4"] * x4 +
               ALTMAN_WEIGHTS["x5"] * x5)
    z_score = round(z_score, 4)

    if z_score > ALTMAN_SAFE_ZONE:
        zone = "SAFE"
        interpretation = f"Z-Score {z_score:.2f} > 2.99 — low bankruptcy risk"
    elif z_score > ALTMAN_GREY_ZONE:
        zone = "GREY"
        interpretation = f"Z-Score {z_score:.2f} between 1.81-2.99 — caution warranted"
    else:
        zone = "DISTRESS"
        interpretation = f"Z-Score {z_score:.2f} < 1.81 — HIGH bankruptcy risk"

    logger.info(f"Altman Z-Score: {z_score:.4f} → {zone}")

    return {
        "z_score":        z_score,
        "zone":           zone,
        "interpretation": interpretation,
        "components": {
            "x1_working_capital_ratio": round(x1, 4),
            "x2_retained_earnings_ratio": round(x2, 4),
            "x3_ebit_to_assets": round(x3, 4),
            "x4_equity_to_debt": round(x4, 4),
            "x5_asset_turnover": round(x5, 4),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# C.  PIOTROSKI F-SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_piotroski_f_score(
    current: Dict[str, Any],
    prior: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute the Piotroski F-Score — 9 binary signals across 3 groups.

    Group A: Profitability (4 signals)
    Group B: Leverage, Liquidity, Source of Funds (3 signals)
    Group C: Operating Efficiency (2 signals)

    Parameters
    ----------
    current, prior : financial dicts

    Returns
    -------
    dict: f_score (0-9), strength, signal_breakdown, passed_signals
    """
    signals = {}

    ta_c = _safe(current.get("total_assets"), 1.0)
    ta_p = _safe(prior.get("total_assets"), 1.0)

    # ── GROUP A: Profitability ────────────────────────────────────────────────

    # A1. ROA positive (net income / beginning total assets > 0)
    roa_c = _ratio(
        _safe(current.get("pat")),
        ta_p,  # denominator = beginning-of-period assets
    )
    signals["A1_positive_roa"] = int(roa_c > 0)

    # A2. Operating cash flow positive
    cfo = _safe(current.get("cfo"))
    signals["A2_positive_cfo"] = int(cfo > 0)

    # A3. ROA increasing (current ROA > prior ROA)
    roa_p = _ratio(_safe(prior.get("pat")), ta_p)
    signals["A3_roa_increasing"] = int(roa_c > roa_p)

    # A4. Accruals: CFO > Net Income / Assets (cash quality)
    accrual_c = roa_c - _ratio(cfo, ta_c)
    signals["A4_low_accruals"] = int(accrual_c < 0)  # CFO > net income = good

    # ── GROUP B: Leverage / Liquidity ────────────────────────────────────────

    # B5. Leverage decreasing (long-term debt ratio lower)
    lt_debt_c = _safe(current.get("lt_borrowings", current.get("total_debt", 0) * 0.67))
    lt_debt_p = _safe(prior.get("lt_borrowings",   prior.get("total_debt",   0) * 0.67))
    lev_c = _ratio(lt_debt_c, ta_c)
    lev_p = _ratio(lt_debt_p, ta_p)
    signals["B5_leverage_decreasing"] = int(lev_c < lev_p)

    # B6. Current ratio increasing
    cr_c = _safe(current.get("current_ratio",
                 _ratio(_safe(current.get("total_current_assets",
                               _safe(current.get("trade_receivables")) +
                               _safe(current.get("inventories")) +
                               _safe(current.get("cash_equivalents")))),
                        _safe(current.get("total_current_liab"), 1.0))))
    cr_p = _safe(prior.get("current_ratio",
                 _ratio(_safe(prior.get("total_current_assets",
                               _safe(prior.get("trade_receivables")) +
                               _safe(prior.get("inventories")) +
                               _safe(prior.get("cash_equivalents")))),
                        _safe(prior.get("total_current_liab"), 1.0))))
    signals["B6_current_ratio_improving"] = int(cr_c > cr_p)

    # B7. No dilution — shares outstanding not increased (equity shares constant)
    eq_shares_c = _safe(current.get("equity_share_capital"))
    eq_shares_p = _safe(prior.get("equity_share_capital"))
    if eq_shares_c > 0 and eq_shares_p > 0:
        signals["B7_no_dilution"] = int(eq_shares_c <= eq_shares_p * 1.02)  # allow 2% tolerance
    else:
        signals["B7_no_dilution"] = 1  # assume no dilution if data unavailable

    # ── GROUP C: Operating Efficiency ────────────────────────────────────────

    # C8. Gross margin improving
    gm_c = _ratio(_safe(current.get("gross_profit")), _safe(current.get("revenue"), 1.0))
    gm_p = _ratio(_safe(prior.get("gross_profit")),   _safe(prior.get("revenue"), 1.0))
    if gm_c == 0.0 and current.get("gross_margin"):
        gm_c = _safe(current.get("gross_margin"))
    if gm_p == 0.0 and prior.get("gross_margin"):
        gm_p = _safe(prior.get("gross_margin"))
    signals["C8_gross_margin_improving"] = int(gm_c > gm_p)

    # C9. Asset turnover improving
    at_c = _ratio(_safe(current.get("revenue")), ta_c)
    at_p = _ratio(_safe(prior.get("revenue")),   ta_p)
    signals["C9_asset_turnover_improving"] = int(at_c > at_p)

    # ── Aggregate F-Score ─────────────────────────────────────────────────────
    f_score = sum(signals.values())

    if f_score >= 7:
        strength = "STRONG"
        interpretation = f"F-Score {f_score}/9 — strong financial position"
    elif f_score >= 4:
        strength = "MODERATE"
        interpretation = f"F-Score {f_score}/9 — moderate financial health"
    else:
        strength = "WEAK"
        interpretation = f"F-Score {f_score}/9 — weak / distressed financial signals"

    passed_signals = [k for k, v in signals.items() if v == 1]
    failed_signals = [k for k, v in signals.items() if v == 0]

    logger.info(f"Piotroski F-Score: {f_score}/9 → {strength}")

    return {
        "f_score":        f_score,
        "strength":       strength,
        "interpretation": interpretation,
        "signal_breakdown": signals,
        "passed_signals": passed_signals,
        "failed_signals": failed_signals,
    }


# ─────────────────────────────────────────────────────────────────────────────
# D.  AUDITOR DISTRESS SCORE (India-specific)
# ─────────────────────────────────────────────────────────────────────────────

def compute_auditor_distress_score(financials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a composite Auditor Distress Score based on Indian context signals:
      - Going concern qualification
      - Qualified / Adverse / Disclaimer opinion
      - Auditor resignation mid-year (SEBI-mandated disclosure)
      - Auditor is NOT Big 4 or equivalent (higher risk)
      - Multiple auditor changes in 3 years
      - High related-party transaction intensity

    Returns 0-100 distress score + individual flags.
    """
    score = 0
    flags = []

    going_concern = bool(financials.get("going_concern_flag", 0))
    qualified_opinion = bool(financials.get("qualified_opinion_flag", 0))
    auditor_resigned = bool(financials.get("auditor_resigned_flag", 0))
    not_big4 = not bool(financials.get("auditor_big4", 1))
    changes_3yr = int(financials.get("auditor_changes_3yr", 0))
    rpt_ratio = _safe(financials.get("related_party_tx_to_rev", 0))
    din_disq = int(financials.get("din_disqualified_count", 0))

    if going_concern:
        score += 30
        flags.append("Going Concern qualification — auditor doubts the company's ability to continue")
    if qualified_opinion:
        score += 20
        flags.append("Qualified / Adverse / Disclaimer audit opinion")
    if auditor_resigned:
        score += 25
        flags.append("Auditor resigned mid-year — SEBI disclosure triggered")
    if not_big4:
        score += 10
        flags.append("Non-Big4 auditor — lower audit quality assurance")
    if changes_3yr >= 2:
        score += 15
        flags.append(f"{changes_3yr} auditor changes in 3 years — shopping for opinions")
    elif changes_3yr == 1:
        score += 5
        flags.append("1 auditor change in 3 years — marginally elevated risk")
    if rpt_ratio > 0.25:
        score += 20
        flags.append(f"Related-party transactions = {rpt_ratio:.0%} of revenue — potential fund diversion")
    elif rpt_ratio > 0.10:
        score += 10
        flags.append(f"Related-party transactions = {rpt_ratio:.0%} of revenue — elevated")
    if din_disq > 0:
        score += 30
        flags.append(f"{din_disq} director(s) with disqualified DIN — MCA red flag")

    score = min(score, 100)
    level = "HIGH" if score >= 40 else ("MEDIUM" if score >= 20 else "LOW")

    logger.info(f"Auditor Distress Score: {score}/100 → {level}")

    return {
        "distress_score": score,
        "level": level,
        "flags": flags,
    }


# ─────────────────────────────────────────────────────────────────────────────
# E.  FULL FORENSICS REPORT
# ─────────────────────────────────────────────────────────────────────────────

def run_full_forensics(
    current: Dict[str, Any],
    prior: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the complete forensics suite and return a consolidated report.

    Parameters
    ----------
    current : dict — current year financial data (from excel_parser or upload)
    prior   : dict — prior year data. If None, uses heuristic estimates.

    Returns
    -------
    Comprehensive forensics dict ready for pipeline and CAM generator.
    """
    if prior is None:
        # Construct a rough prior-year estimate from current + growth rates
        rev_growth = _safe(current.get("revenue_growth", 0.08))
        ebitda_growth = _safe(current.get("ebitda_growth", 0.07))
        prior = {
            "revenue":      _safe(current.get("revenue")) / (1 + rev_growth) if rev_growth > -1 else _safe(current.get("revenue")) * 0.92,
            "gross_profit": _safe(current.get("gross_profit")) / (1 + ebitda_growth * 0.8),
            "ebitda":       _safe(current.get("ebitda")) / (1 + ebitda_growth),
            "pat":          _safe(current.get("pat")) / (1 + rev_growth * 1.2),
            "total_assets": _safe(current.get("total_assets")) * 0.93,
            "total_equity": _safe(current.get("total_equity")) * 0.91,
            "total_debt":   _safe(current.get("total_debt")) * 1.05,
            "lt_borrowings": _safe(current.get("lt_borrowings")) * 1.05,
            "trade_receivables": _safe(current.get("trade_receivables")) / max(1 + rev_growth, 0.01),
            "inventories":   _safe(current.get("inventories")) / max(1 + rev_growth, 0.01),
            "cash_equivalents": _safe(current.get("cash_equivalents")),
            "fixed_assets":  _safe(current.get("fixed_assets")),
            "net_block":     _safe(current.get("net_block")),
            "depreciation":  _safe(current.get("depreciation")),
            "cfo":           _safe(current.get("cfo")) * 0.95,
            "total_current_assets": _safe(current.get("total_current_assets")) * 0.94,
            "total_current_liab":   _safe(current.get("total_current_liab")) * 0.97,
            "equity_share_capital": _safe(current.get("equity_share_capital")),
            "gross_margin":   _safe(current.get("gross_margin")),
            "current_ratio":  _safe(current.get("current_ratio")),
        }

    logger.info("── Running Beneish M-Score ──────────────────────────────")
    beneish = compute_beneish_m_score(current, prior)

    logger.info("── Running Altman Z-Score ───────────────────────────────")
    altman = compute_altman_z_score(current)

    logger.info("── Running Piotroski F-Score ────────────────────────────")
    piotroski = compute_piotroski_f_score(current, prior)

    logger.info("── Running Auditor Distress Score ───────────────────────")
    auditor = compute_auditor_distress_score(current)

    # ── Overall forensic risk assessment ─────────────────────────────────────
    risk_factors = []
    if beneish["flag"] == "MANIPULATOR":
        risk_factors.append(f"Beneish M-Score {beneish['m_score']:.2f} signals earnings manipulation")
    if altman["zone"] == "DISTRESS":
        risk_factors.append(f"Altman Z-Score {altman['z_score']:.2f} — bankruptcy risk zone")
    if piotroski["strength"] == "WEAK":
        risk_factors.append(f"Piotroski F-Score {piotroski['f_score']}/9 — weak fundamentals")
    if auditor["level"] == "HIGH":
        risk_factors.extend(auditor["flags"][:2])  # top 2 auditor flags

    overall_risk = (
        "HIGH" if len(risk_factors) >= 3 or beneish["flag"] == "MANIPULATOR"
        else "MEDIUM" if len(risk_factors) >= 1
        else "LOW"
    )

    logger.info(f"Overall Forensic Risk: {overall_risk} ({len(risk_factors)} red flags)")

    return {
        # Summary fields used by the rest of the pipeline
        "beneish_m_score":     beneish["m_score"],
        "beneish_flag":        beneish["flag"],
        "beneish_manipulation_probability": beneish["manipulation_probability"],
        "beneish_dsri":        beneish["components"]["dsri"],
        "beneish_gmi":         beneish["components"]["gmi"],
        "beneish_aqi":         beneish["components"]["aqi"],
        "beneish_sgi":         beneish["components"]["sgi"],
        "beneish_depi":        beneish["components"]["depi"],
        "beneish_sgai":        beneish["components"]["sgai"],
        "beneish_tata":        beneish["components"]["tata"],
        "beneish_lvgi":        beneish["components"]["lvgi"],
        "beneish_red_flags":   beneish["red_flags"],
        "altman_z_score":      altman["z_score"],
        "altman_zone":         altman["zone"],
        "altman_components":   altman["components"],
        "piotroski_f_score":   piotroski["f_score"],
        "piotroski_strength":  piotroski["strength"],
        "piotroski_signals":   piotroski["signal_breakdown"],
        "piotroski_passed":    piotroski["passed_signals"],
        "piotroski_failed":    piotroski["failed_signals"],
        "auditor_distress_score": auditor["distress_score"],
        "auditor_distress_level": auditor["level"],
        "auditor_flags":       auditor["flags"],
        "overall_forensic_risk": overall_risk,
        "risk_factors":        risk_factors,
        # Raw objects for deep-dive access
        "_beneish":   beneish,
        "_altman":    altman,
        "_piotroski": piotroski,
        "_auditor":   auditor,
        "source":     "forensics_module",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI — run standalone
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Sunrise Textile Mills demo
    demo_current = {
        "revenue": 850.0, "gross_profit": 323.0,
        "ebitda": 127.5, "depreciation": 38.5,
        "ebit": 89.0, "pat": 51.0,
        "total_assets": 1200.0, "total_equity": 325.0,
        "total_debt": 520.0, "lt_borrowings": 350.0,
        "trade_receivables": 120.0, "inventories": 95.0,
        "cash_equivalents": 45.0, "total_current_assets": 310.0,
        "total_current_liab": 248.0, "fixed_assets": 580.0,
        "cfo": 95.0, "revenue_growth": 0.12,
        "going_concern_flag": 0, "qualified_opinion_flag": 0,
        "auditor_resigned_flag": 0, "auditor_big4": 1,
        "auditor_changes_3yr": 0, "related_party_tx_to_rev": 0.05,
        "din_disqualified_count": 0, "gross_margin": 0.38,
        "current_ratio": 1.25,
    }
    demo_prior = {
        "revenue": 759.0, "gross_profit": 292.0,
        "ebitda": 117.0, "depreciation": 35.0,
        "ebit": 82.0, "pat": 44.0,
        "total_assets": 1115.0, "total_equity": 295.0,
        "total_debt": 495.0, "lt_borrowings": 335.0,
        "trade_receivables": 108.0, "inventories": 88.0,
        "cash_equivalents": 40.0, "total_current_assets": 288.0,
        "total_current_liab": 240.0, "fixed_assets": 540.0,
        "cfo": 88.0, "gross_margin": 0.384,
        "current_ratio": 1.20,
    }

    result = run_full_forensics(demo_current, demo_prior)
    import json
    print(json.dumps(
        {k: v for k, v in result.items() if not k.startswith("_")},
        indent=2, default=str
    ))
