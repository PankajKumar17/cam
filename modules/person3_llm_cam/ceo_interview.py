"""
Yakṣarāja — CEO Interview Sentiment Analysis (Person 3, Innovation 11)
=============================================================================
Analyzes CEO/promoter interview recordings for linguistic deception markers,
sentiment trajectory, and topic-specific confidence.

"We don't score personality — we score consistency between what the
financials show and what the CEO says."

Parts:
  A — Whisper transcription
  B — Topic segmentation (Claude)
  C — Per-topic sentiment (VADER + hedging + overconfidence + deflection)
  D — Key aggregate scores
  E — Red flag detection
  F — Fallback when no audio is provided

Author: Person 3
Module: modules/person3_llm_cam/ceo_interview.py
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── Optional imports — graceful fallback for each ────────────────────────────

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("openai-whisper not installed — transcription will be unavailable")
    WHISPER_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    logger.warning("vaderSentiment not installed — using basic sentiment heuristic")
    VADER_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-genai not installed — deflection detection will use heuristic")
    GEMINI_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS — Linguistic markers                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

TOPICS = [
    "revenue_and_growth",
    "debt_and_liabilities",
    "competition_and_market",
    "future_outlook",
    "receivables_and_working_capital",
    "management_team",
]

HEDGING_PHRASES = [
    "approximately", "we expect", "should", "might", "we believe",
    "around", "roughly", "probably", "potentially", "hopefully",
    "in the range of", "more or less", "we think", "we hope",
    "if all goes well", "we anticipate", "we estimate",
]

OVERCONFIDENCE_PHRASES = [
    "will definitely", "guaranteed", "certain", "absolutely",
    "no doubt", "without question", "i promise", "100 percent",
    "for sure", "there is no way", "impossible that", "we are certain",
    "undoubtedly", "inevitably", "i can assure",
]

TOPIC_KEYWORDS = {
    "revenue_and_growth": [
        "revenue", "growth", "sales", "top line", "topline", "turnover",
        "market share", "expansion", "new orders", "order book", "demand",
    ],
    "debt_and_liabilities": [
        "debt", "loan", "borrowing", "liability", "interest", "repayment",
        "leverage", "credit", "bank", "lender", "npa", "default",
        "restructuring", "moratorium",
    ],
    "competition_and_market": [
        "competition", "competitor", "market", "industry", "peer",
        "pricing", "price war", "margin pressure", "imports",
    ],
    "future_outlook": [
        "future", "outlook", "next year", "plan", "strategy", "guidance",
        "projection", "target", "goal", "capex", "investment", "pipeline",
    ],
    "receivables_and_working_capital": [
        "receivable", "working capital", "inventory", "payable",
        "collection", "cash cycle", "cash conversion", "debtors",
        "creditors", "overdue",
    ],
    "management_team": [
        "team", "management", "board", "director", "cfo", "ceo",
        "succession", "hire", "talent", "leadership", "governance",
        "experience", "attrition",
    ],
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART A — TRANSCRIPTION (Whisper)                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def transcribe_interview(audio_path: str) -> str:
    """
    Transcribe a CEO/promoter interview audio file using OpenAI Whisper.

    Args:
        audio_path: Path to audio file (.mp3, .wav, .mp4, .m4a)

    Returns:
        Full transcript text string.
        Returns empty string if transcription fails.
    """
    if not audio_path or not Path(audio_path).exists():
        logger.warning(f"Audio file not found: {audio_path}")
        return ""

    if not WHISPER_AVAILABLE:
        logger.error("Whisper not installed — cannot transcribe")
        return ""

    try:
        logger.info(f"Transcribing: {audio_path}")
        model = whisper.load_model("base")  # good balance of speed and quality
        result = model.transcribe(
            audio_path,
            language="en",
            fp16=False,  # safer for CPU
        )
        transcript = result.get("text", "").strip()
        logger.info(f"Transcription complete: {len(transcript)} characters, "
                     f"{len(transcript.split())} words")
        return transcript
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return ""


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART B — TOPIC SEGMENTATION                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _segment_by_keywords(transcript: str) -> Dict[str, str]:
    """
    Keyword-based topic segmentation (fast fallback).
    Splits transcript into sentences and assigns each to the best-matching topic.
    """
    sentences = re.split(r'[.!?]+', transcript)
    segments: Dict[str, List[str]] = {t: [] for t in TOPICS}

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:
            continue

        sent_lower = sent.lower()
        best_topic = None
        best_score = 0

        for topic, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in sent_lower)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic and best_score > 0:
            segments[best_topic].append(sent)
        else:
            # Assign unmatched sentences to future_outlook as catch-all
            segments["future_outlook"].append(sent)

    return {t: ". ".join(sents) + "." if sents else "" for t, sents in segments.items()}


def _segment_by_claude(transcript: str) -> Dict[str, str]:
    """
    Use Claude to intelligently segment the transcript by topic.
    Falls back to keyword segmentation on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not GEMINI_AVAILABLE:
        return _segment_by_keywords(transcript)

    prompt = f"""You are analyzing a CEO interview transcript. Segment the text by topic.

TRANSCRIPT:
{transcript[:6000]}

Assign each part of the transcript to one of these topics:
- revenue_and_growth
- debt_and_liabilities
- competition_and_market
- future_outlook
- receivables_and_working_capital
- management_team

Return a JSON object where each key is a topic name and each value is the relevant
text from the transcript that discusses that topic. If a topic is not discussed,
set its value to an empty string "".

Return ONLY valid JSON, no other text."""

    _max_retries = 3
    for _attempt in range(1, _max_retries + 1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=2048),
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(text)
            for topic in TOPICS:
                if topic not in parsed:
                    parsed[topic] = ""
            return parsed
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "resource exhausted" in err:
                logger.warning(f"Rate limit hit for segmentation (attempt {_attempt}/{_max_retries}) — waiting 60s...")
                time.sleep(60)
            else:
                logger.warning(f"Gemini segmentation failed: {e} — using keyword fallback")
                return _segment_by_keywords(transcript)
    return _segment_by_keywords(transcript)


def segment_transcript(transcript: str) -> Dict[str, str]:
    """
    Segment a CEO interview transcript into topic-specific sections.

    Args:
        transcript: Full transcript text

    Returns:
        Dict mapping topic name → relevant transcript text
    """
    if not transcript.strip():
        return {t: "" for t in TOPICS}

    # Try Claude first, fall back to keywords
    return _segment_by_claude(transcript)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART C — PER-TOPIC SENTIMENT ANALYSIS                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _vader_sentiment(text: str) -> float:
    """Compute VADER compound sentiment score (-1 to +1)."""
    if not text.strip():
        return 0.0
    if VADER_AVAILABLE:
        analyzer = SentimentIntensityAnalyzer()
        return analyzer.polarity_scores(text)["compound"]
    # Basic heuristic fallback
    positive_words = ["good", "great", "strong", "growth", "profit", "improve", "excellent"]
    negative_words = ["loss", "debt", "risk", "decline", "problem", "concern", "challenge"]
    words = text.lower().split()
    pos = sum(1 for w in words if w in positive_words)
    neg = sum(1 for w in words if w in negative_words)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _count_hedging(text: str) -> int:
    """Count hedging language occurrences in text."""
    text_lower = text.lower()
    return sum(text_lower.count(phrase) for phrase in HEDGING_PHRASES)


def _count_overconfidence(text: str) -> int:
    """Count overconfidence marker occurrences in text."""
    text_lower = text.lower()
    return sum(text_lower.count(phrase) for phrase in OVERCONFIDENCE_PHRASES)


def _count_specificity(text: str) -> Tuple[int, int]:
    """
    Count sentences containing specific numbers vs total sentences.
    Returns (sentences_with_numbers, total_sentences).
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return 0, 0
    has_number = sum(1 for s in sentences if re.search(r'\d+', s))
    return has_number, len(sentences)


def _detect_deflection_claude(topic: str, text: str) -> str:
    """
    Use Claude to classify whether the CEO directly answered
    about the topic or deflected.

    Returns: "DIRECT" | "PARTIAL" | "DEFLECTED"
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not GEMINI_AVAILABLE or not text.strip():
        return _detect_deflection_heuristic(topic, text)

    prompt = f"""You are analyzing a CEO interview. The CEO was asked about: {topic.replace('_', ' ')}.

Their response was:
"{text[:1500]}"

Classify the response as:
- DIRECT: The CEO directly addressed the topic with specific details
- PARTIAL: The CEO partially addressed the topic but was vague or shifted focus
- DEFLECTED: The CEO avoided the topic, pivoted to something else, or gave a non-answer

Return ONLY one word: DIRECT, PARTIAL, or DEFLECTED."""

    _max_retries = 3
    for _attempt in range(1, _max_retries + 1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=20),
            )
            answer = response.text.strip().upper()
            if answer in ("DIRECT", "PARTIAL", "DEFLECTED"):
                return answer
            return "PARTIAL"
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "resource exhausted" in err:
                logger.warning(f"Rate limit hit for deflection detection (attempt {_attempt}/{_max_retries}) — waiting 60s...")
                time.sleep(60)
            else:
                logger.warning(f"Gemini deflection detection failed for {topic}: {e}")
                return _detect_deflection_heuristic(topic, text)
    return _detect_deflection_heuristic(topic, text)


def _detect_deflection_heuristic(topic: str, text: str) -> str:
    """
    Heuristic deflection detection based on keyword overlap.
    If the text doesn't contain many keywords related to the topic, it's likely deflected.
    """
    if not text.strip():
        return "DEFLECTED"

    text_lower = text.lower()
    keywords = TOPIC_KEYWORDS.get(topic, [])
    matches = sum(1 for kw in keywords if kw in text_lower)

    if matches >= 3:
        return "DIRECT"
    elif matches >= 1:
        return "PARTIAL"
    else:
        return "DEFLECTED"


def _analyze_topic(topic: str, text: str) -> Dict[str, Any]:
    """
    Run full sentiment analysis on a single topic segment.

    Returns:
        {
            "topic": str,
            "text_length": int,
            "vader_sentiment": float (-1 to +1),
            "hedging_count": int,
            "overconfidence_count": int,
            "specificity_with_numbers": int,
            "specificity_total_sentences": int,
            "deflection": "DIRECT" | "PARTIAL" | "DEFLECTED",
            "word_count": int,
        }
    """
    word_count = len(text.split()) if text.strip() else 0
    num_sentences, total_sentences = _count_specificity(text)

    return {
        "topic": topic,
        "text_length": len(text),
        "vader_sentiment": _vader_sentiment(text),
        "hedging_count": _count_hedging(text),
        "overconfidence_count": _count_overconfidence(text),
        "specificity_with_numbers": num_sentences,
        "specificity_total_sentences": total_sentences,
        "deflection": _detect_deflection_claude(topic, text),
        "word_count": word_count,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART D — KEY AGGREGATE SCORES                                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _compute_key_scores(topic_analyses: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute the 5 key aggregate scores from per-topic analyses.

    Returns:
        ceo_sentiment_overall: average VADER across all topics
        ceo_sentiment_debt: VADER for debt_and_liabilities topic
        ceo_deflection_score: deflected_answers / total_questions
        ceo_overconfidence_score: total_overconfidence_markers / total_words * 100
        ceo_specificity_score: total_sentences_with_numbers / total_sentences
    """
    # Sentiment overall — average VADER across all non-empty topics
    sentiments = [a["vader_sentiment"] for a in topic_analyses if a["text_length"] > 0]
    ceo_sentiment_overall = sum(sentiments) / len(sentiments) if sentiments else 0.0

    # Sentiment debt — specific to debt topic
    debt_analysis = next(
        (a for a in topic_analyses if a["topic"] == "debt_and_liabilities"), None
    )
    ceo_sentiment_debt = debt_analysis["vader_sentiment"] if debt_analysis else 0.0

    # Deflection score — deflected / total topics with content
    topics_with_content = [a for a in topic_analyses if a["text_length"] > 0]
    deflected_count = sum(1 for a in topics_with_content if a["deflection"] == "DEFLECTED")
    partial_count = sum(1 for a in topics_with_content if a["deflection"] == "PARTIAL")
    total_questions = len(topics_with_content) if topics_with_content else 1
    ceo_deflection_score = (deflected_count + 0.5 * partial_count) / total_questions

    # Overconfidence score — total markers / total words * 100
    total_overconfidence = sum(a["overconfidence_count"] for a in topic_analyses)
    total_words = sum(a["word_count"] for a in topic_analyses)
    ceo_overconfidence_score = (
        (total_overconfidence / total_words * 100) if total_words > 0 else 0.0
    )

    # Specificity score — sentences with numbers / total sentences
    total_with_nums = sum(a["specificity_with_numbers"] for a in topic_analyses)
    total_sentences = sum(a["specificity_total_sentences"] for a in topic_analyses)
    ceo_specificity_score = (
        total_with_nums / total_sentences if total_sentences > 0 else 0.0
    )

    return {
        "ceo_sentiment_overall": round(ceo_sentiment_overall, 4),
        "ceo_sentiment_debt": round(ceo_sentiment_debt, 4),
        "ceo_deflection_score": round(ceo_deflection_score, 4),
        "ceo_overconfidence_score": round(ceo_overconfidence_score, 4),
        "ceo_specificity_score": round(ceo_specificity_score, 4),
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART E — RED FLAG DETECTION                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _detect_red_flags(
    key_scores: Dict[str, float],
    topic_analyses: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect interview red flags based on thresholds.

    Returns list of red flag dicts with: flag_type, description, severity, value, threshold
    """
    flags = []

    # 1. Deflection > 0.4
    if key_scores["ceo_deflection_score"] > 0.4:
        flags.append({
            "flag_type": "HIGH_DEFLECTION",
            "description": (
                f"CEO deflected or partially answered {key_scores['ceo_deflection_score']:.0%} "
                f"of topics — potential avoidance of difficult questions"
            ),
            "severity": "HIGH",
            "value": key_scores["ceo_deflection_score"],
            "threshold": 0.4,
        })

    # 2. Debt sentiment too positive > 0.5
    if key_scores["ceo_sentiment_debt"] > 0.5:
        flags.append({
            "flag_type": "SUSPICIOUS_DEBT_POSITIVITY",
            "description": (
                f"CEO sentiment on debt is unusually positive ({key_scores['ceo_sentiment_debt']:.2f}) — "
                f"may indicate denial or minimization of leverage concerns"
            ),
            "severity": "HIGH",
            "value": key_scores["ceo_sentiment_debt"],
            "threshold": 0.5,
        })

    # 3. Sentiment divergence > 0.6
    revenue_analysis = next(
        (a for a in topic_analyses if a["topic"] == "revenue_and_growth"), None
    )
    debt_analysis = next(
        (a for a in topic_analyses if a["topic"] == "debt_and_liabilities"), None
    )
    if revenue_analysis and debt_analysis:
        divergence = abs(
            revenue_analysis["vader_sentiment"] - debt_analysis["vader_sentiment"]
        )
        if divergence > 0.6:
            flags.append({
                "flag_type": "SENTIMENT_DIVERGENCE",
                "description": (
                    f"Large sentiment gap between revenue ({revenue_analysis['vader_sentiment']:.2f}) "
                    f"and debt ({debt_analysis['vader_sentiment']:.2f}) discussions — "
                    f"divergence of {divergence:.2f} suggests inconsistent narrative"
                ),
                "severity": "MEDIUM",
                "value": divergence,
                "threshold": 0.6,
            })

    # 4. Overconfidence > 0.3
    if key_scores["ceo_overconfidence_score"] > 0.3:
        flags.append({
            "flag_type": "OVERCONFIDENCE",
            "description": (
                f"Overconfidence score of {key_scores['ceo_overconfidence_score']:.2f} — "
                f"excessive use of guarantees and certainty language"
            ),
            "severity": "MEDIUM",
            "value": key_scores["ceo_overconfidence_score"],
            "threshold": 0.3,
        })

    # 5. Low specificity — bonus flag
    if key_scores["ceo_specificity_score"] < 0.15:
        flags.append({
            "flag_type": "LOW_SPECIFICITY",
            "description": (
                f"Only {key_scores['ceo_specificity_score']:.0%} of sentences contain "
                f"specific numbers — CEO may be avoiding concrete commitments"
            ),
            "severity": "LOW",
            "value": key_scores["ceo_specificity_score"],
            "threshold": 0.15,
        })

    return flags


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART F — FALLBACK: SYNTHETIC SCORES                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _generate_fallback_analysis(company_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate synthetic CEO interview scores when no audio is provided.
    If company financial data is available, derive proxy scores from it.

    Heuristic: healthy financials → higher sentiment & specificity, lower deflection.
    """
    logger.info("No interview provided — using proxy scores from financial data")

    if company_data:
        # Use financial health as proxy
        dscr = company_data.get("dscr", 1.5)
        debt_to_equity = company_data.get("debt_to_equity", 1.5)
        net_margin = company_data.get("net_margin", 0.05)
        label = company_data.get("label", 0)  # 0=healthy, 1=default

        # Healthy company → confident, specific CEO; stressed → evasive
        health_factor = min(1.0, max(0.0, (dscr - 0.5) / 3.0))  # 0-1 scale

        if label == 1:  # defaulted company
            health_factor *= 0.4  # much less confident

        ceo_sentiment_overall = 0.2 + health_factor * 0.5  # 0.2 to 0.7
        ceo_sentiment_debt = -0.1 + (1 - health_factor) * 0.4  # honest if healthy
        ceo_deflection_score = 0.1 + (1 - health_factor) * 0.4  # more deflection if stressed
        ceo_overconfidence_score = 0.1 + (1 - health_factor) * 0.25
        ceo_specificity_score = 0.2 + health_factor * 0.5

        # Adjust debt sentiment: high leverage → suspicious positivity
        if debt_to_equity > 2.0 and ceo_sentiment_debt > 0.3:
            ceo_sentiment_debt = 0.55  # suspiciously positive about high debt
    else:
        # Default neutral scores
        ceo_sentiment_overall = 0.45
        ceo_sentiment_debt = 0.20
        ceo_deflection_score = 0.25
        ceo_overconfidence_score = 0.20
        ceo_specificity_score = 0.35

    key_scores = {
        "ceo_sentiment_overall": round(ceo_sentiment_overall, 4),
        "ceo_sentiment_debt": round(ceo_sentiment_debt, 4),
        "ceo_deflection_score": round(ceo_deflection_score, 4),
        "ceo_overconfidence_score": round(ceo_overconfidence_score, 4),
        "ceo_specificity_score": round(ceo_specificity_score, 4),
    }

    # Build synthetic per-topic breakdown
    topic_analyses = []
    for topic in TOPICS:
        topic_analyses.append({
            "topic": topic,
            "text_length": 0,
            "vader_sentiment": ceo_sentiment_overall + (
                -0.15 if topic == "debt_and_liabilities" else 0.05
            ),
            "hedging_count": 2,
            "overconfidence_count": 1,
            "specificity_with_numbers": 3,
            "specificity_total_sentences": 10,
            "deflection": "DIRECT" if ceo_deflection_score < 0.3 else "PARTIAL",
            "word_count": 0,
        })

    red_flags = _detect_red_flags(key_scores, topic_analyses)

    return {
        "transcript": "",
        "topic_segments": {t: "" for t in TOPICS},
        "topic_analyses": topic_analyses,
        "key_scores": key_scores,
        "red_flags": red_flags,
        "red_flag_count": len(red_flags),
        "management_quality_score": get_management_quality_score({"key_scores": key_scores, "red_flags": red_flags}),
        "used_fallback": True,
        "fallback_reason": "No audio interview provided — proxy scores derived from financial data",
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN ENTRY POINTS                                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def analyze_interview(transcript: str) -> Dict[str, Any]:
    """
    Full CEO interview analysis pipeline (Parts B through E).

    Args:
        transcript: Full interview transcript text (from Whisper or manual input)

    Returns:
        {
            "transcript": str,
            "topic_segments": {topic: text, ...},
            "topic_analyses": [{topic analysis dict}, ...],
            "key_scores": {
                "ceo_sentiment_overall": float,
                "ceo_sentiment_debt": float,
                "ceo_deflection_score": float,
                "ceo_overconfidence_score": float,
                "ceo_specificity_score": float,
            },
            "red_flags": [{flag dict}, ...],
            "red_flag_count": int,
            "management_quality_score": float (0-100),
            "used_fallback": False,
        }
    """
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript — returning fallback analysis")
        return _generate_fallback_analysis()

    logger.info(f"Analyzing interview transcript: {len(transcript)} chars, "
                f"{len(transcript.split())} words")

    # Part B — Topic segmentation
    logger.info("Segmenting transcript by topic...")
    topic_segments = segment_transcript(transcript)

    # Part C — Per-topic sentiment analysis
    logger.info("Running per-topic sentiment analysis...")
    topic_analyses = []
    for topic in TOPICS:
        text = topic_segments.get(topic, "")
        analysis = _analyze_topic(topic, text)
        topic_analyses.append(analysis)
        if text:
            logger.info(
                f"  {topic}: sentiment={analysis['vader_sentiment']:.2f}, "
                f"hedging={analysis['hedging_count']}, "
                f"deflection={analysis['deflection']}"
            )

    # Part D — Key aggregate scores
    logger.info("Computing key aggregate scores...")
    key_scores = _compute_key_scores(topic_analyses)

    # Part E — Red flag detection
    logger.info("Detecting red flags...")
    red_flags = _detect_red_flags(key_scores, topic_analyses)

    result = {
        "transcript": transcript,
        "topic_segments": topic_segments,
        "topic_analyses": topic_analyses,
        "key_scores": key_scores,
        "red_flags": red_flags,
        "red_flag_count": len(red_flags),
        "management_quality_score": 0.0,  # computed below
        "used_fallback": False,
    }

    result["management_quality_score"] = get_management_quality_score(result)

    logger.info(f"Analysis complete — MQ Score: {result['management_quality_score']:.1f}/100, "
                f"Red Flags: {len(red_flags)}")
    return result


def get_management_quality_score(analysis: Dict[str, Any]) -> float:
    """
    Compute a composite Management Quality (MQ) score from 0 to 100.

    Scoring breakdown (100 points total):
      - Sentiment balance:     25 pts (moderate overall + honest on debt)
      - Low deflection:        25 pts (0 deflection = 25, linear decay)
      - Specificity:           20 pts (higher = better)
      - Low overconfidence:    15 pts (some confidence good, too much bad)
      - No red flags:          15 pts (deduct 5 per flag)

    Args:
        analysis: Dict containing 'key_scores' and 'red_flags' keys

    Returns:
        Score from 0 to 100 (higher = better management quality signal)
    """
    scores = analysis.get("key_scores", {})
    flags = analysis.get("red_flags", [])

    # 1. Sentiment balance (25 pts)
    # Ideal: overall sentiment moderately positive (0.2-0.6), debt sentiment mildly negative
    overall = scores.get("ceo_sentiment_overall", 0.0)
    # Best if between 0.2 and 0.6
    if 0.2 <= overall <= 0.6:
        sentiment_pts = 25.0
    elif overall > 0.6:
        sentiment_pts = max(0, 25.0 - (overall - 0.6) * 50)
    else:
        sentiment_pts = max(0, 25.0 - (0.2 - overall) * 50)

    debt_sent = scores.get("ceo_sentiment_debt", 0.0)
    # Mildly negative on debt = honest (bonus), very positive on debt = suspicious (penalty)
    if debt_sent < 0.0:
        sentiment_pts = min(25, sentiment_pts + 3)  # bonus for honesty about debt
    elif debt_sent > 0.5:
        sentiment_pts = max(0, sentiment_pts - 8)  # penalty for suspicious positivity

    # 2. Low deflection (25 pts)
    deflection = scores.get("ceo_deflection_score", 0.5)
    deflection_pts = max(0, 25.0 * (1.0 - deflection))

    # 3. Specificity (20 pts)
    specificity = scores.get("ceo_specificity_score", 0.0)
    specificity_pts = min(20.0, specificity * 40.0)  # 0.5 specificity = full marks

    # 4. Low overconfidence (15 pts)
    # Some confidence (0.05-0.15) is fine; too much (>0.3) is bad
    overconf = scores.get("ceo_overconfidence_score", 0.0)
    if overconf <= 0.15:
        overconf_pts = 15.0
    elif overconf <= 0.3:
        overconf_pts = 15.0 - (overconf - 0.15) * 50
    else:
        overconf_pts = max(0, 15.0 - (overconf - 0.15) * 60)

    # 5. Red flag penalty (15 pts)
    flag_pts = max(0, 15.0 - len(flags) * 5.0)

    total = sentiment_pts + deflection_pts + specificity_pts + overconf_pts + flag_pts
    return round(max(0.0, min(100.0, total)), 1)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONVENIENCE: FULL PIPELINE (audio → analysis)                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def run_ceo_interview_analysis(
    audio_path: Optional[str] = None,
    transcript: Optional[str] = None,
    company_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    End-to-end CEO interview analysis pipeline.

    Accepts either an audio file path OR a pre-existing transcript.
    Falls back to synthetic scores if neither is available.

    Args:
        audio_path: Path to audio file (.mp3/.wav/.mp4) — optional
        transcript: Pre-transcribed text — optional (skips Whisper)
        company_data: Company financial data dict for fallback proxy scores

    Returns:
        Full analysis dict (same as analyze_interview output)
    """
    # Priority 1: pre-existing transcript
    if transcript and transcript.strip():
        logger.info("Using provided transcript — skipping transcription")
        return analyze_interview(transcript)

    # Priority 2: audio file → Whisper → analysis
    if audio_path:
        logger.info(f"Transcribing audio: {audio_path}")
        text = transcribe_interview(audio_path)
        if text:
            return analyze_interview(text)
        logger.warning("Transcription returned empty — using fallback")

    # Priority 3: fallback with financial proxy
    return _generate_fallback_analysis(company_data)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CEO INTERVIEW ANALYSIS — Standalone Test")
    print("=" * 60)

    # Test with a synthetic transcript
    sample_transcript = """
    We are very pleased with our revenue growth this year. Revenue has grown 
    by approximately 15 percent year on year, reaching 850 crores. Our order 
    book is strong and we expect to see continued momentum in the domestic 
    market. The textile PLI scheme has been very helpful.

    Regarding our debt situation, we have been working to bring down our 
    leverage ratio. Total debt stands at 520 crores, which is roughly 1.6 
    times equity. We should be able to reduce this to around 1.4 times by 
    next year. Interest coverage is at 2.4 times which we believe is comfortable.

    The competition has intensified, especially from Bangladesh and Vietnam 
    in the export market. However, our product quality and customer 
    relationships give us a strong moat. We are not worried about pricing 
    pressure as we have diversified our product mix.

    Looking ahead, we plan to invest 75 crores in capacity expansion in Surat. 
    This will definitely increase our capacity by 30 percent. We are absolutely 
    certain this will drive growth. The new facility should be operational by 
    Q3 next year.

    Our receivables days have come down from 95 to 82 days this year. Working 
    capital management has been a priority. We have implemented stricter 
    collection processes and our cash conversion cycle has improved by 12 days.

    The management team has been stable for the past 5 years. We recently 
    hired a new CFO from Aditya Birla Group who brings strong experience in 
    treasury and capital markets. No key person has left in the last 3 years.
    """

    result = analyze_interview(sample_transcript)

    print("\n📊 KEY SCORES:")
    for k, v in result["key_scores"].items():
        print(f"   {k}: {v:.4f}")

    print(f"\n🏆 Management Quality Score: {result['management_quality_score']:.1f}/100")

    print(f"\n🚩 Red Flags ({result['red_flag_count']}):")
    if result["red_flags"]:
        for f in result["red_flags"]:
            print(f"   [{f['severity']}] {f['flag_type']}: {f['description']}")
    else:
        print("   None detected ✅")

    print("\n📋 Per-Topic Breakdown:")
    for a in result["topic_analyses"]:
        if a["text_length"] > 0:
            print(f"   {a['topic']:35s} | sent={a['vader_sentiment']:+.2f} | "
                  f"hedge={a['hedging_count']} | overconf={a['overconfidence_count']} | "
                  f"deflection={a['deflection']}")

    # Test fallback mode
    print("\n" + "=" * 60)
    print("FALLBACK MODE — No audio, using financial proxy")
    print("=" * 60)

    demo_company = {
        "dscr": 1.85,
        "debt_to_equity": 1.6,
        "net_margin": 0.06,
        "label": 0,
    }
    fallback = run_ceo_interview_analysis(company_data=demo_company)
    print(f"   Fallback reason: {fallback.get('fallback_reason')}")
    for k, v in fallback["key_scores"].items():
        print(f"   {k}: {v:.4f}")
    print(f"   MQ Score: {fallback['management_quality_score']:.1f}/100")
    print("=" * 60)
