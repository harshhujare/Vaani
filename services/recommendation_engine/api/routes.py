"""
Recommendation API — FastAPI Router
=====================================
REST endpoint for the recommendation engine.
POST /api/v1/recommendations
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.recommendation_engine.core.exceptions import (
    RecommendationEngineError,
    ValidationError,
)
from services.recommendation_engine.engine import RecommendationEngine
from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    EmploymentPreference,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["recommendations"])

# ── Singleton engine instance ─────────────────────────────────────
_engine: RecommendationEngine | None = None


def get_engine() -> RecommendationEngine:
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine


# ── Request/Response Schemas ──────────────────────────────────────


class LocationInput(BaseModel):
    """Optional nested location object matching API specification."""

    district: str = ""
    block: str = ""
    state: str = ""
    latitude: float | None = None
    longitude: float | None = None


class LivelihoodProfileInput(BaseModel):
    """Optional nested livelihood profile matching API specification."""

    current_occupation: str = ""
    experience_years: float = 0.0
    education_level: str = "none"
    employment_preference: str = "unknown"
    canonical_skill_ids: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    asset_ids: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    interest_tags: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """API request model for recommendations.

    Supports both flat fields and nested location/livelihood_profile objects
    to ensure full compatibility with the SIH specification and voice pipeline.
    """

    beneficiary_id: str = Field(..., description="Unique beneficiary identifier")
    name: str = ""
    language: str = "hi"

    # Flat fields
    district: str = ""
    state: str = ""
    latitude: float | None = None
    longitude: float | None = None
    education_level: str = "none"
    experience_years: float = 0.0
    skills: list[str] = Field(
        default_factory=list,
        description="Raw skill strings or canonical skill IDs",
    )
    interests: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    employment_preference: str = "unknown"

    # Nested specification objects
    location: LocationInput | None = None
    livelihood_profile: LivelihoodProfileInput | None = None


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: str
    details: dict | None = None


# ── Endpoints ─────────────────────────────────────────────────────


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get training recommendations for a beneficiary",
    description=(
        "Accepts a beneficiary profile and returns up to 3 diverse, "
        "deterministically-scored training recommendations with full "
        "auditability."
    ),
)
@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    include_in_schema=False,
)
async def get_recommendations(
    request: RecommendationRequest,
) -> RecommendationResponse:
    """Generate recommendations for a beneficiary."""
    try:
        # Merge nested structures if provided
        district = request.district
        state = request.state
        latitude = request.latitude
        longitude = request.longitude
        if request.location:
            if request.location.district:
                district = request.location.district
            if request.location.state:
                state = request.location.state
            if request.location.latitude is not None:
                latitude = request.location.latitude
            if request.location.longitude is not None:
                longitude = request.location.longitude

        education_level = request.education_level
        experience_years = request.experience_years
        employment_pref_raw = request.employment_preference
        skills = list(request.skills)
        interests = list(request.interests)
        assets = list(request.assets)

        if request.livelihood_profile:
            lp = request.livelihood_profile
            if lp.education_level and lp.education_level != "none":
                education_level = lp.education_level
            if lp.experience_years > 0:
                experience_years = lp.experience_years
            if lp.employment_preference and lp.employment_preference != "unknown":
                employment_pref_raw = lp.employment_preference
            skills.extend(lp.canonical_skill_ids)
            skills.extend(lp.skills)
            assets.extend(lp.asset_ids)
            assets.extend(lp.assets)
            interests.extend(lp.interest_tags)
            interests.extend(lp.interests)

        # Deduplicate while preserving order
        deduped_skills = list(dict.fromkeys(skills))
        deduped_interests = list(dict.fromkeys(interests))
        deduped_assets = list(dict.fromkeys(assets))

        # Convert preference to enum
        pref = employment_pref_raw.lower().strip()
        if pref not in EmploymentPreference.__members__.values():
            pref = "unknown"

        profile = BeneficiaryProfile(
            beneficiary_id=request.beneficiary_id,
            name=request.name,
            language=request.language,
            district=district,
            state=state,
            latitude=latitude,
            longitude=longitude,
            education_level=education_level,
            experience_years=experience_years,
            skills=deduped_skills,
            interests=deduped_interests,
            assets=deduped_assets,
            employment_preference=EmploymentPreference(pref),
        )

        engine = get_engine()
        response = await engine.recommend(profile)
        return response

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except RecommendationEngineError as e:
        logger.error(f"Engine error: {e.message}", extra={"details": e.details})
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.exception("Unexpected error in recommendation endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", summary="Health check")
async def health_check():
    """Simple health check for the recommendation engine."""
    return {"status": "healthy", "engine_version": "1.0.0"}
