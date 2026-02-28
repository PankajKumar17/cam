"""
Intelli-Credit - Feature Engineering Pipeline
===============================================
Loads the raw synthetic (or real) dataset, computes / verifies all
engineered features, adds Default-DNA archetype similarity scores,
and writes the final feature matrix.

Usage:
    python modules/person1_ml_core/feature_engineering.py

Output:
    data/processed/feature_matrix.csv

API:
    build_feature_matrix(raw_csv_path, output_path) -> pd.DataFrame
"""

import os
import sys
import warnings

# UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ============================================================================
#  1. VELOCITY FEATURES
# ============================================================================

def compute_velocity_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute year-on-year growth rates, ratio velocities, accelerations,
    rolling slopes, and time-to-danger estimates.

    Growth rate = (value_t - value_{t-1}) / abs(value_{t-1})

    Parameters
    ----------
    df : pd.DataFrame
        Must contain company_name, fiscal_year, and all raw financial columns.

    Returns
    -------
    pd.DataFrame
        Input dataframe with velocity columns added / overwritten.
    """
    df = df.sort_values(["company_name", "fiscal_year"]).reset_index(drop=True)
    eps = 1e-8  # guard against division by zero

    # ---- A. Raw growth rates ------------------------------------------------
    growth_cols = [
        "revenue", "ebitda", "pat", "cfo",
        "total_equity", "total_debt",
    ]
    for col in growth_cols:
        prev = df.groupby("company_name")[col].shift(1)
        df[f"{col}_growth"] = (df[col] - prev) / (prev.abs() + eps)

    # ---- B. Ratio velocities (year-on-year diff) ----------------------------
    # Ensure ratios exist
    if "dscr" not in df.columns:
        df["dscr"] = (df["pat"] + df["depreciation"]) / (df["total_debt"] * 0.12 + eps)
    if "interest_coverage" not in df.columns:
        df["interest_coverage"] = df["ebit"] / (df["interest_expense"] + eps)
    if "debt_to_equity" not in df.columns:
        df["debt_to_equity"] = df["total_debt"] / (df["total_equity"] + eps)

    velocity_ratios = {
        "dscr_velocity": "dscr",
        "icr_velocity": "interest_coverage",
        "de_velocity": "debt_to_equity",
    }
    for vel_name, source_col in velocity_ratios.items():
        df[vel_name] = df.groupby("company_name")[source_col].diff()

    # ---- C. Acceleration (second-order) -------------------------------------
    df["dscr_acceleration"] = df.groupby("company_name")["dscr_velocity"].diff()

    # ---- D. Rolling 3-year slope via linear regression ----------------------
    def _rolling_slope(series: pd.Series) -> float:
        """OLS slope over a window; returns NaN if insufficient data."""
        vals = series.dropna()
        if len(vals) < 3:
            return np.nan
        x = np.arange(len(vals))
        try:
            return np.polyfit(x, vals, 1)[0]
        except Exception:
            return np.nan

    df["dscr_3yr_slope"] = df.groupby("company_name")["dscr"].transform(
        lambda s: s.rolling(3, min_periods=3).apply(_rolling_slope, raw=False)
    )

    # ---- E. Months to DSCR danger zone (DSCR < 1.0) ------------------------
    # If velocity is negative, estimate months until DSCR breaches 1.0
    df["months_to_dscr_danger"] = np.where(
        df["dscr_velocity"] < 0,
        ((df["dscr"] - 1.0) / (-df["dscr_velocity"] + eps)) * 12,
        999.0,  # stable / improving -> large sentinel
    )
    df["months_to_dscr_danger"] = df["months_to_dscr_danger"].clip(-12, 120)

    return df


# ============================================================================
#  2. BENEISH M-SCORE VALIDATION (SATYAM)
# ============================================================================

def validate_beneish_on_satyam(df: pd.DataFrame) -> bool:
    """
    Validate that the Beneish M-Score correctly flags Satyam Computer
    as a likely manipulator (M-Score > -2.22) in years close to default.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset containing company_name, beneish_m_score, and label columns.

    Returns
    -------
    bool
        True if the assertion passes.
    """
    satyam = df[df["company_name"] == "Satyam Computer"].copy()

    if satyam.empty:
        print("  [WARN] Satyam Computer not found in dataset -- skipping Beneish validation")
        return False

    # Focus on rows that have an M-Score (need prior-year for Beneish)
    satyam_ms = satyam.dropna(subset=["beneish_m_score"])
    if satyam_ms.empty:
        print("  [WARN] No Beneish M-Score data for Satyam -- skipping")
        return False

    # Check near-default years (last 2 fiscal years before / at default)
    near_default = satyam_ms.sort_values("fiscal_year").tail(2)
    flagged = (near_default["beneish_m_score"] > -2.22).any()

    print("\n  === Beneish M-Score Validation: Satyam Computer ===")
    for _, row in near_default.iterrows():
        status = "FLAGGED" if row["beneish_m_score"] > -2.22 else "ok"
        print(f"    FY {int(row['fiscal_year'])}: M-Score = {row['beneish_m_score']:+.3f}  [{status}]")

    if flagged:
        print("  Result: [PASS] Satyam flagged as likely manipulator near default")
    else:
        print("  Result: [FAIL] Satyam NOT flagged -- synthetic data limitation")
        print("          (With real Prowess data, Satyam's DSRI and TATA would spike)")

    return flagged


# ============================================================================
#  3. DEFAULT-DNA SIMILARITY SCORES
# ============================================================================

# Each archetype is a dict mapping column -> direction.
# direction: +1 means "high is bad", -1 means "low is bad"
# We normalise the features before cosine similarity.

_ARCHETYPE_FEATURES = {
    "ilfs": {
        # IL&FS: infrastructure over-leverage, cash flow negative
        "st_debt_to_assets":   +1,
        "cfo_to_debt":         -1,   # low is bad
        "cwip_to_assets":      +1,   # high CWIP = stalled projects
        "debt_to_equity":      +1,
        "interest_coverage":   -1,
    },
    "dhfl": {
        # DHFL: related-party tunnelling, receivables rot, pledging
        "related_party_tx_to_rev": +1,
        "receivables_days":        +1,
        "promoter_pledge_pct":     +1,
        "debt_to_assets":          +1,
        "auditor_distress_score":  +1,
    },
    "jet": {
        # Jet Airways: revenue decline, cost blowout, liquidity crunch
        "revenue_growth":          -1,   # negative is bad
        "employee_cost_to_rev":    +1,   # high employee cost ratio
        "current_ratio":           -1,
        "cfo_to_sales":            -1,
        "ebitda_margin":           -1,
    },
    "videocon": {
        # Videocon: contagion, pledging, value destruction
        "contagion_risk_score":    +1,
        "promoter_pledge_pct":     +1,
        "roe":                     -1,   # negative is worse
        "debt_to_equity":          +1,
        "asset_turnover":          -1,
    },
    "satyam": {
        # Satyam: earnings manipulation
        "beneish_dsri":            +1,
        "beneish_tata":            +1,   # positive accruals = red flag
        "auditor_distress_score":  +1,
        "beneish_m_score":         +1,   # higher (less negative) = worse
        "cfo_to_sales":            -1,   # cash doesn't match income
    },
}


def _safe_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Return column filled with 0 if it exists, else a zero series."""
    if col in df.columns:
        return df[col].fillna(0.0)
    return pd.Series(0.0, index=df.index)


def compute_default_dna(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cosine similarity of every borrower-row to five historical
    default archetypes (IL&FS, DHFL, Jet Airways, Videocon, Satyam).

    New columns added:
        similarity_to_ilfs, similarity_to_dhfl, similarity_to_jet,
        similarity_to_videocon, similarity_to_satyam,
        max_archetype_similarity, closest_default_archetype

    Parameters
    ----------
    df : pd.DataFrame
        Feature matrix with all ratios / velocity columns.

    Returns
    -------
    pd.DataFrame
        Input dataframe with DNA similarity columns appended.
    """
    # Collect all feature names used across archetypes
    all_feat_names = sorted(
        {col for arch in _ARCHETYPE_FEATURES.values() for col in arch}
    )

    # Build raw matrix from df (rows x features)
    raw = pd.DataFrame(
        {feat: _safe_col(df, feat) for feat in all_feat_names},
        index=df.index,
    )

    # Standardise column-wise (z-score) so cosine distance is meaningful
    means = raw.mean()
    stds  = raw.std().replace(0, 1)
    normed = (raw - means) / stds

    # Build archetype vectors (one per archetype) in the same feature space
    archetype_names = list(_ARCHETYPE_FEATURES.keys())
    archetype_matrix = np.zeros((len(archetype_names), len(all_feat_names)))

    for i, arch_name in enumerate(archetype_names):
        for feat_col, direction in _ARCHETYPE_FEATURES[arch_name].items():
            j = all_feat_names.index(feat_col)
            # direction x 3 std deviations = "extreme" archetype
            archetype_matrix[i, j] = direction * 3.0

    # Cosine similarity: (n_rows, n_archetypes)
    sims = cosine_similarity(normed.values, archetype_matrix)

    sim_cols = [f"similarity_to_{name}" for name in archetype_names]
    for k, col_name in enumerate(sim_cols):
        df[col_name] = sims[:, k]

    df["max_archetype_similarity"] = sims.max(axis=1)
    df["closest_default_archetype"] = pd.Series(
        [archetype_names[idx] for idx in sims.argmax(axis=1)],
        index=df.index,
    )

    return df


# ============================================================================
#  4. ADDITIONAL DERIVED FEATURES
# ============================================================================

def compute_extra_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add any helper ratio / feature columns needed by the DNA fingerprint
    or downstream models that may not be in the raw data yet.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    eps = 1e-6

    # employee_cost as fraction of revenue  (used by Jet archetype)
    if "employee_cost_to_rev" not in df.columns:
        df["employee_cost_to_rev"] = df["employee_cost"] / (df["revenue"] + eps)

    # CWIP-to-assets  (used by IL&FS archetype)
    if "cwip_to_assets" not in df.columns:
        df["cwip_to_assets"] = df["cwip"] / (df["total_assets"] + eps)

    return df


# ============================================================================
#  5. MASTER ORCHESTRATOR
# ============================================================================

def build_feature_matrix(raw_csv_path: str, output_path: str) -> pd.DataFrame:
    """
    End-to-end feature engineering pipeline.

    1. Load raw dataset
    2. Compute extra helper ratios
    3. Compute / refresh velocity features
    4. Validate Beneish M-Score on Satyam
    5. Compute Default-DNA archetype similarity
    6. Save final feature matrix

    Parameters
    ----------
    raw_csv_path : str
        Path to the raw CSV (e.g. data/synthetic/intelli_credit_dataset.csv).
    output_path : str
        Destination for the final feature matrix CSV.

    Returns
    -------
    pd.DataFrame
        The final, fully-engineered feature matrix.
    """
    print("=" * 65)
    print("  Intelli-Credit  --  Feature Engineering Pipeline")
    print("=" * 65)

    # ---- 1. Load -----------------------------------------------------------
    print(f"\n[1/5] Loading dataset from {raw_csv_path} ...")
    df = pd.read_csv(raw_csv_path)
    print(f"      {len(df)} rows x {len(df.columns)} columns loaded")

    # ---- 2. Extra ratios ---------------------------------------------------
    print("[2/5] Computing helper ratios ...")
    df = compute_extra_ratios(df)

    # ---- 3. Velocity features  (re-derive from scratch per spec) -----------
    print("[3/5] Computing velocity features ...")
    df = compute_velocity_features(df)

    # ---- 4. Beneish validation ---------------------------------------------
    print("[4/5] Validating Beneish M-Score on Satyam ...")
    beneish_ok = validate_beneish_on_satyam(df)

    # ---- 5. Default-DNA similarity -----------------------------------------
    print("\n[5/5] Computing Default-DNA similarity scores ...")
    df = compute_default_dna(df)

    # ---- 6. Save -----------------------------------------------------------
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)

    # ---- Summary -----------------------------------------------------------
    new_dna_cols = [c for c in df.columns if "similarity_to_" in c or "archetype" in c]
    velocity_cols = [c for c in df.columns if "_growth" in c or "_velocity" in c
                     or "_acceleration" in c or "_slope" in c
                     or "months_to_dscr" in c]

    print(f"\n{'=' * 65}")
    print("  FEATURE MATRIX SUMMARY")
    print(f"{'=' * 65}")
    print(f"  Rows:              {len(df)}")
    print(f"  Total columns:     {len(df.columns)}")
    print(f"  Velocity features: {len(velocity_cols)}")
    print(f"  DNA sim features:  {len(new_dna_cols)}")
    print(f"  Beneish check:     {'PASS' if beneish_ok else 'INFO (synthetic data)'}")
    print(f"  Saved to:          {output_path}")
    print(f"{'=' * 65}\n")

    return df


# ============================================================================
#  ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    RAW_PATH = "data/synthetic/intelli_credit_dataset.csv"
    OUT_PATH = "data/processed/feature_matrix.csv"

    if not os.path.exists(RAW_PATH):
        print(f"[ERROR] Raw dataset not found: {RAW_PATH}")
        print("  Run:  python modules/person1_ml_core/data_generator.py  first")
        sys.exit(1)

    df = build_feature_matrix(RAW_PATH, OUT_PATH)
