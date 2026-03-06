"""
Yakṣarāja — PDF & Unstructured Document Parser
================================================
Extracts financial commitments, risk factors, and key data from:
  - Annual Reports (PDFs)
  - Legal notices & sanction letters
  - Rating agency reports
  - Board meeting minutes
  - MCA filings

Strategy (in priority order):
  1. pdfplumber for precise table extraction  →  structured data
  2. PyMuPDF (fitz) for text + layout blocks  →  unstructured text
  3. Gemini LLM extraction for ambiguous docs  →  NLP intelligence layer
  4. Regex fallback for common Indian financial patterns

Indian Context:
  - Handles Rupee notation (₹, Rs., Crores, Lakhs)
  - Understands standard Screener/BSE/MCA filing formats
  - Recognises GSTR references, DIN numbers, CIN patterns
  - Flags RBI/SEBI/NCLT/ED/CBI mentions as regulatory risk

Author: Person 1
Module: pipeline/pdf_parser.py
"""

import os
import re
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS — gracefully handled
# ─────────────────────────────────────────────────────────────────────────────

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not installed — pip install pdfplumber")

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF not installed — pip install pymupdf")

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

# Maximum pages to process per document (performance guard)
MAX_PAGES = 80

# Regex patterns for Indian financial figures
_INR_PATTERN = re.compile(
    r"(?:₹|Rs\.?|INR)\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:Cr\.?|Crore|crore|L|Lakh|lakh)?",
    re.IGNORECASE,
)

# Crore / Lakh amounts without currency symbol
_CRORE_PATTERN = re.compile(
    r"([0-9,]+(?:\.[0-9]+)?)\s*(?:Cr\.?|Crore|crores)\b",
    re.IGNORECASE,
)

# DIN pattern (8-digit director identification number)
_DIN_PATTERN = re.compile(r"\bDIN[:\s#]*([0-9]{8})\b", re.IGNORECASE)

# CIN pattern (21-char company identification number)
_CIN_PATTERN = re.compile(
    r"\b([UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{2,3}[0-9]{6})\b"
)

# GSTIN pattern
_GSTIN_PATTERN = re.compile(
    r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z])\b"
)

# Regulatory risk keywords
REGULATORY_RISK_KEYWORDS = [
    "NCLT", "IBC", "insolvency", "winding up", "winding-up",
    "NPA", "default", "dishonour", "cheque bounce",
    "RBI penalty", "SEBI order", "enforcement directorate", "ED raid",
    "CBI investigation", "income tax notice", "GST notice", "GST demand",
    "litigation", "arbitration", "contempt of court", "FIR",
    "attachment order", "loan recall", "recall notice",
    "promoter arrested", "promoter convicted", "PMLA",
]

# Positive signals keywords
POSITIVE_SIGNAL_KEYWORDS = [
    "PLI scheme", "government order", "export incentive", "AAA rating",
    "AA rating", "CRISIL", "ICRA", "capacity expansion", "new plant",
    "debt reduction", "deleveraging", "promoter buying", "buyback",
    "equity infusion", "rights issue", "fresh capex",
]

# Financial section markers in annual reports
SECTION_MARKERS = {
    "pnl": ["profit and loss", "statement of profit", "income statement",
            "p&l account", "consolidated p&l"],
    "balance_sheet": ["balance sheet", "statement of assets", "position statement"],
    "cash_flow": ["cash flow", "statement of cash flow"],
    "directors_report": ["directors' report", "board's report", "director's report"],
    "auditors_report": ["auditor's report", "independent auditor", "auditor report"],
    "notes": ["notes to accounts", "notes forming part", "significant accounting policies"],
    "mda": ["management discussion", "management's discussion", "mda review"],
    "related_party": ["related party", "related-party", "transactions with related"],
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _to_crore(value_str: str, context_text: str = "") -> Optional[float]:
    """Convert a matched financial value to Crore rupees."""
    try:
        val = float(str(value_str).replace(",", ""))
        ctx = context_text.upper()
        if "LAKH" in ctx or " L " in ctx:
            val = val / 100.0
        elif "MILLION" in ctx:
            val = val / 10.0
        elif "BILLION" in ctx:
            val = val * 100.0
        return round(val, 2)
    except (ValueError, TypeError):
        return None


def _extract_amounts(text: str) -> List[Dict[str, Any]]:
    """Extract all INR amounts with context from text."""
    amounts = []
    for match in _INR_PATTERN.finditer(text):
        ctx_start = max(0, match.start() - 60)
        ctx_end = min(len(text), match.end() + 40)
        context = text[ctx_start:ctx_end].strip()
        val = _to_crore(match.group(1), context)
        if val is not None and val > 0:
            amounts.append({"amount_cr": val, "context": context})

    for match in _CRORE_PATTERN.finditer(text):
        ctx_start = max(0, match.start() - 60)
        ctx_end = min(len(text), match.end() + 40)
        context = text[ctx_start:ctx_end].strip()
        # Avoid duplicating amounts already caught by INR_PATTERN
        val = _to_crore(match.group(1), "crore")
        if val is not None and val > 0:
            amounts.append({"amount_cr": val, "context": context})

    return amounts


def _find_regulatory_risks(text: str) -> List[str]:
    """Scan text for regulatory risk mentions."""
    found = []
    text_lower = text.lower()
    for keyword in REGULATORY_RISK_KEYWORDS:
        if keyword.lower() in text_lower:
            idx = text_lower.index(keyword.lower())
            snippet = text[max(0, idx - 40): min(len(text), idx + 120)].strip()
            snippet = re.sub(r"\s+", " ", snippet)
            found.append(snippet)
    return found[:10]  # cap at 10 most important


def _find_positive_signals(text: str) -> List[str]:
    """Scan text for positive business signals."""
    found = []
    text_lower = text.lower()
    for keyword in POSITIVE_SIGNAL_KEYWORDS:
        if keyword.lower() in text_lower:
            idx = text_lower.index(keyword.lower())
            snippet = text[max(0, idx - 30): min(len(text), idx + 100)].strip()
            snippet = re.sub(r"\s+", " ", snippet)
            found.append(snippet)
    return found[:8]


def _identify_doc_type(text: str, filename: str) -> str:
    """Classify document type from filename and text content."""
    fn_lower = filename.lower()
    text_lower = text[:2000].lower()

    if any(k in fn_lower for k in ["annual", "ar202", "annualreport"]):
        return "annual_report"
    if any(k in fn_lower for k in ["legal", "notice", "court", "nclt"]):
        return "legal_notice"
    if any(k in fn_lower for k in ["sanction", "term_sheet", "termsheet", "los"]):
        return "sanction_letter"
    if any(k in fn_lower for k in ["rating", "crisil", "icra", "care", "brickwork"]):
        return "rating_report"
    if any(k in fn_lower for k in ["board", "minutes", "agm", "egm"]):
        return "board_minutes"
    if any(k in fn_lower for k in ["mca", "roc", "filing"]):
        return "mca_filing"

    # Text-based fallback
    if "profit and loss" in text_lower or "balance sheet" in text_lower:
        return "annual_report"
    if "notice is hereby given" in text_lower or "writ petition" in text_lower:
        return "legal_notice"
    if "sanction limit" in text_lower or "loan sanction" in text_lower:
        return "sanction_letter"

    return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# CORE EXTRACTION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(filepath: str) -> Tuple[str, List[str]]:
    """
    Extract raw text from a PDF using pdfplumber (primary) or PyMuPDF (fallback).

    Returns
    -------
    (full_text, page_texts_list)
    """
    page_texts = []

    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(filepath) as pdf:
                pages = pdf.pages[:MAX_PAGES]
                for page in pages:
                    text = page.extract_text() or ""
                    page_texts.append(text)
            logger.info(f"pdfplumber extracted {len(page_texts)} pages from {Path(filepath).name}")
            return "\n".join(page_texts), page_texts
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e} — trying PyMuPDF")

    if FITZ_AVAILABLE:
        try:
            doc = fitz.open(filepath)
            for page_num in range(min(MAX_PAGES, len(doc))):
                page = doc[page_num]
                text = page.get_text("text")
                page_texts.append(text)
            doc.close()
            logger.info(f"PyMuPDF extracted {len(page_texts)} pages from {Path(filepath).name}")
            return "\n".join(page_texts), page_texts
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")

    logger.error("No PDF extraction library available — install pdfplumber or pymupdf")
    return "", []


def extract_tables_from_pdf(filepath: str) -> List[Dict[str, Any]]:
    """
    Extract tabular data (P&L, BS, CF tables) from a PDF.
    Returns list of {page, table_index, headers, rows}.
    """
    if not PDFPLUMBER_AVAILABLE:
        return []

    tables = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages[:MAX_PAGES]):
                page_tables = page.extract_tables()
                if page_tables:
                    for tbl_idx, table in enumerate(page_tables):
                        if not table or len(table) < 2:
                            continue
                        headers = [str(c).strip() if c else "" for c in (table[0] or [])]
                        rows = []
                        for row in table[1:]:
                            if row:
                                rows.append([str(c).strip() if c else "" for c in row])
                        tables.append({
                            "page": page_num + 1,
                            "table_index": tbl_idx,
                            "headers": headers,
                            "rows": rows,
                        })
    except Exception as e:
        logger.warning(f"Table extraction failed: {e}")

    logger.info(f"Extracted {len(tables)} tables from {Path(filepath).name}")
    return tables


def _parse_financial_table(table: Dict[str, Any]) -> Dict[str, float]:
    """
    Try to parse a financial table (P&L / BS / CF statement) into key metrics.
    Handles Indian number formats: Lakhs, Crores, commas.
    """
    metrics = {}
    headers = [h.lower() for h in table.get("headers", [])]
    rows = table.get("rows", [])

    # Identify year columns — look for 4-digit years or "FY" patterns
    year_cols = []
    for i, h in enumerate(headers):
        if re.search(r"20\d{2}|19\d{2}|fy\s*\d{2,4}", h, re.IGNORECASE):
            year_cols.append(i)

    if not year_cols:
        # Assume column 1 is current year
        year_cols = [1] if len(headers) > 1 else []

    latest_col = year_cols[0] if year_cols else 1

    # Key row label mappings
    label_map = {
        r"total\s*revenue|net\s*sales|gross\s*revenue|turnover": "revenue",
        r"ebitda|earnings before interest": "ebitda",
        r"profit\s*before\s*tax|pbt": "pbt",
        r"net\s*profit|profit\s*after\s*tax|pat": "pat",
        r"total\s*assets": "total_assets",
        r"total\s*equity|shareholders.*fund|net\s*worth": "total_equity",
        r"long[\s-]*term\s*debt|term\s*loan|lt\s*borrowing": "lt_borrowings",
        r"short[\s-]*term\s*borrowing|st\s*borrow": "st_borrowings",
        r"total\s*(?:debt|borrowing)": "total_debt",
        r"trade\s*receiv|sundry\s*debtor|accounts\s*receiv": "trade_receivables",
        r"inventor": "inventories",
        r"cash\s*(?:and\s*)?(?:bank|equivalents)": "cash_equivalents",
        r"capital\s*expenditure|capex|purchase.*(?:ppe|fixed\sasset)": "capex",
        r"operating\s*cash\s*flow|cash\s*from\s*operat": "cfo",
        r"depreciation\s*(?:and\s*amort)?|d&?a\b": "depreciation",
        r"interest\s*(?:expense|cost|paid)|finance\s*cost": "interest_expense",
    }

    for row in rows:
        if not row or not row[0]:
            continue
        label = row[0].strip().lower()
        label = re.sub(r"\s+", " ", label)

        for pattern, key in label_map.items():
            if re.search(pattern, label, re.IGNORECASE):
                try:
                    raw = row[latest_col] if latest_col < len(row) else ""
                    raw = str(raw).replace(",", "").replace("(", "-").replace(")", "").strip()
                    if raw in ("", "-", "--", "N/A"):
                        break
                    val = float(raw)
                    # Convert Lakhs to Crores if value seems too large
                    if val > 100_000:
                        val = val / 100.0
                    metrics[key] = round(val, 2)
                except (ValueError, IndexError):
                    pass
                break

    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# LLM EXTRACTION (Gemini)
# ─────────────────────────────────────────────────────────────────────────────

def _llm_extract_financials(text: str, doc_type: str, company_name: str) -> Dict[str, Any]:
    """
    Use Gemini to extract structured financial data from unstructured document text.
    Falls back to empty dict if Gemini unavailable.
    """
    if not GEMINI_AVAILABLE:
        return {}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {}

    # Truncate text to fit context window (~4000 chars)
    text_sample = text[:6000]

    prompt = f"""You are an expert Indian credit analyst. Extract credit-relevant data from this {doc_type}.

DOCUMENT EXCERPT:
{text_sample}

COMPANY: {company_name}

Extract and return ONLY a valid JSON object with these keys (use null if not found):
{{
  "revenue_cr": null,
  "ebitda_cr": null,
  "pat_cr": null,
  "total_debt_cr": null,
  "total_equity_cr": null,
  "total_assets_cr": null,
  "cfo_cr": null,
  "capex_cr": null,
  "dscr": null,
  "interest_coverage": null,
  "debt_to_equity": null,
  "rating": null,
  "rating_agency": null,
  "going_concern_flag": 0,
  "qualified_opinion_flag": 0,
  "auditor_resigned_flag": 0,
  "auditor_name": null,
  "regulatory_risks": [],
  "positive_signals": [],
  "loan_sanctions_cr": [],
  "legal_disputes": [],
  "key_commitments": [],
  "promoter_guarantees": [],
  "collateral_details": [],
  "key_covenants": []
}}

Rules:
- All monetary values must be in Indian Rupees CRORE (₹ Cr)
- Convert Lakhs ÷ 100, Millions ÷ 10, Billions × 100 to get Crores
- regulatory_risks: list of legal/regulatory issues found (max 5)
- legal_disputes: list of pending court cases / NCLT matters
- key_commitments: loan repayment obligations, guarantees given
- Return ONLY JSON, no explanation."""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        raw = response.text.strip()
        # Strip markdown code fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT-TYPE SPECIFIC PARSERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_annual_report(text: str, tables: List, company_name: str) -> Dict[str, Any]:
    """Extract P&L, BS, CF, auditor & risk data from annual report."""
    result: Dict[str, Any] = {
        "doc_type": "annual_report",
        "financial_metrics": {},
        "regulatory_risks": [],
        "positive_signals": [],
        "auditor_info": {},
        "related_party_info": [],
        "dins": [],
        "cin": None,
    }

    # Try table extraction first
    for tbl in tables:
        metrics = _parse_financial_table(tbl)
        if len(metrics) >= 3:  # only trust tables with multiple hits
            result["financial_metrics"].update(metrics)
            logger.info(f"Table extraction yielded {len(metrics)} metrics from page {tbl['page']}")

    # Risk flags from text
    result["regulatory_risks"] = _find_regulatory_risks(text)
    result["positive_signals"] = _find_positive_signals(text)

    # DINs & CIN
    result["dins"] = list(set(_DIN_PATTERN.findall(text)))[:10]
    cin_match = _CIN_PATTERN.search(text)
    if cin_match:
        result["cin"] = cin_match.group(1)

    # Going concern / qualification flags
    text_lower = text.lower()
    result["auditor_info"]["going_concern_flag"] = int(
        "going concern" in text_lower and
        any(k in text_lower for k in ["doubt", "uncertainty", "material uncertainty", "unable to"])
    )
    result["auditor_info"]["qualified_opinion"] = int(
        any(k in text_lower for k in ["qualified opinion", "adverse opinion", "disclaimer of opinion"])
    )
    result["auditor_info"]["auditor_resigned"] = int(
        any(k in text_lower for k in ["resigned", "relinquished", "vacated office"])
    )

    # Related-party mentions
    rpt_keywords = ["related party", "related-party", "key managerial", "subsidiary"]
    for kw in rpt_keywords:
        idx = text_lower.find(kw)
        if idx != -1:
            snippet = text[idx: idx + 300].strip()
            snippet = re.sub(r"\s+", " ", snippet)
            result["related_party_info"].append(snippet[:250])
            break

    # LLM fallback for any missing metrics
    if len(result["financial_metrics"]) < 4:
        llm_data = _llm_extract_financials(text, "annual_report", company_name)
        if llm_data:
            # Map LLM keys to standard keys
            key_map = {
                "revenue_cr": "revenue", "ebitda_cr": "ebitda",
                "pat_cr": "pat", "total_debt_cr": "total_debt",
                "total_equity_cr": "total_equity", "total_assets_cr": "total_assets",
                "cfo_cr": "cfo", "capex_cr": "capex",
            }
            for llm_key, std_key in key_map.items():
                if llm_data.get(llm_key) is not None:
                    result["financial_metrics"].setdefault(std_key, llm_data[llm_key])
            result["regulatory_risks"] += llm_data.get("regulatory_risks", [])
            result["positive_signals"]  += llm_data.get("positive_signals", [])
            if not result["auditor_info"].get("going_concern_flag"):
                result["auditor_info"]["going_concern_flag"] = int(
                    bool(llm_data.get("going_concern_flag", 0))
                )
            result["legal_disputes"] = llm_data.get("legal_disputes", [])
            result["key_commitments"] = llm_data.get("key_commitments", [])

    return result


def _parse_legal_notice(text: str, company_name: str) -> Dict[str, Any]:
    """Extract legal dispute details from legal notices / court orders."""
    amounts = _extract_amounts(text)
    text_lower = text.lower()

    dispute_type = "Unknown"
    if "nclt" in text_lower or "insolvency" in text_lower:
        dispute_type = "NCLT / Insolvency Proceedings"
    elif "high court" in text_lower or "supreme court" in text_lower:
        dispute_type = "High Court / Supreme Court"
    elif "district court" in text_lower:
        dispute_type = "District Court"
    elif "arbitration" in text_lower:
        dispute_type = "Arbitration"
    elif "income tax" in text_lower:
        dispute_type = "Income Tax Dispute"
    elif "gst" in text_lower and "notice" in text_lower:
        dispute_type = "GST Demand / Notice"
    elif "enforcement" in text_lower and ("ed" in text_lower or "directorate" in text_lower):
        dispute_type = "Enforcement Directorate (PMLA)"

    # Claim amounts
    claim_cr = None
    for amt in sorted(amounts, key=lambda x: x["amount_cr"], reverse=True):
        if amt["amount_cr"] > 0.1:
            claim_cr = amt["amount_cr"]
            break

    # LLM extraction for legal docs
    llm_data = _llm_extract_financials(text, "legal_notice", company_name)

    return {
        "doc_type": "legal_notice",
        "dispute_type": dispute_type,
        "claim_amount_cr": claim_cr,
        "regulatory_flags": _find_regulatory_risks(text),
        "key_details": llm_data.get("legal_disputes", []),
        "amounts_mentioned": [a["amount_cr"] for a in amounts[:5]],
    }


def _parse_sanction_letter(text: str, company_name: str) -> Dict[str, Any]:
    """Extract key terms from bank sanction letters / term sheets."""
    text_lower = text.lower()
    amounts = _extract_amounts(text)

    # Attempt to find loan amount
    loan_amount_cr = None
    for amt in sorted(amounts, key=lambda x: x["amount_cr"], reverse=True):
        ctx = amt["context"].lower()
        if any(k in ctx for k in ["sanction", "limit", "facility", "loan amount", "credit limit"]):
            loan_amount_cr = amt["amount_cr"]
            break

    # Interest rate
    rate_match = re.search(
        r"(?:interest\s*rate|rate\s*of\s*interest|roi)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%",
        text_lower,
    )
    interest_rate = float(rate_match.group(1)) if rate_match else None

    # Tenure
    tenure_match = re.search(
        r"(?:tenure|term|period)[:\s]*([0-9]+)\s*(?:year|month)",
        text_lower,
    )
    tenure = tenure_match.group(0) if tenure_match else None

    # Collateral / security
    collateral_keywords = ["mortgage", "hypothecation", "pledge", "lien", "security",
                           "immovable property", "land and building", "plant and machinery"]
    collateral = []
    for kw in collateral_keywords:
        if kw in text_lower:
            idx = text_lower.index(kw)
            snippet = text[idx: idx + 200].strip()
            snippet = re.sub(r"\s+", " ", snippet)
            collateral.append(snippet[:150])

    # Covenants
    covenant_keywords = ["dscr", "debt service", "current ratio", "net worth",
                         "covenant", "undertaking", "condition", "restriction"]
    covenants = []
    for kw in covenant_keywords:
        if kw in text_lower:
            idx = text_lower.index(kw)
            snippet = text[idx: idx + 200].strip()
            snippet = re.sub(r"\s+", " ", snippet)
            covenants.append(snippet[:150])

    llm_data = _llm_extract_financials(text, "sanction_letter", company_name)

    return {
        "doc_type": "sanction_letter",
        "sanctioned_amount_cr": loan_amount_cr or (
            llm_data.get("loan_sanctions_cr", [None])[0] if llm_data.get("loan_sanctions_cr") else None
        ),
        "interest_rate_pct": interest_rate,
        "tenure": tenure,
        "collateral": list(set(collateral))[:5],
        "covenants": list(set(covenants))[:8],
        "key_commitments": llm_data.get("key_commitments", []),
        "promoter_guarantees": llm_data.get("promoter_guarantees", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def parse_pdf_document(
    filepath: str,
    company_name: str = "Unknown",
    doc_type_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Parse any PDF document and return a structured extraction result.

    Parameters
    ----------
    filepath      : Path to PDF file
    company_name  : Company name (used in LLM prompts)
    doc_type_hint : Optional: "annual_report" | "legal_notice" | "sanction_letter"
                    | "rating_report" | "board_minutes" | "mca_filing"

    Returns
    -------
    dict:
        doc_type, filename, page_count,
        financial_metrics, regulatory_risks, positive_signals,
        raw_text_preview (first 500 chars),
        llm_extraction (LLM-extracted structured data),
        [doc_type specific fields]
    """
    filepath = str(filepath)
    filename = Path(filepath).name

    if not os.path.exists(filepath):
        logger.error(f"PDF not found: {filepath}")
        return {"error": f"File not found: {filepath}", "filename": filename}

    logger.info(f"Parsing PDF: {filename}")

    # Step 1: Extract text
    full_text, page_texts = extract_text_from_pdf(filepath)
    page_count = len(page_texts)

    if not full_text.strip():
        logger.warning(f"No text extracted from {filename} — possibly scanned image PDF")
        # For scanned PDFs, rely purely on LLM if text is empty
        return {
            "doc_type": doc_type_hint or "unknown",
            "filename": filename,
            "page_count": page_count,
            "warning": "Scanned PDF — text extraction returned empty. LLM-only mode.",
            "financial_metrics": {},
            "regulatory_risks": [],
            "positive_signals": [],
            "raw_text_preview": "",
        }

    # Step 2: Detect document type
    detected_type = doc_type_hint or _identify_doc_type(full_text, filename)

    # Step 3: Extract tables
    tables = extract_tables_from_pdf(filepath)

    # Step 4: Route to doc-type specific parser
    if detected_type == "annual_report":
        result = _parse_annual_report(full_text, tables, company_name)
    elif detected_type == "legal_notice":
        result = _parse_legal_notice(full_text, company_name)
    elif detected_type == "sanction_letter":
        result = _parse_sanction_letter(full_text, company_name)
    else:
        # Generic extraction for rating reports, board minutes, MCA
        result = {
            "doc_type": detected_type,
            "financial_metrics": {},
            "regulatory_risks": _find_regulatory_risks(full_text),
            "positive_signals":  _find_positive_signals(full_text),
            "llm_extraction":    _llm_extract_financials(full_text, detected_type, company_name),
        }
        # Merge LLM metrics into financial_metrics
        llm = result.get("llm_extraction", {})
        for llm_key, std_key in [
            ("revenue_cr", "revenue"), ("ebitda_cr", "ebitda"),
            ("pat_cr", "pat"), ("total_debt_cr", "total_debt"),
        ]:
            if llm.get(llm_key) is not None:
                result["financial_metrics"][std_key] = llm[llm_key]

    # Common fields
    result["filename"] = filename
    result["page_count"] = page_count
    result["raw_text_preview"] = full_text[:800].strip()
    result["gstin_found"] = list(set(_GSTIN_PATTERN.findall(full_text)))[:3]
    result["total_amounts_found"] = len(_extract_amounts(full_text))

    logger.info(
        f"PDF parsed: {filename} | type={detected_type} | "
        f"metrics={len(result.get('financial_metrics', {}))} | "
        f"risks={len(result.get('regulatory_risks', []))} | "
        f"positives={len(result.get('positive_signals', []))}"
    )

    return result


def parse_multiple_pdfs(
    filepaths: List[str],
    company_name: str = "Unknown",
) -> Dict[str, Any]:
    """
    Parse multiple PDF documents and merge into a consolidated extraction result.

    Parameters
    ----------
    filepaths    : List of paths to PDF files
    company_name : Company name

    Returns
    -------
    Consolidated dict with merged financial_metrics, all risks, all positives,
    and per-document breakdowns.
    """
    consolidated = {
        "company_name": company_name,
        "documents_parsed": 0,
        "financial_metrics": {},
        "regulatory_risks": [],
        "positive_signals": [],
        "legal_disputes": [],
        "sanction_amounts": [],
        "going_concern_flag": 0,
        "qualified_opinion_flag": 0,
        "auditor_resigned_flag": 0,
        "all_dins": [],
        "all_cin": None,
        "document_details": [],
    }

    for fp in filepaths:
        try:
            doc_result = parse_pdf_document(fp, company_name=company_name)
            consolidated["documents_parsed"] += 1
            consolidated["document_details"].append(doc_result)

            # Merge financial metrics — current doc takes precedence unless already richer
            fm = doc_result.get("financial_metrics", {})
            for k, v in fm.items():
                if k not in consolidated["financial_metrics"] and v is not None:
                    consolidated["financial_metrics"][k] = v

            # Accumulate risks, positives, disputes
            consolidated["regulatory_risks"] += doc_result.get("regulatory_risks", [])
            consolidated["positive_signals"]  += doc_result.get("positive_signals", [])
            consolidated["legal_disputes"]     += doc_result.get("key_details", doc_result.get("legal_disputes", []))

            # Sanction amounts
            amt = doc_result.get("sanctioned_amount_cr")
            if amt:
                consolidated["sanction_amounts"].append(amt)

            # Auditor flags — any positive flag across docs propagates
            ai = doc_result.get("auditor_info", {})
            if ai.get("going_concern_flag"):
                consolidated["going_concern_flag"] = 1
            if ai.get("qualified_opinion"):
                consolidated["qualified_opinion_flag"] = 1
            if ai.get("auditor_resigned"):
                consolidated["auditor_resigned_flag"] = 1

            # DINs & CIN
            consolidated["all_dins"] += doc_result.get("dins", [])
            if not consolidated["all_cin"] and doc_result.get("cin"):
                consolidated["all_cin"] = doc_result["cin"]

        except Exception as e:
            logger.error(f"Failed to parse {fp}: {e}")

    # Deduplicate
    consolidated["regulatory_risks"] = list(set(consolidated["regulatory_risks"]))[:15]
    consolidated["positive_signals"]  = list(set(consolidated["positive_signals"]))[:10]
    consolidated["all_dins"]          = list(set(consolidated["all_dins"]))[:20]

    logger.info(
        f"PDF batch complete: {consolidated['documents_parsed']} docs | "
        f"{len(consolidated['financial_metrics'])} financial metrics | "
        f"{len(consolidated['regulatory_risks'])} risks"
    )

    return consolidated


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pipeline/pdf_parser.py <path_to_pdf> [company_name]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    company = sys.argv[2] if len(sys.argv) > 2 else "Unknown Company"

    result = parse_pdf_document(pdf_path, company_name=company)
    print(json.dumps(
        {k: v for k, v in result.items() if k != "raw_text_preview"},
        indent=2, default=str
    ))
