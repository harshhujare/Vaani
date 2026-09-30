"""
Pydantic Models — Request / Response schemas for the recommendation API.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ══════════════════════════════════════════
# SCORE BREAKDOWN (for auditability)
# ══════════════════════════════════════════

class ScoreBreakdown(BaseModel):
    """Mathematical breakdown of how each score component was calculated."""
    skill_score: float = Field(..., description="Points from skill compatibility (max 30)")
    nsqf_score: float = Field(..., description="Points from NSQF level fit (max 25)")
    location_score: float = Field(..., description="Points from location proximity (max 20)")
    capacity_score: float = Field(..., description="Points from seat availability (max 15)")
    education_score: float = Field(..., description="Points from education match (max 10)")


# ══════════════════════════════════════════
# NEAREST CENTER
# ══════════════════════════════════════════

class NearestCenter(BaseModel):
    """Training center information."""
    training_center: str
    district: str
    state: str
    seats_available: int


# ══════════════════════════════════════════
# SINGLE RECOMMENDATION
# ══════════════════════════════════════════

class Recommendation(BaseModel):
    """A single training program recommendation with full score audit trail."""
    rank: int
    pathway_type: str = Field(..., description="BEST_MATCH | GROWTH_PATH | ALTERNATIVE")
    program_id: str
    program_name: str
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    nsqf_level: Optional[int] = None
    duration_days: Optional[int] = None
    provider: Optional[str] = None
    certification: Optional[str] = None
    match_score: float = Field(..., description="Total score out of 100")
    score_breakdown: ScoreBreakdown
    matched_skills: list[str] = Field(default_factory=list, description="Skills the beneficiary already has")
    skill_gaps: list[str] = Field(default_factory=list, description="Skills the beneficiary needs to learn")
    nearest_center: NearestCenter
    explanation_text: str = Field(..., description="Plain-language reason for this recommendation")


# ══════════════════════════════════════════
# BENEFICIARY PROFILE (internal)
# ══════════════════════════════════════════

class BeneficiaryProfile(BaseModel):
    """Internal representation of a beneficiary's profile for scoring."""
    id: str
    name: str
    phone: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    education_level: Optional[str] = None
    language: Optional[str] = None
    skills: list[dict] = Field(default_factory=list)


# ══════════════════════════════════════════
# API RESPONSE
# ══════════════════════════════════════════

class RecommendationResponse(BaseModel):
    """Full API response payload."""
    success: bool = True
    beneficiary_id: str
    beneficiary_name: str
    total_candidates_evaluated: int
    eligible_candidates: int
    recommendations: list[Recommendation]
    message: str = "Recommendations generated successfully"


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    data: None = None
