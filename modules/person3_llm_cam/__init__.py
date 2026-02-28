# Person 3 — LLM + CAM module init

from modules.person3_llm_cam.research_agent import run_research
from modules.person3_llm_cam.approval_agent import write_bull_case
from modules.person3_llm_cam.dissent_agent import write_bear_case, synthesize_cam_recommendation
from modules.person3_llm_cam.ceo_interview import (
    transcribe_interview,
    analyze_interview,
    get_management_quality_score,
    run_ceo_interview_analysis,
)
from modules.person3_llm_cam.cam_generator import generate_cam

__all__ = [
    "run_research",
    "write_bull_case",
    "write_bear_case",
    "synthesize_cam_recommendation",
    "transcribe_interview",
    "analyze_interview",
    "get_management_quality_score",
    "run_ceo_interview_analysis",
    "generate_cam",
]
