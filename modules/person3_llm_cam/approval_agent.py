"""
Yakṣarāja — Approval Agent (Person 3, Innovation 10)
==========================================================
The "Bull Case" agent in the adversarial two-agent CAM system.

This agent writes the strongest possible case FOR approving a loan,
using all available financial data, ML scores, and research intelligence.
It mirrors the advocate role in a real credit committee.

Author: Person 3
Module: modules/person3_llm_cam/approval_agent.py
"""

import os
import json
import time
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── Google Gemini ────────────────────────────────────────────────────────────
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-genai not installed — will use fallback bull case")
    GEMINI_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

APPROVAL_SYSTEM_PROMPT = """You are a Senior Credit Analyst at Vivriti Capital generating a Credit Appraisal Memorandum.

Your job is to write the strongest possible case FOR approving this loan application.
Use all available data — financial ratios, industry research, management quality, collateral — 
to build a compelling bull case for lending. Be specific with numbers. Reference actual data points.

=== MANDATORY RULES ===

RULE 1 — FINANCIAL DATA: Use ONLY the figures provided in the [FINANCIAL DATA] section.
Never invent, estimate, or use placeholder financials. If a figure is missing, write "[DATA REQUIRED]".
Never confuse quarterly figures with annual figures. Specify STANDALONE vs. CONSOLIDATED.

RULE 2 — COMPANY IDENTITY: The sector and all narrative content must match the actual company.
Never write about a fictional or substitute company. The bull case must reference the subject
company's actual sector, products, and competitive environment.

RULE 3 — SECTOR-APPROPRIATE ANALYSIS: Use stress scenarios and tailwinds specific to the company's sector.
Never apply textile/agricultural commodity stresses to steel or wind energy companies, or vice versa.

RULE 4 — INTERNAL CONSISTENCY:
(a) DSCR < 1.0 → decision = REJECT. Do NOT build a bull case that ignores this.
(b) Gross margin and EBITDA margin must be arithmetically consistent.
(c) A Bear metric (e.g. DSCR 0.47) cannot be cited as a Bull strength.
(d) PD > 40% → recommend REJECT.

RULE 5 — MANAGEMENT QUALITY: Only discuss management quality if an earnings call transcript or
interview is provided. If not provided, write: "Management Quality Assessment: INSUFFICIENT DATA —
No transcript provided."

RULE 6 — DEFAULT ARCHETYPE: For companies with strong positive operating cash flows, write:
"No close default archetype." Never assign an unrelated industry's default archetype.

RULE 7 — PROMOTER SHAREHOLDING: Use only figures from actual data. Never default to 50% or 62%.

You write in a formal but confident tone appropriate for an Indian NBFC credit committee memo.
Always structure your analysis with clear headers and bullet points.
Reference specific financial metrics (DSCR, ICR, D/E ratio, margins) with exact values.
"""

BULL_CASE_TEMPLATE = """Write a comprehensive BULL CASE (case for approval) for the following loan application.

## COMPANY PROFILE
Company: {company_name}
Sector: {sector}
Fiscal Year: {fiscal_year}

## [FINANCIAL DATA]
- Revenue (Annual): {revenue_display}
- EBITDA: {ebitda_display} (Margin: {ebitda_margin_display})
- PAT: {pat_display} (Net Margin: {net_margin_display})
- DSCR: {dscr_display}
- Interest Coverage Ratio: {interest_coverage_display}
- Debt-to-Equity: {debt_to_equity_display}
- Current Ratio: {current_ratio_display}
- ROE: {roe_display}
- ROA: {roa_display}
- Cash Flow from Operations: {cfo_display}
- Free Cash Flow: {free_cash_flow_display}
- Total Debt: {total_debt_display}
- Total Equity: {total_equity_display}

## ML CREDIT SCORES
- Ensemble PD (Probability of Default): {ensemble_pd:.2%}
- XGBoost PD: {xgb_pd:.2%}
- Lending Decision: {lending_decision}
- Model Confidence: {model_confidence}
- Risk Premium Suggested: {risk_premium:.2f}%

## ALTERNATIVE DATA SIGNALS
- Satellite Activity Score: {satellite_activity_score:.1f} ({satellite_activity_category})
- GST Compliance: Divergence={gst_vs_bank_divergence:.1%}, Filing Delays={gst_filing_delays_count}
- Network Contagion Risk: {contagion_risk_score:.2f}
- Promoter Holding: {promoter_holding_pct_display} (Pledged: {promoter_pledge_pct_display})

## MANAGEMENT TRANSCRIPT
{management_transcript_status}

## RESEARCH INTELLIGENCE
Industry Outlook: {industry_outlook}
Research Sentiment: {research_sentiment_score:.2f}

Key Positives from Research:
{research_positives}

---

IMPORTANT REMINDERS:
- If any financial figure above shows [DATA REQUIRED], do NOT invent a value.
- Stress scenarios and tailwinds must be specific to the {sector} sector.
- If MANAGEMENT TRANSCRIPT says NOT PROVIDED, write: "Management Quality Assessment: INSUFFICIENT DATA"
- If DSCR < 1.0 or PD > 40%, do NOT build an approval case — acknowledge the weakness.

WRITE THE BULL CASE WITH THESE EXACT SECTIONS:

1. **EXECUTIVE SUMMARY** — 3-4 sentences positively framing the lending opportunity
2. **FINANCIAL STRENGTHS** — Top 3-5 strongest ratios/metrics with exact numbers
3. **BUSINESS MOMENTUM** — Growth signals, revenue trajectory, market position
4. **MANAGEMENT QUALITY** — Positive signals from CEO interview, promoter track record (ONLY if transcript provided)
5. **INDUSTRY TAILWINDS** — Sector-level positives, policy support, demand outlook
6. **RISK MITIGANTS** — Why the identified risks are manageable

Target length: 400-600 words. Be specific. Cite exact numbers from the data above.
"""


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HELPER: EXTRACT SAFE VALUES FROM COMPANY DATA                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _safe_get(data: dict, key: str, default: Any = 0.0) -> Any:
    """Safely extract a value from company_data, returning default if missing."""
    val = data.get(key, default)
    if val is None:
        return default
    return val


def _display_val(value, fmt=".1f", prefix="₹", suffix=" Cr"):
    """Format a financial value for display, or return [DATA REQUIRED] if missing."""
    if value is None or value == 0.0:
        return "[DATA REQUIRED]"
    try:
        return f"{prefix}{float(value):{fmt}}{suffix}"
    except (ValueError, TypeError):
        return "[DATA REQUIRED]"


def _display_pct(value):
    """Format a percentage value for display, or return [DATA REQUIRED] if missing."""
    if value is None or value == 0.0:
        return "[DATA REQUIRED]"
    try:
        return f"{float(value):.1%}"
    except (ValueError, TypeError):
        return "[DATA REQUIRED]"


def _display_ratio(value, suffix="x"):
    """Format a ratio value for display, or return [DATA REQUIRED] if missing."""
    if value is None or value == 0.0:
        return "[DATA REQUIRED]"
    try:
        return f"{float(value):.2f}{suffix}"
    except (ValueError, TypeError):
        return "[DATA REQUIRED]"


def _build_prompt_context(company_data: dict, research: dict) -> dict:
    """
    Build the template context dict from raw company_data and research.
    Uses [DATA REQUIRED] for missing values (Rule 1) instead of silent defaults.
    """
    has_transcript = bool(company_data.get("management_transcript"))
    if has_transcript:
        mgmt_status = "Transcript provided — see CEO INTERVIEW SIGNALS below."
    else:
        mgmt_status = "NOT PROVIDED"

    return {
        "company_name": _safe_get(company_data, "company_name", "Unknown Company"),
        "sector": _safe_get(company_data, "sector", "General"),
        "fiscal_year": _safe_get(company_data, "fiscal_year", "FY2024"),
        # P&L — display versions (Rule 1: [DATA REQUIRED] if missing)
        "revenue_display": _display_val(company_data.get("revenue")),
        "ebitda_display": _display_val(company_data.get("ebitda")),
        "ebitda_margin_display": _display_pct(company_data.get("ebitda_margin")),
        "pat_display": _display_val(company_data.get("pat")),
        "net_margin_display": _display_pct(company_data.get("net_margin")),
        # Ratios — display versions
        "dscr_display": _display_ratio(company_data.get("dscr")),
        "interest_coverage_display": _display_ratio(company_data.get("interest_coverage")),
        "debt_to_equity_display": _display_ratio(company_data.get("debt_to_equity")),
        "current_ratio_display": _display_ratio(company_data.get("current_ratio")),
        "roe_display": _display_pct(company_data.get("roe")),
        "roa_display": _display_pct(company_data.get("roa")),
        # Cash flow — display versions
        "cfo_display": _display_val(company_data.get("cfo")),
        "free_cash_flow_display": _display_val(company_data.get("free_cash_flow")),
        # Balance sheet — display versions
        "total_debt_display": _display_val(company_data.get("total_debt")),
        "total_equity_display": _display_val(company_data.get("total_equity")),
        # Promoter — display versions (Rule 7: never default to 50%/62%)
        "promoter_holding_pct_display": _display_pct(company_data.get("promoter_holding_pct")),
        "promoter_pledge_pct_display": _display_pct(company_data.get("promoter_pledge_pct")),
        # ML scores (numeric — always available from pipeline)
        "ensemble_pd": _safe_get(company_data, "ensemble_pd", 0.15),
        "xgb_pd": _safe_get(company_data, "xgb_pd", 0.15),
        "lending_decision": _safe_get(company_data, "lending_decision", "REVIEW"),
        "model_confidence": _safe_get(company_data, "model_confidence", "MODERATE"),
        "risk_premium": _safe_get(company_data, "risk_premium", 4.0),
        # Alt data (numeric — always available from pipeline)
        "satellite_activity_score": _safe_get(company_data, "satellite_activity_score", 70.0),
        "satellite_activity_category": _safe_get(company_data, "satellite_activity_category", "ACTIVE"),
        "gst_vs_bank_divergence": _safe_get(company_data, "gst_vs_bank_divergence"),
        "gst_filing_delays_count": _safe_get(company_data, "gst_filing_delays_count", 0),
        "contagion_risk_score": _safe_get(company_data, "contagion_risk_score"),
        # Management transcript status (Rule 5)
        "management_transcript_status": mgmt_status,
        # Research
        "industry_outlook": research.get("industry_outlook", "NEUTRAL"),
        "research_sentiment_score": research.get("research_sentiment_score", 0.5),
        "research_positives": "\n".join(
            f"  - {p}" for p in research.get("key_positives_found", ["No data available"])
        ),
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  GEMINI API WITH RETRY                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _get_gemini_api_key() -> Optional[str]:
    """Return the Gemini API key from environment, or None if not set."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not GEMINI_AVAILABLE:
        return None
    return api_key


def _call_gemini_with_retry(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Call Gemini API with exponential backoff retry logic.

    Args:
        api_key: Gemini API key
        system_prompt: System-level instruction
        user_prompt: User message content
        max_retries: Number of retry attempts (default 3)
        max_tokens: Max response tokens

    Returns:
        Response text or None on failure
    """
    for attempt in range(1, max_retries + 1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text.strip()
        except Exception as e:
            err = str(e).lower()
            if "503" in err or "unavailable" in err or "service unavailable" in err:
                logger.warning(f"Gemini service unavailable — using fallback immediately")
                return None
            if "429" in err or "quota" in err or "resource exhausted" in err:
                wait = 15
                logger.warning(f"Rate limit hit (attempt {attempt}/{max_retries}) — waiting {wait}s before retry...")
                time.sleep(wait)
            elif attempt < max_retries:
                logger.warning(f"Gemini API error (attempt {attempt}/{max_retries}): {e}")
                time.sleep(2)
            else:
                logger.error(f"Gemini API error (attempt {attempt}/{max_retries}): {e}")

    logger.error("All Gemini API retries exhausted — using fallback")
    return None


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FALLBACK BULL CASE                                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _fallback_bull_case(company_data: dict, research: dict) -> str:
    """
    Generate a rule-based bull case when Claude API is unavailable.
    Uses template filling with actual data values — no LLM needed.
    Enforces Rules 1 (DATA REQUIRED), 5 (management transcript), 6 (default archetype).
    """
    name = _safe_get(company_data, "company_name", "Unknown Company")
    sector = _safe_get(company_data, "sector", "General")

    # Rule 1: Use display helpers — [DATA REQUIRED] for missing values
    dscr = company_data.get("dscr")
    ebitda_margin = company_data.get("ebitda_margin")
    cfo = company_data.get("cfo")
    revenue = company_data.get("revenue")
    ebitda = company_data.get("ebitda")
    free_cash_flow = company_data.get("free_cash_flow")
    interest_coverage = company_data.get("interest_coverage")
    current_ratio = company_data.get("current_ratio")
    debt_to_equity = company_data.get("debt_to_equity")
    ensemble_pd = _safe_get(company_data, "ensemble_pd", 0.15)
    lending_decision = _safe_get(company_data, "lending_decision", "REVIEW")
    has_transcript = bool(company_data.get("management_transcript"))

    # Identify top financial strengths (only from actual data)
    strengths = []
    if dscr is not None and dscr >= 1.5:
        strengths.append(f"Healthy DSCR of {dscr:.2f}x (well above 1.0 threshold)")
    if interest_coverage is not None and interest_coverage >= 1.5:
        strengths.append(f"Strong interest coverage of {interest_coverage:.2f}x")
    if ebitda_margin is not None and ebitda_margin >= 0.12:
        strengths.append(f"Robust EBITDA margin of {ebitda_margin:.1%}")
    if current_ratio is not None and current_ratio >= 1.0:
        strengths.append(f"Adequate liquidity with current ratio of {current_ratio:.2f}x")
    if cfo is not None and cfo > 0:
        strengths.append(f"Positive operating cash flow of ₹{cfo:.1f} Cr")
    if debt_to_equity is not None and debt_to_equity < 2.5:
        strengths.append(f"Manageable leverage at {debt_to_equity:.2f}x D/E")
    if not strengths:
        strengths.append("Operational track record in the sector")

    strengths_text = "\n".join(f"   - {s}" for s in strengths[:5])

    research_positives = "\n".join(
        f"  - {p}" for p in research.get("key_positives_found", ["No data available"])
    )
    industry_outlook = research.get("industry_outlook", "NEUTRAL")
    research_sentiment = research.get("research_sentiment_score", 0.5)

    # Rule 5: Management quality gating
    if has_transcript:
        mgmt_section = f"""## 4. MANAGEMENT QUALITY

Promoter holding at {_display_pct(company_data.get('promoter_holding_pct'))} reflects skin in the game. \
CEO interview sentiment and specificity scores suggest reasonable management transparency."""
    else:
        mgmt_section = """## 4. MANAGEMENT QUALITY

Management Quality Assessment: INSUFFICIENT DATA — No transcript provided.
Schedule management interaction before final credit decision."""

    # Rule 6: Default archetype
    if cfo is not None and cfo > 0:
        archetype_note = "No close default archetype — strong positive operating cash flows."
    else:
        archetype_note = "Default archetype assessment requires further analysis."

    return f"""## 1. EXECUTIVE SUMMARY

{name} operating in the {sector} sector presents a viable lending opportunity. \
The company demonstrates {_display_ratio(dscr)} DSCR, {_display_pct(ebitda_margin)} EBITDA margin, \
and {_display_val(cfo)} positive operating cash flow, indicating adequate \
debt servicing capacity. ML models assign an ensemble PD of {ensemble_pd:.2%}, \
supporting a {lending_decision} recommendation.

## 2. FINANCIAL STRENGTHS

{strengths_text}

## 3. BUSINESS MOMENTUM

Revenue of {_display_val(revenue)} with EBITDA of {_display_val(ebitda)} \
reflects a functioning business model. Free cash flow of {_display_val(free_cash_flow)} \
provides internal funding capacity. The satellite activity score of \
{_safe_get(company_data, 'satellite_activity_score', 70.0):.1f} \
({_safe_get(company_data, 'satellite_activity_category', 'ACTIVE')}) \
confirms operational activity at the physical premises.

{mgmt_section}

## 5. INDUSTRY TAILWINDS

Industry outlook is assessed as {industry_outlook}. \
Research sentiment score: {research_sentiment:.2f}.

Key positives identified:
{research_positives}

## 6. RISK MITIGANTS

- GST filings are largely compliant with {_safe_get(company_data, 'gst_filing_delays_count', 0)} delays reported
- Network contagion risk score of {_safe_get(company_data, 'contagion_risk_score', 0.0):.2f} is within monitored range
- Promoter pledge at {_display_pct(company_data.get('promoter_pledge_pct'))} is manageable with covenant oversight
- {archetype_note}
- Ensemble ML model consensus supports the lending decision
"""


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN ENTRY: WRITE BULL CASE                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def write_bull_case(company_data: dict, research: dict) -> str:
    """
    Write the strongest possible case FOR approving the loan application.

    Uses Claude API to generate a structured bull case analysis.
    Falls back to rule-based template if API is unavailable.

    Args:
        company_data: Dict with all company financials, ML scores, alt data signals.
                      Keys match the synthetic dataset schema (dscr, ebitda_margin, etc.)
        research: Dict from research_agent.run_research() output.
                  Keys: industry_outlook, key_positives_found, research_sentiment_score, etc.

    Returns:
        Structured bull case text (400-600 words) with sections:
        1. Executive Summary, 2. Financial Strengths, 3. Business Momentum,
        4. Management Quality, 5. Industry Tailwinds, 6. Risk Mitigants
    """
    logger.info(f"Writing bull case for: {company_data.get('company_name', 'Unknown')}")

    # Build the prompt
    ctx = _build_prompt_context(company_data, research)
    user_prompt = BULL_CASE_TEMPLATE.format(**ctx)

    # Try Gemini API
    api_key = _get_gemini_api_key()
    if api_key:
        result = _call_gemini_with_retry(
            api_key=api_key,
            system_prompt=APPROVAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_retries=2,
            max_tokens=2048,
        )
        if result:
            logger.info("Bull case generated via Gemini API")
            return result
        logger.warning("Gemini API returned no result — using fallback")

    # Fallback: rule-based generation
    logger.info("Using rule-based fallback bull case")
    return _fallback_bull_case(company_data, research)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    # Demo with Sunrise Textile Mills sample data
    demo_company = {
        "company_name": "Sunrise Textile Mills",
        "sector": "Textiles",
        "fiscal_year": "FY2024",
        "revenue": 850.0,
        "ebitda": 127.5,
        "ebitda_margin": 0.15,
        "pat": 51.0,
        "net_margin": 0.06,
        "dscr": 1.85,
        "interest_coverage": 2.4,
        "debt_to_equity": 1.6,
        "current_ratio": 1.25,
        "roe": 0.14,
        "roa": 0.06,
        "cfo": 95.0,
        "free_cash_flow": 42.0,
        "total_debt": 520.0,
        "total_equity": 325.0,
        "ensemble_pd": 0.12,
        "xgb_pd": 0.11,
        "lending_decision": "APPROVE",
        "model_confidence": "HIGH_CONSENSUS",
        "risk_premium": 3.5,
        "satellite_activity_score": 82.5,
        "satellite_activity_category": "ACTIVE",
        "gst_vs_bank_divergence": 0.03,
        "gst_filing_delays_count": 1,
        "contagion_risk_score": 0.15,
        "promoter_holding_pct": 0.62,
        "promoter_pledge_pct": 0.08,
        "ceo_sentiment_overall": 0.72,
        "ceo_specificity_score": 0.65,
        "ceo_deflection_score": 0.18,
    }

    demo_research = {
        "industry_outlook": "POSITIVE",
        "research_sentiment_score": 0.72,
        "key_positives_found": [
            "Government PLI scheme support for textile sector",
            "China+1 sourcing trend benefiting Indian manufacturers",
            "Steady domestic demand growth",
        ],
        "key_risks_found": [
            "Raw material price volatility",
            "Global demand slowdown risk",
        ],
    }

    print("\n" + "=" * 60)
    print("APPROVAL AGENT — Bull Case (Standalone Test)")
    print("=" * 60)

    bull_case = write_bull_case(demo_company, demo_research)
    print(bull_case)
    print("=" * 60)
