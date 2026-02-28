"""
Intelli-Credit — Satellite Activity Scoring Module (Person 2)
==============================================================
Verifies that a factory is *actually running* — not just on paper —
by analysing Sentinel-2 (ESA) free satellite imagery.

Parts:
  A — Sentinel Hub API integration (fetch Sentinel-2 RGB + NIR bands)
  B — Activity Score computation (NDVI, brightness, temporal delta)
  C — Classification (ACTIVE / MODERATE / LOW / DORMANT)
  D — Fallback mode (synthetic proxy score when API unavailable)
  E — Revenue Consistency Check (e-way bill proxy vs satellite flag)

Author: Person 2
Module: modules/person2_alt_data/satellite_module.py
"""

import os
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

from loguru import logger

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("requests not installed — Sentinel Hub API unavailable")
    REQUESTS_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("matplotlib not installed — visualization unavailable")
    MATPLOTLIB_AVAILABLE = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

RANDOM_SEED = 42

# ── Sentinel Hub configuration ───────────────────────────────────────────
SENTINEL_CLIENT_ID     = os.getenv("SENTINEL_CLIENT_ID", "")
SENTINEL_CLIENT_SECRET = os.getenv("SENTINEL_CLIENT_SECRET", "")
SENTINEL_TOKEN_URL     = "https://services.sentinel-hub.com/oauth/token"
SENTINEL_PROCESS_URL   = "https://services.sentinel-hub.com/api/v1/process"

# ── Default test location: factory in Pune, MH ──────────────────────────
DEFAULT_LAT  = 18.52
DEFAULT_LON  = 73.85
DEFAULT_BBOX_DELTA = 0.005   # ~500 m bounding box around GPS point

# ── Image parameters ─────────────────────────────────────────────────────
IMAGE_WIDTH  = 256
IMAGE_HEIGHT = 256
CLOUD_COVER_MAX = 30   # percent

# ── Activity thresholds ──────────────────────────────────────────────────
ACTIVITY_THRESHOLDS = {
    "ACTIVE":   70,
    "MODERATE": 50,
    "LOW":      30,
    "DORMANT":   0,
}

# ── Demo / fallback synthetic data ───────────────────────────────────────
DEMO_COMPANIES: Dict[str, Dict[str, Any]] = {
    "Sunrise Textile Mills": {
        "lat": 18.52, "lon": 73.85,
        "sector": "Textiles",
        "base_activity": 78,
        "revenue_cr": 1250.0,
        "industry_avg_revenue_cr": 900.0,
    },
    "Suzlon Energy": {
        "lat": 18.52, "lon": 73.85,
        "sector": "Power",
        "base_activity": 65,
        "revenue_cr": 5200.0,
        "industry_avg_revenue_cr": 4000.0,
    },
    "Gujarat Spinners Ltd": {
        "lat": 23.03, "lon": 72.58,
        "sector": "Textiles",
        "base_activity": 28,
        "revenue_cr": 85.0,
        "industry_avg_revenue_cr": 900.0,
    },
    "TechFab Industries": {
        "lat": 19.08, "lon": 72.88,
        "sector": "Textiles",
        "base_activity": 72,
        "revenue_cr": 620.0,
        "industry_avg_revenue_cr": 900.0,
    },
}


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART A — SENTINEL HUB INTEGRATION                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _get_sentinel_token() -> Optional[str]:
    """
    Obtain an OAuth2 bearer token from Sentinel Hub.

    Requires SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET in .env.

    Returns:
        Bearer token string, or None if authentication fails
    """
    if not SENTINEL_CLIENT_ID or not SENTINEL_CLIENT_SECRET:
        logger.debug("Sentinel Hub credentials not configured in .env")
        return None

    if not REQUESTS_AVAILABLE:
        logger.debug("requests library not available")
        return None

    try:
        resp = requests.post(
            SENTINEL_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": SENTINEL_CLIENT_ID,
                "client_secret": SENTINEL_CLIENT_SECRET,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            logger.info("Sentinel Hub authentication successful")
            return token
        else:
            logger.warning(f"Sentinel Hub auth failed: HTTP {resp.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Sentinel Hub auth error: {e}")
        return None


def _build_evalscript() -> str:
    """
    Build a Sentinel Hub Evalscript that returns 4 bands:
    Red (B04), Green (B03), Blue (B02), NIR (B08).

    The evalscript runs server-side on Sentinel Hub and selects
    which bands to return in the response.
    """
    return """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04", "B08"],
                units: "DN"
            }],
            output: {
                bands: 4,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B04, sample.B03, sample.B02, sample.B08];
    }
    """


def _build_bbox(lat: float, lon: float, delta: float = DEFAULT_BBOX_DELTA) -> list:
    """Build a WGS84 bounding box [minLon, minLat, maxLon, maxLat]."""
    return [
        lon - delta,
        lat - delta,
        lon + delta,
        lat + delta,
    ]


def fetch_satellite_image(
    lat: float,
    lon: float,
    date: str,
    width: int = IMAGE_WIDTH,
    height: int = IMAGE_HEIGHT,
) -> Optional[np.ndarray]:
    """
    Fetch a Sentinel-2 satellite image for given GPS coordinates and date.

    Uses the Sentinel Hub Process API to retrieve a 4-band image:
      Band 0 = Red (B04)
      Band 1 = Green (B03)
      Band 2 = Blue (B02)
      Band 3 = NIR (B08)

    Args:
        lat:    Latitude (WGS84)
        lon:    Longitude (WGS84)
        date:   Date string in "YYYY-MM-DD" format
        width:  Output image width in pixels (default 256)
        height: Output image height in pixels (default 256)

    Returns:
        np.ndarray of shape (height, width, 4) with float32 values,
        or None if the API call fails.
    """
    logger.info(f"Fetching Sentinel-2 image: ({lat}, {lon}) on {date}")

    token = _get_sentinel_token()
    if token is None:
        logger.warning("Sentinel Hub token unavailable — cannot fetch imagery")
        return None

    # Build date range: target date ± 15 days (to find cloud-free image)
    try:
        target = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format: {date}. Expected YYYY-MM-DD")
        return None

    date_from = (target - timedelta(days=15)).strftime("%Y-%m-%dT00:00:00Z")
    date_to   = (target + timedelta(days=15)).strftime("%Y-%m-%dT23:59:59Z")

    bbox = _build_bbox(lat, lon)

    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {"from": date_from, "to": date_to},
                    "maxCloudCoverage": CLOUD_COVER_MAX,
                    "mosaickingOrder": "leastCC",
                },
            }],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/tiff"},
            }],
        },
        "evalscript": _build_evalscript(),
    }

    try:
        resp = requests.post(
            SENTINEL_PROCESS_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "image/tiff",
            },
            json=payload,
            timeout=60,
        )

        if resp.status_code == 200:
            # Parse TIFF bytes into numpy array
            try:
                from io import BytesIO
                try:
                    from PIL import Image
                    img = Image.open(BytesIO(resp.content))
                    arr = np.array(img, dtype=np.float32)
                    logger.info(f"Satellite image fetched: shape={arr.shape}")
                    return arr
                except ImportError:
                    # Without PIL, try raw parsing for 4-band float32
                    raw = np.frombuffer(resp.content, dtype=np.float32)
                    expected = height * width * 4
                    if raw.size >= expected:
                        arr = raw[:expected].reshape(height, width, 4)
                        logger.info(f"Satellite image fetched (raw): shape={arr.shape}")
                        return arr
                    else:
                        logger.warning(f"Image size mismatch: got {raw.size}, "
                                       f"expected {expected}")
                        return None
            except Exception as e:
                logger.warning(f"Image parsing error: {e}")
                return None
        else:
            logger.warning(f"Sentinel Hub API error: HTTP {resp.status_code}")
            logger.debug(f"Response: {resp.text[:500]}")
            return None

    except Exception as e:
        logger.warning(f"Sentinel Hub request failed: {e}")
        return None


def _generate_synthetic_image(
    lat: float,
    lon: float,
    activity_level: float = 0.7,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generate a synthetic 4-band satellite image for demo/fallback.

    Simulates a factory area with:
      - Low NDVI (industrial, not green)
      - Brightness proportional to activity level
      - Some noise for realism

    Args:
        lat:            Latitude (used for seed stability)
        lon:            Longitude (used for seed stability)
        activity_level: 0-1, how active the factory is
        seed:           Optional random seed

    Returns:
        np.ndarray shape (256, 256, 4): [Red, Green, Blue, NIR]
    """
    if seed is None:
        # Deterministic from coordinates
        coord_hash = hashlib.md5(f"{lat:.4f},{lon:.4f}".encode()).hexdigest()
        seed = int(coord_hash[:8], 16) % (2**31)

    rng = np.random.default_rng(seed)

    h, w = IMAGE_HEIGHT, IMAGE_WIDTH

    # Base reflectance for industrial area
    base_brightness = 0.15 + 0.35 * activity_level   # 0.15-0.50

    # Red band (B04): moderate for industrial
    red = rng.normal(base_brightness, 0.03, (h, w)).astype(np.float32)

    # Green band (B03): slightly lower
    green = rng.normal(base_brightness * 0.9, 0.03, (h, w)).astype(np.float32)

    # Blue band (B02): slightly lower still
    blue = rng.normal(base_brightness * 0.85, 0.03, (h, w)).astype(np.float32)

    # NIR band (B08): for industrial/active areas, NIR ≈ Red (low NDVI)
    # For vegetated/dormant areas, NIR > Red (higher NDVI)
    if activity_level > 0.5:
        # Active factory: NIR close to Red → low NDVI
        nir = rng.normal(base_brightness * 1.05, 0.04, (h, w)).astype(np.float32)
    else:
        # Dormant / overgrown: NIR higher than Red → higher NDVI
        nir = rng.normal(base_brightness * 1.6, 0.05, (h, w)).astype(np.float32)

    # Add some spatial structure (simulate buildings / patches)
    for _ in range(int(10 * activity_level) + 2):
        cx, cy = rng.integers(20, w - 20), rng.integers(20, h - 20)
        bw, bh = rng.integers(8, 25), rng.integers(8, 25)
        bright_patch = rng.uniform(0.3, 0.55) * activity_level
        red[cy:cy+bh, cx:cx+bw] = bright_patch
        green[cy:cy+bh, cx:cx+bw] = bright_patch * 0.85
        blue[cy:cy+bh, cx:cx+bw] = bright_patch * 0.80
        nir[cy:cy+bh, cx:cx+bw] = bright_patch * 1.05

    # Clip to valid range
    image = np.stack([red, green, blue, nir], axis=-1)
    image = np.clip(image, 0.0, 1.0)

    return image


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART B — ACTIVITY SCORE COMPUTATION                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _compute_ndvi(image: np.ndarray) -> np.ndarray:
    """
    Compute NDVI from a 4-band image.

    NDVI = (NIR - Red) / (NIR + Red)

    For industrial (active factory) areas, NDVI is low (close to 0).
    For vegetated (dormant/abandoned) areas, NDVI is high (0.3-0.8).

    Args:
        image: np.ndarray shape (H, W, 4) — bands [Red, Green, Blue, NIR]

    Returns:
        np.ndarray shape (H, W) with NDVI values in [-1, 1]
    """
    red = image[:, :, 0].astype(np.float64)
    nir = image[:, :, 3].astype(np.float64)

    denominator = nir + red
    # Avoid division by zero
    ndvi = np.where(
        denominator > 1e-6,
        (nir - red) / denominator,
        0.0,
    )
    return ndvi.astype(np.float32)


def _compute_brightness(image: np.ndarray) -> float:
    """
    Compute mean pixel brightness across RGB bands.

    Higher brightness generally indicates more built-up / active
    industrial surfaces (concrete, metal roofs, machinery).

    Args:
        image: np.ndarray shape (H, W, 4)

    Returns:
        float — mean brightness in [0, 1]
    """
    rgb = image[:, :, :3]
    return float(np.mean(rgb))


def compute_activity_score(
    image_current: np.ndarray,
    image_baseline: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Compute factory activity score from satellite imagery.

    Combines:
      1. NDVI analysis (low = active industrial, high = abandoned/vegetated)
      2. Mean brightness (higher = more built-up / active)
      3. Temporal brightness delta (current vs baseline from 6-12 months ago)

    Score formula:
      ndvi_score       = 100 * (1 − clamp(mean_ndvi, 0, 0.6) / 0.6)
      brightness_score = 100 * clamp(brightness / 0.45, 0, 1)
      delta_score      = 50 + 50 * clamp(brightness_delta / 0.10, -1, 1)
      activity_score   = 0.35 * ndvi_score + 0.40 * brightness_score + 0.25 * delta_score

    Args:
        image_current:  Current satellite image (H, W, 4)
        image_baseline: Baseline image from ~6-12 months ago (optional)

    Returns:
        Dict with detailed metrics:
        {
            "mean_ndvi": float,
            "ndvi_score": float (0-100),
            "mean_brightness": float,
            "brightness_score": float (0-100),
            "baseline_brightness": float | None,
            "brightness_delta": float | None,
            "delta_score": float (0-100),
            "activity_score": float (0-100),
            "classification": str,
        }
    """
    # ── NDVI ─────────────────────────────────────────────────────────────
    ndvi = _compute_ndvi(image_current)
    mean_ndvi = float(np.mean(ndvi))
    # Low NDVI (industrial) → high score; high NDVI (vegetation) → low score
    ndvi_score = 100.0 * (1.0 - min(max(mean_ndvi, 0.0), 0.6) / 0.6)

    # ── Brightness ───────────────────────────────────────────────────────
    brightness = _compute_brightness(image_current)
    brightness_score = 100.0 * min(max(brightness / 0.45, 0.0), 1.0)

    # ── Temporal delta ───────────────────────────────────────────────────
    if image_baseline is not None:
        baseline_brightness = _compute_brightness(image_baseline)
        brightness_delta = brightness - baseline_brightness
        # Positive delta = getting brighter (more active) → good
        # Negative delta = getting dimmer (less active) → bad
        clamped_delta = min(max(brightness_delta / 0.10, -1.0), 1.0)
        delta_score = 50.0 + 50.0 * clamped_delta
    else:
        baseline_brightness = None
        brightness_delta = None
        delta_score = 50.0   # Neutral if no baseline

    # ── Composite score ──────────────────────────────────────────────────
    activity_score = (
        0.35 * ndvi_score +
        0.40 * brightness_score +
        0.25 * delta_score
    )
    activity_score = round(min(max(activity_score, 0.0), 100.0), 2)

    # ── Classification ───────────────────────────────────────────────────
    classification = _classify_activity(activity_score)

    result = {
        "mean_ndvi":            round(mean_ndvi, 4),
        "ndvi_score":           round(ndvi_score, 2),
        "mean_brightness":      round(brightness, 4),
        "brightness_score":     round(brightness_score, 2),
        "baseline_brightness":  round(baseline_brightness, 4) if baseline_brightness is not None else None,
        "brightness_delta":     round(brightness_delta, 4) if brightness_delta is not None else None,
        "delta_score":          round(delta_score, 2),
        "activity_score":       activity_score,
        "classification":       classification,
    }

    logger.info(f"Activity score: {activity_score:.2f} → {classification}")
    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART C — CLASSIFICATION                                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _classify_activity(score: float) -> str:
    """
    Classify factory activity level from the composite score.

    Thresholds:
      > 70:   ACTIVE   — factory visibly operational
      50-70:  MODERATE — some activity but reduced
      30-50:  LOW      — minimal signs of operation
      < 30:   DORMANT  — appears non-operational

    Args:
        score: Activity score (0-100)

    Returns:
        Classification string
    """
    if score > 70:
        return "ACTIVE"
    elif score > 50:
        return "MODERATE"
    elif score > 30:
        return "LOW"
    else:
        return "DORMANT"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART D — FALLBACK (SYNTHETIC PROXY SCORE)                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _compute_fallback_activity(
    company_name: str,
    lat: float,
    lon: float,
) -> Dict[str, Any]:
    """
    Generate a synthetic activity score when Sentinel Hub API is unavailable.

    Uses pre-defined demo data or a deterministic hash of the company name
    and coordinates to produce a reproducible score.

    Args:
        company_name: Name of the company
        lat:          Factory latitude
        lon:          Factory longitude

    Returns:
        Same dict structure as compute_activity_score(), plus a
        "data_source" key set to "synthetic_fallback"
    """
    logger.warning("Satellite API unavailable — using proxy score")

    # Check demo companies first
    demo = DEMO_COMPANIES.get(company_name)
    if demo is not None:
        base = demo["base_activity"]
    else:
        # Deterministic hash-based score
        seed_str = f"{company_name}:{lat:.4f}:{lon:.4f}"
        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        base = 30 + (hash_val % 50)   # Range 30-79

    # Add small noise for realism
    rng = np.random.default_rng(RANDOM_SEED)
    noise = rng.normal(0, 3)
    score = round(min(max(base + noise, 0), 100), 2)

    classification = _classify_activity(score)

    # Simulate realistic sub-metrics
    if score > 60:
        mean_ndvi = round(rng.uniform(0.02, 0.12), 4)
        brightness = round(rng.uniform(0.30, 0.45), 4)
    elif score > 40:
        mean_ndvi = round(rng.uniform(0.10, 0.25), 4)
        brightness = round(rng.uniform(0.20, 0.32), 4)
    else:
        mean_ndvi = round(rng.uniform(0.25, 0.50), 4)
        brightness = round(rng.uniform(0.10, 0.22), 4)

    return {
        "mean_ndvi":            mean_ndvi,
        "ndvi_score":           round(100 * (1 - min(mean_ndvi, 0.6) / 0.6), 2),
        "mean_brightness":      brightness,
        "brightness_score":     round(100 * min(brightness / 0.45, 1.0), 2),
        "baseline_brightness":  round(brightness * rng.uniform(0.90, 1.10), 4),
        "brightness_delta":     round(rng.uniform(-0.05, 0.05), 4),
        "delta_score":          50.0,
        "activity_score":       score,
        "classification":       classification,
        "data_source":          "synthetic_fallback",
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PART E — REVENUE CONSISTENCY CHECK                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _check_revenue_consistency(
    activity_score: float,
    revenue_cr: Optional[float] = None,
    industry_avg_revenue_cr: Optional[float] = None,
    company_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Flag discrepancy between satellite activity and reported revenue.

    For manufacturers, e-way bill volume should be proportional to revenue.
    If a factory appears DORMANT on satellite but reports high revenue,
    that is a red flag worth investigating.

    Flag condition:
      satellite_vs_revenue_flag = 1  if  activity_score < 40  AND
                                          revenue > industry_avg_revenue

    Args:
        activity_score:           Satellite activity score (0-100)
        revenue_cr:               Company's reported revenue (₹ Cr)
        industry_avg_revenue_cr:  Industry average revenue (₹ Cr)
        company_name:             Company name (for demo lookup)

    Returns:
        Dict with consistency check results
    """
    # Try demo data if revenue not provided
    if revenue_cr is None and company_name and company_name in DEMO_COMPANIES:
        demo = DEMO_COMPANIES[company_name]
        revenue_cr = demo.get("revenue_cr")
        industry_avg_revenue_cr = demo.get("industry_avg_revenue_cr")

    if revenue_cr is None or industry_avg_revenue_cr is None:
        return {
            "satellite_vs_revenue_flag": 0,
            "flag_reason": "Revenue data not available for comparison",
            "revenue_cr": revenue_cr,
            "industry_avg_revenue_cr": industry_avg_revenue_cr,
            "revenue_ratio": None,
        }

    revenue_ratio = revenue_cr / max(industry_avg_revenue_cr, 1.0)

    # Flag: low activity but high revenue
    flag = 1 if (activity_score < 40 and revenue_cr > industry_avg_revenue_cr) else 0

    if flag:
        reason = (
            f"RED FLAG: Factory appears {'DORMANT' if activity_score < 30 else 'LOW activity'} "
            f"(score={activity_score:.1f}) but reports revenue ₹{revenue_cr:.0f} Cr "
            f"which exceeds industry avg ₹{industry_avg_revenue_cr:.0f} Cr "
            f"({revenue_ratio:.1f}x). Possible revenue inflation or "
            f"outsourced manufacturing."
        )
        logger.warning(reason)
    else:
        reason = "Activity and revenue are consistent"

    return {
        "satellite_vs_revenue_flag": flag,
        "flag_reason": reason,
        "revenue_cr": revenue_cr,
        "industry_avg_revenue_cr": industry_avg_revenue_cr,
        "revenue_ratio": round(revenue_ratio, 2),
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HIGH-LEVEL ENTRY POINT                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def get_factory_activity(
    company_name: str = "Sunrise Textile Mills",
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    revenue_cr: Optional[float] = None,
    industry_avg_revenue_cr: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Get complete factory activity analysis for a borrower company.

    Pipeline:
      1. Attempt to fetch Sentinel-2 imagery (current + baseline)
      2. If API unavailable → fall back to synthetic proxy score
      3. Compute activity score (NDVI + brightness + temporal delta)
      4. Classify activity level
      5. Run revenue consistency check

    Args:
        company_name:            Name of the company
        lat:                     Factory latitude (WGS84)
        lon:                     Factory longitude (WGS84)
        revenue_cr:              Reported annual revenue (₹ Cr), optional
        industry_avg_revenue_cr: Industry average revenue (₹ Cr), optional

    Returns:
        Comprehensive dict:
        {
            "company_name":              str,
            "location":                  {"lat": float, "lon": float},
            "data_source":               "sentinel_api" | "synthetic_fallback",
            "current_date":              str,
            "baseline_date":             str,
            # Activity metrics
            "mean_ndvi":                 float,
            "ndvi_score":                float,
            "mean_brightness":           float,
            "brightness_score":          float,
            "baseline_brightness":       float | None,
            "brightness_delta":          float | None,
            "delta_score":               float,
            "activity_score":            float (0-100),
            "classification":            str,
            # Revenue check
            "satellite_vs_revenue_flag": 0 | 1,
            "flag_reason":               str,
            "revenue_cr":                float | None,
            "industry_avg_revenue_cr":   float | None,
            "revenue_ratio":             float | None,
        }
    """
    logger.info(f"{'='*60}")
    logger.info(f"SATELLITE ACTIVITY ANALYSIS — {company_name}")
    logger.info(f"Location: ({lat}, {lon})")
    logger.info(f"{'='*60}")

    today = datetime.now()
    current_date = today.strftime("%Y-%m-%d")
    baseline_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")

    # ── Attempt Sentinel Hub API ─────────────────────────────────────────
    image_current = fetch_satellite_image(lat, lon, current_date)
    use_api = image_current is not None

    if use_api:
        image_baseline = fetch_satellite_image(lat, lon, baseline_date)
        activity_data = compute_activity_score(image_current, image_baseline)
        activity_data["data_source"] = "sentinel_api"
        logger.info("Using real Sentinel-2 imagery")
    else:
        # ── Fallback: synthetic proxy ────────────────────────────────────
        activity_data = _compute_fallback_activity(company_name, lat, lon)
        logger.info(f"Using synthetic fallback (score={activity_data['activity_score']:.2f})")

    # ── Revenue consistency check ────────────────────────────────────────
    revenue_check = _check_revenue_consistency(
        activity_score=activity_data["activity_score"],
        revenue_cr=revenue_cr,
        industry_avg_revenue_cr=industry_avg_revenue_cr,
        company_name=company_name,
    )

    # ── Merge results ────────────────────────────────────────────────────
    result = {
        "company_name":    company_name,
        "location":        {"lat": lat, "lon": lon},
        "current_date":    current_date,
        "baseline_date":   baseline_date,
    }
    result.update(activity_data)
    result.update(revenue_check)

    logger.info(f"{'='*60}")
    logger.info(f"SATELLITE ANALYSIS COMPLETE — {company_name}")
    logger.info(f"  Activity Score: {result['activity_score']:.2f} → {result['classification']}")
    logger.info(f"  Data Source:    {result['data_source']}")
    logger.info(f"  Revenue Flag:   {result['satellite_vs_revenue_flag']}")
    logger.info(f"{'='*60}")

    return result


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  VISUALIZATION HELPER                                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def plot_satellite_analysis(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a summary visualization of the satellite activity analysis.

    Creates a 2-panel figure:
      Left:  Gauge-style bar chart showing activity score + thresholds
      Right: Breakdown of sub-scores (NDVI, brightness, delta)

    Args:
        result:      Output dict from get_factory_activity()
        output_path: Path to save PNG. Auto-generated if None.

    Returns:
        Path to saved PNG, or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib required for visualization")
        return None

    company_name = result.get("company_name", "Unknown")
    score = result.get("activity_score", 0)
    classification = result.get("classification", "UNKNOWN")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor("#FAFAFA")

    # ── Left panel: Activity score gauge ─────────────────────────────────
    categories = ["DORMANT\n(0-30)", "LOW\n(30-50)", "MODERATE\n(50-70)", "ACTIVE\n(70-100)"]
    thresholds = [30, 50, 70, 100]
    colors = ["#E53935", "#FF8F00", "#FFB300", "#2E7D32"]

    # Background bars showing zones
    for i, (cat, thresh, color) in enumerate(zip(categories, thresholds, colors)):
        bottom = [0, 30, 50, 70][i]
        ax1.barh(0, thresh - bottom, left=bottom, height=0.5,
                 color=color, alpha=0.3, edgecolor="white")

    # Score marker
    score_color = (
        "#E53935" if score < 30 else
        "#FF8F00" if score < 50 else
        "#FFB300" if score < 70 else
        "#2E7D32"
    )
    ax1.barh(0, score, height=0.25, color=score_color, alpha=0.9,
             edgecolor="#424242", linewidth=0.5)
    ax1.axvline(score, color=score_color, linewidth=2, linestyle="--")
    ax1.text(score, 0.4, f" {score:.1f}", fontsize=14, fontweight="bold",
             color=score_color, va="bottom")
    ax1.text(score, -0.35, f" {classification}", fontsize=10,
             color=score_color, va="top", fontweight="bold")

    ax1.set_xlim(0, 100)
    ax1.set_ylim(-0.6, 0.8)
    ax1.set_yticks([])
    ax1.set_xlabel("Activity Score", fontsize=10)
    ax1.set_title(f"Factory Activity — {company_name}", fontsize=12, fontweight="bold")
    ax1.grid(axis="x", alpha=0.3)

    # Zone labels
    for i, (cat, thresh) in enumerate(zip(categories, thresholds)):
        mid = ([0, 30, 50, 70][i] + thresh) / 2
        ax1.text(mid, -0.55, cat, ha="center", va="top", fontsize=7, color="#757575")

    # ── Right panel: Sub-score breakdown ─────────────────────────────────
    sub_scores = {
        "NDVI Score": result.get("ndvi_score", 0),
        "Brightness Score": result.get("brightness_score", 0),
        "Delta Score": result.get("delta_score", 50),
    }
    sub_colors = ["#1565C0", "#FF8F00", "#2E7D32"]
    weights = [0.35, 0.40, 0.25]

    bars = ax2.barh(
        list(sub_scores.keys()), list(sub_scores.values()),
        color=sub_colors, alpha=0.8, edgecolor="white", height=0.5,
    )

    for bar, val, w in zip(bars, sub_scores.values(), weights):
        ax2.text(val + 1, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f}  (w={w})", va="center", fontsize=9)

    ax2.set_xlim(0, 110)
    ax2.set_xlabel("Score (0-100)", fontsize=10)
    ax2.set_title("Score Breakdown", fontsize=12, fontweight="bold")
    ax2.grid(axis="x", alpha=0.3)

    # Revenue flag annotation
    flag = result.get("satellite_vs_revenue_flag", 0)
    source = result.get("data_source", "unknown")
    fig.text(
        0.5, 0.01,
        f"Data Source: {source}  |  "
        f"Revenue Flag: {'🔴 FLAGGED' if flag else '🟢 OK'}  |  "
        f"Location: ({result.get('location', {}).get('lat', '?')}, "
        f"{result.get('location', {}).get('lon', '?')})",
        ha="center", fontsize=9, color="#757575",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    # ── Save ─────────────────────────────────────────────────────────────
    if output_path is None:
        safe_name = company_name.replace(" ", "_").replace("/", "_")
        output_dir = os.path.join("data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"satellite_{safe_name}.png")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="#FAFAFA")
    plt.close(fig)

    logger.info(f"Satellite analysis chart saved: {output_path}")
    return output_path


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — STANDALONE TEST                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SATELLITE ACTIVITY MODULE — Standalone Test")
    print("=" * 60)

    # ── Test 1: Active factory (Sunrise Textile Mills) ───────────────────
    print("\n[1] Testing: Sunrise Textile Mills (expected: ACTIVE)")
    result1 = get_factory_activity("Sunrise Textile Mills", 18.52, 73.85)
    print(f"   Activity Score: {result1['activity_score']:.2f}")
    print(f"   Classification: {result1['classification']}")
    print(f"   Data Source:    {result1['data_source']}")
    print(f"   NDVI:           {result1['mean_ndvi']:.4f}")
    print(f"   Brightness:     {result1['mean_brightness']:.4f}")
    print(f"   Revenue Flag:   {result1['satellite_vs_revenue_flag']}")

    # ── Test 2: Dormant factory (Gujarat Spinners) ───────────────────────
    print("\n[2] Testing: Gujarat Spinners Ltd (expected: DORMANT)")
    result2 = get_factory_activity("Gujarat Spinners Ltd", 23.03, 72.58)
    print(f"   Activity Score: {result2['activity_score']:.2f}")
    print(f"   Classification: {result2['classification']}")
    print(f"   Revenue Flag:   {result2['satellite_vs_revenue_flag']}")

    # ── Test 3: Compute from synthetic images directly ───────────────────
    print("\n[3] Testing: Direct image-based computation")
    img_active = _generate_synthetic_image(18.52, 73.85, activity_level=0.8)
    img_dormant = _generate_synthetic_image(18.52, 73.85, activity_level=0.2, seed=99)
    score_data = compute_activity_score(img_active, img_dormant)
    print(f"   Active image  → Score: {score_data['activity_score']:.2f} "
          f"({score_data['classification']})")

    score_data2 = compute_activity_score(img_dormant)
    print(f"   Dormant image → Score: {score_data2['activity_score']:.2f} "
          f"({score_data2['classification']})")

    # ── Test 4: Revenue consistency check ────────────────────────────────
    print("\n[4] Testing: Revenue consistency (flag scenario)")
    flag_result = _check_revenue_consistency(
        activity_score=25.0,
        revenue_cr=2000.0,
        industry_avg_revenue_cr=900.0,
    )
    print(f"   Flag: {flag_result['satellite_vs_revenue_flag']}")
    print(f"   Reason: {flag_result['flag_reason']}")

    # ── Test 5: Visualization ────────────────────────────────────────────
    print("\n[5] Generating visualization...")
    chart_path = plot_satellite_analysis(result1)
    if chart_path:
        print(f"   Chart saved: {chart_path}")

    print("\n" + "=" * 60)
    print("✅ Satellite module test complete!")
    print("=" * 60)
