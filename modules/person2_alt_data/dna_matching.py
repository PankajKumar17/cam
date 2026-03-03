"""
Yakṣarāja — Corporate DNA Matching Module (Person 2)
==========================================================
Encodes financial fingerprints of India's major corporate collapses
and checks if a borrower resembles any of them 12-24 months before
their collapse.

"Companies don't fail in unique ways — they fail in patterns."

Archetypes:
  1. IL&FS         — Asset-liability mismatch (short funding long assets)
  2. DHFL          — Fund diversion via related parties
  3. Jet Airways   — Revenue decline + cost rigidity
  4. Videocon      — Group contagion + promoter desperation
  5. Satyam        — Accounting manipulation
  6. Kingfisher    — Overleveraged + cash burn

Method: Cosine similarity between borrower's normalised feature vector
and each archetype fingerprint.

Author: Person 2
Module: modules/person2_alt_data/dna_matching.py
"""

import os
from typing import Dict, Any, Optional, List, Tuple

import numpy as np

from loguru import logger


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ARCHETYPE FINGERPRINTS                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# Each fingerprint captures the KEY financial ratios observed 12-24 months
# before the company's collapse.  Not every archetype uses the same
# features — missing features are treated as "not informative" and excluded
# from the similarity computation.

IL_IFS_FINGERPRINT: Dict[str, float] = {
    "st_debt_to_lt_assets_ratio": 2.1,   # short funding long assets
    "cfo_to_debt":                0.02,   # terrible cash coverage of debt
    "debt_growth_3yr":            0.45,   # rapid debt accumulation
    "current_ratio":              0.6,    # severe liquidity stress
}

DHFL_FINGERPRINT: Dict[str, float] = {
    "related_party_tx_to_rev":    0.35,   # massive fund diversion
    "receivables_days":         180.0,    # fake receivables
    "promoter_pledge_pct":        0.72,   # desperate pledging
    "gst_vs_bank_divergence":     0.42,   # revenue inflation
}

JET_AIRWAYS_FINGERPRINT: Dict[str, float] = {
    "revenue_growth":            -0.15,   # declining revenue
    "employee_cost_to_rev":       0.35,   # cost not reducing with revenue
    "current_ratio":              0.45,   # severe working capital stress
    "free_cash_flow_margin":     -0.08,   # burning cash
}

VIDEOCON_FINGERPRINT: Dict[str, float] = {
    "contagion_risk_score":       0.75,   # group contagion
    "promoter_pledge_pct":        0.85,   # extreme pledging
    "roe":                       -0.12,   # destroying equity value
    "network_npa_ratio":          0.45,   # group companies failing
}

SATYAM_FINGERPRINT: Dict[str, float] = {
    "beneish_dsri":               1.35,   # receivables manipulation
    "beneish_tata":               0.09,   # accruals = manipulation
    "cfo_to_pat":                 0.08,   # cash flow disconnected from profit
    "auditor_distress_score":     1.0,    # auditor discomfort
}

KINGFISHER_FINGERPRINT: Dict[str, float] = {
    "revenue_growth":            -0.25,   # steep revenue decline
    "debt_to_equity":            12.0,    # extreme leverage
    "interest_coverage":          0.3,    # can't service debt
    "promoter_pledge_pct":        0.90,   # near-total pledging
}

# Registry of all archetypes
ARCHETYPES: Dict[str, Dict[str, float]] = {
    "IL&FS":       IL_IFS_FINGERPRINT,
    "DHFL":        DHFL_FINGERPRINT,
    "Jet Airways": JET_AIRWAYS_FINGERPRINT,
    "Videocon":    VIDEOCON_FINGERPRINT,
    "Satyam":      SATYAM_FINGERPRINT,
    "Kingfisher":  KINGFISHER_FINGERPRINT,
}

# Collapse backstories for warning text
ARCHETYPE_DESCRIPTIONS: Dict[str, str] = {
    "IL&FS": (
        "IL&FS collapsed in Sep-2018 due to extreme asset-liability mismatch — "
        "short-term borrowing funded long-term infra projects.  When refinancing "
        "dried up, ₹91,000 Cr in debt defaulted, triggering an NBFC credit crisis."
    ),
    "DHFL": (
        "DHFL failed in 2019 due to massive fund diversion through shell entities.  "
        "₹31,000 Cr was siphoned via related-party transactions.  The company "
        "inflated receivables and revenue while promoters pledged shares to cover gaps."
    ),
    "Jet Airways": (
        "Jet Airways ceased operations in Apr-2019 after years of declining revenue "
        "while fixed costs (employees, leases) remained rigid.  Negative free cash "
        "flow eroded all equity, leaving ₹8,500 Cr in unpaid debt."
    ),
    "Videocon": (
        "Videocon Industries was admitted to NCLT in 2018 with ₹64,838 Cr debt.  "
        "The group's multiple entities had severe contagion — NPA in one entity "
        "infected the rest.  Promoter pledging reached 85% as the group unwound."
    ),
    "Satyam": (
        "Satyam Computer Services — India's biggest accounting fraud (2009).  "
        "₹7,136 Cr in fictitious cash and receivables were fabricated.  "
        "Cash flow bore no relation to reported profit.  The auditor missed "
        "years of manipulation."
    ),
    "Kingfisher": (
        "Kingfisher Airlines accumulated ₹9,091 Cr in debt with a D/E ratio "
        "of 12x+.  Revenue declined 25% YoY while interest coverage fell below "
        "0.3x.  Promoter pledged 90% of shares before eventual NCLT proceedings."
    ),
}

# ── Default borrower feature set (Sunrise Textile Mills demo) ────────────
DEFAULT_BORROWER_FEATURES: Dict[str, float] = {
    # Leverage & liquidity
    "st_debt_to_lt_assets_ratio": 0.8,
    "current_ratio":              1.35,
    "debt_to_equity":             1.8,
    "interest_coverage":          1.95,
    # Cash flow
    "cfo_to_debt":                0.15,
    "cfo_to_pat":                 0.85,
    "free_cash_flow_margin":      0.04,
    # Growth
    "revenue_growth":             0.08,
    "debt_growth_3yr":            0.12,
    # Profitability
    "roe":                        0.12,
    "employee_cost_to_rev":       0.15,
    # Governance
    "promoter_pledge_pct":        0.15,
    "related_party_tx_to_rev":    0.05,
    "receivables_days":          55.0,
    # Alt data (from other Person 2 modules)
    "gst_vs_bank_divergence":     0.03,
    "contagion_risk_score":       0.12,
    "network_npa_ratio":          0.05,
    # Forensic
    "beneish_dsri":               0.95,
    "beneish_tata":               0.03,
    "auditor_distress_score":     0.0,
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SIMILARITY ENGINE                                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns value in [-1, 1]:
      1.0 = identical direction (borrower matches archetype exactly)
      0.0 = orthogonal (no similarity)
     -1.0 = opposite direction
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def _normalize_features(features: Dict[str, float]) -> Dict[str, float]:
    """
    Min-max style normalization using domain-reasonable ranges.

    Each feature is scaled to [0, 1] based on a domain range so that
    cosine similarity is meaningful even when features have very
    different magnitudes (e.g., D/E ratio 12 vs NPA ratio 0.45).
    """
    # (feature_name, min_val, max_val)
    RANGES: Dict[str, Tuple[float, float]] = {
        "st_debt_to_lt_assets_ratio": (0.0, 3.0),
        "cfo_to_debt":                (-0.1, 0.5),
        "debt_growth_3yr":            (-0.3, 1.0),
        "current_ratio":              (0.0, 3.0),
        "related_party_tx_to_rev":    (0.0, 0.5),
        "receivables_days":           (0.0, 365.0),
        "promoter_pledge_pct":        (0.0, 1.0),
        "gst_vs_bank_divergence":     (-0.2, 0.6),
        "revenue_growth":             (-0.5, 0.5),
        "employee_cost_to_rev":       (0.0, 0.5),
        "free_cash_flow_margin":      (-0.3, 0.3),
        "contagion_risk_score":       (0.0, 1.0),
        "roe":                        (-0.5, 0.5),
        "network_npa_ratio":          (0.0, 1.0),
        "beneish_dsri":               (0.5, 2.0),
        "beneish_tata":               (-0.1, 0.2),
        "cfo_to_pat":                 (-0.5, 1.5),
        "auditor_distress_score":     (0.0, 1.0),
        "debt_to_equity":             (0.0, 15.0),
        "interest_coverage":          (0.0, 5.0),
    }

    normalised = {}
    for feat, val in features.items():
        lo, hi = RANGES.get(feat, (0.0, 1.0))
        if hi - lo < 1e-9:
            normalised[feat] = 0.5
        else:
            normalised[feat] = (val - lo) / (hi - lo)
    return normalised


def compute_dna_similarity(
    borrower_features: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute cosine similarity between a borrower's feature vector and
    each of the 6 corporate-collapse archetype fingerprints.

    Only features present in BOTH the borrower data and the archetype
    fingerprint are used for comparison (intersection approach).

    Args:
        borrower_features: Dict mapping feature names to numeric values.
                           If None, uses DEFAULT_BORROWER_FEATURES (demo).

    Returns:
        {
            "similarities": {
                "IL&FS":       {"score": float, "matched_features": int, "features_used": [...]},
                "DHFL":        {...},
                "Jet Airways": {...},
                "Videocon":    {...},
                "Satyam":      {...},
                "Kingfisher":  {...},
            },
            "closest_archetype":     str,
            "max_similarity":        float,
            "borrower_risk_profile": str,
            "warning":               str | None,
        }
    """
    if borrower_features is None:
        borrower_features = DEFAULT_BORROWER_FEATURES.copy()

    logger.info(f"Computing DNA similarity ({len(borrower_features)} borrower features)")

    # Normalise borrower features
    norm_borrower = _normalize_features(borrower_features)

    similarities: Dict[str, Dict[str, Any]] = {}

    for archetype_name, fingerprint in ARCHETYPES.items():
        # Find common features
        common_features = sorted(
            set(norm_borrower.keys()) & set(fingerprint.keys())
        )

        if len(common_features) == 0:
            similarities[archetype_name] = {
                "score": 0.0,
                "matched_features": 0,
                "features_used": [],
            }
            continue

        # Normalise archetype features
        norm_archetype = _normalize_features(fingerprint)

        # Build aligned vectors
        vec_borrower = np.array([norm_borrower[f] for f in common_features])
        vec_archetype = np.array([norm_archetype[f] for f in common_features])

        cos_sim = _cosine_similarity(vec_borrower, vec_archetype)

        # Clamp to [0, 1] for interpretability (negative = anti-correlated)
        score = round(max(0.0, cos_sim), 4)

        similarities[archetype_name] = {
            "score": score,
            "matched_features": len(common_features),
            "features_used": common_features,
        }

        logger.debug(f"  {archetype_name}: {score:.4f} "
                      f"({len(common_features)} features)")

    # ── Identify closest archetype ───────────────────────────────────────
    closest = max(similarities, key=lambda k: similarities[k]["score"])
    max_sim = similarities[closest]["score"]

    # ── Risk profile ─────────────────────────────────────────────────────
    if max_sim > 0.85:
        risk_profile = "CRITICAL"
    elif max_sim > 0.75:
        risk_profile = "HIGH"
    elif max_sim > 0.60:
        risk_profile = "ELEVATED"
    elif max_sim > 0.40:
        risk_profile = "MODERATE"
    else:
        risk_profile = "LOW"

    # ── Warning text ─────────────────────────────────────────────────────
    warning = get_dna_warning(similarities)

    result = {
        "similarities": similarities,
        "closest_archetype": closest,
        "max_similarity": max_sim,
        "borrower_risk_profile": risk_profile,
        "warning": warning,
    }

    logger.info(f"Closest archetype: {closest} (similarity={max_sim:.4f})")
    logger.info(f"Risk profile: {risk_profile}")

    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  WARNING GENERATOR                                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def get_dna_warning(
    similarity_results: Dict[str, Dict[str, Any]],
    threshold: float = 0.75,
) -> Optional[str]:
    """
    Generate a human-readable warning if any archetype similarity
    exceeds the threshold.

    Args:
        similarity_results: Dict of {archetype_name: {"score": float, ...}}
                            This is the "similarities" key from compute_dna_similarity().
        threshold:          Similarity threshold for triggering a warning (default 0.75)

    Returns:
        Warning string if any archetype exceeds threshold, else None
    """
    warnings = []

    for name, data in similarity_results.items():
        score = data.get("score", 0.0) if isinstance(data, dict) else 0.0
        if score > threshold:
            description = ARCHETYPE_DESCRIPTIONS.get(name, "")
            features = data.get("features_used", []) if isinstance(data, dict) else []
            warnings.append(
                f"⚠️  HIGH SIMILARITY TO {name.upper()} PATTERN "
                f"(score={score:.2f}, {len(features)} matching features)\n"
                f"   Background: {description}\n"
                f"   Matching on: {', '.join(features)}"
            )

    if not warnings:
        return None

    header = (
        "🔴 CORPORATE DNA WARNING — COLLAPSE PATTERN DETECTED\n"
        "=" * 55 + "\n"
        "The borrower's financial profile shows significant similarity\n"
        "to companies that collapsed 12-24 months after exhibiting\n"
        "these same patterns.\n"
        "=" * 55
    )
    return header + "\n\n" + "\n\n".join(warnings)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONVENIENCE: FULL DNA REPORT                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def run_dna_analysis(
    borrower_features: Optional[Dict[str, float]] = None,
    company_name: str = "Sunrise Textile Mills",
) -> Dict[str, Any]:
    """
    Run full Corporate DNA analysis and return a structured report.

    Args:
        borrower_features: Feature dict (None → demo defaults)
        company_name:      Company name for the report header

    Returns:
        Complete analysis dict (same as compute_dna_similarity output,
        plus "company_name" and "archetype_details" keys)
    """
    logger.info(f"{'='*60}")
    logger.info(f"CORPORATE DNA ANALYSIS — {company_name}")
    logger.info(f"{'='*60}")

    result = compute_dna_similarity(borrower_features)
    result["company_name"] = company_name

    # Add archetype descriptions
    archetype_details = []
    for name, data in result["similarities"].items():
        archetype_details.append({
            "archetype": name,
            "similarity_score": data["score"],
            "matched_features": data["matched_features"],
            "features_used": data["features_used"],
            "description": ARCHETYPE_DESCRIPTIONS.get(name, ""),
        })
    # Sort by score descending
    archetype_details.sort(key=lambda x: x["similarity_score"], reverse=True)
    result["archetype_details"] = archetype_details

    logger.info(f"{'='*60}")
    logger.info(f"DNA ANALYSIS COMPLETE — {company_name}")
    logger.info(f"  Closest: {result['closest_archetype']} "
                f"({result['max_similarity']:.4f})")
    logger.info(f"  Risk:    {result['borrower_risk_profile']}")
    for ad in archetype_details:
        emoji = "🔴" if ad["similarity_score"] > 0.75 else (
            "🟡" if ad["similarity_score"] > 0.50 else "🟢"
        )
        logger.info(f"    {emoji} {ad['archetype']:>12s}: "
                     f"{ad['similarity_score']:.4f} "
                     f"({ad['matched_features']} features)")
    logger.info(f"{'='*60}")

    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CORPORATE DNA MATCHING — Standalone Test")
    print("=" * 60)

    # ── Test 1: Healthy company (Sunrise Textile Mills defaults) ─────────
    print("\n[1] Sunrise Textile Mills (expected: LOW risk)")
    r1 = run_dna_analysis(company_name="Sunrise Textile Mills")
    print(f"   Closest archetype: {r1['closest_archetype']} "
          f"(similarity={r1['max_similarity']:.4f})")
    print(f"   Risk profile:      {r1['borrower_risk_profile']}")
    print(f"   Warning:           {r1['warning'] is not None}")
    for ad in r1["archetype_details"]:
        bar = "█" * int(ad["similarity_score"] * 20)
        print(f"     {ad['archetype']:>12s}: {ad['similarity_score']:.4f} {bar}")

    # ── Test 2: IL&FS-like company ───────────────────────────────────────
    print("\n[2] IL&FS-like borrower (expected: HIGH IL&FS match)")
    ilfs_like = {
        "st_debt_to_lt_assets_ratio": 1.9,
        "cfo_to_debt":                0.03,
        "debt_growth_3yr":            0.50,
        "current_ratio":              0.55,
        "revenue_growth":             0.02,
        "debt_to_equity":             4.5,
        "interest_coverage":          0.8,
        "promoter_pledge_pct":        0.30,
    }
    r2 = run_dna_analysis(ilfs_like, "Suspicious Infra Corp")
    print(f"   Closest: {r2['closest_archetype']} ({r2['max_similarity']:.4f})")
    print(f"   Risk: {r2['borrower_risk_profile']}")
    if r2["warning"]:
        print(f"\n{r2['warning']}")

    # ── Test 3: DHFL-like company ────────────────────────────────────────
    print("\n[3] DHFL-like borrower (expected: HIGH DHFL match)")
    dhfl_like = {
        "related_party_tx_to_rev":    0.30,
        "receivables_days":         170.0,
        "promoter_pledge_pct":        0.68,
        "gst_vs_bank_divergence":     0.38,
        "cfo_to_pat":                 0.10,
        "roe":                       -0.05,
    }
    r3 = run_dna_analysis(dhfl_like, "Shady Housing Finance")
    print(f"   Closest: {r3['closest_archetype']} ({r3['max_similarity']:.4f})")
    print(f"   Risk: {r3['borrower_risk_profile']}")

    # ── Test 4: Kingfisher-like company ──────────────────────────────────
    print("\n[4] Kingfisher-like borrower (expected: HIGH Kingfisher match)")
    king_like = {
        "revenue_growth":            -0.22,
        "debt_to_equity":            10.0,
        "interest_coverage":          0.35,
        "promoter_pledge_pct":        0.88,
        "free_cash_flow_margin":     -0.12,
        "current_ratio":              0.50,
    }
    r4 = run_dna_analysis(king_like, "Failing Airlines Ltd")
    print(f"   Closest: {r4['closest_archetype']} ({r4['max_similarity']:.4f})")
    print(f"   Risk: {r4['borrower_risk_profile']}")

    print("\n" + "=" * 60)
    print("✅ DNA matching test complete!")
    print("=" * 60)
