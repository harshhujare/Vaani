"""
Recommendation Engine — Domain Models Package
=============================================
Export all domain types for convenient top-level access.
"""

from services.recommendation_engine.models.beneficiary import (
    LocationCoordinates,
)
from services.recommendation_engine.models.types import (
    AssetGapInfo,
    AuditMetadata,
    Batch,
    BeneficiaryProfile,
    CenterMatch,
    EligibilityResult,
    EmploymentPreference,
    NormalizationSource,
    NormalizedSkill,
    PathwayType,
    Qualification,
    RawCandidateProfile,
    Recommendation,
    RecommendationResponse,
    ScoreBreakdown,
    Skill,
    SkillGapResult,
    TrainingCenter,
)

__all__ = [
    "AssetGapInfo",
    "AuditMetadata",
    "Batch",
    "BeneficiaryProfile",
    "CenterMatch",
    "EligibilityResult",
    "EmploymentPreference",
    "LocationCoordinates",
    "NormalizationSource",
    "NormalizedSkill",
    "PathwayType",
    "Qualification",
    "RawCandidateProfile",
    "Recommendation",
    "RecommendationResponse",
    "ScoreBreakdown",
    "Skill",
    "SkillGapResult",
    "TrainingCenter",
]
