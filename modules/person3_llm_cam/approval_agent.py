"""
Intelli-Credit — Approval Agent (Person 3, Innovation 10)
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

# ── Anthropic Claude ─────────────────────────────────────────────────────────
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic not installed — will use fallback bull case")
    ANTHROPIC_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

APPROVAL_SYSTEM_PROMPT = """You are a senior credit analyst at Vivriti Capital. Your job is to \
write the strongest possible case FOR approving this loan application. \
Use all available data — financial ratios, industry research, management \
quality, collateral — to build a compelling bull case for lending. \
Be specific with numbers. Reference actual data points.

You write in a formal but confident tone appropriate for an Indian NBFC credit committee memo.
Always structure your analysis with clear headers and bullet points.
Reference specific financial metrics (DSCR, ICR, D/E ratio, margins) with exact values.
"""

BULL_CASE_TEMPLATE = """Write a comprehensive BULL CASE (case for approval) for the following loan application.

## COMPANY PROFILE
Company: {company_name}
Sector: {sector}
Fiscal Year: {fiscal_year}

## KEY FINANCIAL METRICS
- Revenue: ₹{revenue:.1f} Cr
- EBITDA: ₹{ebitda:.1f} Cr (Margin: {ebitda_margin:.1%})
- PAT: ₹{pat:.1f} Cr (Net Margin: {net_margin:.1%})
- DSCR: {dscr:.2f}x
- Interest Coverage Ratio: {interest_coverage:.2f}x
- Debt-to-Equity: {debt_to_equity:.2f}x
- Current Ratio: {current_ratio:.2f}x
- ROE: {roe:.1%}
- ROA: {roa:.1%}
- Cash Flow from Operations: ₹{cfo:.1f} Cr
- Free Cash Flow: ₹{free_cash_flow:.1f} Cr
- Total Debt: ₹{total_debt:.1f} Cr
- Total Equity: ₹{total_equity:.1f} Cr

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
- Promoter Holding: {promoter_holding_pct:.1%} (Pledged: {promoter_pledge_pct:.1%})

## CEO INTERVIEW SIGNALS
- Overall Sentiment: {ceo_sentiment_overall:.2f}
- Specificity Score: {ceo_specificity_score:.2f}
- Deflection Score: {ceo_deflection_score:.2f}

## RESEARCH INTELLIGENCE
Industry Outlook: {industry_outlook}
Research Sentiment: {research_sentiment_score:.2f}

Key Positives from Research:
{research_positives}

---

WRITE THE BULL CASE WITH THESE EXACT SECTIONS:

1. **EXECUTIVE SUMMARY** — 3-4 sentences positively framing the lending opportunity
2. **FINANCIAL STRENGTHS** — Top 3-5 strongest ratios/metrics with exact numbers
3. **BUSINESS MOMENTUM** — Growth signals, revenue trajectory, market position
4. **MANAGEMENT QUALITY** — Positive signals from CEO interview, promoter track record
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


def _build_prompt_context(company_data: dict, research: dict) -> dict:
    """
    Build the template context dict from raw company_data and research.
    All values are safely extracted with sensible defaults.
    """
    return {
        "company_name": _safe_get(company_data, "company_name", "Unknown Company"),
        "sector": _safe_get(company_data, "sector", "General"),
        "fiscal_year": _safe_get(company_data, "fiscal_year", "FY2024"),
        # P&L
        "revenue": _safe_get(company_data, "revenue"),
        "ebitda": _safe_get(company_data, "ebitda"),
        "ebitda_margin": _safe_get(company_data, "ebitda_margin"),
        "pat": _safe_get(company_data, "pat"),
        "net_margin": _safe_get(company_data, "net_margin"),
        # Ratios
        "dscr": _safe_get(company_data, "dscr", 1.0),
        "interest_coverage": _safe_get(company_data, "interest_coverage", 1.0),
        "debt_to_equity": _safe_get(company_data, "debt_to_equity"),
        "current_ratio": _safe_get(company_data, "current_ratio"),
        "roe": _safe_get(company_data, "roe"),
        "roa": _safe_get(company_data, "roa"),
        # Cash flow
        "cfo": _safe_get(company_data, "cfo"),
        "free_cash_flow": _safe_get(company_data, "free_cash_flow"),
        # Balance sheet
        "total_debt": _safe_get(company_data, "total_debt"),
        "total_equity": _safe_get(company_data, "total_equity"),
        # ML scores
        "ensemble_pd": _safe_get(company_data, "ensemble_pd", 0.15),
        "xgb_pd": _safe_get(company_data, "xgb_pd", 0.15),
        "lending_decision": _safe_get(company_data, "lending_decision", "REVIEW"),
        "model_confidence": _safe_get(company_data, "model_confidence", "MODERATE"),
        "risk_premium": _safe_get(company_data, "risk_premium", 4.0),
        # Alt data
        "satellite_activity_score": _safe_get(company_data, "satellite_activity_score", 70.0),
        "satellite_activity_category": _safe_get(company_data, "satellite_activity_category", "ACTIVE"),
        "gst_vs_bank_divergence": _safe_get(company_data, "gst_vs_bank_divergence"),
        "gst_filing_delays_count": _safe_get(company_data, "gst_filing_delays_count", 0),
        "contagion_risk_score": _safe_get(company_data, "contagion_risk_score"),
        "promoter_holding_pct": _safe_get(company_data, "promoter_holding_pct", 0.5),
        "promoter_pledge_pct": _safe_get(company_data, "promoter_pledge_pct"),
        # CEO interview
        "ceo_sentiment_overall": _safe_get(company_data, "ceo_sentiment_overall", 0.5),
        "ceo_specificity_score": _safe_get(company_data, "ceo_specificity_score", 0.5),
        "ceo_deflection_score": _safe_get(company_data, "ceo_deflection_score", 0.2),
        # Research
        "industry_outlook": research.get("industry_outlook", "NEUTRAL"),
        "research_sentiment_score": research.get("research_sentiment_score", 0.5),
        "research_positives": "\n".join(
            f"  - {p}" for p in research.get("key_positives_found", ["No data available"])
        ),
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ANTHROPIC API WITH RETRY                                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _get_anthropic_client() -> Optional[Any]:
    """Initialize Anthropic client from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not ANTHROPIC_AVAILABLE:
        return None
    try:
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to init Anthropic client: {e}")
        return None


def _call_claude_with_retry(
    client: Any,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Call Claude API with exponential backoff retry logic.

    Args:
        client: Anthropic client instance
        system_prompt: System-level instruction
        user_prompt: User message content
        max_retries: Number of retry attempts (default 3)
        max_tokens: Max response tokens

    Returns:
        Response text or None on failure
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text.strip()
        except anthropic.RateLimitError as e:
            wait = 2 ** attempt
            logger.warning(f"Rate limited (attempt {attempt}/{max_retries}), waiting {wait}s...")
            time.sleep(wait)
        except anthropic.APIConnectionError as e:
            wait = 2 ** attempt
            logger.warning(f"Connection error (attempt {attempt}/{max_retries}), waiting {wait}s: {e}")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"Claude API error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    logger.error("All Claude API retries exhausted")
    return None


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FALLBACK BULL CASE                                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _fallback_bull_case(company_data: dict, research: dict) -> str:
    """
    Generate a rule-based bull case when Claude API is unavailable.
    Uses template filling with actual data values — no LLM needed.
    """
    ctx = _build_prompt_context(company_data, research)
    name = ctx["company_name"]
    sector = ctx["sector"]

    # Identify top financial strengths
    strengths = []
    if ctx["dscr"] >= 1.5:
        strengths.append(f"Healthy DSCR of {ctx['dscr']:.2f}x (well above 1.0 threshold)")
    if ctx["interest_coverage"] >= 1.5:
        strengths.append(f"Strong interest coverage of {ctx['interest_coverage']:.2f}x")
    if ctx["ebitda_margin"] >= 0.12:
        strengths.append(f"Robust EBITDA margin of {ctx['ebitda_margin']:.1%}")
    if ctx["current_ratio"] >= 1.0:
        strengths.append(f"Adequate liquidity with current ratio of {ctx['current_ratio']:.2f}x")
    if ctx["cfo"] > 0:
        strengths.append(f"Positive operating cash flow of ₹{ctx['cfo']:.1f} Cr")
    if ctx["debt_to_equity"] < 2.5:
        strengths.append(f"Manageable leverage at {ctx['debt_to_equity']:.2f}x D/E")
    if not strengths:
        strengths.append("Operational track record in the sector")

    strengths_text = "\n".join(f"   - {s}" for s in strengths[:5])
    positives_text = ctx["research_positives"]

    return f"""## 1. EXECUTIVE SUMMARY

{name} operating in the {sector} sector presents a viable lending opportunity. \
The company demonstrates {ctx['dscr']:.2f}x DSCR, {ctx['ebitda_margin']:.1%} EBITDA margin, \
and ₹{ctx['cfo']:.1f} Cr positive operating cash flow, indicating adequate \
debt servicing capacity. ML models assign an ensemble PD of {ctx['ensemble_pd']:.2%}, \
supporting a {ctx['lending_decision']} recommendation.

## 2. FINANCIAL STRENGTHS

{strengths_text}

## 3. BUSINESS MOMENTUM

Revenue of ₹{ctx['revenue']:.1f} Cr with EBITDA of ₹{ctx['ebitda']:.1f} Cr \
reflects a functioning business model. Free cash flow of ₹{ctx['free_cash_flow']:.1f} Cr \
provides internal funding capacity. The satellite activity score of \
{ctx['satellite_activity_score']:.1f} ({ctx['satellite_activity_category']}) \
confirms operational activity at the physical premises.

## 4. MANAGEMENT QUALITY

Promoter holding at {ctx['promoter_holding_pct']:.1%} reflects skin in the game. \
CEO interview sentiment score of {ctx['ceo_sentiment_overall']:.2f} with specificity \
at {ctx['ceo_specificity_score']:.2f} suggests reasonable management transparency. \
Deflection score of {ctx['ceo_deflection_score']:.2f} is within acceptable range.

## 5. INDUSTRY TAILWINDS

Industry outlook is assessed as {ctx['industry_outlook']}. \
Research sentiment score: {ctx['research_sentiment_score']:.2f}.

Key positives identified:
{positives_text}

## 6. RISK MITIGANTS

- GST filings are largely compliant with {ctx['gst_filing_delays_count']} delays reported
- Network contagion risk score of {ctx['contagion_risk_score']:.2f} is within monitored range
- Promoter pledge at {ctx['promoter_pledge_pct']:.1%} is manageable with covenant oversight
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

    # Try Claude API
    client = _get_anthropic_client()
    if client:
        result = _call_claude_with_retry(
            client=client,
            system_prompt=APPROVAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_retries=3,
            max_tokens=2048,
        )
        if result:
            logger.info("Bull case generated via Claude API")
            return result
        logger.warning("Claude API returned no result — using fallback")

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
