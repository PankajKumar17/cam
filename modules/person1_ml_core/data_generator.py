"""
Yakṣarāja — Synthetic Dataset Generator
=============================================
Generates realistic Indian corporate financial data for ALL 146 features.
Calibrated from RBI NPA statistics and real Indian company distributions.

IMPORTANT: This dataset is designed to be replaced by real Prowess/Screener data.
           All column names and dtypes exactly match the real dataset schema.

Usage:
    python modules/person1_ml_core/data_generator.py

Output:
    data/synthetic/intelli_credit_dataset.csv  (main training dataset)
    data/synthetic/demo_sunrise_textile.csv    (demo company)
    data/synthetic/schema.json                 (column descriptions)
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime

np.random.seed(42)

# ── COMPANY CONFIGURATIONS ────────────────────────────────────────────────────

DEFAULTED_COMPANIES = [
    {"name": "Jet Airways",        "sector": "Aviation",        "default_year": 2019},
    {"name": "DHFL",               "sector": "NBFC",            "default_year": 2019},
    {"name": "Videocon Industries","sector": "Electronics",     "default_year": 2020},
    {"name": "Reliance Capital",   "sector": "NBFC",            "default_year": 2021},
    {"name": "IL&FS Engineering",  "sector": "Infrastructure",  "default_year": 2018},
    {"name": "Alok Industries",    "sector": "Textiles",        "default_year": 2017},
    {"name": "Lanco Infratech",    "sector": "Infrastructure",  "default_year": 2017},
    {"name": "Suzlon Energy",      "sector": "Energy",          "default_year": 2013},
    {"name": "Sintex Industries",  "sector": "Plastics",        "default_year": 2019},
    {"name": "Bhushan Steel",      "sector": "Steel",           "default_year": 2017},
    {"name": "Essar Steel",        "sector": "Steel",           "default_year": 2017},
    {"name": "Amtek Auto",         "sector": "Auto",            "default_year": 2016},
    {"name": "Kingfisher Airlines","sector": "Aviation",        "default_year": 2012},
    {"name": "Satyam Computer",    "sector": "IT",              "default_year": 2009},
    {"name": "Deccan Chronicle",   "sector": "Media",           "default_year": 2012},
]

HEALTHY_COMPANIES = [
    {"name": "IndiGo Airlines",    "sector": "Aviation"},
    {"name": "Bajaj Finance",      "sector": "NBFC"},
    {"name": "Titan Company",      "sector": "Consumer"},
    {"name": "Asian Paints",       "sector": "Manufacturing"},
    {"name": "Pidilite Industries","sector": "Chemicals"},
    {"name": "Marico",             "sector": "FMCG"},
    {"name": "Page Industries",    "sector": "Textiles"},
    {"name": "Havells India",      "sector": "Electronics"},
    {"name": "TCS",                "sector": "IT"},
    {"name": "Infosys",            "sector": "IT"},
    {"name": "Sun Pharma",         "sector": "Pharma"},
    {"name": "Britannia",          "sector": "FMCG"},
    {"name": "Tata Steel",         "sector": "Steel"},
    {"name": "KEC International",  "sector": "Infrastructure"},
    {"name": "Torrent Power",      "sector": "Energy"},
]

SECTOR_NPA_RATES = {
    "Aviation":       0.18,
    "NBFC":           0.14,
    "Infrastructure": 0.16,
    "Steel":          0.13,
    "Textiles":       0.09,
    "Electronics":    0.08,
    "Energy":         0.11,
    "Auto":           0.07,
    "IT":             0.02,
    "FMCG":           0.02,
    "Pharma":         0.03,
    "Chemicals":      0.04,
    "Manufacturing":  0.05,
    "Consumer":       0.03,
    "Media":          0.09,
    "Plastics":       0.07,
}


# ── CORE GENERATOR FUNCTIONS ──────────────────────────────────────────────────

def generate_healthy_year(company_name, sector, fiscal_year):
    """Generate one year of financial data for a HEALTHY company"""

    # Base revenue (varies by company size)
    base_rev = np.random.uniform(500, 50000)
    growth = np.random.normal(0.14, 0.08)
    revenue = base_rev * (1 + growth)

    # P&L
    ebitda_margin = np.random.normal(0.18, 0.05)
    ebitda = revenue * max(ebitda_margin, 0.05)
    depreciation = revenue * np.random.uniform(0.03, 0.07)
    ebit = ebitda - depreciation
    interest = revenue * np.random.uniform(0.01, 0.04)
    pbt = ebit - interest
    tax = max(pbt * 0.25, 0)
    pat = pbt - tax
    employee_cost = revenue * np.random.uniform(0.05, 0.15)
    sga = revenue * np.random.uniform(0.03, 0.08)
    cogs = revenue * np.random.uniform(0.45, 0.65)
    gross_profit = revenue - cogs

    # Balance Sheet
    total_assets = revenue * np.random.uniform(0.8, 1.5)
    fixed_assets = total_assets * np.random.uniform(0.3, 0.5)
    cwip = total_assets * np.random.uniform(0.01, 0.05)
    inventories = revenue * np.random.uniform(0.05, 0.12)
    trade_receivables = revenue * np.random.uniform(0.08, 0.15)
    cash_equiv = total_assets * np.random.uniform(0.05, 0.15)
    other_current_assets = total_assets * np.random.uniform(0.03, 0.08)
    total_current_assets = inventories + trade_receivables + cash_equiv + other_current_assets
    total_investments = total_assets * np.random.uniform(0.02, 0.08)

    equity_share_capital = total_assets * np.random.uniform(0.02, 0.06)
    reserves_surplus = total_assets * np.random.uniform(0.30, 0.55)
    total_equity = equity_share_capital + reserves_surplus
    lt_borrowings = total_assets * np.random.uniform(0.10, 0.25)
    st_borrowings = total_assets * np.random.uniform(0.05, 0.15)
    total_debt = lt_borrowings + st_borrowings
    trade_payables = revenue * np.random.uniform(0.05, 0.12)
    other_current_liab = total_assets * np.random.uniform(0.03, 0.08)
    total_current_liab = st_borrowings + trade_payables + other_current_liab

    # Cash Flow
    cfo = pat + depreciation - np.random.uniform(-0.02, 0.05) * revenue
    capex = revenue * np.random.uniform(0.03, 0.08)
    cfi = -capex - np.random.uniform(0, 0.03) * total_assets
    cff = np.random.uniform(-0.05, 0.02) * total_assets
    free_cash_flow = cfo - capex

    # Governance
    promoter_holding = np.random.uniform(0.45, 0.75)
    promoter_pledge = np.random.uniform(0.0, 0.12)
    institutional_holding = np.random.uniform(0.15, 0.40)

    return {
        # ── IDENTITY ──────────────────────────────────────────────────────────
        "company_name": company_name,
        "sector": sector,
        "fiscal_year": fiscal_year,
        "label": 0,
        "years_to_default": None,
        "sector_npa_rate": SECTOR_NPA_RATES.get(sector, 0.05),

        # ── P&L ───────────────────────────────────────────────────────────────
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "ebitda": round(ebitda, 2),
        "depreciation": round(depreciation, 2),
        "ebit": round(ebit, 2),
        "interest_expense": round(interest, 2),
        "pbt": round(pbt, 2),
        "tax": round(tax, 2),
        "pat": round(pat, 2),
        "sga_expense": round(sga, 2),
        "employee_cost": round(employee_cost, 2),

        # ── BALANCE SHEET ─────────────────────────────────────────────────────
        "total_assets": round(total_assets, 2),
        "fixed_assets": round(fixed_assets, 2),
        "cwip": round(cwip, 2),
        "total_investments": round(total_investments, 2),
        "trade_receivables": round(trade_receivables, 2),
        "inventories": round(inventories, 2),
        "cash_equivalents": round(cash_equiv, 2),
        "other_current_assets": round(other_current_assets, 2),
        "total_current_assets": round(total_current_assets, 2),
        "equity_share_capital": round(equity_share_capital, 2),
        "reserves_surplus": round(reserves_surplus, 2),
        "total_equity": round(total_equity, 2),
        "lt_borrowings": round(lt_borrowings, 2),
        "st_borrowings": round(st_borrowings, 2),
        "total_debt": round(total_debt, 2),
        "trade_payables": round(trade_payables, 2),
        "other_current_liab": round(other_current_liab, 2),
        "total_current_liab": round(total_current_liab, 2),

        # ── CASH FLOW ─────────────────────────────────────────────────────────
        "cfo": round(cfo, 2),
        "cfi": round(cfi, 2),
        "cff": round(cff, 2),
        "capex": round(abs(capex), 2),
        "free_cash_flow": round(free_cash_flow, 2),

        # ── GOVERNANCE ────────────────────────────────────────────────────────
        "promoter_holding_pct": round(promoter_holding, 4),
        "promoter_pledge_pct": round(promoter_pledge, 4),
        "promoter_pledge_change": round(np.random.normal(0.0, 0.02), 4),
        "institutional_holding_pct": round(institutional_holding, 4),
        "auditor_changes_3yr": np.random.choice([0, 0, 0, 1], p=[0.85, 0.08, 0.05, 0.02]),
        "auditor_big4": np.random.choice([0, 1], p=[0.3, 0.7]),
        "din_disqualified_count": 0,
        "related_party_tx_to_rev": round(np.random.uniform(0.01, 0.08), 4),
        "dividend_payout_ratio": round(np.random.uniform(0.15, 0.45), 4),

        # ── AUDITOR SIGNALS ───────────────────────────────────────────────────
        "going_concern_flag": 0,
        "qualified_opinion_flag": 0,
        "emphasis_matter_flag": np.random.choice([0, 1], p=[0.92, 0.08]),
        "scope_limitation_flag": 0,
        "auditor_resigned_flag": 0,
        "auditor_distress_score": np.random.randint(0, 2),

        # ── NETWORK ───────────────────────────────────────────────────────────
        "promoter_total_companies": np.random.randint(1, 5),
        "promoter_npa_companies": 0,
        "promoter_struck_off_companies": np.random.randint(0, 2),
        "network_npa_ratio": round(np.random.uniform(0.0, 0.05), 4),
        "contagion_risk_score": round(np.random.uniform(0.0, 0.12), 4),
        "customer_concentration": round(np.random.uniform(0.08, 0.25), 4),
        "supplier_concentration": round(np.random.uniform(0.05, 0.20), 4),

        # ── SATELLITE ─────────────────────────────────────────────────────────
        "satellite_activity_score": round(np.random.uniform(65, 95), 2),
        "satellite_activity_category": np.random.choice(
            ["ACTIVE", "ACTIVE", "ACTIVE", "MODERATE"], p=[0.6, 0.2, 0.1, 0.1]
        ),
        "satellite_vs_revenue_flag": 0,

        # ── GST ───────────────────────────────────────────────────────────────
        "gst_vs_bank_divergence": round(np.random.uniform(-0.05, 0.08), 4),
        "gst_divergence_flag": 0,
        "gst_filing_delays_count": np.random.randint(0, 2),
        "ewaybill_volume_consistency": round(np.random.uniform(0.88, 1.05), 4),
        "gst_payment_delay_days": round(np.random.uniform(0, 10), 1),

        # ── CEO INTERVIEW ─────────────────────────────────────────────────────
        "ceo_sentiment_overall": round(np.random.uniform(0.2, 0.7), 4),
        "ceo_sentiment_revenue": round(np.random.uniform(0.3, 0.8), 4),
        "ceo_sentiment_debt": round(np.random.uniform(0.1, 0.5), 4),
        "ceo_deflection_score": round(np.random.uniform(0.0, 0.2), 4),
        "ceo_overconfidence_score": round(np.random.uniform(0.0, 0.15), 4),
        "ceo_specificity_score": round(np.random.uniform(0.6, 0.9), 4),
    }


def generate_distressed_year(company_name, sector, fiscal_year,
                              years_to_default, deterioration_factor):
    """
    Generate one year of financial data for a DEFAULTED company.
    deterioration_factor: 0.0 = early (looks healthy), 1.0 = at default
    """

    # Revenue declining as company deteriorates
    base_rev = np.random.uniform(500, 30000)
    growth = np.random.normal(-0.08, 0.12) * deterioration_factor
    revenue = base_rev * (1 + growth)

    # Margins compressed
    ebitda_margin = np.random.normal(0.18, 0.05) - (0.15 * deterioration_factor)
    ebitda_margin = max(ebitda_margin, -0.05)
    ebitda = revenue * ebitda_margin

    depreciation = revenue * np.random.uniform(0.04, 0.09)
    ebit = ebitda - depreciation
    interest = revenue * (0.03 + 0.08 * deterioration_factor)
    pbt = ebit - interest
    tax = max(pbt * 0.25, 0)
    pat = pbt - tax
    employee_cost = revenue * np.random.uniform(0.08, 0.18)
    sga = revenue * np.random.uniform(0.04, 0.10)
    cogs = revenue * np.random.uniform(0.55, 0.78)
    gross_profit = revenue - cogs

    # Balance sheet — overleveraged
    total_assets = revenue * np.random.uniform(1.2, 3.0)
    fixed_assets = total_assets * np.random.uniform(0.4, 0.6)
    cwip = total_assets * np.random.uniform(0.05, 0.15)
    inventories = revenue * np.random.uniform(0.12, 0.25)
    trade_receivables = revenue * (0.12 + 0.10 * deterioration_factor)  # rising receivables = risk
    cash_equiv = total_assets * max(0.01, np.random.uniform(0.02, 0.08) - 0.05 * deterioration_factor)
    other_current_assets = total_assets * np.random.uniform(0.04, 0.10)
    total_current_assets = inventories + trade_receivables + cash_equiv + other_current_assets
    total_investments = total_assets * np.random.uniform(0.01, 0.05)

    equity_share_capital = total_assets * np.random.uniform(0.01, 0.04)
    reserves_surplus = total_assets * max(0.01, np.random.uniform(0.10, 0.30) - 0.15 * deterioration_factor)
    total_equity = equity_share_capital + reserves_surplus
    lt_borrowings = total_assets * (0.25 + 0.20 * deterioration_factor)
    st_borrowings = total_assets * (0.15 + 0.15 * deterioration_factor)
    total_debt = lt_borrowings + st_borrowings
    trade_payables = revenue * np.random.uniform(0.10, 0.20)
    other_current_liab = total_assets * np.random.uniform(0.05, 0.12)
    total_current_liab = st_borrowings + trade_payables + other_current_liab

    # Cash flow — deteriorating
    cfo = pat + depreciation - (0.05 * deterioration_factor * revenue)
    capex = revenue * np.random.uniform(0.02, 0.06)
    cfi = -capex
    cff = (lt_borrowings * 0.1) - (total_debt * 0.05 * deterioration_factor)
    free_cash_flow = cfo - capex

    # Governance — stress signals
    promoter_holding = np.random.uniform(0.30, 0.60) - (0.10 * deterioration_factor)
    promoter_pledge = min(0.95, np.random.uniform(0.15, 0.40) + (0.40 * deterioration_factor))
    institutional_holding = np.random.uniform(0.05, 0.25)

    return {
        # ── IDENTITY ──────────────────────────────────────────────────────────
        "company_name": company_name,
        "sector": sector,
        "fiscal_year": fiscal_year,
        "label": 1,
        "years_to_default": years_to_default,
        "sector_npa_rate": SECTOR_NPA_RATES.get(sector, 0.05),

        # ── P&L ───────────────────────────────────────────────────────────────
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "ebitda": round(ebitda, 2),
        "depreciation": round(depreciation, 2),
        "ebit": round(ebit, 2),
        "interest_expense": round(interest, 2),
        "pbt": round(pbt, 2),
        "tax": round(tax, 2),
        "pat": round(pat, 2),
        "sga_expense": round(sga, 2),
        "employee_cost": round(employee_cost, 2),

        # ── BALANCE SHEET ─────────────────────────────────────────────────────
        "total_assets": round(total_assets, 2),
        "fixed_assets": round(fixed_assets, 2),
        "cwip": round(cwip, 2),
        "total_investments": round(total_investments, 2),
        "trade_receivables": round(trade_receivables, 2),
        "inventories": round(inventories, 2),
        "cash_equivalents": round(cash_equiv, 2),
        "other_current_assets": round(other_current_assets, 2),
        "total_current_assets": round(total_current_assets, 2),
        "equity_share_capital": round(equity_share_capital, 2),
        "reserves_surplus": round(reserves_surplus, 2),
        "total_equity": round(total_equity, 2),
        "lt_borrowings": round(lt_borrowings, 2),
        "st_borrowings": round(st_borrowings, 2),
        "total_debt": round(total_debt, 2),
        "trade_payables": round(trade_payables, 2),
        "other_current_liab": round(other_current_liab, 2),
        "total_current_liab": round(total_current_liab, 2),

        # ── CASH FLOW ─────────────────────────────────────────────────────────
        "cfo": round(cfo, 2),
        "cfi": round(cfi, 2),
        "cff": round(cff, 2),
        "capex": round(abs(capex), 2),
        "free_cash_flow": round(free_cash_flow, 2),

        # ── GOVERNANCE ────────────────────────────────────────────────────────
        "promoter_holding_pct": round(max(0.1, promoter_holding), 4),
        "promoter_pledge_pct": round(promoter_pledge, 4),
        "promoter_pledge_change": round(np.random.normal(0.05, 0.04) * deterioration_factor, 4),
        "institutional_holding_pct": round(institutional_holding, 4),
        "auditor_changes_3yr": int(np.random.choice([0, 1, 2], p=[0.5, 0.35, 0.15]) * max(1, deterioration_factor)),
        "auditor_big4": np.random.choice([0, 1], p=[0.5, 0.5]),
        "din_disqualified_count": int(np.random.choice([0, 0, 1, 2], p=[0.6, 0.2, 0.15, 0.05])),
        "related_party_tx_to_rev": round(np.random.uniform(0.05, 0.25) * (1 + deterioration_factor), 4),
        "dividend_payout_ratio": round(max(0, np.random.uniform(0.0, 0.15) - 0.10 * deterioration_factor), 4),

        # ── AUDITOR SIGNALS ───────────────────────────────────────────────────
        "going_concern_flag": int(deterioration_factor > 0.7 and np.random.random() > 0.4),
        "qualified_opinion_flag": int(deterioration_factor > 0.6 and np.random.random() > 0.5),
        "emphasis_matter_flag": int(deterioration_factor > 0.4 and np.random.random() > 0.4),
        "scope_limitation_flag": int(deterioration_factor > 0.8 and np.random.random() > 0.5),
        "auditor_resigned_flag": int(deterioration_factor > 0.85 and np.random.random() > 0.6),
        "auditor_distress_score": int(np.random.randint(0, 3) + int(deterioration_factor * 5)),

        # ── NETWORK ───────────────────────────────────────────────────────────
        "promoter_total_companies": np.random.randint(2, 8),
        "promoter_npa_companies": int(np.random.randint(0, 3) * deterioration_factor),
        "promoter_struck_off_companies": np.random.randint(0, 3),
        "network_npa_ratio": round(np.random.uniform(0.1, 0.6) * deterioration_factor, 4),
        "contagion_risk_score": round(min(1.0, np.random.uniform(0.2, 0.5) + 0.4 * deterioration_factor), 4),
        "customer_concentration": round(np.random.uniform(0.35, 0.80), 4),
        "supplier_concentration": round(np.random.uniform(0.25, 0.60), 4),

        # ── SATELLITE ─────────────────────────────────────────────────────────
        "satellite_activity_score": round(max(5, np.random.uniform(70, 95) - 60 * deterioration_factor), 2),
        "satellite_activity_category": (
            "DORMANT" if deterioration_factor > 0.8 else
            "LOW" if deterioration_factor > 0.6 else
            "MODERATE" if deterioration_factor > 0.3 else "ACTIVE"
        ),
        "satellite_vs_revenue_flag": int(deterioration_factor > 0.5),

        # ── GST ───────────────────────────────────────────────────────────────
        "gst_vs_bank_divergence": round(np.random.uniform(0.10, 0.50) * deterioration_factor, 4),
        "gst_divergence_flag": int(deterioration_factor > 0.3),
        "gst_filing_delays_count": int(np.random.randint(0, 3) + int(deterioration_factor * 6)),
        "ewaybill_volume_consistency": round(max(0.1, np.random.uniform(0.5, 1.0) - 0.4 * deterioration_factor), 4),
        "gst_payment_delay_days": round(np.random.uniform(5, 30) * (1 + deterioration_factor), 1),

        # ── CEO INTERVIEW ─────────────────────────────────────────────────────
        "ceo_sentiment_overall": round(max(-0.8, np.random.uniform(0.2, 0.6) - 0.6 * deterioration_factor), 4),
        "ceo_sentiment_revenue": round(max(-0.5, np.random.uniform(0.1, 0.5) - 0.5 * deterioration_factor), 4),
        "ceo_sentiment_debt": round(max(-0.9, np.random.uniform(-0.1, 0.3) - 0.7 * deterioration_factor), 4),
        "ceo_deflection_score": round(min(1.0, np.random.uniform(0.1, 0.3) + 0.5 * deterioration_factor), 4),
        "ceo_overconfidence_score": round(np.random.uniform(0.1, 0.4) * (1 - deterioration_factor * 0.3), 4),
        "ceo_specificity_score": round(max(0.1, np.random.uniform(0.3, 0.7) - 0.4 * deterioration_factor), 4),
    }


# ── COMPUTE DERIVED FEATURES ──────────────────────────────────────────────────

def compute_ratios(df):
    """Compute all financial ratios from raw fields"""
    eps = 1e-6  # avoid division by zero

    # Core Ratios
    df["debt_to_equity"]       = df["total_debt"] / (df["total_equity"] + eps)
    df["debt_to_assets"]       = df["total_debt"] / (df["total_assets"] + eps)
    df["lt_debt_to_assets"]    = df["lt_borrowings"] / (df["total_assets"] + eps)
    df["st_debt_to_assets"]    = df["st_borrowings"] / (df["total_assets"] + eps)
    df["equity_to_assets"]     = df["total_equity"] / (df["total_assets"] + eps)
    df["interest_coverage"]    = df["ebit"] / (df["interest_expense"] + eps)
    df["current_ratio"]        = df["total_current_assets"] / (df["total_current_liab"] + eps)
    df["quick_ratio"]          = (df["total_current_assets"] - df["inventories"]) / (df["total_current_liab"] + eps)
    df["dscr"]                 = (df["pat"] + df["depreciation"]) / (df["total_debt"] * 0.12 + eps)
    df["ebitda_margin"]        = df["ebitda"] / (df["revenue"] + eps)
    df["net_margin"]           = df["pat"] / (df["revenue"] + eps)
    df["gross_margin"]         = df["gross_profit"] / (df["revenue"] + eps)
    df["roe"]                  = df["pat"] / (df["total_equity"] + eps)
    df["roa"]                  = df["pat"] / (df["total_assets"] + eps)
    df["ebitda_to_assets"]     = df["ebitda"] / (df["total_assets"] + eps)
    df["ebitda_to_equity"]     = df["ebitda"] / (df["total_equity"] + eps)
    df["ebitda_to_fin_exp"]    = df["ebitda"] / (df["interest_expense"] + eps)
    df["cfo_to_assets"]        = df["cfo"] / (df["total_assets"] + eps)
    df["cfo_to_equity"]        = df["cfo"] / (df["total_equity"] + eps)
    df["cfo_to_sales"]         = df["cfo"] / (df["revenue"] + eps)
    df["cfo_to_debt"]          = df["cfo"] / (df["total_debt"] + eps)
    df["asset_turnover"]       = df["revenue"] / (df["total_assets"] + eps)
    df["inventory_days"]       = (df["inventories"] / (df["cogs"] + eps)) * 365
    df["receivables_days"]     = (df["trade_receivables"] / (df["revenue"] + eps)) * 365
    df["payables_days"]        = (df["trade_payables"] / (df["cogs"] + eps)) * 365
    df["cash_conversion_cycle"]= df["inventory_days"] + df["receivables_days"] - df["payables_days"]
    df["ln_total_assets"]      = np.log(df["total_assets"].clip(lower=1))
    df["ln_revenue"]           = np.log(df["revenue"].clip(lower=1))
    df["ln_net_income"]        = np.log(df["pat"].abs().clip(lower=1))

    return df


def compute_velocity_features(df):
    """Compute year-on-year change features (most predictive per research paper)"""
    df = df.sort_values(["company_name", "fiscal_year"]).reset_index(drop=True)

    for col in ["revenue", "ebitda", "pat", "cfo", "total_equity",
                "total_debt", "total_assets", "trade_receivables"]:
        df[f"{col}_growth"] = df.groupby("company_name")[col].pct_change()

    # Ratio velocities
    for ratio in ["dscr", "interest_coverage", "debt_to_equity", "net_margin"]:
        df[f"{ratio}_velocity"] = df.groupby("company_name")[ratio].diff()

    # Accelerations
    df["dscr_acceleration"] = df.groupby("company_name")["dscr_velocity"].diff()
    df["debt_acceleration"]  = df.groupby("company_name")["total_debt_growth"].diff()

    # 3-year slope
    def rolling_slope(series):
        if len(series) < 3:
            return np.nan
        x = np.arange(len(series))
        return np.polyfit(x, series, 1)[0] if not series.isna().any() else np.nan

    df["dscr_3yr_slope"] = df.groupby("company_name")["dscr"].transform(
        lambda x: x.rolling(3).apply(rolling_slope, raw=False)
    )

    # Months to DSCR danger zone
    df["months_to_dscr_danger"] = np.where(
        df["dscr_velocity"] < 0,
        ((df["dscr"] - 1.0) / (-df["dscr_velocity"] + 1e-6)) * 12,
        999
    )
    df["months_to_dscr_danger"] = df["months_to_dscr_danger"].clip(-12, 120)

    return df


def compute_beneish_scores(df):
    """Compute all 8 Beneish M-Score components"""
    eps = 1e-6

    # Shift previous year values
    prev = df.groupby("company_name")[
        ["trade_receivables", "revenue", "gross_margin",
         "total_current_assets", "fixed_assets", "total_assets",
         "depreciation", "sga_expense", "total_debt",
         "total_current_liab", "pat", "cfo"]
    ].shift(1)

    df["beneish_dsri"] = (df["trade_receivables"] / (df["revenue"] + eps)) / \
                          (prev["trade_receivables"] / (prev["revenue"] + eps))

    df["beneish_gmi"]  = prev["gross_margin"] / (df["gross_margin"] + eps)

    df["beneish_aqi"]  = (1 - (df["total_current_assets"] + df["fixed_assets"]) / (df["total_assets"] + eps)) / \
                          (1 - (prev["total_current_assets"] + prev["fixed_assets"]) / (prev["total_assets"] + eps) + eps)

    df["beneish_sgi"]  = df["revenue"] / (prev["revenue"] + eps)

    df["beneish_depi"] = (prev["depreciation"] / (prev["depreciation"] + prev["fixed_assets"] + eps)) / \
                          (df["depreciation"] / (df["depreciation"] + df["fixed_assets"] + eps))

    df["beneish_sgai"] = (df["sga_expense"] / (df["revenue"] + eps)) / \
                          (prev["sga_expense"] / (prev["revenue"] + eps))

    df["beneish_lvgi"] = ((df["total_debt"] + df["total_current_liab"]) / (df["total_assets"] + eps)) / \
                          ((prev["total_debt"] + prev["total_current_liab"]) / (prev["total_assets"] + eps) + eps)

    df["beneish_tata"] = (df["pat"] - df["cfo"]) / (df["total_assets"] + eps)

    df["beneish_m_score"] = (
        -4.84
        + 0.920 * df["beneish_dsri"].fillna(1)
        + 0.528 * df["beneish_gmi"].fillna(1)
        + 0.404 * df["beneish_aqi"].fillna(1)
        + 0.892 * df["beneish_sgi"].fillna(1)
        + 0.115 * df["beneish_depi"].fillna(1)
        - 0.172 * df["beneish_sgai"].fillna(1)
        + 4.679 * df["beneish_tata"].fillna(0)
        - 0.327 * df["beneish_lvgi"].fillna(1)
    )

    df["beneish_manipulation_flag"] = (df["beneish_m_score"] > -2.22).astype(int)

    return df


def compute_altman_zscore(df):
    """Compute Altman Z-Score"""
    eps = 1e-6
    working_capital = df["total_current_assets"] - df["total_current_liab"]

    df["altman_x1"] = working_capital / (df["total_assets"] + eps)
    df["altman_x2"] = df["reserves_surplus"] / (df["total_assets"] + eps)
    df["altman_x3"] = df["ebit"] / (df["total_assets"] + eps)
    df["altman_x4"] = df["total_equity"] / (df["total_debt"] + eps)
    df["altman_x5"] = df["revenue"] / (df["total_assets"] + eps)

    df["altman_z_score"] = (
        1.2 * df["altman_x1"] +
        1.4 * df["altman_x2"] +
        3.3 * df["altman_x3"] +
        0.6 * df["altman_x4"] +
        1.0 * df["altman_x5"]
    )

    df["altman_zone"] = pd.cut(
        df["altman_z_score"],
        bins=[-np.inf, 1.81, 2.99, np.inf],
        labels=["DANGER", "GREY", "SAFE"]
    )

    return df


def compute_piotroski(df):
    """Compute Piotroski F-Score (9 components)"""
    prev = df.groupby("company_name")[
        ["roa", "current_ratio", "lt_debt_to_assets", "gross_margin", "asset_turnover"]
    ].shift(1)

    df["piotroski_roa"]       = (df["roa"] > 0).astype(int)
    df["piotroski_cfo"]       = (df["cfo"] > 0).astype(int)
    df["piotroski_roa_change"]= (df["roa"] > prev["roa"]).astype(int)
    df["piotroski_accrual"]   = (df["cfo_to_assets"] > df["roa"]).astype(int)
    df["piotroski_leverage"]  = (df["lt_debt_to_assets"] < prev["lt_debt_to_assets"]).astype(int)
    df["piotroski_liquidity"] = (df["current_ratio"] > prev["current_ratio"]).astype(int)
    df["piotroski_shares"]    = (df["equity_share_capital"] <= df.groupby("company_name")["equity_share_capital"].shift(1)).astype(int)
    df["piotroski_margin"]    = (df["gross_margin"] > prev["gross_margin"]).astype(int)
    df["piotroski_turnover"]  = (df["asset_turnover"] > prev["asset_turnover"]).astype(int)

    df["piotroski_f_score"] = (
        df["piotroski_roa"] + df["piotroski_cfo"] + df["piotroski_roa_change"] +
        df["piotroski_accrual"] + df["piotroski_leverage"] + df["piotroski_liquidity"] +
        df["piotroski_shares"] + df["piotroski_margin"] + df["piotroski_turnover"]
    )

    return df


# ── MAIN DATASET BUILDER ──────────────────────────────────────────────────────

def build_dataset():
    """Build the complete synthetic dataset"""

    print("=" * 60)
    print("Yakṣarāja Synthetic Dataset Generator")
    print("=" * 60)

    all_rows = []

    # Generate defaulted company data
    print("\n[1/2] Generating DEFAULTED company data...")
    for company in DEFAULTED_COMPANIES:
        default_yr = company["default_year"]
        start_yr = max(2009, default_yr - 8)

        for yr in range(start_yr, default_yr + 1):
            years_before = default_yr - yr
            # deterioration_factor: 0 far from default, 1 at default
            deterioration = max(0.0, min(1.0, 1.0 - (years_before / 6.0)))

            row = generate_distressed_year(
                company["name"], company["sector"],
                yr, years_before, deterioration
            )
            all_rows.append(row)

        print(f"  ✓ {company['name']}: {default_yr - start_yr + 1} years")

    # Generate healthy company data
    print("\n[2/2] Generating HEALTHY company data...")
    for company in HEALTHY_COMPANIES:
        for yr in range(2009, 2025):
            row = generate_healthy_year(company["name"], company["sector"], yr)
            all_rows.append(row)
        print(f"  ✓ {company['name']}: 15 years")

    # Build DataFrame
    df = pd.DataFrame(all_rows)
    print(f"\nRaw dataset: {len(df)} rows, {len(df.columns)} columns")

    # Compute derived features
    print("\nComputing derived features...")
    df = compute_ratios(df)
    df = compute_velocity_features(df)
    df = compute_beneish_scores(df)
    df = compute_altman_zscore(df)
    df = compute_piotroski(df)

    print(f"Final dataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"Default rate: {df['label'].mean():.1%}")
    print(f"Companies: {df['company_name'].nunique()}")
    print(f"Years: {df['fiscal_year'].min()} – {df['fiscal_year'].max()}")

    return df


def build_demo_company():
    """Build the demo company: Sunrise Textile Mills"""
    print("\nGenerating demo company: Sunrise Textile Mills...")

    rows = []
    for yr in range(2016, 2025):
        years_before_demo_default = 2024 - yr
        # Starts healthy, gradually deteriorates
        deterioration = max(0.0, min(1.0, (yr - 2018) / 6.0))

        if yr < 2018:
            row = generate_healthy_year("Sunrise Textile Mills", "Textiles", yr)
        else:
            row = generate_distressed_year(
                "Sunrise Textile Mills", "Textiles",
                yr, years_before_demo_default, deterioration
            )
        rows.append(row)

    df = pd.DataFrame(rows)
    df = compute_ratios(df)
    df = compute_velocity_features(df)
    df = compute_beneish_scores(df)
    df = compute_altman_zscore(df)
    df = compute_piotroski(df)

    return df


def save_schema(df):
    """Save column descriptions as JSON"""
    schema = {
        col: {
            "dtype": str(df[col].dtype),
            "non_null": int(df[col].notna().sum()),
            "sample": str(df[col].dropna().iloc[0]) if df[col].notna().any() else "N/A"
        }
        for col in df.columns
    }
    return schema


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Create output directories
    os.makedirs("data/synthetic", exist_ok=True)

    # Build main training dataset
    df_main = build_dataset()
    output_path = "data/synthetic/intelli_credit_dataset.csv"
    df_main.to_csv(output_path, index=False)
    print(f"\n✅ Saved training dataset → {output_path}")

    # Build demo company
    df_demo = build_demo_company()
    demo_path = "data/synthetic/demo_sunrise_textile.csv"
    df_demo.to_csv(demo_path, index=False)
    print(f"✅ Saved demo company → {demo_path}")

    # Save schema
    schema = save_schema(df_main)
    schema_path = "data/synthetic/schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"✅ Saved schema → {schema_path}")

    print(f"\n{'='*60}")
    print("DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"Total rows:     {len(df_main)}")
    print(f"Total features: {len(df_main.columns)}")
    print(f"Companies:      {df_main['company_name'].nunique()}")
    print(f"Defaulted:      {df_main[df_main['label']==1]['company_name'].nunique()}")
    print(f"Healthy:        {df_main[df_main['label']==0]['company_name'].nunique()}")
    print(f"Default rate:   {df_main['label'].mean():.1%}")
    print(f"\nNOTE: Replace with real Prowess data when available.")
    print(f"      All column names match the real schema exactly.")
    print(f"{'='*60}")
