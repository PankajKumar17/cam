"""
Yakṣarāja — Person 2 Module Tests
========================================
Covers all Person 2 (Alternative Data) modules:
  1. Network Graph     — build_promoter_network(), compute_contagion_score()
  2. Stress Test       — run_monte_carlo(), get_named_scenarios()
  3. GST Intelligence  — analyze_gst_data(), divergence detection
  4. DNA Matching      — compute_dna_similarity(), get_dna_warning()
  5. Satellite Module  — get_factory_activity() fallback mode

All tests run OFFLINE — no API keys, no network calls, deterministic seeds.

Run:
    pytest tests/test_person2.py -v
    pytest tests/test_person2.py -v --tb=short
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# ── Ensure project root is on sys.path ───────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SHARED FIXTURES                                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

DEMO_CIN = "U17100MH2010PLC123456"   # Sunrise Textile Mills


@pytest.fixture
def demo_financials():
    """Default company financials for stress testing (Sunrise Textile Mills)."""
    return {
        "company_name":       "Sunrise Textile Mills",
        "company_cin":        DEMO_CIN,
        "sector":             "Textiles",
        "revenue":            1250.0,
        "ebitda":              187.5,
        "ebitda_margin":        0.15,
        "pat":                  75.0,
        "depreciation":         37.5,
        "total_debt":          520.0,
        "interest_expense":     52.0,
        "principal_repayment":  65.0,
        "current_dscr":          1.0,
        "loan_maturity_years":    3,
        "commodity_sensitivity":  0.40,
        "export_share":           0.30,
    }


@pytest.fixture
def tmp_output_dir():
    """Temporary directory for chart / file outputs."""
    d = tempfile.mkdtemp(prefix="test_p2_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  1. NETWORK GRAPH TESTS                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestNetworkGraph:
    """Tests for modules/person2_alt_data/network_graph.py."""

    def _clear_cache(self):
        """Reset module-level caches so each test starts fresh."""
        import modules.person2_alt_data.network_graph as ng
        ng._MCA_DATA_CACHE = None
        ng._GRAPH_CACHE = None

    # ── 1a. Synthetic MCA data generation ────────────────────────────────

    def test_generate_mca_data_shape(self):
        """MCA data should have expected columns and row count."""
        from modules.person2_alt_data.network_graph import generate_synthetic_mca_data
        self._clear_cache()

        df = generate_synthetic_mca_data(
            n_directors=50, n_companies=100, n_linkages=200, seed=42,
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 200
        expected_cols = {
            "din", "director_name", "company_cin", "company_name",
            "sector", "appointment_date", "cessation_date",
            "company_status", "company_debt_cr",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_generate_mca_data_includes_demo_companies(self):
        """Demo companies (Sunrise Textile Mills etc.) must appear."""
        from modules.person2_alt_data.network_graph import generate_synthetic_mca_data
        self._clear_cache()

        df = generate_synthetic_mca_data(seed=42)
        cins = set(df["company_cin"].unique())
        assert DEMO_CIN in cins, "Sunrise Textile Mills CIN missing"

    # ── 1b. Promoter network construction ────────────────────────────────

    def test_build_promoter_network_has_nodes_and_edges(self):
        """Network for Sunrise Textile should contain nodes and edges."""
        from modules.person2_alt_data.network_graph import build_promoter_network
        self._clear_cache()

        G = build_promoter_network(DEMO_CIN)

        assert G is not None
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0

    def test_build_promoter_network_contains_target(self):
        """Target company CIN must be a node in the subgraph."""
        from modules.person2_alt_data.network_graph import build_promoter_network
        self._clear_cache()

        G = build_promoter_network(DEMO_CIN)
        assert DEMO_CIN in G.nodes

    def test_build_promoter_network_unknown_cin(self):
        """Unknown CIN should return an empty graph, not crash."""
        from modules.person2_alt_data.network_graph import build_promoter_network
        self._clear_cache()

        G = build_promoter_network("NONEXISTENT_CIN_999")
        assert G.number_of_nodes() == 0

    # ── 1c. Contagion risk score ─────────────────────────────────────────

    def test_contagion_score_range_and_keys(self):
        """Contagion score should be 0-1 and dict should have all keys."""
        from modules.person2_alt_data.network_graph import compute_contagion_score
        self._clear_cache()

        result = compute_contagion_score(DEMO_CIN)

        assert isinstance(result, dict)
        required_keys = {
            "company_cin", "company_name",
            "promoter_total_companies", "promoter_npa_companies",
            "promoter_struck_off_companies", "promoter_directors",
            "network_npa_ratio", "network_clustering_coefficient",
            "size_factor", "contagion_risk_score", "risk_level",
            "related_companies",
        }
        assert required_keys.issubset(set(result.keys()))

        score = result["contagion_risk_score"]
        assert 0.0 <= score <= 1.0, f"Score {score} out of [0,1]"
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_contagion_score_npa_ratio_bounded(self):
        """NPA ratio must be between 0 and 1."""
        from modules.person2_alt_data.network_graph import compute_contagion_score
        self._clear_cache()

        result = compute_contagion_score(DEMO_CIN)
        assert 0.0 <= result["network_npa_ratio"] <= 1.0

    def test_contagion_fallback_for_unknown_company(self):
        """Unknown CIN should return zero-risk fallback."""
        from modules.person2_alt_data.network_graph import compute_contagion_score
        self._clear_cache()

        result = compute_contagion_score("NONEXISTENT_CIN_999")
        assert result["contagion_risk_score"] == 0.0
        assert result["risk_level"] == "LOW"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  2. STRESS TEST — MONTE CARLO                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestStressTestMonteCarlo:
    """Tests for modules/person2_alt_data/stress_test.py — Monte Carlo."""

    def test_monte_carlo_produces_distribution(self, demo_financials):
        """1000 simulations should produce P10 < P50 < P90."""
        from modules.person2_alt_data.stress_test import run_monte_carlo

        result = run_monte_carlo(demo_financials, n_simulations=1000, seed=42)

        assert isinstance(result, dict)
        assert "p10_dscr" in result
        assert "p50_dscr" in result
        assert "p90_dscr" in result
        assert "simulated_dscrs" in result

        # Correct percentile ordering
        assert result["p10_dscr"] <= result["p50_dscr"], \
            f"P10 ({result['p10_dscr']}) > P50 ({result['p50_dscr']})"
        assert result["p50_dscr"] <= result["p90_dscr"], \
            f"P50 ({result['p50_dscr']}) > P90 ({result['p90_dscr']})"

    def test_monte_carlo_default_probability_bounded(self, demo_financials):
        """Default probability should be between 0 and 1."""
        from modules.person2_alt_data.stress_test import run_monte_carlo

        result = run_monte_carlo(demo_financials, n_simulations=500, seed=42)
        prob = result["default_probability_3yr"]

        assert 0.0 <= prob <= 1.0, f"Default prob {prob} out of [0,1]"

    def test_monte_carlo_covenant_trigger_reasonable(self, demo_financials):
        """Covenant trigger (P20) should be in a reasonable DSCR range."""
        from modules.person2_alt_data.stress_test import run_monte_carlo

        result = run_monte_carlo(demo_financials, n_simulations=1000, seed=42)
        covenant = result["covenant_trigger_level"]

        # P20 DSCR should be between P10 and P50
        assert result["p10_dscr"] <= covenant <= result["p50_dscr"], \
            f"Covenant {covenant} not between P10 and P50"

    def test_monte_carlo_simulation_count(self, demo_financials):
        """Array of simulated DSCRs should have exactly n_simulations entries."""
        from modules.person2_alt_data.stress_test import run_monte_carlo

        n = 500
        result = run_monte_carlo(demo_financials, n_simulations=n, seed=42)
        assert len(result["simulated_dscrs"]) == n

    def test_monte_carlo_base_case_positive(self, demo_financials):
        """Base-case DSCR (zero shocks) should be a positive number."""
        from modules.person2_alt_data.stress_test import run_monte_carlo

        result = run_monte_carlo(demo_financials, n_simulations=100, seed=42)
        assert result["base_dscr"] > 0

    def test_monte_carlo_deterministic(self, demo_financials):
        """Same seed should produce identical results."""
        from modules.person2_alt_data.stress_test import run_monte_carlo

        r1 = run_monte_carlo(demo_financials, n_simulations=200, seed=99)
        r2 = run_monte_carlo(demo_financials, n_simulations=200, seed=99)

        assert r1["p50_dscr"] == r2["p50_dscr"]
        assert r1["default_probability_3yr"] == r2["default_probability_3yr"]


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  3. STRESS TEST — NAMED SCENARIOS                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestStressNamedScenarios:
    """Tests for named deterministic stress scenarios."""

    def test_named_scenarios_returns_four(self, demo_financials):
        """Should return exactly 4 named scenarios."""
        from modules.person2_alt_data.stress_test import get_named_scenarios

        result = get_named_scenarios(demo_financials)
        assert "scenarios" in result
        assert len(result["scenarios"]) == 4

    def test_rate_hike_lowers_dscr(self, demo_financials):
        """RBI Rate Hike +200bps should produce lower DSCR than base."""
        from modules.person2_alt_data.stress_test import (
            run_monte_carlo, get_named_scenarios,
        )

        mc = run_monte_carlo(demo_financials, n_simulations=100, seed=42)
        named = get_named_scenarios(demo_financials, mc)

        base_dscr = mc["base_dscr"]
        rate_hike = next(
            s for s in named["scenarios"]
            if "Rate Hike" in s["name"]
        )
        assert rate_hike["dscr"] < base_dscr, \
            f"Rate hike DSCR {rate_hike['dscr']} should be < base {base_dscr}"

    def test_revenue_decline_lowers_dscr(self, demo_financials):
        """Revenue Decline -20% should produce lower DSCR than base."""
        from modules.person2_alt_data.stress_test import (
            run_monte_carlo, get_named_scenarios,
        )

        mc = run_monte_carlo(demo_financials, n_simulations=100, seed=42)
        named = get_named_scenarios(demo_financials, mc)

        base_dscr = mc["base_dscr"]
        rev_decline = next(
            s for s in named["scenarios"]
            if "Revenue Decline" in s["name"]
        )
        assert rev_decline["dscr"] < base_dscr, \
            f"Revenue decline DSCR {rev_decline['dscr']} should be < base {base_dscr}"

    def test_combined_adverse_is_worst(self, demo_financials):
        """Combined Adverse should produce the lowest (or among lowest) DSCR."""
        from modules.person2_alt_data.stress_test import get_named_scenarios

        named = get_named_scenarios(demo_financials)
        combined = next(
            s for s in named["scenarios"]
            if "Combined" in s["name"]
        )
        # It should be the worst or very close
        worst_dscr = min(s["dscr"] for s in named["scenarios"])
        assert combined["dscr"] <= worst_dscr + 0.05, \
            "Combined Adverse should be near the worst scenario"

    def test_named_scenarios_have_verdict(self, demo_financials):
        """Each scenario should have a verdict of PASS, STRESS, or FAIL."""
        from modules.person2_alt_data.stress_test import get_named_scenarios

        named = get_named_scenarios(demo_financials)
        valid_verdicts = {"PASS", "STRESS", "FAIL"}
        for sc in named["scenarios"]:
            assert "verdict" in sc
            assert sc["verdict"] in valid_verdicts, \
                f"Invalid verdict: {sc['verdict']}"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  4. GST INTELLIGENCE                                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestGSTIntelligence:
    """Tests for modules/person2_alt_data/gst_intelligence.py."""

    def test_healthy_company_low_divergence(self):
        """Healthy company (Sunrise) should have low divergence and LOW risk."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        result = analyze_gst_data("Sunrise Textile Mills")

        assert isinstance(result, dict)
        assert result["fraud_risk_level"] == "LOW"
        assert result["gst_divergence_flag"] == 0
        assert abs(result["gst_vs_bank_divergence"]) < 0.20

    def test_distressed_company_high_divergence(self):
        """Distressed company (Gujarat Spinners) should have HIGH fraud risk."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        result = analyze_gst_data("Gujarat Spinners Ltd")

        assert result["gst_divergence_flag"] == 1
        assert result["fraud_risk_level"] in ("HIGH", "MEDIUM")
        # Bank revenue should exceed GST revenue significantly
        assert result["gst_vs_bank_divergence"] > 0.15

    def test_gst_divergence_flag_threshold(self):
        """Flag should trigger at >20% divergence and not below."""
        from modules.person2_alt_data.gst_intelligence import _compute_divergence

        # 45% inflation → flag
        div_high, flag_high = _compute_divergence(
            bank_revenue_cr=145.0, gst_revenue_cr=100.0,
        )
        assert flag_high == 1
        assert div_high > 0.40

        # 5% divergence → no flag
        div_low, flag_low = _compute_divergence(
            bank_revenue_cr=105.0, gst_revenue_cr=100.0,
        )
        assert flag_low == 0
        assert div_low < 0.10

    def test_fraud_risk_classification(self):
        """Classification thresholds: HIGH > 40%, MEDIUM 20-40%, LOW < 20%."""
        from modules.person2_alt_data.gst_intelligence import _classify_fraud_risk

        assert _classify_fraud_risk(0.50) == "HIGH"
        assert _classify_fraud_risk(0.42) == "HIGH"
        assert _classify_fraud_risk(0.30) == "MEDIUM"
        assert _classify_fraud_risk(0.21) == "MEDIUM"
        assert _classify_fraud_risk(0.15) == "LOW"
        assert _classify_fraud_risk(0.00) == "LOW"

    def test_gst_health_score_bounded(self):
        """GST health score should be between 0 and 100."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        r1 = analyze_gst_data("Sunrise Textile Mills")
        assert 0.0 <= r1["gst_health_score"] <= 100.0

        r2 = analyze_gst_data("Gujarat Spinners Ltd")
        assert 0.0 <= r2["gst_health_score"] <= 100.0

    def test_healthy_score_beats_distressed(self):
        """Healthy company should have higher GST health score than distressed."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        healthy = analyze_gst_data("Sunrise Textile Mills")
        distressed = analyze_gst_data("Gujarat Spinners Ltd")

        assert healthy["gst_health_score"] > distressed["gst_health_score"], \
            (f"Healthy ({healthy['gst_health_score']}) should beat "
             f"distressed ({distressed['gst_health_score']})")

    def test_filing_delay_metrics_present(self):
        """Analysis should include filing delay metrics."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        result = analyze_gst_data("Sunrise Textile Mills")
        assert "avg_filing_delay_days" in result
        assert "filing_delay_score" in result
        assert "filing_delay_risk" in result
        assert result["filing_delay_risk"] in ("LOW", "MEDIUM", "HIGH")

    def test_ewaybill_metrics_present(self):
        """Analysis should include e-way bill consistency metrics."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        result = analyze_gst_data("Sunrise Textile Mills")
        assert "ewaybill_consistency_ratio" in result
        assert "ewaybill_divergence_flag" in result
        assert result["ewaybill_divergence_flag"] in (0, 1)

    def test_unknown_company_defaults_to_healthy(self):
        """Unknown company should default to healthy profile (LOW risk)."""
        from modules.person2_alt_data.gst_intelligence import analyze_gst_data

        result = analyze_gst_data("Random Unknown Corp", bank_revenue_cr=500.0)
        assert result["fraud_risk_level"] == "LOW"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  5. DNA MATCHING                                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestDNAMatching:
    """Tests for modules/person2_alt_data/dna_matching.py."""

    def test_healthy_company_low_similarity(self):
        """Default (Sunrise) borrower should return valid similarity results."""
        from modules.person2_alt_data.dna_matching import compute_dna_similarity

        result = compute_dna_similarity()   # Uses default healthy features

        assert isinstance(result, dict)
        assert "similarities" in result
        assert "closest_archetype" in result
        assert "max_similarity" in result
        assert "borrower_risk_profile" in result

        # Verify all 6 archetypes are scored
        assert len(result["similarities"]) == 6
        # Max similarity must be in [0, 1]
        assert 0.0 <= result["max_similarity"] <= 1.0
        # Risk profile must be a recognised level
        assert result["borrower_risk_profile"] in (
            "LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"
        )

    def test_satyam_fingerprint_match(self):
        """Borrower with Satyam-like features should match Satyam archetype."""
        from modules.person2_alt_data.dna_matching import compute_dna_similarity

        satyam_like = {
            "beneish_dsri":           1.30,   # receivables manipulation
            "beneish_tata":           0.08,   # accruals manipulation
            "cfo_to_pat":             0.10,   # cash disconnected from profit
            "auditor_distress_score": 0.90,   # auditor discomfort
        }

        result = compute_dna_similarity(satyam_like)

        assert result["closest_archetype"] == "Satyam", \
            f"Expected Satyam, got {result['closest_archetype']}"
        assert result["similarities"]["Satyam"]["score"] > 0.70, \
            f"Satyam similarity {result['similarities']['Satyam']['score']} should be > 0.70"

    def test_ilfs_fingerprint_match(self):
        """Borrower with IL&FS-like features should match IL&FS archetype."""
        from modules.person2_alt_data.dna_matching import compute_dna_similarity

        # Include ALL 4 IL&FS fingerprint features so that IL&FS gets a
        # 4-feature comparison (strong signal) while other archetypes only
        # overlap on 1-2 features.
        ilfs_like = {
            "st_debt_to_lt_assets_ratio": 2.0,    # IL&FS-unique
            "cfo_to_debt":                0.03,    # IL&FS-unique
            "debt_growth_3yr":            0.50,    # IL&FS-unique
            "current_ratio":              0.55,    # shared with Jet Airways
        }

        result = compute_dna_similarity(ilfs_like)

        # IL&FS should be among the top matches with high similarity
        ilfs_score = result["similarities"]["IL&FS"]["score"]
        assert ilfs_score > 0.70, \
            f"IL&FS similarity {ilfs_score} should be > 0.70"
        assert result["similarities"]["IL&FS"]["matched_features"] == 4

    def test_kingfisher_fingerprint_match(self):
        """Borrower with Kingfisher-like features should score high on Kingfisher."""
        from modules.person2_alt_data.dna_matching import compute_dna_similarity

        # ALL 4 Kingfisher features — some overlap other archetypes on fewer features
        king_like = {
            "revenue_growth":        -0.23,   # shared with Jet Airways
            "debt_to_equity":        11.0,    # Kingfisher-unique
            "interest_coverage":      0.32,   # Kingfisher-unique
            "promoter_pledge_pct":    0.88,   # shared with DHFL/Videocon
        }

        result = compute_dna_similarity(king_like)

        # Kingfisher should have all 4 features matched with high similarity
        king_score = result["similarities"]["Kingfisher"]["score"]
        assert king_score > 0.70, \
            f"Kingfisher similarity {king_score} should be > 0.70"
        assert result["similarities"]["Kingfisher"]["matched_features"] == 4

    def test_dna_warning_generated_for_high_similarity(self):
        """Warning text should be generated when similarity > 0.75."""
        from modules.person2_alt_data.dna_matching import get_dna_warning

        # Simulate high similarity result
        sim_results = {
            "Satyam": {"score": 0.85, "matched_features": 4,
                       "features_used": ["beneish_dsri", "beneish_tata",
                                          "cfo_to_pat", "auditor_distress_score"]},
            "IL&FS":  {"score": 0.30, "matched_features": 2, "features_used": []},
        }

        warning = get_dna_warning(sim_results, threshold=0.75)

        assert warning is not None
        assert "SATYAM" in warning.upper()
        assert "COLLAPSE PATTERN" in warning.upper()

    def test_dna_warning_none_for_low_similarity(self):
        """No warning when all similarities are below threshold."""
        from modules.person2_alt_data.dna_matching import get_dna_warning

        sim_results = {
            "Satyam":    {"score": 0.30, "matched_features": 4, "features_used": []},
            "IL&FS":     {"score": 0.25, "matched_features": 2, "features_used": []},
            "Kingfisher": {"score": 0.20, "matched_features": 3, "features_used": []},
        }

        warning = get_dna_warning(sim_results, threshold=0.75)
        assert warning is None

    def test_all_six_archetypes_present(self):
        """Similarity result should include all 6 archetypes."""
        from modules.person2_alt_data.dna_matching import compute_dna_similarity

        result = compute_dna_similarity()
        archetypes = set(result["similarities"].keys())
        expected = {"IL&FS", "DHFL", "Jet Airways", "Videocon", "Satyam", "Kingfisher"}

        assert archetypes == expected, f"Missing archetypes: {expected - archetypes}"

    def test_similarity_scores_bounded(self):
        """All similarity scores should be between 0 and 1."""
        from modules.person2_alt_data.dna_matching import compute_dna_similarity

        result = compute_dna_similarity()
        for name, data in result["similarities"].items():
            score = data["score"]
            assert 0.0 <= score <= 1.0, \
                f"{name} score {score} out of [0,1]"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  6. SATELLITE MODULE — FALLBACK MODE                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestSatelliteModule:
    """Tests for modules/person2_alt_data/satellite_module.py."""

    def test_fallback_returns_valid_dict(self):
        """When API unavailable, fallback should return a valid result dict."""
        from modules.person2_alt_data.satellite_module import get_factory_activity

        # Ensure Sentinel credentials are empty → triggers fallback
        with patch.dict(os.environ, {
            "SENTINEL_CLIENT_ID": "",
            "SENTINEL_CLIENT_SECRET": "",
        }):
            result = get_factory_activity("Sunrise Textile Mills", 18.52, 73.85)

        assert isinstance(result, dict)
        assert "activity_score" in result
        assert "classification" in result
        assert "data_source" in result
        assert result["data_source"] == "synthetic_fallback"

    def test_fallback_classification_valid(self):
        """Classification should be one of the 4 valid categories."""
        from modules.person2_alt_data.satellite_module import get_factory_activity

        with patch.dict(os.environ, {
            "SENTINEL_CLIENT_ID": "",
            "SENTINEL_CLIENT_SECRET": "",
        }):
            result = get_factory_activity("Sunrise Textile Mills", 18.52, 73.85)

        valid = {"ACTIVE", "MODERATE", "LOW", "DORMANT"}
        assert result["classification"] in valid, \
            f"Invalid classification: {result['classification']}"

    def test_fallback_activity_score_bounded(self):
        """Activity score should be between 0 and 100."""
        from modules.person2_alt_data.satellite_module import get_factory_activity

        with patch.dict(os.environ, {
            "SENTINEL_CLIENT_ID": "",
            "SENTINEL_CLIENT_SECRET": "",
        }):
            result = get_factory_activity("TechFab Industries", 19.08, 72.88)

        assert 0.0 <= result["activity_score"] <= 100.0

    def test_fallback_has_ndvi_and_brightness(self):
        """Fallback result should include NDVI and brightness sub-metrics."""
        from modules.person2_alt_data.satellite_module import get_factory_activity

        with patch.dict(os.environ, {
            "SENTINEL_CLIENT_ID": "",
            "SENTINEL_CLIENT_SECRET": "",
        }):
            result = get_factory_activity("Sunrise Textile Mills", 18.52, 73.85)

        assert "mean_ndvi" in result
        assert "mean_brightness" in result
        assert "ndvi_score" in result
        assert "brightness_score" in result

    def test_dormant_factory_low_score(self):
        """Gujarat Spinners (demo: dormant) should score low in fallback."""
        from modules.person2_alt_data.satellite_module import get_factory_activity

        with patch.dict(os.environ, {
            "SENTINEL_CLIENT_ID": "",
            "SENTINEL_CLIENT_SECRET": "",
        }):
            result = get_factory_activity("Gujarat Spinners Ltd", 23.03, 72.58)

        assert result["activity_score"] < 50, \
            f"Dormant factory score {result['activity_score']} should be < 50"

    def test_revenue_consistency_flag(self):
        """Low activity + high revenue should trigger the flag."""
        from modules.person2_alt_data.satellite_module import _check_revenue_consistency

        result = _check_revenue_consistency(
            activity_score=25.0,
            revenue_cr=2000.0,
            industry_avg_revenue_cr=900.0,
        )
        assert result["satellite_vs_revenue_flag"] == 1
        assert "RED FLAG" in result["flag_reason"]

    def test_revenue_consistency_no_flag_when_consistent(self):
        """High activity + high revenue should NOT trigger flag."""
        from modules.person2_alt_data.satellite_module import _check_revenue_consistency

        result = _check_revenue_consistency(
            activity_score=75.0,
            revenue_cr=1200.0,
            industry_avg_revenue_cr=900.0,
        )
        assert result["satellite_vs_revenue_flag"] == 0

    # ── Synthetic image tests ────────────────────────────────────────────

    def test_synthetic_image_shape(self):
        """Synthetic image should be (256, 256, 4) float32."""
        from modules.person2_alt_data.satellite_module import _generate_synthetic_image

        img = _generate_synthetic_image(18.52, 73.85, activity_level=0.7)

        assert isinstance(img, np.ndarray)
        assert img.shape == (256, 256, 4)
        assert img.dtype == np.float32

    def test_compute_activity_from_images(self):
        """Activity score from synthetic images should have all keys."""
        from modules.person2_alt_data.satellite_module import (
            _generate_synthetic_image, compute_activity_score,
        )

        img_now = _generate_synthetic_image(18.52, 73.85, activity_level=0.8)
        img_old = _generate_synthetic_image(18.52, 73.85, activity_level=0.7, seed=99)

        result = compute_activity_score(img_now, img_old)

        assert "activity_score" in result
        assert "classification" in result
        assert "mean_ndvi" in result
        assert "brightness_delta" in result
        assert 0.0 <= result["activity_score"] <= 100.0

    def test_active_image_scores_higher_than_dormant(self):
        """Active factory image should score higher than dormant."""
        from modules.person2_alt_data.satellite_module import (
            _generate_synthetic_image, compute_activity_score,
        )

        img_active = _generate_synthetic_image(18.52, 73.85, activity_level=0.9)
        img_dormant = _generate_synthetic_image(18.52, 73.85, activity_level=0.1, seed=99)

        score_active = compute_activity_score(img_active)
        score_dormant = compute_activity_score(img_dormant)

        assert score_active["activity_score"] > score_dormant["activity_score"], \
            (f"Active ({score_active['activity_score']}) should beat "
             f"dormant ({score_dormant['activity_score']})")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  7. INTEGRATION — CROSS-MODULE CONSISTENCY                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TestCrossModuleIntegration:
    """Light integration tests verifying modules work together."""

    def test_macro_scenarios_shape(self):
        """Macro scenario generator should produce correct DataFrame shape."""
        from modules.person2_alt_data.stress_test import generate_macro_scenarios

        df = generate_macro_scenarios(n_simulations=100, seed=42)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        expected_cols = {
            "scenario_id", "repo_rate_shock", "inflation_shock",
            "revenue_shock", "commodity_price_shock",
            "customer_default_probability",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_shock_variables_within_bounds(self):
        """All shock variables should respect their clipping bounds."""
        from modules.person2_alt_data.stress_test import generate_macro_scenarios

        df = generate_macro_scenarios(n_simulations=1000, seed=42)

        assert df["repo_rate_shock"].min() >= -2.0
        assert df["repo_rate_shock"].max() <= 4.0
        assert df["inflation_shock"].min() >= -1.0
        assert df["inflation_shock"].max() <= 6.0
        assert df["revenue_shock"].min() >= -0.40
        assert df["revenue_shock"].max() <= 0.20
        assert df["commodity_price_shock"].min() >= -0.30
        assert df["commodity_price_shock"].max() <= 0.50
        assert df["customer_default_probability"].min() >= 0.0
        assert df["customer_default_probability"].max() <= 0.30

    def test_gst_filings_dataframe_valid(self):
        """GST filing generator should return valid DataFrame."""
        from modules.person2_alt_data.gst_intelligence import generate_gst_filings

        df = generate_gst_filings(
            company_name="Test Corp",
            bank_revenue_cr=500.0,
            health="good",
            filing_discipline="good",
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "gst_declared_rev_cr" in df.columns
        assert "delay_days" in df.columns
        assert "ewaybill_value_cr" in df.columns


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ENTRY POINT                                                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
