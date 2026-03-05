"""
Yakṣarāja — Web Data Fetcher
============================
Fetches missing company data from public internet sources when it is not
provided in the uploaded file.

Sources tried (in order):
  1. Yahoo Finance via yfinance  — shareholding, P&L, sector
  2. NSE India unofficial API   — promoter / institutional holding
  3. Screener.in web scrape     — shareholding pattern, pledge %, financials
  4. Moneycontrol search        — sector, overview
"""

import re
import time
import requests
from typing import Any, Dict, Optional
from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com",
}

NSE_HEADERS = {
    **HEADERS,
    "X-Requested-With": "XMLHttpRequest",
}

# Fields that should be fetched from the web (i.e. pure governance/market data)
FETCHABLE_FIELDS = [
    "promoter_holding_pct",
    "promoter_pledge_pct",
    "institutional_holding_pct",
    "public_holding_pct",
    "related_party_tx_to_rev",
    "sector",
    "market_cap_cr",
    "pe_ratio",
    "book_value_per_share",
    "dividend_yield",
    "face_value",
    "revenue",
    "ebitda",
    "ebitda_margin",
    "pat",
    "net_margin",
    "roe",
    "roa",
    "debt_to_equity",
    "current_ratio",
    "interest_coverage",
]

_NOT_GIVEN = {None, "N/A", "Not Given", "", "none", "nan"}


def _is_missing(val: Any) -> bool:
    """Return True if a value is considered missing / not given."""
    if val is None:
        return True
    if isinstance(val, float):
        import math
        if math.isnan(val):
            return True
    return str(val).strip() in _NOT_GIVEN


# ─────────────────────────────────────────────────────────────────────────────
# SYMBOL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _clean_symbol(company_name: str) -> str:
    """
    Convert a company name to a plausible NSE / Yahoo ticker.
    E.g. "Sunrise Textile Mills" → "SUNRISETEX"
    """
    # Strip common suffixes
    for suffix in [
        " LIMITED", " LTD", " PRIVATE", " PVT", " LTD.", "& CO.",
        " INDUSTRIES", " MILLS", " ENTERPRISES", " HOLDINGS",
        " CORPORATION", " CORP", " INFRASTRUCTURE", " INFRA",
    ]:
        company_name = company_name.upper().replace(suffix, "")

    symbol = re.sub(r"[^A-Z0-9]", "", company_name.upper())
    return symbol[:10]


def _candidate_symbols(company_name: str) -> list[str]:
    """Generate a list of candidate ticker symbols to try."""
    base = _clean_symbol(company_name)
    words = re.sub(r"[^A-Z0-9 ]", "", company_name.upper()).split()
    candidates = [
        base,
        "".join(words),
        "".join(w[:3] for w in words if w)[:10],
        words[0][:10] if words else base,
    ]
    # Remove duplicates while preserving order
    seen, out = set(), []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1 — Yahoo Finance (via yfinance)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_yahoo(symbol: str) -> Dict[str, Any]:
    """Fetch key ratios and shareholding from Yahoo Finance."""
    result: Dict[str, Any] = {}
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        logger.warning("yfinance not installed — skipping Yahoo Finance source")
        return result

    for suffix in [".NS", ".BO", ""]:
        ticker_sym = f"{symbol}{suffix}"
        try:
            tk = yf.Ticker(ticker_sym)
            info = tk.info
            if not info or info.get("regularMarketPrice") is None:
                continue

            logger.info(f"Yahoo Finance hit: {ticker_sym}")

            # Shareholding
            held_insiders = info.get("heldPercentInsiders")
            held_inst = info.get("heldPercentInstitutions")
            if held_insiders is not None:
                result["promoter_holding_pct"] = round(float(held_insiders), 4)
            if held_inst is not None:
                result["institutional_holding_pct"] = round(float(held_inst), 4)

            # Sector
            if info.get("sector"):
                result["sector"] = info["sector"]
            if info.get("industry"):
                result["industry"] = info["industry"]

            # Financials (converted to ₹ Cr — Yahoo gives in INR, so divide by 1e7)
            for yf_key, our_key, scale in [
                ("totalRevenue",        "revenue",           1e7),
                ("ebitda",              "ebitda",            1e7),
                ("netIncomeToCommon",   "pat",               1e7),
                ("returnOnEquity",      "roe",               None),
                ("returnOnAssets",      "roa",               None),
                ("debtToEquity",        "debt_to_equity",    None),
                ("currentRatio",        "current_ratio",     None),
                ("marketCap",           "market_cap_cr",     1e7),
                ("priceToBook",         "pb_ratio",          None),
                ("trailingPE",          "pe_ratio",          None),
                ("dividendYield",       "dividend_yield",    None),
            ]:
                v = info.get(yf_key)
                if v is not None:
                    if scale:
                        result[our_key] = round(float(v) / scale, 2)
                    else:
                        result[our_key] = round(float(v), 4) if v else None

            # Derived
            rev = result.get("revenue")
            ebit = result.get("ebitda")
            pat = result.get("pat")
            if rev and rev > 0:
                if ebit:
                    result["ebitda_margin"] = round(ebit / rev, 4)
                if pat:
                    result["net_margin"] = round(pat / rev, 4)

            break  # success — no need to try more suffixes
        except Exception as e:
            logger.debug(f"Yahoo {ticker_sym} failed: {e}")
            continue

    return result


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2 — NSE India unofficial API
# ─────────────────────────────────────────────────────────────────────────────

def _nse_session() -> requests.Session:
    """Create a requests Session with valid NSE cookies."""
    sess = requests.Session()
    try:
        sess.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=10)
        time.sleep(0.8)
    except Exception as e:
        logger.debug(f"NSE warm-up failed: {e}")
    return sess


def _fetch_nse(symbol: str) -> Dict[str, Any]:
    """Fetch shareholding pattern from NSE India."""
    result: Dict[str, Any] = {}
    sess = _nse_session()

    try:
        url = (
            f"https://www.nseindia.com/api/corporate-share-holdings-master"
            f"?symbol={symbol}&series=EQ"
        )
        resp = sess.get(url, headers=NSE_HEADERS, timeout=12)
        if resp.status_code != 200:
            return result

        data = resp.json()
        # NSE returns a list of records with category and percentage
        if isinstance(data, list):
            promoter_pct = 0.0
            fii_pct = 0.0
            dii_pct = 0.0
            pledge_pct = 0.0
            for record in data:
                cat = str(record.get("category", "")).upper()
                try:
                    pct = float(record.get("percentage", 0)) / 100
                except (ValueError, TypeError):
                    pct = 0.0
                if "PROMOTER" in cat and "PLEDGE" not in cat:
                    promoter_pct += pct
                elif "PROMOTER" in cat and "PLEDGE" in cat:
                    pledge_pct += pct
                elif "FII" in cat or "FOREIGN" in cat:
                    fii_pct += pct
                elif "DII" in cat or "DOMESTIC INST" in cat:
                    dii_pct += pct

            if promoter_pct > 0:
                result["promoter_holding_pct"] = round(promoter_pct, 4)
            if pledge_pct > 0:
                result["promoter_pledge_pct"] = round(pledge_pct, 4)
            if fii_pct + dii_pct > 0:
                result["institutional_holding_pct"] = round(fii_pct + dii_pct, 4)
                result["public_holding_pct"] = round(
                    max(0, 1 - promoter_pct - fii_pct - dii_pct), 4
                )

    except Exception as e:
        logger.debug(f"NSE shareholding API failed for {symbol}: {e}")

    # Additional: quote info for financial ratios
    try:
        quote_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        resp = sess.get(quote_url, headers=NSE_HEADERS, timeout=12)
        if resp.status_code == 200:
            q = resp.json()
            meta = q.get("metadata", {})
            pd_info = q.get("priceInfo", {})
            if meta.get("industry"):
                result["sector"] = meta["industry"]
            mc = pd_info.get("intrinsicValue") or meta.get("pdSymbolPe")
            if mc:
                try:
                    result.setdefault("pe_ratio", float(mc))
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        logger.debug(f"NSE quote fetch failed for {symbol}: {e}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 3 — Screener.in
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_screener(company_name: str) -> Dict[str, Any]:
    """Fetch financials and shareholding from Screener.in."""
    result: Dict[str, Any] = {}
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        logger.warning("beautifulsoup4 not installed — skipping Screener.in source")
        return result

    try:
        # Step 1: search for the company
        search_url = (
            f"https://www.screener.in/api/company/search/"
            f"?q={requests.utils.quote(company_name)}&fields=name,url"
        )
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return result

        hits = resp.json()
        if not hits:
            return result

        company_path = hits[0].get("url", "")
        if not company_path:
            return result

        # Step 2: fetch company page
        page_url = f"https://www.screener.in{company_path}"
        resp = requests.get(page_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, "html.parser")

        # ── Parse shareholding table ──
        promoter_pct = None
        pledge_pct = None
        inst_pct = 0.0

        sh_section = soup.find("section", {"id": "shareholding"})
        if sh_section:
            for table in sh_section.find_all("table"):
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    if len(cells) < 2:
                        continue
                    label = cells[0].get_text(strip=True).lower()
                    # Take last column (most recent)
                    val_text = cells[-1].get_text(strip=True).replace(",", "").replace("%", "")
                    try:
                        val = float(val_text) / 100
                    except (ValueError, TypeError):
                        continue
                    if "promoter" in label and "pledge" not in label:
                        promoter_pct = round(val, 4)
                    elif "pledge" in label or "pledged" in label:
                        pledge_pct = round(val, 4)
                    elif "fii" in label or "foreign" in label:
                        inst_pct += val
                    elif "dii" in label or "institution" in label:
                        inst_pct += val

        if promoter_pct is not None:
            result["promoter_holding_pct"] = promoter_pct
        if pledge_pct is not None:
            result["promoter_pledge_pct"] = pledge_pct
        if inst_pct > 0:
            result["institutional_holding_pct"] = round(inst_pct, 4)

        # ── Parse company ratios (top li items) ──
        ratios_section = soup.find("ul", {"id": "top-ratios"})
        if ratios_section:
            for li in ratios_section.find_all("li"):
                name_tag = li.find("span", {"class": "name"})
                val_tag = li.find("span", {"class": "value"})
                if not name_tag or not val_tag:
                    continue
                n = name_tag.get_text(strip=True).lower()
                v_text = val_tag.get_text(strip=True).replace(",", "").replace("₹", "").replace("%", "").strip()
                try:
                    v = float(v_text)
                    if "market cap" in n:
                        result["market_cap_cr"] = v
                    elif "current price" in n:
                        result["current_price"] = v
                    elif "book value" in n:
                        result["book_value_per_share"] = v
                    elif "stock p/e" in n or "p/e" in n:
                        result["pe_ratio"] = v
                    elif "roe" in n:
                        result["roe"] = round(v / 100, 4)
                    elif "roce" in n:
                        result["roce"] = round(v / 100, 4)
                    elif "debt / equity" in n or "d/e" in n:
                        result["debt_to_equity"] = v
                    elif "dividend yield" in n:
                        result["dividend_yield"] = round(v / 100, 4)
                except (ValueError, TypeError):
                    pass

        # ── Sector ──
        sec_tag = soup.find("a", {"class": "sub"}) or soup.find("span", {"class": "sector"})
        if not sec_tag:
            sec_tag = soup.select_one("div.company-info a")
        if sec_tag and sec_tag.get_text(strip=True):
            result.setdefault("sector", sec_tag.get_text(strip=True))

    except Exception as e:
        logger.warning(f"Screener.in fetch failed for '{company_name}': {e}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def fetch_missing_data(
    company_name: str,
    existing_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Attempt to fill in missing company data from public internet sources.

    Args:
        company_name:  Full company name, e.g. "Tata Steel Limited"
        existing_data: Current data dict — fields that are None / "Not Given"
                       will be replaced if fetched successfully.

    Returns:
        Dict containing ONLY the newly fetched / enriched fields.
        Empty dict if nothing could be fetched.
    """
    if existing_data is None:
        existing_data = {}

    # Determine which fields are currently missing
    missing = {
        k for k in FETCHABLE_FIELDS
        if _is_missing(existing_data.get(k))
    }
    logger.info(f"Fetching {len(missing)} missing fields for '{company_name}'")
    logger.info(f"Missing fields: {sorted(missing)}")

    fetched: Dict[str, Any] = {}
    candidates = _candidate_symbols(company_name)
    primary_symbol = candidates[0]

    # ── Source 1: Yahoo Finance ──────────────────────────────────────────
    logger.info(f"[1/3] Trying Yahoo Finance ({primary_symbol})...")
    yf_data = {}
    for sym in candidates:
        yf_data = _fetch_yahoo(sym)
        if yf_data:
            logger.info(f"Yahoo Finance returned {len(yf_data)} fields for {sym}")
            break
    fetched.update(yf_data)

    # ── Source 2: NSE India ──────────────────────────────────────────────
    if "promoter_holding_pct" not in fetched:
        logger.info(f"[2/3] Trying NSE India ({primary_symbol})...")
        for sym in candidates:
            nse_data = _fetch_nse(sym)
            if nse_data:
                logger.info(f"NSE returned {len(nse_data)} fields for {sym}")
                fetched.update(nse_data)
                break

    # ── Source 3: Screener.in ────────────────────────────────────────────
    if "promoter_holding_pct" not in fetched or "promoter_pledge_pct" not in fetched:
        logger.info("[3/3] Trying Screener.in...")
        scr_data = _fetch_screener(company_name)
        if scr_data:
            logger.info(f"Screener.in returned {len(scr_data)} fields")
            # Screener data takes precedence for shareholding (more accurate)
            for k, v in scr_data.items():
                if k in ("promoter_holding_pct", "promoter_pledge_pct",
                         "institutional_holding_pct"):
                    fetched[k] = v  # overwrite with Screener value
                else:
                    fetched.setdefault(k, v)

    # ── Filter: only return fields that were missing and now have a value ──
    result = {}
    for k, v in fetched.items():
        if not _is_missing(v):
            if k in missing or k not in existing_data:
                result[k] = v

    logger.info(f"Successfully fetched {len(result)} fields: {sorted(result.keys())}")
    return result


def describe_fetched(fetched: Dict[str, Any]) -> list[dict]:
    """
    Return a human-readable list of fetched fields for display.
    """
    LABELS = {
        "promoter_holding_pct":     ("Promoter Holding",       lambda v: f"{v*100:.1f}%"),
        "promoter_pledge_pct":      ("Promoter Pledge %",      lambda v: f"{v*100:.1f}%"),
        "institutional_holding_pct":("Institutional Holding",  lambda v: f"{v*100:.1f}%"),
        "public_holding_pct":       ("Public Holding",         lambda v: f"{v*100:.1f}%"),
        "sector":                   ("Sector",                  str),
        "industry":                 ("Industry",                str),
        "market_cap_cr":            ("Market Cap (₹ Cr)",      lambda v: f"₹{v:,.0f} Cr"),
        "pe_ratio":                 ("P/E Ratio",               lambda v: f"{v:.1f}x"),
        "roe":                      ("ROE",                     lambda v: f"{v*100:.1f}%"),
        "roce":                     ("ROCE",                    lambda v: f"{v*100:.1f}%"),
        "debt_to_equity":           ("Debt / Equity",          lambda v: f"{v:.2f}x"),
        "current_ratio":            ("Current Ratio",           lambda v: f"{v:.2f}x"),
        "dividend_yield":           ("Dividend Yield",          lambda v: f"{v*100:.2f}%"),
        "revenue":                  ("Revenue (₹ Cr)",          lambda v: f"₹{v:,.1f} Cr"),
        "ebitda":                   ("EBITDA (₹ Cr)",           lambda v: f"₹{v:,.1f} Cr"),
        "ebitda_margin":            ("EBITDA Margin",           lambda v: f"{v*100:.1f}%"),
        "pat":                      ("PAT (₹ Cr)",              lambda v: f"₹{v:,.1f} Cr"),
        "net_margin":               ("Net Margin",              lambda v: f"{v*100:.1f}%"),
        "book_value_per_share":     ("Book Value/Share",        lambda v: f"₹{v:.1f}"),
        "related_party_tx_to_rev":  ("Related Party Tx/Rev",   lambda v: f"{v*100:.1f}%"),
        "interest_coverage":        ("Interest Coverage",       lambda v: f"{v:.2f}x"),
    }

    rows = []
    for k, v in fetched.items():
        if k in LABELS:
            label, fmt = LABELS[k]
            try:
                display = fmt(v)
            except Exception:
                display = str(v)
            rows.append({"field": k, "label": label, "value": display})
        else:
            rows.append({"field": k, "label": k.replace("_", " ").title(), "value": str(v)})

    return sorted(rows, key=lambda r: r["label"])
