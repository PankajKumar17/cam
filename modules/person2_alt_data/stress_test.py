"""
Yakṣarāja — Monte Carlo Stress Testing Engine (Person 2)
==============================================================
Outputs a PROBABILITY DISTRIBUTION of DSCR outcomes across 1000 macro
scenarios instead of a binary approve / reject. This is how real credit
committees think — in distributions, not binary decisions.

Parts:
  A — Macro Scenario Engine (5 RBI-calibrated shock variables)
  B — DSCR Monte Carlo Simulation (1000 paths, 3-yr forward)
  C — Percentile Outputs (P10 / P50 / P90, default probability, covenant)
  D — Visualization (histogram + danger-zone + percentile markers)
  E — Named Stress Scenarios (4 deterministic what-if scenarios)

Author: Person 2
Module: modules/person2_alt_data/stress_test.py
"""

import os
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd

from loguru import logger

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for server / CI
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("matplotlib not installed — visualization unavailable")
    MATPLOTLIB_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

RANDOM_SEED = 42

# ── Default base financials (Sunrise Textile Mills demo) ─────────────────
DEFAULT_FINANCIALS: Dict[str, Any] = {
    "company_name":       "Sunrise Textile Mills",
    "company_cin":        "U17100MH2010PLC123456",
    "sector":             "Textiles",
    # Income statement (₹ Cr)
    "revenue":            1250.0,
    "ebitda":              187.5,   # 15% margin
    "ebitda_margin":        0.15,
    "pat":                  75.0,
    "depreciation":         37.5,
    # Balance sheet
    "total_debt":          520.0,
    "interest_expense":     52.0,   # ~10% avg cost of debt
    "principal_repayment":  65.0,   # annual principal repayment
    # Derived
    "current_dscr":          1.0,   # (PAT + Dep) / (Interest + Principal)
    # Loan tenure
    "loan_maturity_years":    3,
    # Sector-specific sensitivity
    "commodity_sensitivity":  0.40,  # Textiles: 40% raw-material cost share
    "export_share":           0.30,  # 30% revenue is export
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART A — MACRO SCENARIO ENGINE                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Each shock variable: (distribution_name, *params, clip_low, clip_high)
# Parameters are calibrated from RBI historical distributions (2015-2024)

MACRO_SHOCK_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "repo_rate_shock": {
        "description": "Change in RBI repo rate (percentage points)",
        "distribution": "normal",
        "mean": 0.0,
        "std": 1.5,
        "clip_low": -2.0,
        "clip_high": 4.0,
        "unit": "pp",
    },
    "inflation_shock": {
        "description": "CPI inflation deviation from target (percentage points)",
        "distribution": "normal",
        "mean": 0.0,
        "std": 2.0,
        "clip_low": -1.0,
        "clip_high": 6.0,
        "unit": "pp",
    },
    "revenue_shock": {
        "description": "Revenue growth shock (fraction, e.g. -0.20 = -20%)",
        "distribution": "normal",
        "mean": 0.0,
        "std": 0.15,
        "clip_low": -0.40,
        "clip_high": 0.20,
        "unit": "fraction",
    },
    "commodity_price_shock": {
        "description": "Commodity / raw-material price shock (fraction)",
        "distribution": "normal",
        "mean": 0.0,
        "std": 0.20,
        "clip_low": -0.30,
        "clip_high": 0.50,
        "unit": "fraction",
    },
    "customer_default_probability": {
        "description": "Probability of key customer default (fraction 0-0.30)",
        "distribution": "uniform",
        "low": 0.0,
        "high": 0.30,
        "clip_low": 0.0,
        "clip_high": 0.30,
        "unit": "probability",
    },
}


def _draw_shock(defn: Dict[str, Any], rng: np.random.Generator) -> float:
    """Draw a single shock value from its defined distribution."""
    dist = defn["distribution"]
    if dist == "normal":
        val = rng.normal(defn["mean"], defn["std"])
    elif dist == "uniform":
        val = rng.uniform(defn["low"], defn["high"])
    else:
        val = 0.0
    return float(np.clip(val, defn["clip_low"], defn["clip_high"]))


def generate_macro_scenarios(
    n_simulations: int = 1000,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate *n_simulations* sets of macro shock variables.

    Each row is one macro scenario with 5 shock columns drawn from
    their RBI-calibrated distributions.

    Args:
        n_simulations: Number of Monte Carlo paths (default 1000)
        seed:          Random seed for reproducibility

    Returns:
        DataFrame with columns:
          scenario_id, repo_rate_shock, inflation_shock,
          revenue_shock, commodity_price_shock, customer_default_probability
    """
    rng = np.random.default_rng(seed)
    logger.info(f"Generating {n_simulations} macro scenarios (seed={seed})")

    records = []
    for i in range(n_simulations):
        row: Dict[str, Any] = {"scenario_id": i}
        for shock_name, defn in MACRO_SHOCK_DEFINITIONS.items():
            row[shock_name] = _draw_shock(defn, rng)
        records.append(row)

    df = pd.DataFrame(records)
    logger.info(f"Macro scenarios shape: {df.shape}")
    return df


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART B — DSCR SIMULATION ENGINE                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _simulate_single_dscr(
    financials: Dict[str, Any],
    shocks: Dict[str, float],
) -> Dict[str, float]:
    """
    Recompute DSCR for a single macro scenario.

    Steps:
      1. New Revenue  = base_revenue × (1 + revenue_shock)
                        × (1 − customer_default_probability × export_share)
      2. Margin impact = commodity_sensitivity × commodity_price_shock
                       + inflation_pass_through (0.3 × inflation_shock/100)
      3. New EBITDA   = new_revenue × (base_margin − margin_impact)
      4. New Interest  = base_interest × (1 + repo_rate_shock × 0.5)
      5. New PAT       ≈ new_EBITDA − new_interest − depreciation × tax_adj
      6. DSCR          = (new_PAT + depreciation) / (new_interest + principal)

    The computation is a 3-year forward projection — we compound annual
    shocks over the loan tenure, assuming they persist.

    Args:
        financials: Borrower's base financial data
        shocks:     Dict of 5 shock variables for this scenario

    Returns:
        Dict with intermediate and final values for the scenario
    """
    # ── Unpack base financials ───────────────────────────────────────────
    base_revenue     = financials.get("revenue", 1250.0)
    base_ebitda      = financials.get("ebitda", 187.5)
    base_margin      = financials.get("ebitda_margin", 0.15)
    base_pat         = financials.get("pat", 75.0)
    base_dep         = financials.get("depreciation", 37.5)
    base_interest    = financials.get("interest_expense", 52.0)
    base_principal   = financials.get("principal_repayment", 65.0)
    commodity_sens   = financials.get("commodity_sensitivity", 0.40)
    export_share     = financials.get("export_share", 0.30)
    maturity_years   = financials.get("loan_maturity_years", 3)

    # ── Unpack shocks ───────────────────────────────────────────────────
    revenue_shock    = shocks.get("revenue_shock", 0.0)
    repo_shock       = shocks.get("repo_rate_shock", 0.0)
    inflation_shock  = shocks.get("inflation_shock", 0.0)
    commodity_shock  = shocks.get("commodity_price_shock", 0.0)
    cust_default     = shocks.get("customer_default_probability", 0.0)

    # ── Step 1: Revenue impact ───────────────────────────────────────────
    # Revenue shock + customer default eroding export revenue
    revenue_multiplier = (1.0 + revenue_shock) * (1.0 - cust_default * export_share)
    # Compound over maturity period (assume shock persists annually)
    compounded_revenue = base_revenue * (revenue_multiplier ** maturity_years)

    # ── Step 2: Margin impact ────────────────────────────────────────────
    # Higher commodity prices compress margins
    margin_hit_commodity = commodity_sens * commodity_shock
    # Inflation pass-through (partial: 30% of inflation eats into margin)
    margin_hit_inflation = 0.3 * (inflation_shock / 100.0)
    total_margin_hit = margin_hit_commodity + margin_hit_inflation
    # Margin floor at 2% (company doesn't go below breakeven easily)
    new_margin = max(0.02, base_margin - total_margin_hit)

    # ── Step 3: New EBITDA ───────────────────────────────────────────────
    new_ebitda = compounded_revenue * new_margin

    # ── Step 4: New interest expense ─────────────────────────────────────
    # Repo rate shock → 50% pass-through to borrower's cost of funds
    rate_multiplier = 1.0 + repo_shock * 0.5 / 100.0 * base_interest
    # Simplified: interest scales with repo shock
    new_interest = base_interest * (1.0 + repo_shock * 0.5 / 10.0)
    # Floor at 70% of base (rates don't drop to zero)
    new_interest = max(new_interest, base_interest * 0.70)

    # ── Step 5: New PAT (simplified) ─────────────────────────────────────
    # Tax rate ~25%
    tax_rate = 0.25
    new_pbt = new_ebitda - new_interest - base_dep
    new_pat = new_pbt * (1.0 - tax_rate) if new_pbt > 0 else new_pbt

    # ── Step 6: DSCR ────────────────────────────────────────────────────
    debt_service = new_interest + base_principal
    # Guard against zero / negative debt service
    debt_service = max(debt_service, 1.0)
    new_dscr = (new_pat + base_dep) / debt_service

    return {
        "compounded_revenue":  round(compounded_revenue, 2),
        "new_margin":          round(new_margin, 4),
        "new_ebitda":          round(new_ebitda, 2),
        "new_interest":        round(new_interest, 2),
        "new_pat":             round(new_pat, 2),
        "debt_service":        round(debt_service, 2),
        "simulated_dscr":      round(new_dscr, 4),
    }


def run_monte_carlo(
    company_financials: Optional[Dict[str, Any]] = None,
    n_simulations: int = 1000,
    seed: int = RANDOM_SEED,
) -> Dict[str, Any]:
    """
    Run full Monte Carlo stress test for a borrower company.

    Generates 1000 macro scenarios, simulates DSCR for each, and computes
    the probability distribution of outcomes at loan maturity.

    Args:
        company_financials: Borrower's base financials dict. Keys expected:
            revenue, ebitda, ebitda_margin, pat, depreciation,
            interest_expense, principal_repayment, total_debt,
            commodity_sensitivity, export_share, loan_maturity_years,
            company_name, company_cin, sector
            Uses DEFAULT_FINANCIALS (Sunrise Textile Mills) if None.
        n_simulations: Number of Monte Carlo paths (default 1000)
        seed: Random seed for reproducibility

    Returns:
        Dict containing:
        {
            "company_name":              str,
            "n_simulations":             int,
            "base_dscr":                 float,
            "simulated_dscrs":           np.ndarray (1000,),
            "p10_dscr":                  float,
            "p50_dscr":                  float,
            "p90_dscr":                  float,
            "mean_dscr":                 float,
            "std_dscr":                  float,
            "min_dscr":                  float,
            "max_dscr":                  float,
            "default_probability_3yr":   float (0-1),
            "covenant_trigger_level":    float,
            "scenarios_df":              pd.DataFrame,
            "simulation_details":        pd.DataFrame,
        }
    """
    if company_financials is None:
        company_financials = DEFAULT_FINANCIALS.copy()

    company_name = company_financials.get("company_name", "Unknown")
    logger.info(f"{'='*60}")
    logger.info(f"MONTE CARLO STRESS TEST — {company_name}")
    logger.info(f"Running {n_simulations} simulations (seed={seed})")
    logger.info(f"{'='*60}")

    # ── Generate macro scenarios ─────────────────────────────────────────
    scenarios_df = generate_macro_scenarios(n_simulations, seed)

    # ── Base-case DSCR (no shocks) ───────────────────────────────────────
    base_result = _simulate_single_dscr(company_financials, {
        "repo_rate_shock": 0.0,
        "inflation_shock": 0.0,
        "revenue_shock": 0.0,
        "commodity_price_shock": 0.0,
        "customer_default_probability": 0.0,
    })
    base_dscr = base_result["simulated_dscr"]
    logger.info(f"Base-case DSCR (zero shocks): {base_dscr:.4f}")

    # ── Run simulations ──────────────────────────────────────────────────
    sim_results = []
    for _, scenario in scenarios_df.iterrows():
        shocks = {
            "repo_rate_shock":             scenario["repo_rate_shock"],
            "inflation_shock":             scenario["inflation_shock"],
            "revenue_shock":               scenario["revenue_shock"],
            "commodity_price_shock":       scenario["commodity_price_shock"],
            "customer_default_probability": scenario["customer_default_probability"],
        }
        result = _simulate_single_dscr(company_financials, shocks)
        result["scenario_id"] = scenario["scenario_id"]
        sim_results.append(result)

    sim_df = pd.DataFrame(sim_results)
    dscrs = sim_df["simulated_dscr"].values

    # ── PART C: Compute percentile outputs ───────────────────────────────
    p10_dscr = float(np.percentile(dscrs, 10))
    p50_dscr = float(np.percentile(dscrs, 50))
    p90_dscr = float(np.percentile(dscrs, 90))
    mean_dscr = float(np.mean(dscrs))
    std_dscr = float(np.std(dscrs))

    # Default probability: fraction of simulations where DSCR < 1.0
    n_defaults = int(np.sum(dscrs < 1.0))
    default_probability_3yr = n_defaults / n_simulations

    # Covenant trigger level: DSCR value where 20% of simulations fall below
    # i.e., the 20th percentile — bank should set covenant at this level
    covenant_trigger_level = float(np.percentile(dscrs, 20))

    logger.info(f"P10 DSCR: {p10_dscr:.4f}")
    logger.info(f"P50 DSCR: {p50_dscr:.4f}")
    logger.info(f"P90 DSCR: {p90_dscr:.4f}")
    logger.info(f"Default probability (3yr): {default_probability_3yr:.2%}")
    logger.info(f"Covenant trigger level: {covenant_trigger_level:.4f}")

    result = {
        "company_name":              company_name,
        "company_cin":               company_financials.get("company_cin", ""),
        "sector":                    company_financials.get("sector", ""),
        "n_simulations":             n_simulations,
        "loan_maturity_years":       company_financials.get("loan_maturity_years", 3),
        "base_dscr":                 base_dscr,
        "simulated_dscrs":           dscrs,
        "p10_dscr":                  p10_dscr,
        "p50_dscr":                  p50_dscr,
        "p90_dscr":                  p90_dscr,
        "mean_dscr":                 mean_dscr,
        "std_dscr":                  std_dscr,
        "min_dscr":                  float(np.min(dscrs)),
        "max_dscr":                  float(np.max(dscrs)),
        "default_probability_3yr":   default_probability_3yr,
        "n_default_scenarios":       n_defaults,
        "covenant_trigger_level":    covenant_trigger_level,
        "scenarios_df":              scenarios_df,
        "simulation_details":        sim_df,
    }

    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART E — NAMED STRESS SCENARIOS                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Define the 4 named deterministic scenarios
NAMED_SCENARIO_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "RBI Rate Hike +200bps",
        "description": "RBI raises repo rate by 200 basis points; all other variables at base",
        "shocks": {
            "repo_rate_shock": 2.0,
            "inflation_shock": 0.0,
            "revenue_shock": 0.0,
            "commodity_price_shock": 0.0,
            "customer_default_probability": 0.0,
        },
    },
    {
        "name": "Revenue Decline -20%",
        "description": "Demand shock causing 20% revenue decline; all other variables at base",
        "shocks": {
            "repo_rate_shock": 0.0,
            "inflation_shock": 0.0,
            "revenue_shock": -0.20,
            "commodity_price_shock": 0.0,
            "customer_default_probability": 0.0,
        },
    },
    {
        "name": "Cotton Price +30%",
        "description": "Raw material (cotton) price surge of 30%; textile sector stress",
        "shocks": {
            "repo_rate_shock": 0.0,
            "inflation_shock": 0.0,
            "revenue_shock": 0.0,
            "commodity_price_shock": 0.30,
            "customer_default_probability": 0.0,
        },
    },
    {
        "name": "Combined Adverse",
        "description": "All shocks hit simultaneously at P10 (worst 10%) levels",
        "shocks": "P10",  # Sentinel — will be replaced dynamically
    },
]


def get_named_scenarios(
    company_financials: Optional[Dict[str, Any]] = None,
    monte_carlo_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run 4 named deterministic stress scenarios and report DSCR for each.

    Named scenarios:
      1. "RBI Rate Hike +200bps"  — repo_rate_shock = +2.0
      2. "Revenue Decline -20%"   — revenue_shock = -0.20
      3. "Cotton Price +30%"      — commodity_shock = +0.30
      4. "Combined Adverse"       — all shocks at P10 levels simultaneously

    Args:
        company_financials: Borrower's base financials (None → demo defaults)
        monte_carlo_results: If provided, P10 levels are drawn from this
                             to set the "Combined Adverse" scenario. Otherwise,
                             a quick 1000-sim run is done to determine P10.

    Returns:
        Dict with scenario results:
        {
            "scenarios": [
                {
                    "name": str,
                    "description": str,
                    "shocks": {shock_name: value, ...},
                    "dscr": float,
                    "revenue": float,
                    "ebitda": float,
                    "verdict": "PASS" | "STRESS" | "FAIL",
                },
                ...
            ],
            "worst_scenario": str,
            "all_pass": bool,
        }
    """
    if company_financials is None:
        company_financials = DEFAULT_FINANCIALS.copy()

    logger.info("Running 4 named stress scenarios")

    # ── Determine P10 levels for "Combined Adverse" ──────────────────────
    if monte_carlo_results is not None:
        scenarios_df = monte_carlo_results["scenarios_df"]
    else:
        scenarios_df = generate_macro_scenarios(1000, RANDOM_SEED)

    p10_shocks = {
        col: float(np.percentile(scenarios_df[col].values, 10))
        if col != "customer_default_probability"
        else float(np.percentile(scenarios_df[col].values, 90))  # Worst = high default
        for col in MACRO_SHOCK_DEFINITIONS.keys()
    }
    # For adverse: revenue shock should be at P10 (most negative), repo at P90 (highest)
    p10_shocks["repo_rate_shock"] = float(np.percentile(
        scenarios_df["repo_rate_shock"].values, 90
    ))
    p10_shocks["inflation_shock"] = float(np.percentile(
        scenarios_df["inflation_shock"].values, 90
    ))
    p10_shocks["commodity_price_shock"] = float(np.percentile(
        scenarios_df["commodity_price_shock"].values, 90
    ))

    # ── Run each named scenario ──────────────────────────────────────────
    results = []
    for defn in NAMED_SCENARIO_DEFINITIONS:
        name = defn["name"]
        desc = defn["description"]

        # Resolve "P10" sentinel for Combined Adverse
        if defn["shocks"] == "P10":
            shocks = p10_shocks.copy()
        else:
            shocks = defn["shocks"].copy()

        sim = _simulate_single_dscr(company_financials, shocks)
        dscr = sim["simulated_dscr"]

        # Verdict
        if dscr >= 1.5:
            verdict = "PASS"
        elif dscr >= 1.0:
            verdict = "STRESS"
        else:
            verdict = "FAIL"

        results.append({
            "name": name,
            "description": desc,
            "shocks": {k: round(v, 4) for k, v in shocks.items()},
            "dscr": dscr,
            "revenue": sim["compounded_revenue"],
            "ebitda": sim["new_ebitda"],
            "interest": sim["new_interest"],
            "pat": sim["new_pat"],
            "verdict": verdict,
        })

        emoji = "✅" if verdict == "PASS" else ("⚠️" if verdict == "STRESS" else "❌")
        logger.info(f"  {emoji} {name}: DSCR = {dscr:.4f} → {verdict}")

    # ── Summary ──────────────────────────────────────────────────────────
    worst = min(results, key=lambda r: r["dscr"])
    all_pass = all(r["verdict"] == "PASS" for r in results)

    return {
        "scenarios": results,
        "worst_scenario": worst["name"],
        "worst_dscr": worst["dscr"],
        "all_pass": all_pass,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART D — VISUALIZATION                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Vivriti brand-ish color palette
COLOR_HIST       = "#1565C0"   # Blue histogram bars
COLOR_DANGER     = "#E53935"   # Red danger zone
COLOR_P10        = "#D32F2F"   # Red P10 line
COLOR_P50        = "#FF8F00"   # Amber P50 line
COLOR_P90        = "#2E7D32"   # Green P90 line
COLOR_BASE       = "#0A1F3C"   # Navy base-case line
COLOR_BACKGROUND = "#FAFAFA"


def plot_stress_distribution(
    results: Dict[str, Any],
    company_name: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Plot the probability distribution of simulated DSCR outcomes.

    Creates a publication-quality histogram showing:
      - Distribution of 1000 DSCR outcomes
      - Danger zone (DSCR < 1.0) highlighted in red
      - Vertical lines for P10, P50, P90 percentiles
      - Base-case DSCR marked
      - Default probability annotation

    Args:
        results:      Output dict from run_monte_carlo()
        company_name: Override company name for the title (optional)
        output_path:  Path to save PNG. Auto-generated if None.

    Returns:
        Path to saved PNG file, or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib required for visualization. pip install matplotlib")
        return None

    dscrs = results["simulated_dscrs"]
    n_sims = results["n_simulations"]
    p10 = results["p10_dscr"]
    p50 = results["p50_dscr"]
    p90 = results["p90_dscr"]
    base = results["base_dscr"]
    default_prob = results["default_probability_3yr"]
    covenant = results["covenant_trigger_level"]
    maturity = results.get("loan_maturity_years", 3)

    if company_name is None:
        company_name = results.get("company_name", "Unknown")

    # ── Create figure ────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(COLOR_BACKGROUND)
    ax.set_facecolor(COLOR_BACKGROUND)

    # ── Histogram ────────────────────────────────────────────────────────
    bin_edges = np.linspace(
        max(0, np.min(dscrs) - 0.2),
        np.max(dscrs) + 0.2,
        60,
    )

    # Split into danger (< 1.0) and safe (>= 1.0)
    n_all, bins_all, patches_all = ax.hist(
        dscrs, bins=bin_edges, alpha=0.85, color=COLOR_HIST,
        edgecolor="white", linewidth=0.5, zorder=3,
    )
    # Color danger-zone bars red
    for patch, left_edge in zip(patches_all, bins_all[:-1]):
        if left_edge < 1.0:
            patch.set_facecolor(COLOR_DANGER)
            patch.set_alpha(0.80)

    # ── Danger zone shading ──────────────────────────────────────────────
    ax.axvspan(
        bins_all[0], 1.0,
        alpha=0.08, color=COLOR_DANGER, zorder=1,
        label="Danger Zone (DSCR < 1.0)",
    )

    # ── Percentile lines ─────────────────────────────────────────────────
    ymax = ax.get_ylim()[1]

    ax.axvline(p10, color=COLOR_P10, linewidth=2.5, linestyle="--", zorder=5,
               label=f"P10 = {p10:.2f}")
    ax.axvline(p50, color=COLOR_P50, linewidth=2.5, linestyle="-", zorder=5,
               label=f"P50 = {p50:.2f}")
    ax.axvline(p90, color=COLOR_P90, linewidth=2.5, linestyle="--", zorder=5,
               label=f"P90 = {p90:.2f}")

    # Base-case line
    ax.axvline(base, color=COLOR_BASE, linewidth=2, linestyle=":", zorder=5,
               label=f"Base Case = {base:.2f}")

    # Covenant trigger
    ax.axvline(covenant, color="#6A1B9A", linewidth=1.5, linestyle="-.", zorder=5,
               label=f"Covenant Trigger (P20) = {covenant:.2f}")

    # DSCR = 1.0 reference
    ax.axvline(1.0, color="#424242", linewidth=1.5, linestyle="-", zorder=4, alpha=0.6)
    ax.annotate(
        "DSCR = 1.0\n(Default Threshold)",
        xy=(1.0, ymax * 0.95), fontsize=8,
        color="#424242", ha="center", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    # ── Annotations ──────────────────────────────────────────────────────
    # P10 label
    ax.annotate(
        f"P10\n{p10:.2f}",
        xy=(p10, ymax * 0.85), fontsize=9, fontweight="bold",
        color=COLOR_P10, ha="center",
    )
    # P50 label
    ax.annotate(
        f"P50 (Median)\n{p50:.2f}",
        xy=(p50, ymax * 0.90), fontsize=9, fontweight="bold",
        color=COLOR_P50, ha="center",
    )
    # P90 label
    ax.annotate(
        f"P90\n{p90:.2f}",
        xy=(p90, ymax * 0.85), fontsize=9, fontweight="bold",
        color=COLOR_P90, ha="center",
    )

    # ── Default probability box ──────────────────────────────────────────
    info_text = (
        f"Default Probability ({maturity}yr): {default_prob:.1%}\n"
        f"Defaults: {results['n_default_scenarios']} / {n_sims} simulations\n"
        f"Mean DSCR: {results['mean_dscr']:.3f}  |  Std: {results['std_dscr']:.3f}\n"
        f"Covenant Trigger (P20): {covenant:.3f}"
    )
    props = dict(boxstyle="round,pad=0.6", facecolor="white", alpha=0.9,
                 edgecolor="#B0BEC5")
    ax.text(
        0.98, 0.97, info_text, transform=ax.transAxes,
        fontsize=9, verticalalignment="top", horizontalalignment="right",
        bbox=props, fontfamily="monospace", zorder=10,
    )

    # ── Labels & legend ──────────────────────────────────────────────────
    ax.set_title(
        f"{n_sims} Macro Scenarios — DSCR Distribution at Loan Maturity\n"
        f"{company_name} | {maturity}-Year Forward Projection",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Simulated DSCR at Maturity", fontsize=11, labelpad=8)
    ax.set_ylabel("Number of Scenarios", fontsize=11, labelpad=8)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_xlim(left=max(0, bins_all[0]))

    plt.tight_layout()

    # ── Save ─────────────────────────────────────────────────────────────
    if output_path is None:
        safe_name = company_name.replace(" ", "_").replace("/", "_")
        output_dir = os.path.join("data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"stress_test_{safe_name}.png")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor=COLOR_BACKGROUND)
    plt.close(fig)

    logger.info(f"Stress distribution chart saved: {output_path}")
    return output_path


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONVENIENCE: HIGH-LEVEL ENTRY POINT                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def run_stress_test(
    company_financials: Optional[Dict[str, Any]] = None,
    n_simulations: int = 1000,
    save_chart: bool = True,
) -> Dict[str, Any]:
    """
    Run the complete stress testing pipeline for a borrower company.

    1. Run 1000 Monte Carlo simulations
    2. Compute P10/P50/P90, default probability, covenant trigger
    3. Run 4 named stress scenarios
    4. Generate distribution chart

    Args:
        company_financials: Borrower's base financials dict (None → demo)
        n_simulations: Number of Monte Carlo paths (default 1000)
        save_chart: Whether to save the matplotlib chart

    Returns:
        Merged dict with:
          - All run_monte_carlo() outputs
          - "named_scenarios": get_named_scenarios() output
          - "chart_path": path to saved chart (or None)
    """
    if company_financials is None:
        company_financials = DEFAULT_FINANCIALS.copy()

    company_name = company_financials.get("company_name", "Unknown")
    logger.info(f"{'='*60}")
    logger.info(f"FULL STRESS TEST PIPELINE — {company_name}")
    logger.info(f"{'='*60}")

    # Step 1-2: Monte Carlo
    mc_results = run_monte_carlo(company_financials, n_simulations)

    # Step 3: Named scenarios
    named = get_named_scenarios(company_financials, mc_results)
    mc_results["named_scenarios"] = named

    # Step 4: Chart
    if save_chart:
        chart_path = plot_stress_distribution(mc_results, company_name)
        mc_results["chart_path"] = chart_path
    else:
        mc_results["chart_path"] = None

    # ── Summary log ──────────────────────────────────────────────────────
    logger.info(f"{'='*60}")
    logger.info(f"STRESS TEST COMPLETE — {company_name}")
    logger.info(f"  Base DSCR:          {mc_results['base_dscr']:.4f}")
    logger.info(f"  P10 / P50 / P90:    {mc_results['p10_dscr']:.4f} / "
                f"{mc_results['p50_dscr']:.4f} / {mc_results['p90_dscr']:.4f}")
    logger.info(f"  Default Prob (3yr): {mc_results['default_probability_3yr']:.2%}")
    logger.info(f"  Covenant Trigger:   {mc_results['covenant_trigger_level']:.4f}")
    logger.info(f"  Named Scenarios:")
    for sc in named["scenarios"]:
        logger.info(f"    {sc['verdict']:>6s}  {sc['name']}: DSCR = {sc['dscr']:.4f}")
    logger.info(f"{'='*60}")

    return mc_results


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MONTE CARLO STRESS TEST — Standalone Test")
    print("=" * 60)

    # Demo: Sunrise Textile Mills
    print("\n[1] Generating 1000 macro scenarios...")
    scenarios = generate_macro_scenarios(1000)
    print(f"   Shape: {scenarios.shape}")
    print(f"   Shock ranges:")
    for col in MACRO_SHOCK_DEFINITIONS:
        vals = scenarios[col].values
        print(f"     {col:>30s}: [{vals.min():.4f}, {vals.max():.4f}]  "
              f"mean={vals.mean():.4f}")

    print("\n[2] Running Monte Carlo simulation...")
    mc = run_monte_carlo(n_simulations=1000)
    print(f"   Base DSCR:  {mc['base_dscr']:.4f}")
    print(f"   P10 DSCR:   {mc['p10_dscr']:.4f}")
    print(f"   P50 DSCR:   {mc['p50_dscr']:.4f}")
    print(f"   P90 DSCR:   {mc['p90_dscr']:.4f}")
    print(f"   Mean ± Std: {mc['mean_dscr']:.4f} ± {mc['std_dscr']:.4f}")
    print(f"   Default Prob (3yr): {mc['default_probability_3yr']:.2%}")
    print(f"   Covenant Trigger:   {mc['covenant_trigger_level']:.4f}")

    print("\n[3] Named stress scenarios...")
    named = get_named_scenarios()
    for sc in named["scenarios"]:
        emoji = "✅" if sc["verdict"] == "PASS" else (
            "⚠️" if sc["verdict"] == "STRESS" else "❌"
        )
        print(f"   {emoji} {sc['name']:>25s}: DSCR = {sc['dscr']:.4f} → {sc['verdict']}")
    print(f"   Worst scenario: {named['worst_scenario']} "
          f"(DSCR = {named['worst_dscr']:.4f})")

    print("\n[4] Generating distribution chart...")
    chart = plot_stress_distribution(mc, "Sunrise Textile Mills")
    if chart:
        print(f"   Chart saved: {chart}")

    print("\n" + "=" * 60)
    print("✅ Stress test complete!")
    print("=" * 60)
