"""
Recommendation Engine — Constants
==================================
Immutable domain constants used across the engine.
"""

# ── Engine Versioning ──────────────────────────────────────────────
ENGINE_VERSION = "1.0.0"
SCORING_VERSION = "1.0"

# ── Education Level Hierarchy ──────────────────────────────────────
# Numeric rank used for deterministic comparison.
# Higher number = higher education level.
EDUCATION_LEVELS: dict[str, int] = {
    "none": 0,
    "below_5th": 1,
    "5th": 2,
    "8th": 3,
    "10th": 4,
    "12th": 5,
    "iti": 6,
    "diploma": 7,
    "graduate": 8,
    "post_graduate": 9,
}

# ── Employment Preference Options ─────────────────────────────────
EMPLOYMENT_PREFERENCES = {
    "self_employment",
    "wage_employment",
    "both",
    "unknown",
}

from services.recommendation_engine.models.types import (
    EmploymentPreference,
    PathwayType,
)

# ── Pathway Types ─────────────────────────────────────────────────
PATHWAY_BEST_MATCH = "BEST_MATCH"
PATHWAY_GROWTH = "GROWTH_PATH"
PATHWAY_ALTERNATIVE = "ALTERNATIVE_OPTION"

# ── Geospatial ────────────────────────────────────────────────────
EARTH_RADIUS_KM = 6371.0

# ── Scoring ───────────────────────────────────────────────────────
PERFECT_SCORE = 100.0
MAX_RECOMMENDATIONS = 3
