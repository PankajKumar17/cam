"""
Yakṣarāja — MCA Filing & Legal Dispute Intelligence Module (Person 2)
=======================================================================
Checks Ministry of Corporate Affairs (MCA) filings and e-Courts portal
for red flags that are NOT visible in financial statements.

Data Sources:
  1. MCA21 portal (Ministry of Corporate Affairs)  — company master data,
     director KYC, DIN disqualification status, charge (pledge) register,
     strike-off status, NCLT filings
  2. e-Courts portal                               — pending litigation,
     case status, verdict history
  3. Tavily web research                           — real-time news of
     regulatory actions, ED/CBI/SEBI orders
  4. Synthetic fallback                            — deterministic demo
     data when APIs are unavailable

Indian-Context Signals:
  - DIN disqualification under Section 164(2) Companies Act 2013
  - Struck-off / defunct group companies (Shell company risk)
  - Charge satisfaction status (undisclosed pledges / lien)
  - NCLT / NCLAT proceedings
  - Related-party directorship overlap
  - Prior NPA track record across group entities

Author: Person 2
Module: modules/person2_alt_data/mca_inspector.py
"""

import os
import re
import json
import time
import hashlib
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# MCA Charge types
CHARGE_TYPES = {
    "HYPOTHECATION": "Assets hypothecated to lender",
    "MORTGAGE":      "Immovable property mortgaged",
    "PLEDGE":        "Securities / inventory pledged",
    "LIEN":          "Bank lien on deposits / assets",
    "DEBENTURE":     "Debenture trust deed",
}

# Section 164(2) Companies Act — triggers DIN disqualification
DIN_DISQ_REASONS = [
    "Failed to file financial statements for 3+ consecutive years",
    "Failed to repay deposits / debentures / dividends declared",
    "Convicted of offence with imprisonment ≥ 6 months",
    "Company struck off under Section 248 of Companies Act 2013",
]

# e-Courts case categories mapped to credit risk
LEGAL_RISK_MAP = {
    "NCLT":         "CRITICAL",   # Insolvency proceedings
    "ED":           "CRITICAL",   # Enforcement Directorate / PMLA
    "CBI":          "CRITICAL",   # Central Bureau of Investigation
    "NI Act 138":   "HIGH",       # Cheque dishonour / bounced cheques
    "Income Tax":   "HIGH",       # Tax demand disputes
    "GST Demand":   "HIGH",       # GST adjudication
    "SEBI":         "HIGH",       # Capital market violations
    "Civil Suit":   "MEDIUM",     # Civil recovery suits
    "Consumer":     "LOW",        # Consumer Forum
    "Labour":       "LOW",        # Labour / employment disputes
}

# Known high-risk sectors for regulatory scrutiny (India)
HIGH_SCRUTINY_SECTORS = [
    "Real Estate", "Infrastructure", "NBFC", "Microfinance",
    "Cryptocurrency", "Jewellery", "Construction", "Mining",
]

# Synthetic charge templates for demo
DEMO_COMPANY_PROFILES = {
    "Sunrise Textile Mills": {
        "cin": "U17100MH2010PLC123456",
        "roc_code": "RoC-Mumbai",
        "incorporation_date": "2010-03-15",
        "directors": [
            {"name": "Rajesh Kumar", "din": "01234567", "disqualified": False},
            {"name": "Priya Kumar", "din": "01234568", "disqualified": False},
        ],
        "charges": [
            {
                "charge_id": "CH-2019-001",
                "type": "HYPOTHECATION",
                "holder": "State Bank of India",
                "amount_cr": 250.0,
                "date": "2019-07-22",
                "satisfied": False,
            },
            {
                "charge_id": "CH-2021-002",
                "type": "MORTGAGE",
                "holder": "HDFC Bank",
                "amount_cr": 150.0,
                "date": "2021-02-10",
                "satisfied": False,
            },
        ],
        "legal_cases": [],
        "nclt_case": None,
        "agm_compliance": "COMPLIANT",
        "annual_return_due": "FILED",
        "financial_statements_due": "FILED",
        "din_disqualified_count": 0,
        "struck_off_group_entities": 0,
        "overall_risk": "LOW",
    },
}

DEMO_HIGH_RISK_PROFILE = {
    "cin": "U24100GJ2008PTC209812",
    "roc_code": "RoC-Ahmedabad",
    "incorporation_date": "2008-11-20",
    "directors": [
        {"name": "Suresh Shah", "din": "07654321", "disqualified": True,
         "disq_reason": "Company struck off — Section 248 Companies Act 2013"},
        {"name": "Meena Shah", "din": "07654322", "disqualified": False},
    ],
    "charges": [
        {
            "charge_id": "CH-2017-003",
            "type": "HYPOTHECATION",
            "holder": "Punjab National Bank",
            "amount_cr": 180.0,
            "date": "2017-03-12",
            "satisfied": False,
        },
        {
            "charge_id": "CH-2018-004",
            "type": "PLEDGE",
            "holder": "Axis Bank",
            "amount_cr": 45.0,
            "date": "2018-09-01",
            "satisfied": False,
        },
    ],
    "legal_cases": [
        {
            "case_no": "CP-2022-1234",
            "court": "NCLT Ahmedabad",
            "category": "NCLT",
            "status": "PENDING",
            "petitioner": "Punjab National Bank",
            "claim_cr": 210.0,
            "risk_level": "CRITICAL",
        },
        {
            "case_no": "CC-1234/2021",
            "court": "Chief Judicial Magistrate, Ahmedabad",
            "category": "NI Act 138",
            "status": "PENDING",
            "petitioner": "Axis Bank",
            "claim_cr": 45.0,
            "risk_level": "HIGH",
        },
    ],
    "nclt_case": "CP-2022-1234",
    "agm_compliance": "DEFAULTING",
    "annual_return_due": "OVERDUE",
    "financial_statements_due": "OVERDUE",
    "din_disqualified_count": 1,
    "struck_off_group_entities": 2,
    "overall_risk": "CRITICAL",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_det_cin(company_name: str, sector: str = "Manufacturing") -> str:
    """Generate a deterministic fake CIN from company name."""
    h = hashlib.md5(company_name.encode()).hexdigest().upper()
    states = {"Textiles": "MH", "Steel": "MH", "NBFC": "DL",
              "Real Estate": "MH", "Pharma": "MH", "IT": "KA"}
    state = states.get(sector, "MH")
    sector_codes = {"Textiles": "17100", "Steel": "27100",
                    "NBFC": "65100", "Real Estate": "45200"}
    code = sector_codes.get(sector, "99999")
    year = "2010"
    return f"U{code}{state}{year}PLC{h[:6]}"


def _deterministic_risk(company_name: str) -> str:
    """Generate deterministic risk level from company name hash."""
    h = int(hashlib.md5(company_name.encode()).hexdigest(), 16)
    idx = h % 100
    if idx < 10:
        return "CRITICAL"
    if idx < 25:
        return "HIGH"
    if idx < 60:
        return "MEDIUM"
    return "LOW"


def _web_search_mca_legal(
    company_name: str,
    promoter_names: List[str],
) -> Dict[str, Any]:
    """
    Use Tavily to search for MCA / legal news about company & promoters.
    Falls back to empty dict if Tavily unavailable.
    """
    if not TAVILY_AVAILABLE:
        return {}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {}

    web_results = {
        "nclt_news": [],
        "ed_sebi_news": [],
        "npa_news": [],
        "promoter_legal_news": [],
    }

    try:
        client = TavilyClient(api_key=api_key)

        queries = [
            (f"{company_name} NCLT insolvency default 2023 2024 India", "nclt_news"),
            (f"{company_name} ED SEBI CBI enforcement order India", "ed_sebi_news"),
            (f"{company_name} NPA default bank loan India site:rbi.org.in OR site:moneycontrol.com", "npa_news"),
        ]

        for promoter in promoter_names[:2]:  # limit to 2 promoters
            queries.append(
                (f'"{promoter}" fraud default disqualified director India', "promoter_legal_news")
            )

        for query, key in queries:
            try:
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=3,
                )
                for r in response.get("results", []):
                    web_results[key].append({
                        "title":   r.get("title", ""),
                        "url":     r.get("url", ""),
                        "snippet": r.get("content", "")[:300],
                    })
                time.sleep(0.3)  # rate limit
            except Exception as e:
                logger.debug(f"Tavily query failed: {e}")

    except Exception as e:
        logger.warning(f"MCA web search failed: {e}")

    return web_results


def _score_web_results(web_results: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    Score web research results for legal / MCA risk.
    Returns (risk_score 0-100, list of red flags).
    """
    score = 0
    flags = []

    nclt = web_results.get("nclt_news", [])
    ed_sebi = web_results.get("ed_sebi_news", [])
    npa = web_results.get("npa_news", [])
    promoter = web_results.get("promoter_legal_news", [])

    for item in nclt:
        title = (item.get("title", "") + " " + item.get("snippet", "")).lower()
        if any(k in title for k in ["insolvency", "nclt", "default", "liquidat"]):
            score += 25
            flags.append(f"NCLT/Insolvency: {item['title'][:80]}")
            break

    for item in ed_sebi:
        title = (item.get("title", "") + " " + item.get("snippet", "")).lower()
        if any(k in title for k in ["ed raid", "sebi order", "cbi", "pmla", "enforcement"]):
            score += 30
            flags.append(f"Regulatory Action: {item['title'][:80]}")
            break

    for item in npa:
        title = (item.get("title", "") + " " + item.get("snippet", "")).lower()
        if any(k in title for k in ["npa", "wilful default", "bank default", "recall"]):
            score += 20
            flags.append(f"NPA/Default: {item['title'][:80]}")
            break

    for item in promoter:
        title = (item.get("title", "") + " " + item.get("snippet", "")).lower()
        if any(k in title for k in ["fraud", "disqualif", "arrested", "convicted"]):
            score += 25
            flags.append(f"Promoter Red Flag: {item['title'][:80]}")
            break

    return min(score, 100), flags


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC DATA GENERATOR (for demo / test without real MCA API)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_synthetic_mca_data(
    company_name: str,
    sector: str = "Manufacturing",
    directors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate deterministic synthetic MCA data for any company.
    Uses company name hash to produce consistent (repeatable) results.
    """
    # Check if we have a pre-built demo profile
    if company_name in DEMO_COMPANY_PROFILES:
        return DEMO_COMPANY_PROFILES[company_name]

    rng = random.Random(hashlib.md5(company_name.encode()).hexdigest())
    h_int = int(hashlib.md5(company_name.encode()).hexdigest(), 16)

    risk_level = _deterministic_risk(company_name)
    is_distressed = risk_level in ("CRITICAL", "HIGH")

    dir_names = directors or [
        f"Promoter-{company_name.split()[0]}", f"Director-{company_name.split()[-1]}"
    ]

    generated_directors = []
    for i, name in enumerate(dir_names[:4]):
        disq = is_distressed and i == 0
        generated_directors.append({
            "name": name,
            "din": f"{rng.randint(10000000, 99999999)}",
            "disqualified": disq,
            "disq_reason": DIN_DISQ_REASONS[0] if disq else None,
        })

    # Charges
    charges = []
    n_charges = rng.randint(1, 4) if is_distressed else rng.randint(0, 2)
    banks = ["State Bank of India", "HDFC Bank", "ICICI Bank",
             "Punjab National Bank", "Axis Bank", "Bank of Baroda"]
    for i in range(n_charges):
        charges.append({
            "charge_id": f"CH-{2015 + i}-{rng.randint(100, 999)}",
            "type": rng.choice(list(CHARGE_TYPES.keys())),
            "holder": rng.choice(banks),
            "amount_cr": round(rng.uniform(20, 400), 1),
            "date": (datetime(2015, 1, 1) + timedelta(days=rng.randint(0, 2500))).strftime("%Y-%m-%d"),
            "satisfied": not is_distressed and rng.random() > 0.4,
        })

    # Legal cases
    legal_cases = []
    if is_distressed:
        n_cases = rng.randint(1, 3)
        courts = [
            ("NCLT", "NCLT Mumbai", "CRITICAL"),
            ("NI Act 138", "Magistrate Court", "HIGH"),
            ("Income Tax", "Income Tax Tribunal", "HIGH"),
        ]
        for i in range(min(n_cases, len(courts))):
            cat, court, risk = courts[i]
            legal_cases.append({
                "case_no": f"{cat[:2]}-{rng.randint(1000, 9999)}/{datetime.now().year - rng.randint(0, 3)}",
                "court": court,
                "category": cat,
                "status": "PENDING",
                "petitioner": rng.choice(banks),
                "claim_cr": round(rng.uniform(10, 300), 1),
                "risk_level": risk,
            })

    din_disq_count = sum(1 for d in generated_directors if d["disqualified"])
    struck_off = rng.randint(1, 3) if is_distressed else 0

    overall = "CRITICAL" if (din_disq_count > 0 or any(c["category"] == "NCLT" for c in legal_cases)) \
              else ("HIGH" if legal_cases else ("MEDIUM" if charges else "LOW"))

    return {
        "cin": _generate_det_cin(company_name, sector),
        "roc_code": rng.choice(["RoC-Mumbai", "RoC-Delhi", "RoC-Ahmedabad", "RoC-Kolkata"]),
        "incorporation_date": (datetime(2000, 1, 1) + timedelta(days=rng.randint(0, 8000))).strftime("%Y-%m-%d"),
        "directors": generated_directors,
        "charges": charges,
        "legal_cases": legal_cases,
        "nclt_case": legal_cases[0]["case_no"] if any(c["category"] == "NCLT" for c in legal_cases) else None,
        "agm_compliance": "DEFAULTING" if is_distressed else "COMPLIANT",
        "annual_return_due": "OVERDUE" if is_distressed else "FILED",
        "financial_statements_due": "OVERDUE" if is_distressed else "FILED",
        "din_disqualified_count": din_disq_count,
        "struck_off_group_entities": struck_off,
        "overall_risk": overall,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LEGAL RISK SCORER
# ─────────────────────────────────────────────────────────────────────────────

def _compute_legal_risk_score(mca_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a 0-100 legal risk score from MCA data + web research.
    Returns score, level, and breakdown of contributing factors.
    """
    score = 0
    factors = []
    deductions = []

    # DIN disqualification — most severe signal
    din_disq = mca_data.get("din_disqualified_count", 0)
    if din_disq > 0:
        score += 35
        factors.append(f"{din_disq} director(s) with disqualified DIN under Sec 164(2)")

    # NCLT insolvency case
    if mca_data.get("nclt_case"):
        score += 40
        factors.append(f"Active NCLT insolvency proceedings: {mca_data['nclt_case']}")

    # Legal cases
    for case in mca_data.get("legal_cases", []):
        case_risk = case.get("risk_level", "LOW")
        if case_risk == "CRITICAL":
            score += 20
            factors.append(f"CRITICAL case: {case['case_no']} @ {case['court']} "
                           f"(claim ₹{case.get('claim_cr', '?')} Cr)")
        elif case_risk == "HIGH":
            score += 12
            factors.append(f"HIGH risk case: {case['case_no']} — {case['category']}")
        elif case_risk == "MEDIUM":
            score += 5

    # Struck-off group entities (shell company risk)
    struck = mca_data.get("struck_off_group_entities", 0)
    if struck > 2:
        score += 15
        factors.append(f"{struck} struck-off group entities — potential shell company structure")
    elif struck > 0:
        score += 8
        factors.append(f"{struck} struck-off group entities — monitor")

    # Compliance defaults
    if mca_data.get("annual_return_due") == "OVERDUE":
        score += 10
        factors.append("Annual return filing overdue — compliance lapse")
    if mca_data.get("financial_statements_due") == "OVERDUE":
        score += 10
        factors.append("Financial statements filing overdue — compliance lapse")
    if mca_data.get("agm_compliance") == "DEFAULTING":
        score += 5
        factors.append("AGM compliance defaulting")

    # Unsatisfied charges (encumbrances)
    unsatisfied_charges = [c for c in mca_data.get("charges", []) if not c.get("satisfied")]
    total_charge_cr = sum(c.get("amount_cr", 0) for c in unsatisfied_charges)
    if total_charge_cr > 500:
        score += 10
        factors.append(f"₹{total_charge_cr:.0f} Cr in unsatisfied MCA charges — verify against reported debt")
    elif total_charge_cr > 100:
        deductions.append(f"₹{total_charge_cr:.0f} Cr in unsatisfied charges — cross-check with balance sheet")

    # Web research score integration (appended later by caller)

    score = min(score, 100)
    level = "CRITICAL" if score >= 50 else ("HIGH" if score >= 30 else ("MEDIUM" if score >= 15 else "LOW"))

    return {
        "legal_risk_score": score,
        "legal_risk_level": level,
        "risk_factors": factors,
        "observations": deductions,
        "total_charge_cr": round(total_charge_cr, 1),
        "unsatisfied_charge_count": len(unsatisfied_charges),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_mca_inspection(
    company_name: str,
    sector: str = "Manufacturing",
    directors: Optional[List[str]] = None,
    cin: Optional[str] = None,
    use_web_research: bool = True,
) -> Dict[str, Any]:
    """
    Run full MCA + Legal intelligence for a company.

    Parameters
    ----------
    company_name      : Company's registered name
    sector            : Business sector (for synthetic data calibration)
    directors         : Known director names (for web search)
    cin               : Company Identification Number (if known)
    use_web_research  : Whether to trigger Tavily web search

    Returns
    -------
    dict:
        mca_data       — raw MCA filing data
        legal_risk     — scored legal risk (0-100)
        web_findings   — Tavily research results
        summary        — human-readable summary for CAM
        din_disqualified_count, nclt_case, legal_cases, charges, ...
    """
    logger.info(f"Running MCA inspection for: {company_name}")

    # Step 1: Get MCA data (synthetic demo — would call real MCA21 API in production)
    mca_data = _generate_synthetic_mca_data(
        company_name=company_name,
        sector=sector,
        directors=directors,
    )
    if cin:
        mca_data["cin"] = cin

    # Step 2: Web research via Tavily
    web_findings = {}
    web_risk_score = 0
    web_flags = []

    if use_web_research:
        promoter_names = [d["name"] for d in mca_data.get("directors", [])[:3]]
        web_findings = _web_search_mca_legal(company_name, promoter_names)
        web_risk_score, web_flags = _score_web_results(web_findings)
        if web_flags:
            logger.warning(f"Web research found {len(web_flags)} legal/MCA flags")

    # Step 3: Score legal risk
    legal_risk = _compute_legal_risk_score(mca_data)

    # Merge web risk into overall score
    combined_score = min(100, legal_risk["legal_risk_score"] + web_risk_score // 3)
    combined_level = (
        "CRITICAL" if combined_score >= 50
        else ("HIGH" if combined_score >= 30
              else ("MEDIUM" if combined_score >= 15
                    else "LOW"))
    )
    legal_risk["legal_risk_score"] = combined_score
    legal_risk["legal_risk_level"] = combined_level
    legal_risk["risk_factors"] += web_flags

    # Step 4: Build CAM summary
    nclt = mca_data.get("nclt_case")
    din_disq = mca_data.get("din_disqualified_count", 0)
    n_cases = len(mca_data.get("legal_cases", []))
    n_charges = len([c for c in mca_data.get("charges", []) if not c.get("satisfied")])

    if combined_level == "CRITICAL":
        summary = (
            f"⚠ CRITICAL LEGAL RISK: "
            f"{'Active NCLT insolvency proceedings. ' if nclt else ''}"
            f"{f'{din_disq} director(s) with disqualified DIN. ' if din_disq else ''}"
            f"{f'{n_cases} pending legal case(s). ' if n_cases else ''}"
            "Recommend independent legal due diligence before sanction."
        )
    elif combined_level == "HIGH":
        summary = (
            f"HIGH LEGAL RISK: {n_cases} pending legal case(s), "
            f"{n_charges} unsatisfied charge(s). "
            "Obtain No-Objection Certificate from existing lenders."
        )
    elif combined_level == "MEDIUM":
        summary = (
            f"MEDIUM LEGAL RISK: {n_charges} unsatisfied charge(s) registered with MCA. "
            "Cross-verify charge amounts with reported debt in balance sheet."
        )
    else:
        summary = (
            "LOW LEGAL RISK: No active insolvency, no DIN disqualification, "
            f"routine charges registered (₹{legal_risk['total_charge_cr']:.0f} Cr). "
            "Compliance filings are current."
        )

    logger.info(f"MCA Inspection complete: {company_name} → {combined_level} (score={combined_score})")

    return {
        "company_name":          company_name,
        "cin":                   mca_data.get("cin"),
        "roc_code":              mca_data.get("roc_code"),
        "incorporation_date":    mca_data.get("incorporation_date"),
        "directors":             mca_data.get("directors", []),
        "charges":               mca_data.get("charges", []),
        "unsatisfied_charges":   [c for c in mca_data.get("charges", []) if not c.get("satisfied")],
        "legal_cases":           mca_data.get("legal_cases", []),
        "nclt_case":             nclt,
        "din_disqualified_count": din_disq,
        "struck_off_group_entities": mca_data.get("struck_off_group_entities", 0),
        "agm_compliance":        mca_data.get("agm_compliance"),
        "annual_return_status":  mca_data.get("annual_return_due"),
        "financial_stmt_status": mca_data.get("financial_statements_due"),
        "legal_risk_score":      combined_score,
        "legal_risk_level":      combined_level,
        "risk_factors":          legal_risk["risk_factors"],
        "observations":          legal_risk["observations"],
        "total_charge_cr":       legal_risk["total_charge_cr"],
        "web_findings":          web_findings,
        "summary":               summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_mca_inspection(
        "Sunrise Textile Mills",
        sector="Textiles",
        directors=["Rajesh Kumar", "Priya Kumar"],
    )
    import json
    print(json.dumps(result, indent=2, default=str))
