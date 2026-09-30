"""
Recommendation Engine — Domain Models (Types)
===============================================
Strongly-typed Pydantic models for every concept in the engine.
These are the single source of truth for data shapes flowing
through the pipeline.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────

class PathwayType(str, Enum):
    BEST_MATCH = "BEST_MATCH"
    GROWTH_PATH = "GROWTH_PATH"
    ALTERNATIVE_OPTION = "ALTERNATIVE_OPTION"


class EmploymentPreference(str, Enum):
    SELF_EMPLOYMENT = "self_employment"
    WAGE_EMPLOYMENT = "wage_employment"
    BOTH = "both"
    UNKNOWN = "unknown"


class NormalizationSource(str, Enum):
    ALIAS_TABLE = "alias_table"
    EXACT_MATCH = "exact_match"
    UNRESOLVED = "unresolved"


# ── Skill Models ───────────────────────────────────────────────────

class Skill(BaseModel):
    """Canonical skill definition from the taxonomy."""
    skill_id: str
    name: str
    sector: str
    aliases: list[str] = Field(default_factory=list)


class NormalizedSkill(BaseModel):
    """Result of normalizing a raw skill string to a canonical ID."""
    raw_value: str
    canonical_id: str | None = None
    confidence: float = 0.0
    source: NormalizationSource = NormalizationSource.UNRESOLVED


# ── Beneficiary ────────────────────────────────────────────────────

class BeneficiaryProfile(BaseModel):
    """Input profile for a beneficiary requesting recommendations."""
    beneficiary_id: str
    name: str = ""
    language: str = "hi"
    district: str = ""
    state: str = ""
    latitude: float | None = None
    longitude: float | None = None
    location: Any | None = None
    education_level: str = "none"
    experience_years: float = 0.0
    raw_skills: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list, description="List of canonical skill IDs")
    interests: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    employment_preference: EmploymentPreference = EmploymentPreference.UNKNOWN

    def model_post_init(self, __context: Any) -> None:
        """Unpack nested location and raw_skills if present."""
        if self.location is not None:
            if hasattr(self.location, "district") and not self.district:
                self.district = self.location.district or ""
            elif isinstance(self.location, dict) and not self.district:
                self.district = self.location.get("district", "")

            if hasattr(self.location, "state") and not self.state:
                self.state = self.location.state or ""
            elif isinstance(self.location, dict) and not self.state:
                self.state = self.location.get("state", "")

            if hasattr(self.location, "latitude") and self.latitude is None:
                self.latitude = self.location.latitude
            elif isinstance(self.location, dict) and self.latitude is None:
                self.latitude = self.location.get("latitude")

            if hasattr(self.location, "longitude") and self.longitude is None:
                self.longitude = self.location.longitude
            elif isinstance(self.location, dict) and self.longitude is None:
                self.longitude = self.location.get("longitude")

        if self.raw_skills and not self.skills:
            self.skills = list(self.raw_skills)


# ── Raw Extraction (from LLM) ─────────────────────────────────────

class RawCandidateProfile(BaseModel):
    """Unstructured profile extracted from natural language by the LLM.
    May contain uncertain/raw values. Must NOT contain recommendations."""
    raw_skills: list[str] = Field(default_factory=list)
    raw_interests: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education_level: str | None = None
    assets: list[str] = Field(default_factory=list)
    employment_preference: str | None = None
    location: str | None = None
    raw_text: str = ""


# ── Qualification ─────────────────────────────────────────────────

class Qualification(BaseModel):
    """A training qualification/course from the NSQF catalogue."""
    qualification_id: str
    title: str
    sector: str
    occupation: str = ""
    description: str = ""
    required_skills: list[str] = Field(default_factory=list, description="Canonical skill IDs")
    optional_skills: list[str] = Field(default_factory=list)
    min_education: str = "none"
    min_experience_years: float = 0.0
    nsqf_level: int = 1
    employment_types: list[str] = Field(default_factory=list)
    required_assets: list[str] = Field(default_factory=list)
    preferred_assets: list[str] = Field(default_factory=list)
    supports_rpl: bool = False
    rpl_min_experience_years: float = 0.0
    is_active: bool = True
    embedding: list[float] | None = None


# ── Training Center ────────────────────────────────────────────────

class TrainingCenter(BaseModel):
    """An authorized training center."""
    center_id: str
    name: str
    latitude: float
    longitude: float
    address: str = ""
    district: str = ""
    state: str = ""
    authorized: bool = True
    supported_qualifications: list[str] = Field(default_factory=list)


# ── Batch ──────────────────────────────────────────────────────────

class Batch(BaseModel):
    """A training batch at a center for a specific qualification."""
    batch_id: str
    qualification_id: str
    center_id: str
    start_date: date
    end_date: date | None = None
    capacity: int = 30
    seats_available: int = 30
    status: str = "upcoming"  # upcoming | active | completed | cancelled


# ── Scoring & Eligibility Results ─────────────────────────────────

class EligibilityResult(BaseModel):
    """Binary eligibility determination for a single qualification."""
    qualification_id: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    failed_rules: list[str] = Field(default_factory=list)
    rpl_applied: bool = False


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of the 100-point score."""
    skill: float = 0.0
    interest: float = 0.0
    experience: float = 0.0
    education: float = 0.0
    asset: float = 0.0
    location: float = 0.0
    employment: float = 0.0
    batch: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.skill + self.interest + self.experience
            + self.education + self.asset + self.location
            + self.employment + self.batch
        )


class SkillGapResult(BaseModel):
    """Result of set subtraction between required and possessed skills."""
    matched_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)


class CenterMatch(BaseModel):
    """Nearest eligible training center for a qualification."""
    center_id: str
    name: str = ""
    distance_km: float
    seats_available: int | None = None
    next_batch_date: date | None = None
    batch_id: str | None = None


class AssetGapInfo(BaseModel):
    """Information about asset gaps and suggested support."""
    asset_gap: bool = False
    missing_assets: list[str] = Field(default_factory=list)
    suggested_support: str | None = None


class SchemeInfo(BaseModel):
    """Government welfare or skilling scheme applicable to the beneficiary."""
    scheme_code: str
    scheme_name: str
    ministry: str = ""
    benefit_summary: str
    financial_grant: str | None = None
    stipend_details: str | None = None
    loan_subsidy: str | None = None


# ── Recommendation ─────────────────────────────────────────────────

class Recommendation(BaseModel):
    """A single recommendation with full auditability."""
    pathway_type: PathwayType
    qualification_id: str
    qualification_title: str
    nsqf_level: int
    eligible: bool = True
    final_score: float
    score_breakdown: ScoreBreakdown
    eligibility_result: EligibilityResult
    matched_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    related_skills: list[str] = Field(
        default_factory=list,
        description="At least 3 core or adjacent skills taught in this pathway",
    )
    eligible_schemes: list[SchemeInfo] = Field(
        default_factory=list,
        description="At least 3 applicable government schemes (PM-AJAY GIA, PM Vishwakarma, etc.)",
    )
    training_center: CenterMatch | None = None
    asset_info: AssetGapInfo = Field(default_factory=AssetGapInfo)
    suggested_gia_intervention: str | None = None
    explanation: str = ""


class AuditMetadata(BaseModel):
    """Internal audit trail for reproducibility."""
    decision_id: str
    engine_version: str
    scoring_version: str
    candidate_count: int = 0
    eligible_count: int = 0
    selected_count: int = 0
    retrieval_method: str = "sql"
    processing_duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    config_snapshot: dict[str, Any] = Field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """Alias for processing_duration_ms."""
        return self.processing_duration_ms


class RecommendationResponse(BaseModel):
    """The validated final API response."""
    beneficiary_id: str
    engine_version: str
    recommendations: list[Recommendation] = Field(default_factory=list)
    audit: AuditMetadata | None = None
