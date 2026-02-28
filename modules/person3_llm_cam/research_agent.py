"""
Intelli-Credit — Research Agent (Person 3, Innovation 9)
=========================================================
LangGraph-based web research agent that performs secondary research
on borrower companies and their industries before CAM generation.

Uses Tavily Search API for web research and Claude for intelligence
extraction. Falls back to synthetic data when APIs are unavailable.

Author: Person 3
Module: modules/person3_llm_cam/research_agent.py
"""

import os
import json
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── LangGraph imports ────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    logger.warning("langgraph not installed — will use fallback pipeline")
    LANGGRAPH_AVAILABLE = False

# ── Tavily search ────────────────────────────────────────────────────────────
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    logger.warning("tavily-python not installed — will use fallback data")
    TAVILY_AVAILABLE = False

# ── Anthropic Claude ─────────────────────────────────────────────────────────
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic not installed — will use fallback extraction")
    ANTHROPIC_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  GRAPH STATE                                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class ResearchState(TypedDict):
    """State flowing through the LangGraph research pipeline."""
    company_name: str
    sector: str
    promoter_name: str
    # Raw search results per category
    raw_company_news: List[Dict[str, Any]]
    raw_industry_outlook: List[Dict[str, Any]]
    raw_regulatory: List[Dict[str, Any]]
    raw_competitors: List[Dict[str, Any]]
    raw_promoter_info: List[Dict[str, Any]]
    # Extracted intelligence
    company_news_summary: str
    industry_outlook: str  # POSITIVE / NEUTRAL / NEGATIVE
    key_risks_found: List[str]
    key_positives_found: List[str]
    promoter_red_flags: List[str]
    research_sources: List[str]
    research_sentiment_score: float  # 0=very negative, 1=very positive
    # Error tracking
    errors: List[str]
    used_fallback: bool


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  TAVILY SEARCH HELPERS                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _get_tavily_client() -> Optional[Any]:
    """Initialize Tavily client with API key from environment."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or not TAVILY_AVAILABLE:
        return None
    try:
        return TavilyClient(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Tavily client: {e}")
        return None


def _tavily_search(client: Any, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Execute a single Tavily search query.
    Returns list of result dicts with keys: title, url, content, score.
    """
    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:2000],  # cap per-result length
                "score": r.get("score", 0.0),
            })
        # Also capture the AI-generated answer if available
        if response.get("answer"):
            results.insert(0, {
                "title": "Tavily AI Summary",
                "url": "",
                "content": response["answer"],
                "score": 1.0,
            })
        return results
    except Exception as e:
        logger.error(f"Tavily search failed for query '{query}': {e}")
        return []


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLAUDE INTELLIGENCE EXTRACTION                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _get_anthropic_client() -> Optional[Any]:
    """Initialize Anthropic Claude client from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not ANTHROPIC_AVAILABLE:
        return None
    try:
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
        return None


def _extract_intelligence(
    claude_client: Any,
    search_results: List[Dict[str, Any]],
    category: str,
    company_name: str,
) -> Dict[str, Any]:
    """
    Use Claude to extract credit-relevant intelligence from raw search results.
    Returns: {
        "summary": str,
        "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
        "key_facts": [str],
        "red_flags": [str],
        "positive_signals": [str],
        "sentiment_score": float  # 0-1
    }
    """
    if not claude_client or not search_results:
        return _empty_intelligence()

    # Build search context for Claude
    context_parts = []
    for i, r in enumerate(search_results[:8], 1):
        context_parts.append(
            f"[Source {i}] {r['title']}\n{r['content']}\nURL: {r['url']}"
        )
    search_context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a senior credit analyst at an Indian NBFC. Analyze these search results 
about {company_name} (category: {category}) and extract credit-relevant intelligence.

SEARCH RESULTS:
{search_context}

Return a JSON object with EXACTLY these keys:
{{
  "summary": "2-3 sentence summary of findings relevant to credit assessment",
  "sentiment": "POSITIVE" or "NEUTRAL" or "NEGATIVE",
  "key_facts": ["fact1", "fact2", ...],
  "red_flags": ["red flag1", ...],
  "positive_signals": ["positive signal1", ...],
  "sentiment_score": 0.65
}}

The sentiment_score should be 0.0 (extremely negative) to 1.0 (extremely positive).
Focus on financial health, management quality, regulatory risks, and business outlook.
Return ONLY valid JSON, no other text."""

    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Parse JSON — handle potential markdown wrapping
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON for {category}: {e}")
        return _empty_intelligence()
    except Exception as e:
        logger.error(f"Claude extraction failed for {category}: {e}")
        return _empty_intelligence()


def _empty_intelligence() -> Dict[str, Any]:
    """Return an empty intelligence extraction result."""
    return {
        "summary": "",
        "sentiment": "NEUTRAL",
        "key_facts": [],
        "red_flags": [],
        "positive_signals": [],
        "sentiment_score": 0.5,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  LANGGRAPH NODES — PART A: WEB RESEARCH                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def node_web_research(state: ResearchState) -> ResearchState:
    """
    PART A — Execute all 5 Tavily search queries in sequence.
    Populates raw_* fields in state.
    """
    company = state["company_name"]
    sector = state["sector"]
    promoter = state["promoter_name"]
    errors = list(state.get("errors", []))

    client = _get_tavily_client()
    if not client:
        logger.warning("Tavily unavailable — skipping web research")
        errors.append("Tavily API unavailable — web research skipped")
        return {
            **state,
            "raw_company_news": [],
            "raw_industry_outlook": [],
            "raw_regulatory": [],
            "raw_competitors": [],
            "raw_promoter_info": [],
            "errors": errors,
        }

    current_year = datetime.now().year
    queries = {
        "raw_company_news": f"{company} news {current_year} financial performance",
        "raw_industry_outlook": f"{sector} industry India outlook {current_year} challenges growth",
        "raw_regulatory": f"{sector} India regulatory RBI SEBI {current_year}",
        "raw_competitors": f"{sector} India major companies performance {current_year}",
        "raw_promoter_info": f"{promoter} company India news background",
    }

    results = {}
    sources = []
    for key, query in queries.items():
        logger.info(f"Searching: {query}")
        search_results = _tavily_search(client, query, max_results=5)
        results[key] = search_results
        for r in search_results:
            if r.get("url"):
                sources.append(r["url"])

    return {
        **state,
        **results,
        "research_sources": list(set(sources)),
        "errors": errors,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  LANGGRAPH NODE — PART B: INTELLIGENCE EXTRACTION                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def node_extract_intelligence(state: ResearchState) -> ResearchState:
    """
    PART B — Use Claude to extract credit-relevant intelligence
    from each category of search results.
    """
    company = state["company_name"]
    errors = list(state.get("errors", []))

    claude = _get_anthropic_client()
    if not claude:
        logger.warning("Anthropic unavailable — skipping intelligence extraction")
        errors.append("Anthropic API unavailable — extraction skipped")
        return {**state, "errors": errors}

    # Extract intelligence per category
    categories = {
        "Company News": state.get("raw_company_news", []),
        "Industry Outlook": state.get("raw_industry_outlook", []),
        "Regulatory Environment": state.get("raw_regulatory", []),
        "Competitors": state.get("raw_competitors", []),
        "Promoter Background": state.get("raw_promoter_info", []),
    }

    all_risks = []
    all_positives = []
    all_red_flags = []
    sentiment_scores = []
    summaries = []

    for category, results in categories.items():
        if not results:
            continue
        logger.info(f"Extracting intelligence: {category}")
        intel = _extract_intelligence(claude, results, category, company)

        summaries.append(f"**{category}**: {intel.get('summary', 'N/A')}")
        all_risks.extend(intel.get("red_flags", []))
        all_positives.extend(intel.get("positive_signals", []))
        sentiment_scores.append(intel.get("sentiment_score", 0.5))

        if category == "Promoter Background":
            all_red_flags.extend(intel.get("red_flags", []))

    # Determine overall industry outlook from industry extraction
    industry_intel = _extract_intelligence(
        claude, state.get("raw_industry_outlook", []), "Industry Outlook", company
    ) if state.get("raw_industry_outlook") else _empty_intelligence()

    avg_sentiment = (
        sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
    )

    return {
        **state,
        "company_news_summary": "\n\n".join(summaries) if summaries else "No research data available.",
        "industry_outlook": industry_intel.get("sentiment", "NEUTRAL"),
        "key_risks_found": list(set(all_risks)),
        "key_positives_found": list(set(all_positives)),
        "promoter_red_flags": list(set(all_red_flags)),
        "research_sentiment_score": round(avg_sentiment, 2),
        "errors": errors,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  LANGGRAPH NODE — PART C: STRUCTURE OUTPUT                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def node_structure_output(state: ResearchState) -> ResearchState:
    """
    PART C — Final structuring pass. Ensures all output fields are populated
    and applies quality checks.
    """
    # If no real data was gathered, flag for fallback
    has_real_data = bool(
        state.get("company_news_summary", "").strip()
        and state.get("company_news_summary") != "No research data available."
    )

    if not has_real_data:
        return {**state, "used_fallback": True}

    # Clamp sentiment score
    score = max(0.0, min(1.0, state.get("research_sentiment_score", 0.5)))

    # Deduplicate lists
    return {
        **state,
        "key_risks_found": list(set(state.get("key_risks_found", []))),
        "key_positives_found": list(set(state.get("key_positives_found", []))),
        "promoter_red_flags": list(set(state.get("promoter_red_flags", []))),
        "research_sentiment_score": score,
        "used_fallback": False,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART D — FALLBACK: SYNTHETIC RESEARCH DATA                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

FALLBACK_DATABASE = {
    "Sunrise Textile Mills": {
        "company_news_summary": (
            "**Company News**: Sunrise Textile Mills reported steady revenue growth of 12% YoY in FY2024, "
            "driven by strong demand in the domestic and export markets. Management guided for 15% growth "
            "in FY2025 backed by new capacity addition in Surat.\n\n"
            "**Industry Outlook**: The Indian textile sector is expected to grow at 10-12% CAGR, supported "
            "by government PLI scheme and China+1 sourcing shift. However, raw material price volatility "
            "and global demand slowdown remain key headwinds.\n\n"
            "**Regulatory Environment**: GST compliance in textile sector has improved. SEBI's enhanced "
            "disclosure norms for listed entities will increase transparency. RBI's cautious stance on "
            "unsecured lending does not directly impact secured working capital facilities.\n\n"
            "**Competitors**: Arvind Ltd and Welspun India reported mixed results. Arvind posted 8% revenue "
            "growth while Welspun faced margin pressure from cotton price volatility.\n\n"
            "**Promoter Background**: Promoter Mr. Rajesh Kapoor has 25 years of experience in the textile "
            "industry. No adverse regulatory actions found. Clean track record with existing lenders."
        ),
        "industry_outlook": "POSITIVE",
        "key_risks_found": [
            "Raw material (cotton, polyester) price volatility",
            "Global demand slowdown in key export markets (US, EU)",
            "High working capital intensity typical of textile sector",
            "Currency fluctuation risk on export receivables",
            "Increasing competition from Bangladesh and Vietnam",
        ],
        "key_positives_found": [
            "Government PLI scheme support for textile sector",
            "China+1 sourcing trend benefiting Indian manufacturers",
            "Steady domestic demand growth",
            "Company has diversified product mix (yarn + fabric + garments)",
            "Long-standing customer relationships with major brands",
        ],
        "promoter_red_flags": [],
        "research_sources": [
            "https://economictimes.com/textile-sector-outlook-2024",
            "https://livemint.com/sunrise-textile-fy24-results",
            "https://rbi.org.in/textile-sector-health-report",
            "https://bse.india.com/sunrise-textile-annual-report",
        ],
        "research_sentiment_score": 0.72,
    },
    "DEFAULT": {
        "company_news_summary": (
            "**Company News**: Limited public information available for this company. "
            "Further due diligence recommended through direct management interaction.\n\n"
            "**Industry Outlook**: Sector outlook is mixed with moderate growth expectations. "
            "Regulatory environment remains stable with no major policy changes anticipated.\n\n"
            "**Competitors**: Peer companies show varied performance. Market leader maintains "
            "healthy financials while mid-tier players face margin pressure.\n\n"
            "**Promoter Background**: No significant adverse findings in public domain. "
            "Recommend detailed background verification through independent agencies."
        ),
        "industry_outlook": "NEUTRAL",
        "key_risks_found": [
            "Limited public information — higher information asymmetry risk",
            "Sector-level cyclicality may impact revenue stability",
            "Recommend enhanced due diligence given limited data",
        ],
        "key_positives_found": [
            "No adverse regulatory findings in public domain",
            "Sector fundamentals remain broadly stable",
        ],
        "promoter_red_flags": [],
        "research_sources": [],
        "research_sentiment_score": 0.50,
    },
}


def _get_fallback_research(company_name: str) -> Dict[str, Any]:
    """Return pre-built synthetic research for demo mode."""
    if company_name in FALLBACK_DATABASE:
        data = FALLBACK_DATABASE[company_name].copy()
    else:
        data = FALLBACK_DATABASE["DEFAULT"].copy()
        data["company_news_summary"] = data["company_news_summary"].replace(
            "this company", company_name
        )
    data["used_fallback"] = True
    return data


def node_apply_fallback(state: ResearchState) -> ResearchState:
    """
    PART D — If live research failed or returned no data,
    apply fallback synthetic research for demo purposes.
    """
    if not state.get("used_fallback", False):
        return state

    logger.info(f"Using fallback research data for: {state['company_name']}")
    fallback = _get_fallback_research(state["company_name"])

    return {
        **state,
        **fallback,
        "errors": state.get("errors", []) + ["Used fallback synthetic research data"],
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ROUTING: DECIDE WHETHER TO USE FALLBACK                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def should_use_fallback(state: ResearchState) -> str:
    """Route to fallback node if needed, otherwise go to END."""
    if state.get("used_fallback", False):
        return "apply_fallback"
    return "end"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  BUILD THE LANGGRAPH WORKFLOW                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _build_research_graph() -> Any:
    """
    Construct the LangGraph state machine:

        web_research → extract_intelligence → structure_output
                                                    ↓
                                            [needs fallback?]
                                              ↓           ↓
                                        apply_fallback   END
                                              ↓
                                             END
    """
    if not LANGGRAPH_AVAILABLE:
        return None

    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("web_research", node_web_research)
    workflow.add_node("extract_intelligence", node_extract_intelligence)
    workflow.add_node("structure_output", node_structure_output)
    workflow.add_node("apply_fallback", node_apply_fallback)

    # Set entry point
    workflow.set_entry_point("web_research")

    # Linear flow: web_research → extract_intelligence → structure_output
    workflow.add_edge("web_research", "extract_intelligence")
    workflow.add_edge("extract_intelligence", "structure_output")

    # Conditional: structure_output → fallback OR end
    workflow.add_conditional_edges(
        "structure_output",
        should_use_fallback,
        {
            "apply_fallback": "apply_fallback",
            "end": END,
        },
    )

    # Fallback always goes to END
    workflow.add_edge("apply_fallback", END)

    return workflow.compile()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN ENTRY POINT                                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def run_research(
    company_name: str,
    sector: str = "General",
    promoter_name: str = "Promoter",
) -> Dict[str, Any]:
    """
    Execute the full research pipeline for a borrower company.

    Args:
        company_name: Name of the company to research (e.g., "Sunrise Textile Mills")
        sector: Industry sector (e.g., "Textiles", "Infrastructure")
        promoter_name: Name of the promoter/MD for background check

    Returns:
        Structured research summary dict:
        {
            "company_news_summary": str,
            "industry_outlook": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
            "key_risks_found": [str],
            "key_positives_found": [str],
            "promoter_red_flags": [str],
            "research_sources": [str],
            "research_sentiment_score": float (0-1),
            "used_fallback": bool,
            "errors": [str]
        }
    """
    logger.info(f"{'='*60}")
    logger.info(f"RESEARCH AGENT — {company_name}")
    logger.info(f"Sector: {sector} | Promoter: {promoter_name}")
    logger.info(f"{'='*60}")

    # Initial state
    initial_state: ResearchState = {
        "company_name": company_name,
        "sector": sector,
        "promoter_name": promoter_name,
        "raw_company_news": [],
        "raw_industry_outlook": [],
        "raw_regulatory": [],
        "raw_competitors": [],
        "raw_promoter_info": [],
        "company_news_summary": "",
        "industry_outlook": "NEUTRAL",
        "key_risks_found": [],
        "key_positives_found": [],
        "promoter_red_flags": [],
        "research_sources": [],
        "research_sentiment_score": 0.5,
        "errors": [],
        "used_fallback": False,
    }

    # ── Try LangGraph pipeline ───────────────────────────────────────────
    graph = _build_research_graph()

    if graph:
        try:
            logger.info("Running LangGraph research pipeline...")
            final_state = graph.invoke(initial_state)
            return _format_output(final_state)
        except Exception as e:
            logger.error(f"LangGraph pipeline failed: {e}")
            logger.info("Falling back to sequential execution...")

    # ── Fallback: run nodes sequentially if LangGraph unavailable ────────
    try:
        state = node_web_research(initial_state)
        state = node_extract_intelligence(state)
        state = node_structure_output(state)
        if state.get("used_fallback", False):
            state = node_apply_fallback(state)
        return _format_output(state)
    except Exception as e:
        logger.error(f"Sequential pipeline also failed: {e}")
        # Last resort — pure fallback
        fallback = _get_fallback_research(company_name)
        fallback["errors"] = [f"All pipelines failed: {e}", "Using pure fallback data"]
        return fallback


def _format_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only the clean output fields from the full graph state.
    Removes internal/raw fields not needed by downstream consumers.
    """
    return {
        "company_news_summary": state.get("company_news_summary", ""),
        "industry_outlook": state.get("industry_outlook", "NEUTRAL"),
        "key_risks_found": state.get("key_risks_found", []),
        "key_positives_found": state.get("key_positives_found", []),
        "promoter_red_flags": state.get("promoter_red_flags", []),
        "research_sources": state.get("research_sources", []),
        "research_sentiment_score": state.get("research_sentiment_score", 0.5),
        "used_fallback": state.get("used_fallback", False),
        "errors": state.get("errors", []),
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI ENTRY — for standalone testing                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("INTELLI-CREDIT — Research Agent (Standalone Test)")
    print("=" * 60)

    result = run_research(
        company_name="Sunrise Textile Mills",
        sector="Textiles",
        promoter_name="Rajesh Kapoor",
    )

    print("\n📋 RESEARCH RESULTS:")
    print("-" * 40)
    print(f"Industry Outlook : {result['industry_outlook']}")
    print(f"Sentiment Score  : {result['research_sentiment_score']}")
    print(f"Used Fallback    : {result['used_fallback']}")
    print(f"Sources Found    : {len(result['research_sources'])}")

    print(f"\n🔴 Key Risks ({len(result['key_risks_found'])}):")
    for r in result["key_risks_found"]:
        print(f"   • {r}")

    print(f"\n🟢 Key Positives ({len(result['key_positives_found'])}):")
    for p in result["key_positives_found"]:
        print(f"   • {p}")

    if result["promoter_red_flags"]:
        print(f"\n🚩 Promoter Red Flags ({len(result['promoter_red_flags'])}):")
        for f in result["promoter_red_flags"]:
            print(f"   • {f}")

    print(f"\n📰 Summary:\n{result['company_news_summary']}")

    if result["errors"]:
        print(f"\n⚠️  Errors:")
        for e in result["errors"]:
            print(f"   • {e}")

    print("\n" + "=" * 60)
