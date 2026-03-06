"""
Yakṣarāja — Dissent Agent + Coordinator (Person 3, Innovation 10)
========================================================================
The "Bear Case" agent and final recommendation coordinator in the
adversarial two-agent CAM system.

The dissent agent challenges every optimistic assumption made by the
approval agent. The coordinator synthesizes both views into a balanced
lending recommendation — mirroring real credit committee dynamics.

Author: Person 3
Module: modules/person3_llm_cam/dissent_agent.py
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
    logger.warning("google-genai not installed — will use fallback bear case")
    GEMINI_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

DISSENT_SYSTEM_PROMPT = """You are the devil's advocate on Vivriti Capital's credit committee.
Your ONLY job is to find every possible reason NOT to approve this loan.
Challenge every optimistic assumption. Find every red flag in the data.
Be specific and cite exact numbers. You must produce at least 4-5
counter-arguments regardless of how strong the application looks.

=== MANDATORY RULES ===

RULE 1 — FINANCIAL DATA: Use ONLY the figures provided. Never invent, estimate, or
use placeholder financials. If a figure is missing, write "[DATA REQUIRED]".

RULE 2 — COMPANY IDENTITY: The sector and all narrative must match the actual company.
Never write about a fictional or substitute company.

RULE 3 — SECTOR-APPROPRIATE STRESS SCENARIOS:
- Steel: iron ore price spike, coking coal costs, construction/auto demand slowdown,
  EU carbon border adjustment (CBAM), China dumping.
- Wind Energy: nacelle/blade component cost inflation, RPO mandate revision,
  PPA rate compression, interest rate sensitivity on project financing,
  order execution delays, DISCOM credit risk, ISTS waiver policy changes.
- Textiles: cotton/raw material price spike, export demand contraction,
  INR appreciation, working capital squeeze.
- General: revenue decline, interest rate rise, working capital pressure.
Never apply textile or agricultural commodity stresses to steel or wind energy companies.

RULE 4 — INTERNAL CONSISTENCY:
(a) DSCR < 1.0 → decision = REJECT. Do NOT set a credit limit.
(b) Gross margin and EBITDA margin must be arithmetically consistent.
(c) A Bear metric (DSCR 0.47) cannot be cited as a Bull strength.
(d) Bull Case and Bear Case must use the same underlying figures.
(e) PD > 40% → recommend REJECT.

RULE 5 — MANAGEMENT QUALITY: Generate scores ONLY if an earnings call transcript
or interview is provided. If not, write: "INSUFFICIENT DATA — No transcript provided."

RULE 6 — DEFAULT ARCHETYPE: Assign only if genuine distress pattern exists.
For companies with strong positive operating cash flows, write: "No close default archetype."

RULE 7 — PROMOTER SHAREHOLDING: Use only figures from actual data.

You write in a formal, sharply analytical tone. You never hedge — you always
make the strongest possible negative case. You look for hidden risks,
trajectory problems, and data inconsistencies that others miss.
"""

BEAR_CASE_TEMPLATE = """Write a comprehensive BEAR CASE (case against approval) for this loan application.

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

## FORENSIC & AUDIT FLAGS
- Beneish M-Score: {beneish_m_score:.2f} (>{beneish_threshold} = manipulation risk)
- Altman Z-Score: {altman_z_score:.2f}
- Piotroski F-Score: {piotroski_f_score:.0f}/9
- Auditor Distress Score: {auditor_distress_score}/5
- Going Concern Flag: {going_concern_flag}
- Qualified Opinion Flag: {qualified_opinion_flag}
- Related Party Transactions to Revenue: {related_party_tx_to_rev:.1%}

## ML CREDIT SCORES
- Ensemble PD: {ensemble_pd:.2%}
- Model Disagreement: {model_disagreement}
- Risk Premium: {risk_premium:.2f}%

## ALTERNATIVE DATA FLAGS
- Satellite Activity: {satellite_activity_score:.1f} ({satellite_activity_category})
- Satellite vs Revenue Flag: {satellite_vs_revenue_flag}
- GST Divergence: {gst_vs_bank_divergence:.1%} (Flag: {gst_divergence_flag})
- GST Filing Delays: {gst_filing_delays_count}
- GST Payment Delay Days: {gst_payment_delay_days:.0f}
- Network Contagion Risk: {contagion_risk_score:.2f}
- Promoter Pledge: {promoter_pledge_pct:.1%}
- Promoter NPA Companies: {promoter_npa_companies}
- DIN Disqualified Directors: {din_disqualified_count}

## CEO INTERVIEW SIGNALS
- Deflection Score: {ceo_deflection_score:.2f}
- Overconfidence Score: {ceo_overconfidence_score:.2f}
- Specificity Score: {ceo_specificity_score:.2f}
- Revenue Sentiment: {ceo_sentiment_revenue:.2f}
- Debt Sentiment: {ceo_sentiment_debt:.2f}

## RESEARCH INTELLIGENCE — RISKS IDENTIFIED
{research_risks}

## THE APPROVAL AGENT WROTE THIS BULL CASE:
--- BEGIN BULL CASE ---
{approval_text}
--- END BULL CASE ---

---

NOW WRITE THE BEAR CASE. You MUST argue AGAINST approval. Challenge the bull case directly.

Structure your response with EXACTLY these sections:

1. **CRITICAL CONCERNS** — Top 3-5 red flags with exact numbers from the data
2. **CHALLENGES TO BULL CASE ASSUMPTIONS** — Specifically rebut 3-4 claims the approval agent made
3. **HIDDEN RISKS** — Network risk, trajectory problems, audit signals, forensic flags
4. **STRESS SCENARIO IMPACT** — What happens if revenue drops 20%, or interest rates rise 200bps
5. **RECOMMENDED CONDITIONS IF APPROVED** — Specific covenants, guarantees, monitoring requirements

You MUST produce at least 4-5 strong counter-arguments. Target length: 400-600 words.
"""

# ── Coordinator synthesis prompt ─────────────────────────────────────────────

COORDINATOR_SYSTEM_PROMPT = """You are the Chief Risk Officer at Vivriti Capital. You have received \
both a bull case (for approval) and a bear case (against approval) for a loan application. \
Your job is to synthesize these into a balanced, final recommendation.

You must weigh both arguments fairly, consider the ML model scores, and produce \
a practical lending decision. You are neither optimistic nor pessimistic — you are pragmatic.
"""

COORDINATOR_TEMPLATE = """Given the following bull case and bear case arguments, plus ML scores, \
produce a balanced final lending recommendation.

## ML SCORES
- Ensemble PD: {ensemble_pd:.2%}
- DSCR: {dscr:.2f}x
- Lending Decision from ML: {lending_decision}
- Risk Premium: {risk_premium:.2f}%
- Revenue: ₹{revenue:.1f} Cr

## BULL CASE:
{bull_case}

## BEAR CASE:
{bear_case}

---

Return a JSON object with EXACTLY these keys:
{{
  "lending_decision": "APPROVE" or "CONDITIONAL_APPROVE" or "REJECT",
  "recommended_limit_cr": <float, recommended credit limit in Crores>,
  "recommended_rate_pct": <float, recommended interest rate %>,
  "key_conditions": ["condition1", "condition2", ...],
  "bull_summary": "<2-3 sentence summary of the strongest bull arguments>",
  "bear_summary": "<2-3 sentence summary of the strongest bear arguments>",
  "final_rationale": "<balanced 3-4 sentence final paragraph explaining the decision>"
}}

Guidelines for the decision:
- If PD < 0.20 and DSCR > 1.5: lean toward APPROVE or CONDITIONAL_APPROVE
- If PD between 0.20 and 0.40: likely CONDITIONAL_APPROVE with strong covenants
- If PD > 0.40 or DSCR < 1.0: MUST REJECT — do NOT set a credit limit
- If decision is REJECT, set recommended_limit_cr to 0
- recommended_limit_cr = revenue * 0.25 * (1 - PD) as a starting point
- recommended_rate_pct = repo_rate(6.5%) + risk_premium from ML model
- key_conditions should be specific covenants (DSCR floor, pledge limits, reporting requirements)

Return ONLY valid JSON, no other text.
"""


# ── Sector-specific stress scenario registry (Rule 3) ───────────────────────

SECTOR_STRESS_SCENARIOS = {
    "Steel": [
        "Iron ore price spike +40%",
        "Coking coal cost surge +35%",
        "Construction/auto demand slowdown -25%",
        "EU Carbon Border Adjustment (CBAM) impact",
        "China steel dumping — price compression",
    ],
    "Metals & Mining": [
        "Iron ore price spike +40%",
        "Coking coal cost surge +35%",
        "Construction/auto demand slowdown -25%",
        "EU Carbon Border Adjustment (CBAM) impact",
        "China metals dumping — price compression",
    ],
    "Wind Energy": [
        "Nacelle/blade component cost inflation +20%",
        "RPO mandate revision — reduced renewable obligations",
        "PPA rate compression -15%",
        "Interest rate sensitivity on project financing +200bps",
        "Order execution delays — supply chain disruption",
        "DISCOM credit risk / payment delays 180+ days",
        "ISTS waiver policy changes",
    ],
    "Renewable Energy": [
        "Nacelle/blade component cost inflation +20%",
        "RPO mandate revision — reduced renewable obligations",
        "PPA rate compression -15%",
        "Interest rate sensitivity on project financing +200bps",
        "DISCOM credit risk / payment delays 180+ days",
    ],
    "Textiles": [
        "Cotton/raw material price spike +30%",
        "Export demand contraction -20%",
        "INR appreciation eroding export competitiveness",
        "Working capital squeeze — receivable cycle elongation",
        "China+1 trend reversal risk",
    ],
    "default": [
        "Revenue decline -20%",
        "Interest rate increase +200bps",
        "Working capital pressure — receivable cycle elongation",
        "Key customer/supplier concentration risk materializing",
        "Commodity input cost spike +25%",
    ],
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HELPER FUNCTIONS                                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _safe_get(data: dict, key: str, default: Any = 0.0) -> Any:
    """Safely extract a value from company data."""
    val = data.get(key, default)
    return default if val is None else val


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
    Call Gemini with exponential backoff retry on rate-limit and connection errors.
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


def _build_bear_context(company_data: dict, research: dict) -> dict:
    """Build template context for the bear case prompt."""
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
        # Forensic flags
        "beneish_m_score": _safe_get(company_data, "beneish_m_score", -2.5),
        "beneish_threshold": -2.22,
        "altman_z_score": _safe_get(company_data, "altman_z_score", 2.0),
        "piotroski_f_score": _safe_get(company_data, "piotroski_f_score", 5),
        "auditor_distress_score": _safe_get(company_data, "auditor_distress_score", 1),
        "going_concern_flag": _safe_get(company_data, "going_concern_flag", 0),
        "qualified_opinion_flag": _safe_get(company_data, "qualified_opinion_flag", 0),
        "related_party_tx_to_rev": _safe_get(company_data, "related_party_tx_to_rev"),
        # ML scores
        "ensemble_pd": _safe_get(company_data, "ensemble_pd", 0.15),
        "model_disagreement": _safe_get(company_data, "model_disagreement_flag", "CONSENSUS"),
        "risk_premium": _safe_get(company_data, "risk_premium", 4.0),
        # Alt data
        "satellite_activity_score": _safe_get(company_data, "satellite_activity_score", 70.0),
        "satellite_activity_category": _safe_get(company_data, "satellite_activity_category", "ACTIVE"),
        "satellite_vs_revenue_flag": _safe_get(company_data, "satellite_vs_revenue_flag", 0),
        "gst_vs_bank_divergence": _safe_get(company_data, "gst_vs_bank_divergence"),
        "gst_divergence_flag": _safe_get(company_data, "gst_divergence_flag", 0),
        "gst_filing_delays_count": _safe_get(company_data, "gst_filing_delays_count", 0),
        "gst_payment_delay_days": _safe_get(company_data, "gst_payment_delay_days", 0),
        "contagion_risk_score": _safe_get(company_data, "contagion_risk_score"),
        "promoter_pledge_pct": _safe_get(company_data, "promoter_pledge_pct"),
        "promoter_npa_companies": _safe_get(company_data, "promoter_npa_companies", 0),
        "din_disqualified_count": _safe_get(company_data, "din_disqualified_count", 0),
        # CEO interview
        "ceo_deflection_score": _safe_get(company_data, "ceo_deflection_score", 0.2),
        "ceo_overconfidence_score": _safe_get(company_data, "ceo_overconfidence_score", 0.3),
        "ceo_specificity_score": _safe_get(company_data, "ceo_specificity_score", 0.5),
        "ceo_sentiment_revenue": _safe_get(company_data, "ceo_sentiment_revenue", 0.5),
        "ceo_sentiment_debt": _safe_get(company_data, "ceo_sentiment_debt", 0.3),
        # Research
        "research_risks": "\n".join(
            f"  - {r}" for r in research.get("key_risks_found", ["No risk data available"])
        ),
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART B — DISSENT AGENT: WRITE BEAR CASE                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _fallback_bear_case(company_data: dict, approval_text: str, research: dict) -> str:
    """
    Generate a rule-based bear case when Claude API is unavailable.
    Systematically finds and highlights every weak data point.
    Uses sector-appropriate stress scenarios (Rule 3).
    """
    ctx = _build_bear_context(company_data, research)
    name = ctx["company_name"]
    sector = ctx["sector"]

    # ── Identify red flags ────────────────────────────────────────────────────────────
    concerns = []
    if ctx["dscr"] < 1.5:
        concerns.append(f"DSCR of {ctx['dscr']:.2f}x leaves thin margin above 1.0 — any revenue shock could breach covenant")
    if ctx["dscr"] < 1.0:
        concerns.append(f"CRITICAL: DSCR of {ctx['dscr']:.2f}x is BELOW 1.0 — mandatory REJECT per underwriting policy (Rule 4a)")
    if ctx["debt_to_equity"] > 1.5:
        concerns.append(f"Debt-to-equity of {ctx['debt_to_equity']:.2f}x indicates high leverage concentration")
    if ctx["current_ratio"] < 1.2:
        concerns.append(f"Current ratio of {ctx['current_ratio']:.2f}x signals potential liquidity stress")
    if ctx["net_margin"] < 0.05:
        concerns.append(f"Net margin of {ctx['net_margin']:.1%} leaves minimal buffer for cost shocks")
    if ctx["ensemble_pd"] > 0.10:
        concerns.append(f"Ensemble PD of {ctx['ensemble_pd']:.2%} implies non-trivial default probability")
    if ctx["ensemble_pd"] > 0.40:
        concerns.append(f"CRITICAL: PD of {ctx['ensemble_pd']:.2%} exceeds 40% threshold — mandatory REJECT (Rule 4e)")
    if ctx["promoter_pledge_pct"] > 0.15:
        concerns.append(f"Promoter pledge at {ctx['promoter_pledge_pct']:.1%} — forced selling risk in downturn")
    if ctx["contagion_risk_score"] > 0.3:
        concerns.append(f"Network contagion score of {ctx['contagion_risk_score']:.2f} signals related-entity risk")
    if ctx["beneish_m_score"] > -2.22:
        concerns.append(f"Beneish M-Score of {ctx['beneish_m_score']:.2f} exceeds -2.22 manipulation threshold")
    if ctx["ceo_deflection_score"] > 0.3:
        concerns.append(f"CEO deflection score of {ctx['ceo_deflection_score']:.2f} raises transparency concerns")
    if ctx["gst_divergence_flag"]:
        concerns.append(f"GST-bank divergence of {ctx['gst_vs_bank_divergence']:.1%} flagged — potential revenue inflation")

    if len(concerns) < 4:
        concerns.extend([
            "Sector-level cyclicality could compress margins in downturn",
            "Working capital intensity may require additional credit lines",
            "Limited public information increases information asymmetry risk",
            f"Related party transactions at {ctx['related_party_tx_to_rev']:.1%} of revenue warrant scrutiny",
        ])

    concerns_text = "\n".join(f"   - {c}" for c in concerns[:6])
    risks_text = ctx["research_risks"]

    # ── Sector-appropriate stress scenario (Rule 3) ───────────────────────────────
    sector_scenarios = SECTOR_STRESS_SCENARIOS.get(
        sector, SECTOR_STRESS_SCENARIOS["default"]
    )
    sector_stress_text = "\n".join(f"   - {s}" for s in sector_scenarios[:5])

    stressed_revenue = ctx["revenue"] * 0.80
    stressed_ebitda = ctx["ebitda"] * 0.70
    stressed_dscr = ctx["dscr"] * 0.65

    return f"""## 1. CRITICAL CONCERNS

{concerns_text}

## 2. CHALLENGES TO BULL CASE ASSUMPTIONS

The approval agent's optimism must be tempered by the following:
   - DSCR of {ctx['dscr']:.2f}x is presented as "healthy" but in a stressed \
scenario (20% revenue drop) it falls to ~{stressed_dscr:.2f}x — below covenant level
   - Positive cash flow of ₹{ctx['cfo']:.1f} Cr masks high capex and debt service \
requirements; free cash flow to total debt is only {(ctx['free_cash_flow']/max(ctx['total_debt'],1))*100:.1f}%
   - The satellite activity score, while positive, cannot substitute for actual \
bank statement analysis and trade verification
   - Industry tailwinds cited are sector-level — individual company execution risk remains

## 3. HIDDEN RISKS

   - Network contagion risk score of {ctx['contagion_risk_score']:.2f} — if related \
entities face stress, cross-default risk materializes
   - Auditor distress score of {ctx['auditor_distress_score']}/5 warrants \
attention to audit quality and reporting reliability
   - CEO overconfidence score at {ctx['ceo_overconfidence_score']:.2f} suggests \
management may be underestimating downside scenarios
   - Promoter holds {ctx['promoter_npa_companies']} NPA-associated companies and \
{ctx['din_disqualified_count']} disqualified DINs in their director network

Research-identified risks:
{risks_text}

## 4. STRESS SCENARIO IMPACT ({sector} Sector)

Sector-specific stress scenarios to consider:
{sector_stress_text}

Under a moderate stress scenario (20% revenue decline, 200bps rate increase):
   - Revenue falls to ₹{stressed_revenue:.1f} Cr
   - EBITDA compresses to ~₹{stressed_ebitda:.1f} Cr
   - DSCR drops to ~{stressed_dscr:.2f}x — likely covenant breach
   - Interest coverage thins significantly, increasing refinancing risk

## 5. RECOMMENDED CONDITIONS IF APPROVED

If the committee proceeds despite the above concerns:
   - DSCR floor covenant at 1.20x with quarterly monitoring
   - Promoter personal guarantee covering at least 50% of exposure
   - Pledge ceiling at 25% — automatic prepayment trigger if breached
   - Quarterly GST return cross-verification with bank statements
   - Semi-annual independent audit of related party transactions
   - Credit limit step-down clause if EBITDA margin falls below 10%
   - Mandatory escrow of 2 months' debt service as cash collateral
"""


def write_bear_case(
    company_data: dict,
    approval_text: str,
    research: dict,
) -> str:
    """
    Write the strongest possible case AGAINST approving the loan application.

    The dissent agent challenges the bull case and finds every red flag.

    Args:
        company_data: Dict with all company financials, ML scores, alt data signals.
        approval_text: The bull case text from the approval agent (to argue against).
        research: Dict from research_agent.run_research() output.

    Returns:
        Structured bear case text (400-600 words) with sections:
        1. Critical Concerns, 2. Challenges to Bull Case,
        3. Hidden Risks, 4. Stress Scenario, 5. Recommended Conditions
    """
    logger.info(f"Writing bear case for: {company_data.get('company_name', 'Unknown')}")

    # Build prompt context
    ctx = _build_bear_context(company_data, research)
    ctx["approval_text"] = approval_text
    user_prompt = BEAR_CASE_TEMPLATE.format(**ctx)

    # Try Gemini API
    api_key = _get_gemini_api_key()
    if api_key:
        result = _call_gemini_with_retry(
            api_key=api_key,
            system_prompt=DISSENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_retries=2,
            max_tokens=2048,
        )
        if result:
            logger.info("Bear case generated via Gemini API")
            return result
        logger.warning("Gemini API returned no result — using fallback")

    # Fallback
    logger.info("Using rule-based fallback bear case")
    return _fallback_bear_case(company_data, approval_text, research)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART C — COORDINATOR: SYNTHESIZE FINAL RECOMMENDATION                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _fallback_synthesis(
    bull_case: str,
    bear_case: str,
    scores: dict,
) -> dict:
    """
    Rule-based coordinator fallback when Claude API is unavailable.
    Uses ML scores and simple heuristics to produce a recommendation.
    Enforces Rule 4a (DSCR < 1.0 → REJECT) and Rule 4e (PD > 0.40 → REJECT).
    """
    pd = scores.get("ensemble_pd", 0.25)
    dscr = scores.get("dscr", 1.0)
    revenue = scores.get("revenue", 500.0)
    risk_premium = scores.get("risk_premium", 4.0)

    # Decision logic — Rule 4a: DSCR < 1.0 → REJECT, Rule 4e: PD > 0.40 → REJECT
    if dscr < 1.0 or pd > 0.40:
        decision = "REJECT"
    elif pd < 0.20 and dscr > 1.5:
        decision = "APPROVE"
    else:
        decision = "CONDITIONAL_APPROVE"

    # Limit: 0 for REJECT (Rule 4a), revenue * 0.25 * (1 - PD) otherwise
    if decision == "REJECT":
        limit = 0.0
    else:
        limit = round(revenue * 0.25 * (1 - pd), 1)

    # Rate: repo(6.5%) + risk premium
    rate = round(6.5 + risk_premium, 2)

    # Conditions
    conditions = []
    if decision == "REJECT":
        reject_reasons = []
        if dscr < 1.0:
            reject_reasons.append(f"DSCR of {dscr:.2f}x is below 1.0 — mandatory reject per underwriting policy")
        if pd > 0.40:
            reject_reasons.append(f"PD of {pd:.2%} exceeds 40% threshold — mandatory reject per risk policy")
        conditions = reject_reasons
    else:
        if dscr < 2.0:
            conditions.append(f"DSCR floor covenant at 1.20x — quarterly monitoring")
        conditions.append("Promoter personal guarantee covering 50% of exposure")
        if scores.get("promoter_pledge_pct", 0) > 0.10:
            conditions.append("Promoter pledge cap at 25% — automatic prepayment trigger if breached")
        conditions.append("Quarterly GST cross-verification with bank statements")
        if scores.get("contagion_risk_score", 0) > 0.25:
            conditions.append("Semi-annual audit of related party transactions")
        conditions.append("Annual credit review with fresh financials")

    return {
        "lending_decision": decision,
        "recommended_limit_cr": limit,
        "recommended_rate_pct": rate,
        "key_conditions": conditions,
        "bull_summary": (
            f"The approval agent highlights DSCR of {dscr:.2f}x, positive operating cash flow, "
            f"and favourable industry outlook as key strengths supporting a {decision.lower().replace('_', ' ')} decision."
        ),
        "bear_summary": (
            f"The dissent agent flags ensemble PD of {pd:.2%}, leverage concerns, "
            f"and stress scenario vulnerabilities as reasons for caution and strong covenant protection."
        ),
        "final_rationale": (
            f"After weighing both perspectives, the committee recommends a {decision.replace('_', ' ')} "
            f"with {'no credit limit' if decision == 'REJECT' else f'a credit limit of ₹{limit:.1f} Cr at {rate:.2f}% interest rate'}. "
            f"The ML ensemble assigns a PD of {pd:.2%} and DSCR of {dscr:.2f}x. "
            f"{'Key conditions are attached to mitigate downside risks identified by the dissent agent.' if decision != 'REJECT' else 'The risk profile does not meet the minimum underwriting standards at this time.'}"
        ),
    }


def synthesize_cam_recommendation(
    bull_case: str,
    bear_case: str,
    scores: dict,
) -> dict:
    """
    Synthesize a balanced, final lending recommendation from the
    adversarial bull and bear case arguments.

    Acts as the Chief Risk Officer — weighing both sides pragmatically.

    Args:
        bull_case: Full text of the approval agent's bull case
        bear_case: Full text of the dissent agent's bear case
        scores: Dict with key ML scores. Required keys:
                ensemble_pd, dscr, lending_decision, risk_premium, revenue

    Returns:
        {
            "lending_decision": "APPROVE" | "CONDITIONAL_APPROVE" | "REJECT",
            "recommended_limit_cr": float,
            "recommended_rate_pct": float,
            "key_conditions": [str, ...],
            "bull_summary": str,
            "bear_summary": str,
            "final_rationale": str,
        }
    """
    logger.info("Synthesizing adversarial CAM recommendation...")

    # Build coordinator prompt
    ctx = {
        "ensemble_pd": scores.get("ensemble_pd", 0.25),
        "dscr": scores.get("dscr", 1.0),
        "lending_decision": scores.get("lending_decision", "REVIEW"),
        "risk_premium": scores.get("risk_premium", 4.0),
        "revenue": scores.get("revenue", 500.0),
        "bull_case": bull_case,
        "bear_case": bear_case,
    }
    user_prompt = COORDINATOR_TEMPLATE.format(**ctx)

    # Try Gemini API
    api_key = _get_gemini_api_key()
    if api_key:
        result = _call_gemini_with_retry(
            api_key=api_key,
            system_prompt=COORDINATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_retries=2,
            max_tokens=1536,
        )
        if result:
            try:
                # Parse JSON — handle possible markdown wrapping
                text = result.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(text)

                # Validate required keys
                required = [
                    "lending_decision", "recommended_limit_cr", "recommended_rate_pct",
                    "key_conditions", "bull_summary", "bear_summary", "final_rationale",
                ]
                if all(k in parsed for k in required):
                    logger.info(f"Recommendation synthesized: {parsed['lending_decision']}")
                    return parsed
                else:
                    missing = [k for k in required if k not in parsed]
                    logger.warning(f"Gemini response missing keys {missing} — using fallback")
            except json.JSONDecodeError as e:
                logger.error(f"Gemini returned invalid JSON: {e}")

    # Fallback
    logger.info("Using rule-based fallback recommendation synthesis")
    return _fallback_synthesis(bull_case, bear_case, scores)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    # Import the approval agent for full adversarial test
    from modules.person3_llm_cam.approval_agent import write_bull_case

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
        "beneish_m_score": -2.45,
        "altman_z_score": 2.3,
        "piotroski_f_score": 6,
        "auditor_distress_score": 1,
        "going_concern_flag": 0,
        "qualified_opinion_flag": 0,
        "related_party_tx_to_rev": 0.05,
        "ensemble_pd": 0.12,
        "xgb_pd": 0.11,
        "lending_decision": "APPROVE",
        "model_confidence": "HIGH_CONSENSUS",
        "model_disagreement_flag": "CONSENSUS",
        "risk_premium": 3.5,
        "satellite_activity_score": 82.5,
        "satellite_activity_category": "ACTIVE",
        "satellite_vs_revenue_flag": 0,
        "gst_vs_bank_divergence": 0.03,
        "gst_divergence_flag": 0,
        "gst_filing_delays_count": 1,
        "gst_payment_delay_days": 12,
        "contagion_risk_score": 0.15,
        "promoter_holding_pct": 0.62,
        "promoter_pledge_pct": 0.08,
        "promoter_npa_companies": 0,
        "din_disqualified_count": 0,
        "ceo_sentiment_overall": 0.72,
        "ceo_specificity_score": 0.65,
        "ceo_deflection_score": 0.18,
        "ceo_overconfidence_score": 0.22,
        "ceo_sentiment_revenue": 0.70,
        "ceo_sentiment_debt": 0.45,
    }

    demo_research = {
        "industry_outlook": "POSITIVE",
        "research_sentiment_score": 0.72,
        "key_positives_found": [
            "PLI scheme support", "China+1 trend", "Domestic demand growth",
        ],
        "key_risks_found": [
            "Raw material price volatility",
            "Global demand slowdown risk",
            "High working capital intensity",
        ],
    }

    print("\n" + "=" * 60)
    print("ADVERSARIAL CAM SYSTEM — Full Test")
    print("=" * 60)

    # Step 1: Bull case
    print("\n🟢 APPROVAL AGENT — BULL CASE:")
    print("-" * 40)
    bull = write_bull_case(demo_company, demo_research)
    print(bull)

    # Step 2: Bear case (reads & argues against the bull case)
    print("\n🔴 DISSENT AGENT — BEAR CASE:")
    print("-" * 40)
    bear = write_bear_case(demo_company, bull, demo_research)
    print(bear)

    # Step 3: Coordinator synthesis
    print("\n⚖️  COORDINATOR — FINAL RECOMMENDATION:")
    print("-" * 40)
    recommendation = synthesize_cam_recommendation(bull, bear, demo_company)
    print(f"Decision       : {recommendation['lending_decision']}")
    print(f"Limit (₹ Cr)   : {recommendation['recommended_limit_cr']}")
    print(f"Rate (%)       : {recommendation['recommended_rate_pct']}")
    print(f"Conditions     : {len(recommendation['key_conditions'])}")
    for c in recommendation["key_conditions"]:
        print(f"   • {c}")
    print(f"\nBull Summary   : {recommendation['bull_summary']}")
    print(f"Bear Summary   : {recommendation['bear_summary']}")
    print(f"Final Rationale: {recommendation['final_rationale']}")
    print("=" * 60)
