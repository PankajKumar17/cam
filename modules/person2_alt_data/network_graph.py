"""
Yakṣarāja — Promoter Network Graph & Contagion Risk (Person 2)
=====================================================================
Builds a Knowledge Graph of promoter-company relationships from MCA21
director-company linkage data. Computes a Network Contagion Risk Score
that feeds into the ensemble credit model.

Parts:
  A — Synthetic MCA data generation + NetworkX bipartite graph construction
  B — Contagion Risk Score computation (5 network metrics)
  C — Interactive Plotly network visualization

Author: Person 2
Module: modules/person2_alt_data/network_graph.py
"""

import os
import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from loguru import logger

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    logger.warning("networkx not installed — network analysis unavailable")
    NETWORKX_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    logger.warning("plotly not installed — visualization unavailable")
    PLOTLY_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

SECTORS = [
    "Textiles", "Infrastructure", "Steel", "Pharmaceuticals", "IT Services",
    "Real Estate", "FMCG", "Chemicals", "Auto Components", "Power",
    "Construction", "Agriculture", "Mining", "Telecom", "Financial Services",
]

COMPANY_STATUS_OPTIONS = [
    ("ACTIVE", 0.65),
    ("STRUCK_OFF", 0.08),
    ("NPA", 0.10),
    ("DORMANT", 0.07),
    ("UNDER_LIQUIDATION", 0.05),
    ("DISSOLVED", 0.05),
]

# Pre-defined companies for demo consistency
DEMO_COMPANIES = {
    "U17100MH2010PLC123456": {
        "company_name": "Sunrise Textile Mills",
        "sector": "Textiles",
        "status": "ACTIVE",
        "debt_cr": 520.0,
    },
    "U17100MH2012PLC234567": {
        "company_name": "Sunrise Exports Ltd",
        "sector": "Textiles",
        "status": "ACTIVE",
        "debt_cr": 180.0,
    },
    "U45200MH2015PTC345678": {
        "company_name": "Kumar Holdings Pvt Ltd",
        "sector": "Financial Services",
        "status": "ACTIVE",
        "debt_cr": 50.0,
    },
    "U72100MH2018PLC456789": {
        "company_name": "TechFab Industries",
        "sector": "Textiles",
        "status": "ACTIVE",
        "debt_cr": 310.0,
    },
    "U17100GJ2008PLC567890": {
        "company_name": "Gujarat Spinners Ltd",
        "sector": "Textiles",
        "status": "DORMANT",
        "debt_cr": 85.0,
    },
}

DEMO_DIRECTORS = {
    "DIN00012345": "Rajesh Kumar",
    "DIN00012346": "Meera Kumar",
    "DIN00023456": "Arvind Patel",
    "DIN00034567": "Sunita Reddy",
    "DIN00045678": "Vikram Singh",
}

# Seed for reproducibility
RANDOM_SEED = 42


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART A — SYNTHETIC MCA DATA GENERATION                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _generate_cin() -> str:
    """Generate a realistic-looking CIN (Corporate Identity Number)."""
    prefix = random.choice(["U", "L"])
    activity = f"{random.randint(10000, 99999)}"
    state = random.choice(["MH", "DL", "KA", "TN", "GJ", "RJ", "UP", "WB", "AP", "TG"])
    year = f"{random.randint(1990, 2023)}"
    entity = random.choice(["PLC", "PTC", "GAP", "NPL"])
    serial = f"{random.randint(100000, 999999)}"
    return f"{prefix}{activity}{state}{year}{entity}{serial}"


def _generate_din() -> str:
    """Generate a realistic-looking DIN (Director Identification Number)."""
    return f"DIN{random.randint(10000000, 99999999):08d}"


def _generate_company_name(idx: int) -> str:
    """Generate a plausible Indian company name."""
    prefixes = [
        "Shree", "Sri", "Royal", "National", "United", "Indo", "Global",
        "Premier", "Modern", "New", "Star", "Diamond", "Golden", "Silver",
        "Supreme", "Excel", "Prime", "Bharat", "Desh", "Hindustan",
    ]
    middles = [
        "Textile", "Steel", "Infra", "Pharma", "Tech", "Agro", "Petro",
        "Auto", "Power", "Cement", "Chemical", "Food", "Poly", "Paper",
        "Metal", "Electro", "Build", "Trade", "Finance", "Realty",
    ]
    suffixes = [
        "Mills Ltd", "Industries Ltd", "Pvt Ltd", "Corporation",
        "Enterprises", "Solutions Ltd", "Products Ltd", "Works Ltd",
        "International", "India Ltd",
    ]
    return f"{random.choice(prefixes)} {random.choice(middles)} {random.choice(suffixes)}"


def _generate_director_name(idx: int) -> str:
    """Generate a plausible Indian director name."""
    first_names = [
        "Rajesh", "Suresh", "Mukesh", "Anil", "Vikram", "Amit", "Sanjay",
        "Deepak", "Ramesh", "Ashok", "Priya", "Meera", "Sunita", "Kavita",
        "Neha", "Pooja", "Ritu", "Swati", "Anjali", "Divya",
    ]
    last_names = [
        "Kumar", "Sharma", "Patel", "Reddy", "Singh", "Gupta", "Jain",
        "Agarwal", "Mehta", "Shah", "Tiwari", "Verma", "Mishra", "Yadav",
        "Desai", "Iyer", "Nair", "Rao", "Sinha", "Banerjee",
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_synthetic_mca_data(
    n_directors: int = 500,
    n_companies: int = 1000,
    n_linkages: int = 2500,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate synthetic MCA21-like director-company linkage data.

    This mimics the Ministry of Corporate Affairs (MCA) public dataset
    that maps DIN (Director IDs) to CIN (Company IDs).

    Args:
        n_directors: Number of unique directors to generate (default 500)
        n_companies: Number of unique companies to generate (default 1000)
        n_linkages:  Number of director-company relationships (default 2500)
        seed:        Random seed for reproducibility

    Returns:
        DataFrame with columns:
          din, director_name, company_cin, company_name, sector,
          appointment_date, cessation_date, company_status, company_debt_cr
    """
    random.seed(seed)
    np.random.seed(seed)

    logger.info(f"Generating synthetic MCA data: {n_directors} directors, "
                f"{n_companies} companies, {n_linkages} linkages")

    # ── Generate directors ───────────────────────────────────────────────
    directors = {}
    # Add demo directors first
    directors.update(DEMO_DIRECTORS)
    while len(directors) < n_directors:
        din = _generate_din()
        if din not in directors:
            directors[din] = _generate_director_name(len(directors))
    director_list = list(directors.items())

    # ── Generate companies ───────────────────────────────────────────────
    companies = {}
    # Add demo companies first
    for cin, info in DEMO_COMPANIES.items():
        companies[cin] = info
    while len(companies) < n_companies:
        cin = _generate_cin()
        if cin not in companies:
            # Determine status with weighted probability
            status = random.choices(
                [s[0] for s in COMPANY_STATUS_OPTIONS],
                weights=[s[1] for s in COMPANY_STATUS_OPTIONS],
                k=1,
            )[0]
            debt = round(np.random.lognormal(mean=4.5, sigma=1.5), 1)
            if status in ("STRUCK_OFF", "DISSOLVED"):
                debt = round(debt * 0.3, 1)
            companies[cin] = {
                "company_name": _generate_company_name(len(companies)),
                "sector": random.choice(SECTORS),
                "status": status,
                "debt_cr": debt,
            }
    company_list = list(companies.items())

    # ── Generate linkages ────────────────────────────────────────────────
    linkages = []

    # Ensure demo directors are linked to demo companies
    demo_dir_list = list(DEMO_DIRECTORS.keys())
    demo_cin_list = list(DEMO_COMPANIES.keys())
    # Rajesh Kumar → all Sunrise companies + Kumar Holdings
    for cin in demo_cin_list[:3]:
        linkages.append((demo_dir_list[0], cin))
    # Meera Kumar → Sunrise Textile + Kumar Holdings
    linkages.append((demo_dir_list[1], demo_cin_list[0]))
    linkages.append((demo_dir_list[1], demo_cin_list[2]))
    # Arvind Patel → TechFab + Sunrise Exports
    linkages.append((demo_dir_list[2], demo_cin_list[1]))
    linkages.append((demo_dir_list[2], demo_cin_list[3]))
    # Sunita Reddy → Sunrise Textile + Gujarat Spinners
    linkages.append((demo_dir_list[3], demo_cin_list[0]))
    linkages.append((demo_dir_list[3], demo_cin_list[4]))

    existing_pairs = set(linkages)

    # Generate remaining random linkages
    # Most directors sit on 2-8 boards; a few "serial directors" sit on 10-20
    attempts = 0
    max_attempts = n_linkages * 5
    while len(linkages) < n_linkages and attempts < max_attempts:
        attempts += 1
        # Pick director with bias (some directors are more connected)
        d_idx = int(np.random.power(0.5) * len(director_list))
        d_idx = min(d_idx, len(director_list) - 1)
        din, _ = director_list[d_idx]

        c_idx = random.randint(0, len(company_list) - 1)
        cin, _ = company_list[c_idx]

        pair = (din, cin)
        if pair not in existing_pairs:
            existing_pairs.add(pair)
            linkages.append(pair)

    logger.info(f"Generated {len(linkages)} director-company linkages")

    # ── Build DataFrame ──────────────────────────────────────────────────
    records = []
    for din, cin in linkages:
        dir_name = directors[din]
        comp_info = companies[cin]

        # Random appointment date
        appt_year = random.randint(2000, 2023)
        appt_month = random.randint(1, 12)
        appt_date = datetime(appt_year, appt_month, 1)

        # Cessation: None for active, some date for resigned
        cessation_date = None
        if comp_info["status"] in ("STRUCK_OFF", "DISSOLVED"):
            cessation_date = appt_date + timedelta(days=random.randint(365, 3650))
        elif random.random() < 0.15:  # 15% chance resigned
            cessation_date = appt_date + timedelta(days=random.randint(365, 2555))

        records.append({
            "din": din,
            "director_name": dir_name,
            "company_cin": cin,
            "company_name": comp_info["company_name"],
            "sector": comp_info["sector"],
            "appointment_date": appt_date.strftime("%Y-%m-%d"),
            "cessation_date": cessation_date.strftime("%Y-%m-%d") if cessation_date else None,
            "company_status": comp_info["status"],
            "company_debt_cr": comp_info["debt_cr"],
        })

    df = pd.DataFrame(records)
    logger.info(f"MCA DataFrame shape: {df.shape}")
    return df


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART A — NETWORKX BIPARTITE GRAPH CONSTRUCTION                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Module-level cache for the MCA data and graph
_MCA_DATA_CACHE: Optional[pd.DataFrame] = None
_GRAPH_CACHE: Optional[Any] = None


def _get_mca_data() -> pd.DataFrame:
    """Get or generate the MCA dataset (cached)."""
    global _MCA_DATA_CACHE
    if _MCA_DATA_CACHE is None:
        _MCA_DATA_CACHE = generate_synthetic_mca_data()
    return _MCA_DATA_CACHE


def _get_full_graph():
    """Build or retrieve the full bipartite graph (cached)."""
    global _GRAPH_CACHE
    if _GRAPH_CACHE is not None:
        return _GRAPH_CACHE

    if not NETWORKX_AVAILABLE:
        logger.error("networkx is required. pip install networkx")
        return None

    df = _get_mca_data()
    G = nx.Graph()

    # Add director nodes
    for _, row in df.drop_duplicates(subset="din").iterrows():
        G.add_node(
            row["din"],
            node_type="director",
            label=row["director_name"],
            bipartite=0,
        )

    # Add company nodes
    for _, row in df.drop_duplicates(subset="company_cin").iterrows():
        G.add_node(
            row["company_cin"],
            node_type="company",
            label=row["company_name"],
            status=row["company_status"],
            sector=row.get("sector", "Unknown"),
            debt_cr=row.get("company_debt_cr", 0),
            bipartite=1,
        )

    # Add edges (director → company)
    for _, row in df.iterrows():
        G.add_edge(
            row["din"],
            row["company_cin"],
            appointment_date=row["appointment_date"],
            cessation_date=row["cessation_date"],
        )

    logger.info(f"Full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    _GRAPH_CACHE = G
    return G


def build_promoter_network(company_cin: str) -> Any:
    """
    Build the promoter's complete company network for a given target company.

    Starting from the target company CIN:
      1. Find all directors of the target company
      2. Find all other companies those directors are associated with
      3. Build a subgraph containing:
         - The target company node
         - All its directors
         - All companies those directors are linked to
         - All edges between them

    Args:
        company_cin: CIN (Corporate Identity Number) of the target company
                     e.g., "U17100MH2010PLC123456" for Sunrise Textile Mills

    Returns:
        networkx.Graph — subgraph representing the promoter network
        Returns empty Graph if company not found or networkx unavailable
    """
    if not NETWORKX_AVAILABLE:
        logger.error("networkx required for network analysis")
        return nx.Graph() if NETWORKX_AVAILABLE else None

    G = _get_full_graph()
    if G is None or company_cin not in G:
        logger.warning(f"Company {company_cin} not found in graph")
        return nx.Graph()

    # Step 1: Find all directors of target company
    directors = [
        n for n in G.neighbors(company_cin)
        if G.nodes[n].get("node_type") == "director"
    ]
    logger.info(f"Target {company_cin}: found {len(directors)} directors")

    # Step 2: Find all companies those directors are linked to
    related_companies = set()
    related_companies.add(company_cin)
    for din in directors:
        for neighbor in G.neighbors(din):
            if G.nodes[neighbor].get("node_type") == "company":
                related_companies.add(neighbor)

    # Step 3: Build subgraph with all directors and related companies
    all_nodes = set(directors) | related_companies

    # Also include directors of related companies for clustering computation
    for cin in list(related_companies):
        for n in G.neighbors(cin):
            if G.nodes[n].get("node_type") == "director":
                all_nodes.add(n)

    subgraph = G.subgraph(all_nodes).copy()
    logger.info(f"Promoter network: {subgraph.number_of_nodes()} nodes, "
                f"{subgraph.number_of_edges()} edges, "
                f"{len(related_companies)} companies")

    # Tag the target company
    if company_cin in subgraph:
        subgraph.nodes[company_cin]["is_target"] = True

    return subgraph


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART B — CONTAGION RISK SCORE                                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def compute_contagion_score(company_cin: str) -> Dict[str, Any]:
    """
    Compute the Network Contagion Risk Score for a borrower company.

    Metrics computed:
      1. promoter_total_companies: total companies in the promoter network
      2. promoter_npa_companies:   companies with status = NPA
      3. promoter_struck_off:      companies with status = STRUCK_OFF
      4. network_npa_ratio:        npa_companies / total_companies
      5. network_clustering_coeff: how interconnected the promoter group is
      6. contagion_risk_score:     0.4 * npa_ratio + 0.3 * clustering + 0.3 * size_factor

    Args:
        company_cin: CIN of the target company

    Returns:
        Dict with all computed metrics:
        {
            "company_cin": str,
            "company_name": str,
            "promoter_total_companies": int,
            "promoter_npa_companies": int,
            "promoter_struck_off_companies": int,
            "promoter_directors": int,
            "network_npa_ratio": float,
            "network_clustering_coefficient": float,
            "size_factor": float,
            "contagion_risk_score": float (0–1),
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "related_companies": [{"cin": ..., "name": ..., "status": ...}, ...],
        }
    """
    logger.info(f"Computing contagion score for: {company_cin}")

    # Build the promoter network
    subgraph = build_promoter_network(company_cin)

    if subgraph is None or subgraph.number_of_nodes() == 0:
        logger.warning(f"Empty network for {company_cin} — returning zero risk")
        return _fallback_contagion(company_cin)

    # ── Extract company and director nodes ───────────────────────────────
    company_nodes = [
        n for n, d in subgraph.nodes(data=True)
        if d.get("node_type") == "company"
    ]
    director_nodes = [
        n for n, d in subgraph.nodes(data=True)
        if d.get("node_type") == "director"
    ]

    # Get target company info
    target_info = subgraph.nodes.get(company_cin, {})
    company_name = target_info.get("label", "Unknown")

    # ── Metric 1: Total companies ────────────────────────────────────────
    # Exclude the target company itself
    related = [c for c in company_nodes if c != company_cin]
    total_companies = len(related)

    # ── Metric 2 & 3: NPA and struck-off companies ──────────────────────
    npa_companies = 0
    struck_off = 0
    stressed_statuses = {"NPA", "UNDER_LIQUIDATION"}

    related_details = []
    for cin in related:
        node_data = subgraph.nodes[cin]
        status = node_data.get("status", "ACTIVE")
        related_details.append({
            "cin": cin,
            "name": node_data.get("label", "Unknown"),
            "status": status,
            "sector": node_data.get("sector", "Unknown"),
            "debt_cr": node_data.get("debt_cr", 0),
        })
        if status in stressed_statuses:
            npa_companies += 1
        if status == "STRUCK_OFF":
            struck_off += 1

    # ── Metric 4: NPA ratio ──────────────────────────────────────────────
    npa_ratio = npa_companies / max(total_companies, 1)

    # ── Metric 5: Clustering coefficient ─────────────────────────────────
    # For bipartite graph, use the company-projection clustering
    try:
        if len(company_nodes) >= 2:
            # Project onto company nodes (companies connected through shared directors)
            company_projection = nx.bipartite.projected_graph(
                subgraph, company_nodes, multigraph=False
            )
            clustering = nx.average_clustering(company_projection)
        else:
            clustering = 0.0
    except Exception as e:
        logger.warning(f"Clustering computation failed: {e}")
        clustering = 0.0

    # ── Metric 6: Size factor ────────────────────────────────────────────
    # More companies = more contagion surface area (log-scaled, capped at 1)
    # Normalized: 1 company → 0, 5 → 0.5, 15+ → 1.0
    size_factor = min(1.0, max(0.0, np.log1p(total_companies) / np.log1p(15)))

    # ── Composite Contagion Risk Score ───────────────────────────────────
    contagion_risk_score = round(
        0.4 * npa_ratio + 0.3 * clustering + 0.3 * size_factor,
        4,
    )
    contagion_risk_score = min(1.0, max(0.0, contagion_risk_score))

    # Risk level
    if contagion_risk_score > 0.50:
        risk_level = "HIGH"
    elif contagion_risk_score > 0.25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    result = {
        "company_cin": company_cin,
        "company_name": company_name,
        "promoter_total_companies": total_companies,
        "promoter_npa_companies": npa_companies,
        "promoter_struck_off_companies": struck_off,
        "promoter_directors": len(director_nodes),
        "network_npa_ratio": round(npa_ratio, 4),
        "network_clustering_coefficient": round(clustering, 4),
        "size_factor": round(size_factor, 4),
        "contagion_risk_score": contagion_risk_score,
        "risk_level": risk_level,
        "related_companies": related_details,
    }

    logger.info(f"Contagion score for {company_name}: {contagion_risk_score:.4f} ({risk_level})")
    return result


def _fallback_contagion(company_cin: str) -> Dict[str, Any]:
    """Return zero-risk scores when network cannot be built."""
    return {
        "company_cin": company_cin,
        "company_name": "Unknown",
        "promoter_total_companies": 0,
        "promoter_npa_companies": 0,
        "promoter_struck_off_companies": 0,
        "promoter_directors": 0,
        "network_npa_ratio": 0.0,
        "network_clustering_coefficient": 0.0,
        "size_factor": 0.0,
        "contagion_risk_score": 0.0,
        "risk_level": "LOW",
        "related_companies": [],
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART C — INTERACTIVE NETWORK VISUALIZATION                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Status → color mapping
STATUS_COLORS = {
    "ACTIVE":              "#1B7A2B",   # Green
    "DORMANT":             "#E68A00",   # Amber/Orange
    "NPA":                 "#C62828",   # Red
    "STRUCK_OFF":          "#B71C1C",   # Dark Red
    "UNDER_LIQUIDATION":   "#D32F2F",   # Red
    "DISSOLVED":           "#757575",   # Grey
}

DIRECTOR_COLOR = "#90A4AE"   # Light grey-blue
TARGET_COLOR   = "#0A1F3C"   # Navy (target company)


def visualize_network(
    company_cin: str,
    output_path: Optional[str] = None,
    contagion_result: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Generate an interactive Plotly network graph for the promoter network.

    Visual encoding:
      - Target company: NAVY, largest node
      - Related companies: color by status (GREEN/ORANGE/RED)
      - Directors: small grey nodes connecting companies
      - Node size proportional to company debt
      - Edges as grey lines

    Args:
        company_cin: CIN of the target company
        output_path: Path to save HTML file (auto-generated if None)

    Returns:
        Path to saved HTML file, or None on failure
    """
    if not PLOTLY_AVAILABLE:
        logger.error("plotly required for visualization. pip install plotly")
        return None
    if not NETWORKX_AVAILABLE:
        logger.error("networkx required for visualization")
        return None

    subgraph = build_promoter_network(company_cin)
    if subgraph is None or subgraph.number_of_nodes() == 0:
        logger.warning("Empty network — cannot visualize")
        return None

    # Get target info
    target_info = subgraph.nodes.get(company_cin, {})
    company_name = target_info.get("label", "Unknown")

    # ── Layout ───────────────────────────────────────────────────────────
    # Use spring layout for aesthetics
    pos = nx.spring_layout(subgraph, k=2.0, iterations=50, seed=42)

    # ── Build edge traces ────────────────────────────────────────────────
    edge_x, edge_y = [], []
    for u, v in subgraph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.8, color="#D0D0D0"),
        hoverinfo="none",
        showlegend=False,
    )

    # ── Build node traces (separate for companies vs directors) ──────────
    traces = [edge_trace]

    # Separate nodes by type
    for node_id, data in subgraph.nodes(data=True):
        x, y = pos[node_id]
        ntype = data.get("node_type", "unknown")

        if ntype == "director":
            # Small grey node
            traces.append(go.Scatter(
                x=[x], y=[y],
                mode="markers+text",
                marker=dict(
                    size=8,
                    color=DIRECTOR_COLOR,
                    symbol="diamond",
                    line=dict(width=0.5, color="#607D8B"),
                ),
                text=[data.get("label", node_id)],
                textposition="top center",
                textfont=dict(size=7, color="#607D8B"),
                hovertext=(
                    f"<b>{data.get('label', node_id)}</b><br>"
                    f"Type: Director<br>"
                    f"DIN: {node_id}"
                ),
                hoverinfo="text",
                showlegend=False,
            ))
        else:
            # Company node — size by debt, color by status
            is_target = data.get("is_target", False) or node_id == company_cin
            status = data.get("status", "ACTIVE")
            debt = data.get("debt_cr", 50)

            if is_target:
                color = TARGET_COLOR
                size = max(30, min(60, debt / 10))
                symbol = "star"
                border_width = 3
                border_color = "#E86C00"  # orange border for target
            else:
                color = STATUS_COLORS.get(status, "#757575")
                size = max(12, min(40, debt / 15))
                symbol = "circle"
                border_width = 1
                border_color = "#424242"

            traces.append(go.Scatter(
                x=[x], y=[y],
                mode="markers+text",
                marker=dict(
                    size=size,
                    color=color,
                    symbol=symbol,
                    line=dict(width=border_width, color=border_color),
                    opacity=0.9,
                ),
                text=[data.get("label", node_id)],
                textposition="bottom center",
                textfont=dict(
                    size=9 if is_target else 8,
                    color="#0A1F3C" if is_target else "#424242",
                ),
                hovertext=(
                    f"<b>{data.get('label', node_id)}</b><br>"
                    f"Status: {status}<br>"
                    f"Sector: {data.get('sector', 'N/A')}<br>"
                    f"Debt: ₹{debt:.1f} Cr<br>"
                    f"CIN: {node_id}"
                    f"{'<br><b>★ TARGET COMPANY</b>' if is_target else ''}"
                ),
                hoverinfo="text",
                showlegend=False,
            ))

    # ── Layout ───────────────────────────────────────────────────────────
    # Use pre-computed contagion result if provided, otherwise recompute
    contagion = contagion_result if contagion_result is not None else compute_contagion_score(company_cin)

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(
            text=(
                f"<b>Promoter Network — {company_name}</b><br>"
                f"<span style='font-size:12px; color:#757575;'>"
                f"Contagion Risk: {contagion['contagion_risk_score']:.4f} "
                f"({contagion['risk_level']}) | "
                f"Companies: {contagion['promoter_total_companies']} | "
                f"NPA: {contagion['promoter_npa_companies']} | "
                f"Directors: {contagion['promoter_directors']}"
                f"</span>"
            ),
            x=0.5,
            xanchor="center",
        ),
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=700,
        margin=dict(t=100, b=40, l=40, r=40),
        annotations=[
            dict(
                text=(
                    "★ = Target Company | "
                    "◆ = Director | "
                    "● Green = Active | "
                    "● Orange = Dormant | "
                    "● Red = NPA/Struck Off"
                ),
                xref="paper", yref="paper",
                x=0.5, y=-0.02,
                showarrow=False,
                font=dict(size=10, color="#757575"),
                xanchor="center",
            ),
        ],
    )

    # ── Save HTML ────────────────────────────────────────────────────────
    if output_path is None:
        safe_name = company_name.replace(" ", "_").replace("/", "_")
        output_dir = os.path.join("data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"network_graph_{safe_name}.html")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    fig.write_html(output_path, include_plotlyjs="cdn")
    logger.info(f"Network graph saved: {output_path}")
    return output_path


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONVENIENCE: HIGH-LEVEL ENTRY POINT                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def run_network_analysis(
    company_cin: str = "U17100MH2010PLC123456",
    save_visualization: bool = True,
) -> Dict[str, Any]:
    """
    Run the full network analysis pipeline for a borrower company.

    1. Build MCA linkage graph
    2. Extract promoter network
    3. Compute contagion risk score
    4. Generate interactive visualization

    Args:
        company_cin: CIN of the target company
        save_visualization: Whether to save the Plotly HTML graph

    Returns:
        Complete analysis dict (same as compute_contagion_score output,
        plus 'visualization_path' key)
    """
    logger.info(f"{'='*60}")
    logger.info(f"NETWORK ANALYSIS — {company_cin}")
    logger.info(f"{'='*60}")

    result = compute_contagion_score(company_cin)

    if save_visualization:
        viz_path = visualize_network(company_cin, contagion_result=result)
        result["visualization_path"] = viz_path
    else:
        result["visualization_path"] = None

    logger.info(f"{'='*60}")
    logger.info(f"NETWORK ANALYSIS COMPLETE")
    logger.info(f"  Company: {result['company_name']}")
    logger.info(f"  Contagion Risk: {result['contagion_risk_score']:.4f} ({result['risk_level']})")
    logger.info(f"  Network Size: {result['promoter_total_companies']} companies, "
                f"{result['promoter_directors']} directors")
    logger.info(f"{'='*60}")

    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NETWORK GRAPH — Standalone Test")
    print("=" * 60)

    # Demo: Sunrise Textile Mills
    TARGET_CIN = "U17100MH2010PLC123456"

    # Step 1: Generate MCA data
    print("\n[1] Generating synthetic MCA data...")
    mca_df = generate_synthetic_mca_data()
    print(f"   Records: {len(mca_df)}")
    print(f"   Unique directors: {mca_df['din'].nunique()}")
    print(f"   Unique companies: {mca_df['company_cin'].nunique()}")

    # Step 2: Build promoter network
    print(f"\n[2] Building promoter network for Sunrise Textile Mills...")
    subnet = build_promoter_network(TARGET_CIN)
    if subnet:
        companies_in_net = [
            n for n, d in subnet.nodes(data=True)
            if d.get("node_type") == "company"
        ]
        directors_in_net = [
            n for n, d in subnet.nodes(data=True)
            if d.get("node_type") == "director"
        ]
        print(f"   Companies in network: {len(companies_in_net)}")
        print(f"   Directors in network: {len(directors_in_net)}")

    # Step 3: Compute contagion score
    print(f"\n[3] Computing contagion risk score...")
    contagion = compute_contagion_score(TARGET_CIN)
    print(f"   Total companies: {contagion['promoter_total_companies']}")
    print(f"   NPA companies: {contagion['promoter_npa_companies']}")
    print(f"   NPA ratio: {contagion['network_npa_ratio']:.4f}")
    print(f"   Clustering: {contagion['network_clustering_coefficient']:.4f}")
    print(f"   Size factor: {contagion['size_factor']:.4f}")
    print(f"   CONTAGION SCORE: {contagion['contagion_risk_score']:.4f} ({contagion['risk_level']})")

    print(f"\n   Related companies:")
    for rc in contagion["related_companies"][:10]:
        flag = "🔴" if rc["status"] in ("NPA", "STRUCK_OFF") else (
            "🟡" if rc["status"] == "DORMANT" else "🟢"
        )
        print(f"     {flag} {rc['name']} [{rc['status']}] — ₹{rc['debt_cr']:.1f} Cr")

    # Step 4: Visualization
    print(f"\n[4] Generating interactive network graph...")
    viz_path = visualize_network(TARGET_CIN)
    if viz_path:
        print(f"   Saved: {viz_path}")

    print("\n" + "=" * 60)
    print("✅ Network analysis complete!")
    print("=" * 60)
