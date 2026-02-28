# Person 2 — Alternative Data module init
"""
Intelli-Credit Alternative Data Intelligence
=============================================
Modules:
  - network_graph : Promoter Network Graph & Contagion Risk Score
  - dna_matching  : Director Network Analysis & Pattern Matching
  - gst_intelligence : GST Filing Intelligence
  - satellite_module : Satellite / Geospatial Analysis
  - stress_test   : Macro Stress Testing Engine
"""

from .network_graph import (
    generate_synthetic_mca_data,
    build_promoter_network,
    compute_contagion_score,
    visualize_network,
    run_network_analysis,
)

from .stress_test import (
    generate_macro_scenarios,
    run_monte_carlo,
    get_named_scenarios,
    plot_stress_distribution,
    run_stress_test,
)

from .satellite_module import (
    fetch_satellite_image,
    compute_activity_score,
    get_factory_activity,
    plot_satellite_analysis,
)

from .gst_intelligence import (
    generate_gst_filings,
    analyze_gst_data,
)

from .dna_matching import (
    compute_dna_similarity,
    get_dna_warning,
    run_dna_analysis,
)

__all__ = [
    # network_graph
    "generate_synthetic_mca_data",
    "build_promoter_network",
    "compute_contagion_score",
    "visualize_network",
    "run_network_analysis",
    # stress_test
    "generate_macro_scenarios",
    "run_monte_carlo",
    "get_named_scenarios",
    "plot_stress_distribution",
    "run_stress_test",
    # satellite_module
    "fetch_satellite_image",
    "compute_activity_score",
    "get_factory_activity",
    "plot_satellite_analysis",
    # gst_intelligence
    "generate_gst_filings",
    "analyze_gst_data",
    # dna_matching
    "compute_dna_similarity",
    "get_dna_warning",
    "run_dna_analysis",
]
