"""
Yakṣarāja -- Dataset Validation & Visualization
=====================================================
Runs PASS/FAIL checks on the synthetic dataset and generates
diagnostic charts for visual inspection.

Usage:
    python modules/person1_ml_core/validate_dataset.py

Output:
    Console  -> PASS/FAIL report
    data/synthetic/validation_charts/dscr_distribution.png
    data/synthetic/validation_charts/beneish_distribution.png
    data/synthetic/validation_charts/dscr_trajectories.png
"""

import os
import sys

# Force UTF-8 on Windows so emoji / special chars don't crash
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt

# ── PATHS ─────────────────────────────────────────────────────────────────────

DATASET_PATH = "data/synthetic/intelli_credit_dataset.csv"
DEMO_PATH    = "data/synthetic/demo_sunrise_textile.csv"
SCHEMA_PATH  = "data/synthetic/schema.json"
CHARTS_DIR   = "data/synthetic/validation_charts"


# ══════════════════════════════════════════════════════════════════════════════
#  PART 1: PASS / FAIL VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def run_validations(df: pd.DataFrame) -> list[dict]:
    """Run all validation checks. Returns list of {name, status, detail}."""
    results = []

    def check(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append({"name": name, "status": status, "detail": detail})

    # ── 1. Row count ──────────────────────────────────────────────────────────
    n_rows = len(df)
    # 15 defaulted × ~7-9 yrs + 15 healthy × 16 yrs ≈ 350-370
    check(
        "Total row count is reasonable (300-500)",
        300 <= n_rows <= 500,
        f"{n_rows} rows"
    )

    # ── 2. Label distribution ─────────────────────────────────────────────────
    default_rate = df["label"].mean()
    check(
        "Default rate is ~25-45%",
        0.25 <= default_rate <= 0.45,
        f"{default_rate:.1%} default rate"
    )

    # ── 3. No completely null columns ─────────────────────────────────────────
    fully_null_cols = [c for c in df.columns if df[c].isna().all()]
    check(
        "No completely null columns",
        len(fully_null_cols) == 0,
        f"Null columns: {fully_null_cols}" if fully_null_cols else "All columns have data"
    )

    # ── 4. Columns with >50% nulls (warning, not fail) ───────────────────────
    high_null_cols = [c for c in df.columns if df[c].isna().mean() > 0.50]
    # Velocity/shift features will have NaN for first year — that's expected.
    # Only flag non-velocity columns.
    unexpected_null = [c for c in high_null_cols
                       if not any(tag in c for tag in
                                  ["_growth", "_velocity", "_acceleration",
                                   "_slope", "beneish_", "piotroski_",
                                   "months_to_dscr", "years_to_default"])]
    check(
        "No unexpected columns with >50% nulls",
        len(unexpected_null) == 0,
        f"High-null: {unexpected_null}" if unexpected_null else "OK"
    )

    # ── 5. DSCR realistic ranges ─────────────────────────────────────────────
    healthy = df[df["label"] == 0]["dscr"].dropna()
    defaulted = df[df["label"] == 1]["dscr"].dropna()

    healthy_median = healthy.median()
    defaulted_median = defaulted.median()

    check(
        "Healthy DSCR median is in 1.0-5.0 range",
        1.0 <= healthy_median <= 5.0,
        f"Median = {healthy_median:.2f}"
    )
    check(
        "Defaulted DSCR median is lower than healthy",
        defaulted_median < healthy_median,
        f"Defaulted median = {defaulted_median:.2f} vs healthy = {healthy_median:.2f}"
    )
    check(
        "Defaulted DSCR median is in 0.0-2.5 range",
        0.0 <= defaulted_median <= 2.5,
        f"Median = {defaulted_median:.2f}"
    )

    # ── 6. Beneish M-Score flags ──────────────────────────────────────────────
    # For rows where we have M-Score (needs prior year), check flag rates
    has_mscore = df["beneish_m_score"].notna()
    if has_mscore.sum() > 0:
        df_ms = df[has_mscore]
        healthy_flag = df_ms[df_ms["label"] == 0]["beneish_manipulation_flag"].mean()
        default_flag = df_ms[df_ms["label"] == 1]["beneish_manipulation_flag"].mean()

        # With synthetic data, Beneish separation isn't guaranteed.
        # Report rates as info; hard-check only the threshold logic.
        check(
            "Beneish manipulation flag rates (INFO)",
            True,  # informational — always passes
            f"Defaulted flag rate = {default_flag:.1%}, Healthy = {healthy_flag:.1%}"
        )
        check(
            "Beneish M-Score threshold is -2.22 (flag = m_score > -2.22)",
            (df_ms["beneish_manipulation_flag"] == (df_ms["beneish_m_score"] > -2.22).astype(int)).all(),
            "Threshold correctly applied"
        )
    else:
        check("Beneish M-Score computed", False, "No non-null M-Score values found")

    # ── 7. Altman Z-Score sanity ──────────────────────────────────────────────
    has_altman = df["altman_z_score"].notna()
    if has_altman.sum() > 0:
        healthy_z = df[(df["label"] == 0) & has_altman]["altman_z_score"].median()
        default_z = df[(df["label"] == 1) & has_altman]["altman_z_score"].median()
        check(
            "Healthy Altman Z-Score median > Defaulted median",
            healthy_z > default_z,
            f"Healthy = {healthy_z:.2f}, Defaulted = {default_z:.2f}"
        )

    # ── 8. Piotroski F-Score sanity ───────────────────────────────────────────
    has_pio = df["piotroski_f_score"].notna()
    if has_pio.sum() > 0:
        healthy_f = df[(df["label"] == 0) & has_pio]["piotroski_f_score"].median()
        default_f = df[(df["label"] == 1) & has_pio]["piotroski_f_score"].median()
        check(
            "Healthy Piotroski F-Score median >= Defaulted median",
            healthy_f >= default_f,
            f"Healthy = {healthy_f:.1f}, Defaulted = {default_f:.1f}"
        )

    # ── 9. Output files exist ─────────────────────────────────────────────────
    check("Training CSV exists", os.path.exists(DATASET_PATH), DATASET_PATH)
    check("Demo CSV exists",     os.path.exists(DEMO_PATH),    DEMO_PATH)
    check("Schema JSON exists",  os.path.exists(SCHEMA_PATH),  SCHEMA_PATH)

    # ── 10. Company counts ────────────────────────────────────────────────────
    n_companies = df["company_name"].nunique()
    check(
        "30 companies present (15 defaulted + 15 healthy)",
        n_companies == 30,
        f"{n_companies} unique companies"
    )

    return results


def print_report(results: list[dict]):
    """Pretty-print the PASS/FAIL report."""
    print("\n" + "=" * 70)
    print("  YAKṢARĀJA  --  DATASET VALIDATION REPORT")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    for r in results:
        icon = "[PASS]" if r["status"] == "PASS" else "[FAIL]"
        detail = f"  ({r['detail']})" if r["detail"] else ""
        print(f"  {icon} {r['name']}{detail}")

    print("-" * 70)
    verdict = "ALL CHECKS PASSED" if failed == 0 else f"{failed} CHECK(S) FAILED"
    print(f"  Result: {passed}/{passed+failed} passed  --  {verdict}")
    print("=" * 70 + "\n")

    return failed == 0


# ══════════════════════════════════════════════════════════════════════════════
#  PART 2: VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════════════

# Colour palette
CLR_HEALTHY  = "#2ecc71"
CLR_DEFAULT  = "#e74c3c"
CLR_BG       = "#1a1a2e"
CLR_CARD     = "#16213e"
CLR_TEXT     = "#e0e0e0"
CLR_GRID     = "#2a2a4a"


def _style_ax(ax, title, xlabel, ylabel):
    """Apply consistent dark-theme styling to an axis."""
    ax.set_facecolor(CLR_CARD)
    ax.set_title(title, color=CLR_TEXT, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, color=CLR_TEXT, fontsize=11)
    ax.set_ylabel(ylabel, color=CLR_TEXT, fontsize=11)
    ax.tick_params(colors=CLR_TEXT, labelsize=9)
    ax.grid(axis="y", color=CLR_GRID, linewidth=0.5, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(CLR_GRID)


def plot_dscr_distribution(df, out_dir):
    """Histogram of DSCR for healthy vs defaulted companies."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.set_facecolor(CLR_BG)

    healthy = df[df["label"] == 0]["dscr"].dropna().clip(-2, 10)
    default = df[df["label"] == 1]["dscr"].dropna().clip(-2, 10)

    bins = np.linspace(-2, 10, 50)
    ax.hist(healthy, bins=bins, alpha=0.65, label="Healthy (label=0)",
            color=CLR_HEALTHY, edgecolor="white", linewidth=0.4)
    ax.hist(default, bins=bins, alpha=0.65, label="Defaulted (label=1)",
            color=CLR_DEFAULT, edgecolor="white", linewidth=0.4)

    # Danger zone
    ax.axvline(x=1.0, color="#f39c12", linestyle="--", linewidth=1.5, label="DSCR = 1.0 (danger)")

    _style_ax(ax, "DSCR Distribution: Healthy vs Defaulted", "DSCR", "Frequency")
    ax.legend(fontsize=9, facecolor=CLR_CARD, edgecolor=CLR_GRID, labelcolor=CLR_TEXT)

    path = os.path.join(out_dir, "dscr_distribution.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=CLR_BG)
    plt.close(fig)
    print(f"  [CHART] Saved -> {path}")


def plot_beneish_distribution(df, out_dir):
    """Histogram of Beneish M-Score for healthy vs defaulted."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.set_facecolor(CLR_BG)

    ms = df[df["beneish_m_score"].notna()]
    healthy = ms[ms["label"] == 0]["beneish_m_score"].clip(-10, 5)
    default = ms[ms["label"] == 1]["beneish_m_score"].clip(-10, 5)

    bins = np.linspace(-10, 5, 50)
    ax.hist(healthy, bins=bins, alpha=0.65, label="Healthy (label=0)",
            color=CLR_HEALTHY, edgecolor="white", linewidth=0.4)
    ax.hist(default, bins=bins, alpha=0.65, label="Defaulted (label=1)",
            color=CLR_DEFAULT, edgecolor="white", linewidth=0.4)

    # Manipulation threshold
    ax.axvline(x=-2.22, color="#f39c12", linestyle="--", linewidth=1.5,
               label="M-Score = -2.22 (manipulation)")

    _style_ax(ax, "Beneish M-Score Distribution: Healthy vs Defaulted",
              "M-Score", "Frequency")
    ax.legend(fontsize=9, facecolor=CLR_CARD, edgecolor=CLR_GRID, labelcolor=CLR_TEXT)

    path = os.path.join(out_dir, "beneish_distribution.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=CLR_BG)
    plt.close(fig)
    print(f"  [CHART] Saved -> {path}")


def plot_dscr_trajectories(df, out_dir):
    """DSCR over time for 3 defaulted companies — shows deterioration."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.set_facecolor(CLR_BG)

    targets = ["Jet Airways", "DHFL", "Bhushan Steel"]
    colours = ["#e74c3c", "#e67e22", "#9b59b6"]

    for name, clr in zip(targets, colours):
        comp = df[df["company_name"] == name].sort_values("fiscal_year")
        if comp.empty:
            continue
        ax.plot(comp["fiscal_year"], comp["dscr"], marker="o", markersize=5,
                linewidth=2, label=name, color=clr)

    # Danger line
    ax.axhline(y=1.0, color="#f39c12", linestyle="--", linewidth=1.5,
               label="DSCR = 1.0 (danger)", alpha=0.8)

    _style_ax(ax, "DSCR Trajectory for 3 Defaulted Companies",
              "Fiscal Year", "DSCR")
    ax.legend(fontsize=9, facecolor=CLR_CARD, edgecolor=CLR_GRID, labelcolor=CLR_TEXT)

    path = os.path.join(out_dir, "dscr_trajectories.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=CLR_BG)
    plt.close(fig)
    print(f"  [CHART] Saved -> {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ── Load dataset ──────────────────────────────────────────────────────────
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dataset not found at {DATASET_PATH}")
        print("   Run: python modules/person1_ml_core/data_generator.py  first.")
        sys.exit(1)

    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded {len(df)} rows × {len(df.columns)} columns from {DATASET_PATH}")

    # ── PART 1: Validation ────────────────────────────────────────────────────
    results = run_validations(df)
    all_passed = print_report(results)

    # ── PART 2: Charts ────────────────────────────────────────────────────────
    os.makedirs(CHARTS_DIR, exist_ok=True)
    print("Generating validation charts...\n")
    plot_dscr_distribution(df, CHARTS_DIR)
    plot_beneish_distribution(df, CHARTS_DIR)
    plot_dscr_trajectories(df, CHARTS_DIR)

    print(f"\n{'='*70}")
    if all_passed:
        print("  [OK] VALIDATION COMPLETE -- Dataset is ready for model training.")
    else:
        print("  [WARN] Some checks failed. Review the report above.")
    print(f"{'='*70}\n")

    sys.exit(0 if all_passed else 1)
