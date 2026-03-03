"""
Yakṣarāja - Temporal Trajectory Model (LSTM)
===================================================
Predicts default probability from 5-year financial trajectories.
A company with DSCR falling consistently is far riskier than
one with a stable-but-low DSCR — this model captures that.

Usage:
    python modules/person1_ml_core/temporal_model.py

Output:
    models/lstm_trajectory_model.pt
    data/processed/trajectory_sunrise_textile.png

API:
    train_lstm()                               -> dict (loss history, AUC)
    get_trajectory_score(company_name, data)    -> dict (risk, months, level)
    plot_trajectory(company_name, data)         -> saves chart
"""

import os
import sys
import warnings

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ── CONSTANTS ────────────────────────────────────────────────────────────────

FEATURE_MATRIX_PATH = "data/processed/feature_matrix.csv"
MODEL_PATH = "models/lstm_trajectory_model.pt"

# 7 time-series features per timestep (most predictive for trajectory)
SEQ_FEATURES = [
    "dscr",
    "interest_coverage",
    "debt_to_equity",
    "ebitda_margin",
    "net_margin",
    "cfo_to_assets",
    "revenue_growth",
]

SEQ_LEN = 5       # 5-year look-back window
HORIZON = 2       # predict default within 2 years
HIDDEN = 64       # LSTM hidden size
NUM_LAYERS = 2    # stacked LSTM layers
DROPOUT = 0.3
EPOCHS = 50
BATCH_SIZE = 32
LR = 1e-3


# ============================================================================
#  PART A — SEQUENCE PREPARATION
# ============================================================================

def build_sequences(df: pd.DataFrame) -> tuple:
    """
    Build fixed-length (SEQ_LEN) time-series windows for each company.

    For a company with years [2009..2018] and SEQ_LEN=5:
      window 1: [2009-2013] -> label = defaulted by 2015?
      window 2: [2010-2014] -> label = defaulted by 2016?
      ...

    Label = 1 if the company defaulted within HORIZON years of window end.

    Parameters
    ----------
    df : pd.DataFrame
        Feature matrix with company_name, fiscal_year, label, years_to_default.

    Returns
    -------
    tuple (sequences, labels, company_names_for_seqs)
        sequences: np.ndarray (N, SEQ_LEN, n_features)
        labels: np.ndarray (N,)
        company_names_for_seqs: list of company names per sequence
    """
    df = df.sort_values(["company_name", "fiscal_year"]).reset_index(drop=True)

    all_seqs = []
    all_labels = []
    all_companies = []

    for company_name, group in df.groupby("company_name"):
        group = group.sort_values("fiscal_year").reset_index(drop=True)

        if len(group) < SEQ_LEN:
            continue  # not enough history

        # Extract feature values (fill NaN with 0)
        feat_matrix = group[SEQ_FEATURES].fillna(0).values

        # Default year for this company (None if healthy)
        is_defaulted = group["label"].max() == 1
        if is_defaulted:
            default_year = group.loc[
                group["years_to_default"] == group["years_to_default"].min(),
                "fiscal_year"
            ].max()
        else:
            default_year = None

        # Slide windows
        for start in range(len(group) - SEQ_LEN + 1):
            seq = feat_matrix[start : start + SEQ_LEN]
            end_year = group.iloc[start + SEQ_LEN - 1]["fiscal_year"]

            # Label: 1 if default happens within HORIZON years of window end
            if default_year is not None and 0 <= (default_year - end_year) <= HORIZON:
                label = 1
            else:
                label = 0

            # Clip extreme values for numerical stability
            seq = np.clip(seq, -50, 50)

            all_seqs.append(seq)
            all_labels.append(label)
            all_companies.append(company_name)

    return (
        np.array(all_seqs, dtype=np.float32),
        np.array(all_labels, dtype=np.float32),
        all_companies,
    )


def split_by_company(sequences, labels, companies, test_ratio=0.2):
    """
    Split sequences into train/test BY COMPANY (not by row) to prevent leakage.

    Parameters
    ----------
    sequences : np.ndarray (N, SEQ_LEN, n_features)
    labels : np.ndarray (N,)
    companies : list of str
    test_ratio : float

    Returns
    -------
    dict with X_train, X_test, y_train, y_test
    """
    unique_companies = list(set(companies))
    np.random.seed(42)
    np.random.shuffle(unique_companies)

    split_idx = int(len(unique_companies) * (1 - test_ratio))
    train_companies = set(unique_companies[:split_idx])
    test_companies = set(unique_companies[split_idx:])

    train_mask = np.array([c in train_companies for c in companies])
    test_mask = np.array([c in test_companies for c in companies])

    return {
        "X_train": sequences[train_mask],
        "y_train": labels[train_mask],
        "X_test": sequences[test_mask],
        "y_test": labels[test_mask],
        "train_companies": train_companies,
        "test_companies": test_companies,
    }


# ============================================================================
#  PART B — LSTM MODEL
# ============================================================================

class TrajectoryLSTM(nn.Module):
    """
    2-layer LSTM for default trajectory prediction.

    Architecture:
        Input:  (batch, 5 timesteps, 7 features)
        LSTM:   hidden=64, layers=2, dropout=0.3
        FC:     64 -> 32 -> 1
        Output: sigmoid probability of default within 2 years
    """
    def __init__(self, input_size=7, hidden_size=HIDDEN,
                 num_layers=NUM_LAYERS, dropout=DROPOUT):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        # x: (batch, seq_len, features)
        lstm_out, (h_n, _) = self.lstm(x)
        # Use last hidden state from final layer
        last_hidden = h_n[-1]  # (batch, hidden_size)
        logit = self.fc(last_hidden)  # (batch, 1)
        return logit.squeeze(-1)


def train_lstm(df: pd.DataFrame = None) -> dict:
    """
    Train the LSTM trajectory model end-to-end.

    1. Build sequences from feature matrix
    2. Split by company (80/20)
    3. Train for 50 epochs with BCEWithLogitsLoss + Adam
    4. Compute test AUC
    5. Save model

    Parameters
    ----------
    df : pd.DataFrame, optional
        Feature matrix. Loaded from disk if not provided.

    Returns
    -------
    dict
        Keys: loss_history, auc, test_default_rate, n_train, n_test
    """
    if df is None:
        df = pd.read_csv(FEATURE_MATRIX_PATH)

    print("=" * 60)
    print("  Yakṣarāja -- LSTM Trajectory Model")
    print("=" * 60)

    # ---- Build sequences ---------------------------------------------------
    print("\n[1/4] Building 5-year sequences ...")
    sequences, labels, companies = build_sequences(df)
    print(f"      Total sequences: {len(sequences)}")
    print(f"      Default rate: {labels.mean():.1%}")

    # ---- Split by company --------------------------------------------------
    print("[2/4] Splitting by company (80/20) ...")
    data = split_by_company(sequences, labels, companies)
    print(f"      Train: {len(data['X_train'])} seqs "
          f"({data['y_train'].mean():.1%} default)")
    print(f"      Test:  {len(data['X_test'])} seqs "
          f"({data['y_test'].mean():.1%} default)")

    # ---- Tensors and DataLoader --------------------------------------------
    X_train_t = torch.tensor(data["X_train"])
    y_train_t = torch.tensor(data["y_train"])
    X_test_t = torch.tensor(data["X_test"])
    y_test_t = torch.tensor(data["y_test"])

    train_ds = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    # ---- Model, loss, optimizer --------------------------------------------
    print("[3/4] Training LSTM (50 epochs) ...")
    model = TrajectoryLSTM(input_size=len(SEQ_FEATURES))
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    loss_history = []
    best_auc = 0.0

    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(X_batch)

        avg_loss = epoch_loss / len(train_ds)
        loss_history.append(avg_loss)

        # Evaluate every 10 epochs
        if (epoch + 1) % 10 == 0 or epoch == 0:
            model.eval()
            with torch.no_grad():
                test_logits = model(X_test_t)
                test_probs = torch.sigmoid(test_logits).numpy()

            # AUC (handle case where test has only one class)
            try:
                auc = roc_auc_score(data["y_test"], test_probs)
            except ValueError:
                auc = 0.5  # undefined if single class

            if auc > best_auc:
                best_auc = auc

            print(f"    Epoch {epoch+1:3d}/{EPOCHS}  "
                  f"loss={avg_loss:.4f}  test_AUC={auc:.4f}")

    # ---- Save model --------------------------------------------------------
    print(f"\n[4/4] Saving model ...")
    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    torch.save({
        "model_state_dict": model.state_dict(),
        "input_size": len(SEQ_FEATURES),
        "hidden_size": HIDDEN,
        "num_layers": NUM_LAYERS,
        "seq_features": SEQ_FEATURES,
        "seq_len": SEQ_LEN,
    }, MODEL_PATH)
    print(f"      Saved -> {MODEL_PATH}")

    # ---- Final eval --------------------------------------------------------
    model.eval()
    with torch.no_grad():
        test_probs = torch.sigmoid(model(X_test_t)).numpy()
    try:
        final_auc = roc_auc_score(data["y_test"], test_probs)
    except ValueError:
        final_auc = 0.5

    print(f"\n{'=' * 60}")
    print(f"  LSTM TRAINING COMPLETE")
    print(f"  Final AUC = {final_auc:.4f}   Best AUC = {best_auc:.4f}")
    print(f"  Final loss = {loss_history[-1]:.4f}")
    print(f"{'=' * 60}\n")

    return {
        "loss_history": loss_history,
        "auc": final_auc,
        "best_auc": best_auc,
        "test_default_rate": float(data["y_test"].mean()),
        "n_train": len(data["X_train"]),
        "n_test": len(data["X_test"]),
    }


# ============================================================================
#  PART C — EARLY WARNING SCORE
# ============================================================================

def _load_model() -> TrajectoryLSTM:
    """Load trained LSTM from disk."""
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    model = TrajectoryLSTM(
        input_size=checkpoint["input_size"],
        hidden_size=checkpoint["hidden_size"],
        num_layers=checkpoint["num_layers"],
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def get_trajectory_score(company_name: str,
                         data: pd.DataFrame = None) -> dict:
    """
    Compute early-warning trajectory score for a company.

    Uses the last 5 years of data, runs through the LSTM, and
    estimates months to distress based on DSCR velocity.

    Parameters
    ----------
    company_name : str
    data : pd.DataFrame, optional
        Feature matrix. Loaded if not provided.

    Returns
    -------
    dict
        Keys: trajectory_risk_score (0-1),
              estimated_months_to_distress,
              warning_level (GREEN/YELLOW/ORANGE/RED),
              dscr_trend (list of last 5 DSCR values),
              dscr_velocity (annual change rate)
    """
    if data is None:
        data = pd.read_csv(FEATURE_MATRIX_PATH)

    # Get company data sorted by year
    comp = data[data["company_name"] == company_name].sort_values("fiscal_year")
    if len(comp) < SEQ_LEN:
        return {
            "error": f"Need {SEQ_LEN} years of data, got {len(comp)}",
            "trajectory_risk_score": None,
            "warning_level": "UNKNOWN",
        }

    # Take last SEQ_LEN years
    latest = comp.tail(SEQ_LEN)
    seq_values = latest[SEQ_FEATURES].fillna(0).values
    seq_values = np.clip(seq_values, -50, 50).astype(np.float32)

    # Run through model
    model = _load_model()
    with torch.no_grad():
        input_tensor = torch.tensor(seq_values).unsqueeze(0)  # (1, 5, 7)
        logit = model(input_tensor)
        risk_score = float(torch.sigmoid(logit).item())

    # DSCR trajectory analysis
    dscr_values = latest["dscr"].fillna(0).tolist()
    if len(dscr_values) >= 2:
        dscr_velocity = dscr_values[-1] - dscr_values[-2]  # annual change
    else:
        dscr_velocity = 0.0

    # Months to distress (DSCR < 1.0)
    current_dscr = dscr_values[-1]
    if dscr_velocity < 0 and current_dscr > 1.0:
        months = ((current_dscr - 1.0) / abs(dscr_velocity)) * 12
        months = min(months, 120)
    elif current_dscr <= 1.0:
        months = 0  # already in danger
    else:
        months = 999  # improving or stable

    # Warning level
    if risk_score > 0.70 or months < 12:
        level = "RED"
    elif risk_score > 0.45 or months < 24:
        level = "ORANGE"
    elif risk_score > 0.25 or months < 36:
        level = "YELLOW"
    else:
        level = "GREEN"

    return {
        "company_name": company_name,
        "trajectory_risk_score": round(risk_score, 4),
        "estimated_months_to_distress": round(months, 1),
        "warning_level": level,
        "dscr_trend": [round(v, 3) for v in dscr_values],
        "dscr_velocity": round(dscr_velocity, 4),
        "current_dscr": round(current_dscr, 3),
    }


# ============================================================================
#  PART D — VISUALIZATION
# ============================================================================

# Styling constants
CLR_BG   = "#1a1a2e"
CLR_CARD = "#16213e"
CLR_TEXT = "#e0e0e0"
CLR_GRID = "#2a2a4a"


def plot_trajectory(company_name: str, data: pd.DataFrame = None,
                    output_dir: str = "data/processed") -> str:
    """
    Plot DSCR trajectory with trendline and danger-zone crossing estimate.

    Parameters
    ----------
    company_name : str
    data : pd.DataFrame, optional
    output_dir : str

    Returns
    -------
    str
        Path to saved chart.
    """
    if data is None:
        data = pd.read_csv(FEATURE_MATRIX_PATH)

    comp = data[data["company_name"] == company_name].sort_values("fiscal_year")
    if comp.empty:
        print(f"  [WARN] No data for {company_name}")
        return ""

    years = comp["fiscal_year"].values
    dscr = comp["dscr"].fillna(0).values

    # Trendline (linear fit)
    if len(years) >= 2:
        coeffs = np.polyfit(years, dscr, 1)
        trend_line = np.polyval(coeffs, years)
        slope = coeffs[0]

        # Extrapolate: when does trendline cross 1.0?
        if slope < 0 and dscr[-1] > 1.0:
            cross_year = years[-1] + (dscr[-1] - 1.0) / abs(slope)
            months_to_cross = (cross_year - years[-1]) * 12
        elif dscr[-1] <= 1.0:
            cross_year = years[-1]
            months_to_cross = 0
        else:
            cross_year = None
            months_to_cross = None
    else:
        trend_line = dscr
        cross_year = None
        months_to_cross = None

    # ---- Plot ---------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.set_facecolor(CLR_BG)
    ax.set_facecolor(CLR_CARD)

    # DSCR line
    ax.plot(years, dscr, marker="o", markersize=7, linewidth=2.5,
            color="#3498db", label="DSCR (actual)", zorder=5)

    # Trendline
    ax.plot(years, trend_line, linestyle="--", linewidth=1.5,
            color="#e67e22", alpha=0.8, label="Linear trend")

    # Extrapolation to crossing
    if cross_year is not None and months_to_cross is not None and months_to_cross > 0:
        ext_years = np.linspace(years[-1], cross_year, 20)
        ext_dscr = np.polyval(coeffs, ext_years)
        ax.plot(ext_years, ext_dscr, linestyle=":", linewidth=1.5,
                color="#e74c3c", alpha=0.7, label=f"Projected ({months_to_cross:.0f} months to danger)")
        ax.plot(cross_year, 1.0, marker="X", markersize=12, color="#e74c3c",
                zorder=10)

    # Danger zone
    ax.axhline(y=1.0, color="#e74c3c", linestyle="--", linewidth=1.5,
               alpha=0.6, label="DSCR = 1.0 (danger threshold)")
    ax.axhspan(-2, 1.0, alpha=0.08, color="#e74c3c")

    # Annotation
    if months_to_cross is not None:
        if months_to_cross == 0:
            note = "DSCR is BELOW danger threshold"
        elif months_to_cross < 999:
            note = f"Model projects DSCR below 1.0 in {months_to_cross:.0f} months"
        else:
            note = "DSCR trend stable or improving"
        ax.text(0.02, 0.95, note, transform=ax.transAxes,
                fontsize=11, fontweight="bold", color="#e74c3c",
                verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=CLR_CARD,
                          edgecolor="#e74c3c", alpha=0.9))

    # Styling
    ax.set_title(f"DSCR Trajectory: {company_name}",
                 color=CLR_TEXT, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Fiscal Year", color=CLR_TEXT, fontsize=11)
    ax.set_ylabel("Debt Service Coverage Ratio", color=CLR_TEXT, fontsize=11)
    ax.tick_params(colors=CLR_TEXT, labelsize=9)
    ax.grid(axis="both", color=CLR_GRID, linewidth=0.5, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(CLR_GRID)
    ax.legend(fontsize=9, facecolor=CLR_CARD, edgecolor=CLR_GRID,
              labelcolor=CLR_TEXT, loc="upper right")
    ax.set_ylim(bottom=min(-0.5, dscr.min() - 0.5))

    # Save
    os.makedirs(output_dir, exist_ok=True)
    safe_name = company_name.replace(" ", "_")
    path = os.path.join(output_dir, f"trajectory_{safe_name}.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=CLR_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  [CHART] Saved -> {path}")
    return path


# ============================================================================
#  ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if not os.path.exists(FEATURE_MATRIX_PATH):
        print(f"[ERROR] Feature matrix not found: {FEATURE_MATRIX_PATH}")
        print("  Run:  python modules/person1_ml_core/feature_engineering.py  first")
        sys.exit(1)

    # ---- Train LSTM --------------------------------------------------------
    results = train_lstm()

    # ---- Demo: Sunrise Textile Mills trajectory ----------------------------
    print("\n--- Early Warning Demo ---")
    df = pd.read_csv(FEATURE_MATRIX_PATH)

    # Try Sunrise Textile first (demo company), fallback to Jet Airways
    demo_company = "Sunrise Textile Mills"
    if demo_company not in df["company_name"].values:
        demo_company = "Jet Airways"
        print(f"  Sunrise Textile not in main dataset; using {demo_company}")

    score = get_trajectory_score(demo_company, df)
    print(f"\n  Company:              {score.get('company_name', demo_company)}")
    print(f"  Trajectory Risk:      {score.get('trajectory_risk_score', 'N/A')}")
    print(f"  Warning Level:        {score.get('warning_level', 'N/A')}")
    print(f"  Months to Distress:   {score.get('estimated_months_to_distress', 'N/A')}")
    print(f"  DSCR Trend:           {score.get('dscr_trend', [])}")
    print(f"  Current DSCR:         {score.get('current_dscr', 'N/A')}")

    # Plot
    chart_path = plot_trajectory(demo_company, df)
    if chart_path:
        print(f"\n  Trajectory chart -> {chart_path}")
