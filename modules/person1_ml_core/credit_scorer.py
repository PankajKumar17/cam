"""
Yakṣarāja - Core ML Credit Scoring Engine
================================================
Three-model ensemble (XGBoost + LightGBM + Random Forest) with
SMOTE oversampling, temporal train/test split, SHAP explanations,
model disagreement signal, and three-output credit decisions.

Reference: Addo et al. 2018 — "Credit risk analysis using machine and
deep learning models"

Usage:
    python modules/person1_ml_core/credit_scorer.py

Output:
    models/xgb_model.pkl
    models/rf_model.pkl
    models/lgb_model.pkl
    models/scaler.pkl
    Console: AUC, RMSE, classification report
"""

import os
import sys
import warnings
import pickle

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    mean_squared_error,
    classification_report,
)
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings("ignore")

# ── PATHS ────────────────────────────────────────────────────────────────────

FEATURE_MATRIX_PATH = "data/processed/feature_matrix.csv"
MODELS_DIR = "models"

# Columns to drop before training (identifiers, targets, non-numeric)
DROP_COLS = [
    "company_name", "sector", "fiscal_year", "label", "years_to_default",
    "satellite_activity_category", "altman_zone", "closest_default_archetype",
]


# ============================================================================
#  PART A — DATA PREPARATION
# ============================================================================

def prepare_data(df: pd.DataFrame) -> dict:
    """
    Prepare data for model training with temporal split and SMOTE.

    1. Temporal split: train on FY2009-2020, test on FY2021-2024
    2. Drop non-numeric / identifier columns
    3. Apply SMOTE to handle class imbalance (sampling_strategy=0.5)
    4. Scale features with StandardScaler

    Parameters
    ----------
    df : pd.DataFrame
        Full feature matrix with 'label' and 'fiscal_year' columns.

    Returns
    -------
    dict
        Keys: X_train, X_test, y_train, y_test, feature_names, scaler,
              X_train_raw (pre-scaled, for SHAP), df_test (original rows)
    """
    # ---- Temporal split (prevents data leakage) ----------------------------
    # Use 2017 as cutoff so test set has enough defaults for meaningful AUC.
    # Most defaults in the dataset happen between 2012-2021, so a 2017 cutoff
    # gives ~55 default rows in the test set.
    SPLIT_YEAR = 2017
    train_mask = df["fiscal_year"] <= SPLIT_YEAR
    test_mask = df["fiscal_year"] > SPLIT_YEAR

    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()

    print(f"  Temporal split: train FY<={SPLIT_YEAR} ({len(df_train)} rows), "
          f"test FY>{SPLIT_YEAR} ({len(df_test)} rows)")
    print(f"  Train default rate: {df_train['label'].mean():.1%}")
    print(f"  Test  default rate: {df_test['label'].mean():.1%}")

    # ---- Feature selection (drop identifiers + target) ---------------------
    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    X_train = df_train[feature_cols].copy()
    y_train = df_train["label"].copy()
    X_test = df_test[feature_cols].copy()
    y_test = df_test["label"].copy()

    # Fill remaining NaNs with 0 (velocity features have NaN for first year)
    X_train = X_train.fillna(0)
    X_test = X_test.fillna(0)

    # Replace inf/-inf with large finite values
    X_train = X_train.replace([np.inf, -np.inf], 0)
    X_test = X_test.replace([np.inf, -np.inf], 0)

    print(f"  Features: {len(feature_cols)} columns")

    # ---- SMOTE oversampling ------------------------------------------------
    # Only apply SMOTE if minority class is < 50% of majority.
    # If classes are already close to balanced, skip to avoid ValueError.
    n_minority = int(y_train.sum())
    n_majority = len(y_train) - n_minority
    if n_minority < int(n_majority * 0.5):
        smote = SMOTE(sampling_strategy=0.5, random_state=42)
        X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
        print(f"  SMOTE: {len(X_train)} -> {len(X_train_smote)} training rows")
    else:
        X_train_smote, y_train_smote = X_train, y_train
        print(f"  SMOTE: skipped (minority already {n_minority}/{n_majority} = "
              f"{n_minority/n_majority:.0%} of majority)")
    print(f"  Post-SMOTE default rate: {y_train_smote.mean():.1%}")

    # ---- StandardScaler ----------------------------------------------------
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train_smote),
        columns=feature_cols,
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=feature_cols,
    )

    # Save scaler
    os.makedirs(MODELS_DIR, exist_ok=True)
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  Scaler saved -> {scaler_path}")

    return {
        "X_train": X_train_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train_smote,
        "y_test": y_test,
        "feature_names": feature_cols,
        "scaler": scaler,
        "X_train_raw": X_train_smote,   # unscaled, for tree-based SHAP
        "df_test": df_test,
    }


# ============================================================================
#  PART B — THREE MODELS
# ============================================================================

def train_xgboost(data: dict) -> xgb.XGBClassifier:
    """
    Train XGBoost classifier (primary model) with early stopping.

    Uses AUC as eval metric. Validated by Addo et al. 2018.
    """
    # Hold out 20% of training data for early stopping
    X_tr, X_val, y_tr, y_val = train_test_split(
        data["X_train"], data["y_train"],
        test_size=0.2, random_state=42, stratify=data["y_train"],
    )

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="auc",
        use_label_encoder=False,
        random_state=42,
        early_stopping_rounds=30,
    )
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    print(f"  XGBoost: trained ({model.best_iteration} rounds, "
          f"best AUC on val)")
    return model


def train_random_forest(data: dict) -> RandomForestClassifier:
    """
    Train Random Forest classifier (secondary model).
    """
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(data["X_train"], data["y_train"])
    print("  Random Forest: trained (200 trees)")
    return model


def train_lightgbm(data: dict) -> lgb.LGBMClassifier:
    """
    Train LightGBM classifier (tertiary model).
    """
    model = lgb.LGBMClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        verbose=-1,
    )
    model.fit(data["X_train"], data["y_train"])
    print("  LightGBM: trained (300 rounds)")
    return model


def save_models(xgb_model, rf_model, lgb_model):
    """Save all three models to disk."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    paths = {}
    for name, model in [("xgb_model", xgb_model),
                         ("rf_model", rf_model),
                         ("lgb_model", lgb_model)]:
        path = os.path.join(MODELS_DIR, f"{name}.pkl")
        with open(path, "wb") as f:
            pickle.dump(model, f)
        paths[name] = path
    return paths


# ============================================================================
#  PART C — ENSEMBLE + DISAGREEMENT SIGNAL
# ============================================================================

def ensemble_predict(xgb_model, rf_model, lgb_model,
                     X: pd.DataFrame) -> pd.DataFrame:
    """
    Weighted ensemble prediction with model disagreement flag.

    Weights: XGBoost 50%, LightGBM 30%, Random Forest 20%
    (XGBoost primary as validated by Addo et al. 2018)

    Parameters
    ----------
    X : pd.DataFrame
        Scaled feature matrix.

    Returns
    -------
    pd.DataFrame
        Columns: pd_xgb, pd_rf, pd_lgb, pd_ensemble,
                 model_disagreement, model_disagreement_flag
    """
    pd_xgb = xgb_model.predict_proba(X)[:, 1]
    pd_rf = rf_model.predict_proba(X)[:, 1]
    pd_lgb = lgb_model.predict_proba(X)[:, 1]

    # Weighted ensemble
    pd_ensemble = 0.5 * pd_xgb + 0.3 * pd_lgb + 0.2 * pd_rf

    # Model disagreement
    pd_stack = np.column_stack([pd_xgb, pd_rf, pd_lgb])
    disagreement = pd_stack.max(axis=1) - pd_stack.min(axis=1)

    # Disagreement flag
    flags = np.where(
        disagreement > 0.30, "HIGH_UNCERTAINTY",
        np.where(disagreement > 0.15, "MODERATE_UNCERTAINTY", "CONSENSUS")
    )

    return pd.DataFrame({
        "pd_xgb": pd_xgb,
        "pd_rf": pd_rf,
        "pd_lgb": pd_lgb,
        "pd_ensemble": pd_ensemble,
        "model_disagreement": disagreement,
        "model_disagreement_flag": flags,
    })


# ============================================================================
#  PART D — THREE OUTPUTS (Decision, Limit, Premium)
# ============================================================================

def compute_credit_outputs(ensemble_df: pd.DataFrame,
                           raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute lending decision, credit limit, and risk premium.

    Parameters
    ----------
    ensemble_df : pd.DataFrame
        Output from ensemble_predict (contains pd_ensemble).
    raw_df : pd.DataFrame
        Original data rows (contains revenue, dscr for limit calc).

    Returns
    -------
    pd.DataFrame
        ensemble_df with added columns: lending_decision,
        credit_limit_cr, risk_premium_pct
    """
    pd_score = ensemble_df["pd_ensemble"].values

    # ---- 1. Lending decision -----------------------------------------------
    ensemble_df["lending_decision"] = np.where(
        pd_score < 0.35, "APPROVE",
        np.where(pd_score < 0.60, "REVIEW", "REJECT")
    )

    # ---- 2. Credit limit (Crores) ------------------------------------------
    revenue = raw_df["revenue"].values if "revenue" in raw_df.columns else np.ones(len(pd_score)) * 1000
    dscr = raw_df["dscr"].values if "dscr" in raw_df.columns else np.ones(len(pd_score)) * 1.5

    base_limit = revenue * 0.25  # working capital heuristic
    dscr_factor = np.clip(dscr / 1.5, 0.3, 2.0)  # scale by DSCR health
    credit_limit = base_limit * (1 - pd_score) * dscr_factor
    credit_limit = np.maximum(credit_limit, 0)  # floor at 0

    ensemble_df["credit_limit_cr"] = np.round(credit_limit, 2)

    # ---- 3. Risk premium (%) -----------------------------------------------
    base_spread = 2.5   # above repo rate
    pd_adjustment = pd_score * 8.0   # higher PD = higher spread
    ensemble_df["risk_premium_pct"] = np.round(base_spread + pd_adjustment, 2)

    return ensemble_df


# ============================================================================
#  PART E — EVALUATION
# ============================================================================

def evaluate_models(xgb_model, rf_model, lgb_model, data: dict) -> dict:
    """
    Evaluate ensemble on test set. Print AUC, RMSE, classification report.

    Returns
    -------
    dict
        Metrics: auc, rmse, classification_report_text, per-model AUCs.
    """
    X_test = data["X_test"]
    y_test = data["y_test"].values

    # Ensemble predictions
    ens = ensemble_predict(xgb_model, rf_model, lgb_model, X_test)
    pd_ensemble = ens["pd_ensemble"].values

    # Binary predictions at 0.5 threshold
    y_pred_binary = (pd_ensemble >= 0.5).astype(int)

    # AUC
    auc = roc_auc_score(y_test, pd_ensemble)
    auc_xgb = roc_auc_score(y_test, ens["pd_xgb"])
    auc_rf = roc_auc_score(y_test, ens["pd_rf"])
    auc_lgb = roc_auc_score(y_test, ens["pd_lgb"])

    # RMSE (as recommended by Addo et al.)
    rmse = np.sqrt(mean_squared_error(y_test, pd_ensemble))

    # Classification report
    report = classification_report(
        y_test, y_pred_binary,
        target_names=["Healthy", "Default"],
        digits=3,
    )

    # Disagreement stats
    ens_with_outputs = compute_credit_outputs(ens, data["df_test"].reset_index(drop=True))
    flag_counts = ens_with_outputs["model_disagreement_flag"].value_counts().to_dict()

    print(f"\n{'=' * 60}")
    print("  MODEL EVALUATION RESULTS")
    print(f"{'=' * 60}")
    print(f"  Ensemble AUC:   {auc:.4f}")
    print(f"  XGBoost AUC:    {auc_xgb:.4f}")
    print(f"  LightGBM AUC:   {auc_lgb:.4f}")
    print(f"  Random Forest:  {auc_rf:.4f}")
    print(f"  Ensemble RMSE:  {rmse:.4f}")
    print(f"\n  Disagreement flags: {flag_counts}")
    print(f"\n{report}")
    print(f"{'=' * 60}")

    return {
        "auc_ensemble": auc,
        "auc_xgb": auc_xgb,
        "auc_rf": auc_rf,
        "auc_lgb": auc_lgb,
        "rmse": rmse,
        "classification_report": report,
        "disagreement_flags": flag_counts,
    }


# ============================================================================
#  PART F — SHAP EXPLANATIONS
# ============================================================================

def explain_prediction(company_name: str, fiscal_year: int,
                       df: pd.DataFrame = None,
                       xgb_model=None, scaler=None) -> dict:
    """
    Generate SHAP explanation for a single prediction.

    Shows top 10 features driving the credit decision, with a
    SHAP waterfall chart saved to models/shap_[company]_[year].png.

    Parameters
    ----------
    company_name : str
    fiscal_year : int
    df : pd.DataFrame, optional
        Full feature matrix. Loaded from disk if not provided.
    xgb_model : XGBClassifier, optional
        Loaded from disk if not provided.
    scaler : StandardScaler, optional
        Loaded from disk if not provided.

    Returns
    -------
    dict
        Keys: company_name, fiscal_year, pd_score,
              top_features (list of {feature, shap_value, feature_value}),
              shap_chart_path
    """
    import shap

    # Load if not provided
    if df is None:
        df = pd.read_csv(FEATURE_MATRIX_PATH)
    if xgb_model is None:
        with open(os.path.join(MODELS_DIR, "xgb_model.pkl"), "rb") as f:
            xgb_model = pickle.load(f)
    if scaler is None:
        with open(os.path.join(MODELS_DIR, "scaler.pkl"), "rb") as f:
            scaler = pickle.load(f)

    # Find the row
    row_mask = (df["company_name"] == company_name) & (df["fiscal_year"] == fiscal_year)
    if row_mask.sum() == 0:
        return {"error": f"No data found for {company_name} FY{fiscal_year}"}

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    X_row = df.loc[row_mask, feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
    X_scaled = pd.DataFrame(scaler.transform(X_row), columns=feature_cols)

    # SHAP TreeExplainer (fast for XGBoost)
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_scaled)

    # Get the prediction
    pd_score = xgb_model.predict_proba(X_scaled)[0, 1]

    # Top 10 features by absolute SHAP value
    shap_vals = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
    abs_shap = np.abs(shap_vals)
    top_idx = abs_shap.argsort()[-10:][::-1]

    top_features = []
    for idx in top_idx:
        top_features.append({
            "feature": feature_cols[idx],
            "shap_value": round(float(shap_vals[idx]), 4),
            "feature_value": round(float(X_row.iloc[0, idx]), 4),
        })

    # Save waterfall chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_path = os.path.join(
        MODELS_DIR,
        f"shap_{company_name.replace(' ', '_')}_{fiscal_year}.png"
    )
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        shap_exp = shap.Explanation(
            values=shap_vals,
            base_values=explainer.expected_value if np.isscalar(explainer.expected_value)
                        else explainer.expected_value[1],
            data=X_scaled.iloc[0].values,
            feature_names=feature_cols,
        )
        shap.plots.waterfall(shap_exp, max_display=10, show=False)
        plt.tight_layout()
        plt.savefig(chart_path, dpi=120, bbox_inches="tight")
        plt.close()
    except Exception as e:
        chart_path = f"(chart generation failed: {e})"

    return {
        "company_name": company_name,
        "fiscal_year": fiscal_year,
        "pd_score": round(float(pd_score), 4),
        "top_features": top_features,
        "shap_chart_path": chart_path,
    }


# ============================================================================
#  PREDICT FUNCTION (for inference on single rows)
# ============================================================================

def predict(feature_row: pd.Series,
            xgb_model=None, rf_model=None, lgb_model=None,
            scaler=None) -> dict:
    """
    Run full prediction pipeline on a single feature row.

    Returns PD score, credit limit, risk premium, lending decision,
    disagreement flag, and SHAP top features.

    Parameters
    ----------
    feature_row : pd.Series
        One row from the feature matrix.

    Returns
    -------
    dict
        Keys: pd_score, lending_decision, credit_limit_cr,
              risk_premium_pct, model_disagreement_flag,
              pd_xgb, pd_rf, pd_lgb, top_features
    """
    # Load models if not provided
    if xgb_model is None:
        with open(os.path.join(MODELS_DIR, "xgb_model.pkl"), "rb") as f:
            xgb_model = pickle.load(f)
    if rf_model is None:
        with open(os.path.join(MODELS_DIR, "rf_model.pkl"), "rb") as f:
            rf_model = pickle.load(f)
    if lgb_model is None:
        with open(os.path.join(MODELS_DIR, "lgb_model.pkl"), "rb") as f:
            lgb_model = pickle.load(f)
    if scaler is None:
        with open(os.path.join(MODELS_DIR, "scaler.pkl"), "rb") as f:
            scaler = pickle.load(f)

    # Prepare single row — filter to scalar numeric columns only
    # (list-valued columns like dscr_history/fiscal_years cause numpy shape errors)
    feature_cols = [
        c for c in feature_row.index
        if c not in DROP_COLS and not isinstance(feature_row[c], (list, dict, np.ndarray))
    ]
    X_raw = feature_row[feature_cols].values.reshape(1, -1)
    X_raw = np.nan_to_num(X_raw, nan=0.0, posinf=0.0, neginf=0.0)
    X_scaled = scaler.transform(X_raw)
    X_df = pd.DataFrame(X_scaled, columns=feature_cols)

    # Ensemble
    ens = ensemble_predict(xgb_model, rf_model, lgb_model, X_df)

    # Credit outputs
    pd_score = float(ens["pd_ensemble"].iloc[0])
    revenue = float(feature_row.get("revenue", 1000))
    dscr = float(feature_row.get("dscr", 1.5))

    base_limit = revenue * 0.25
    dscr_factor = max(0.3, min(2.0, dscr / 1.5))
    credit_limit = base_limit * (1 - pd_score) * dscr_factor
    risk_premium = 2.5 + pd_score * 8.0

    if pd_score < 0.35:
        decision = "APPROVE"
    elif pd_score < 0.60:
        decision = "REVIEW"
    else:
        decision = "REJECT"

    # Quick SHAP (top 5 for single-row speed)
    import shap
    explainer = shap.TreeExplainer(xgb_model)
    shap_vals = explainer.shap_values(X_df)
    sv = shap_vals[0] if isinstance(shap_vals, list) else shap_vals[0]
    top_idx = np.abs(sv).argsort()[-5:][::-1]
    top_features = [
        {"feature": feature_cols[i], "shap_value": round(float(sv[i]), 4)}
        for i in top_idx
    ]

    return {
        "pd_score": round(pd_score, 4),
        "lending_decision": decision,
        "credit_limit_cr": round(max(0.0, credit_limit), 2),
        "risk_premium_pct": round(risk_premium, 2),
        "model_disagreement_flag": ens["model_disagreement_flag"].iloc[0],
        "model_disagreement": round(float(ens["model_disagreement"].iloc[0]), 4),
        "pd_xgb": round(float(ens["pd_xgb"].iloc[0]), 4),
        "pd_rf": round(float(ens["pd_rf"].iloc[0]), 4),
        "pd_lgb": round(float(ens["pd_lgb"].iloc[0]), 4),
        "top_features": top_features,
    }


# ============================================================================
#  MASTER TRAINING FUNCTION
# ============================================================================

def train_and_evaluate() -> dict:
    """
    End-to-end training and evaluation pipeline.

    1. Load feature matrix
    2. Prepare data (temporal split, SMOTE, scale)
    3. Train XGBoost, Random Forest, LightGBM
    4. Ensemble with disagreement signal
    5. Evaluate (AUC, RMSE, classification report)
    6. Save all models
    7. Generate SHAP for one example

    Returns
    -------
    dict
        All evaluation metrics.
    """
    print("=" * 60)
    print("  Yakṣarāja -- Credit Scoring Engine")
    print("=" * 60)

    # ---- 1. Load -----------------------------------------------------------
    print(f"\n[1/6] Loading feature matrix from {FEATURE_MATRIX_PATH} ...")
    df = pd.read_csv(FEATURE_MATRIX_PATH)
    print(f"      {len(df)} rows x {len(df.columns)} columns")

    # ---- 2. Data preparation -----------------------------------------------
    print("\n[2/6] Preparing data (temporal split + SMOTE + scaling) ...")
    data = prepare_data(df)

    # ---- 3. Train models ---------------------------------------------------
    print("\n[3/6] Training three models ...")
    xgb_model = train_xgboost(data)
    rf_model = train_random_forest(data)
    lgb_model = train_lightgbm(data)

    # ---- 4. Save models ----------------------------------------------------
    print("\n[4/6] Saving models ...")
    paths = save_models(xgb_model, rf_model, lgb_model)
    for name, path in paths.items():
        print(f"  {name} -> {path}")

    # ---- 5. Evaluate -------------------------------------------------------
    print("\n[5/6] Evaluating on test set (FY2021-2024) ...")
    metrics = evaluate_models(xgb_model, rf_model, lgb_model, data)

    # ---- 6. SHAP example ---------------------------------------------------
    print("\n[6/6] Generating SHAP explanation (Jet Airways, last year) ...")
    # Pick a defaulted company for SHAP demo
    shap_result = explain_prediction("Jet Airways", 2019, df, xgb_model, data["scaler"])
    if "error" not in shap_result:
        print(f"  PD Score: {shap_result['pd_score']}")
        print(f"  Top 3 drivers:")
        for feat in shap_result["top_features"][:3]:
            direction = "increases" if feat["shap_value"] > 0 else "decreases"
            print(f"    {feat['feature']}: SHAP={feat['shap_value']:+.4f} ({direction} default risk)")
        print(f"  Chart: {shap_result['shap_chart_path']}")
    else:
        print(f"  {shap_result['error']}")

    metrics["shap_example"] = shap_result

    print(f"\n{'=' * 60}")
    print(f"  TRAINING COMPLETE")
    print(f"  Ensemble AUC = {metrics['auc_ensemble']:.4f}   RMSE = {metrics['rmse']:.4f}")
    print(f"{'=' * 60}\n")

    return metrics


# ============================================================================
#  ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if not os.path.exists(FEATURE_MATRIX_PATH):
        print(f"[ERROR] Feature matrix not found: {FEATURE_MATRIX_PATH}")
        print("  Run:  python modules/person1_ml_core/feature_engineering.py  first")
        sys.exit(1)

    metrics = train_and_evaluate()
