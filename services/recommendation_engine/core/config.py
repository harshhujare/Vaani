"""
Recommendation Engine — Configuration
=======================================
Central, validated configuration for the recommendation engine.
All tunable parameters live here. No magic numbers in business logic.
"""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class ScoringWeights(BaseModel):
    """Weights for each scoring component. Must sum to 100."""

    skill: float = 30.0
    interest: float = 20.0
    experience: float = 15.0
    education: float = 10.0
    asset: float = 10.0
    location: float = 5.0
    employment: float = 5.0
    batch: float = 5.0

    @model_validator(mode="after")
    def weights_must_sum_to_100(self) -> "ScoringWeights":
        total = (
            self.skill
            + self.interest
            + self.experience
            + self.education
            + self.asset
            + self.location
            + self.employment
            + self.batch
        )
        if abs(total - 100.0) > 0.01:
            msg = f"Scoring weights must sum to 100, got {total}"
            raise ValueError(msg)
        return self


class LocationConfig(BaseModel):
    """Parameters for Haversine distance scoring."""

    full_score_km: float = 5.0
    zero_score_km: float = 30.0


class RetrievalConfig(BaseModel):
    """Candidate retrieval pool sizes."""

    sql_top_k: int = 60
    vector_top_k: int = 40
    max_candidate_pool: int = 100


class DiversityConfig(BaseModel):
    """Pathway diversity constraints."""

    growth_nsqf_delta_min: int = 1
    growth_nsqf_delta_max: int = 2
    min_alternative_sector_diff: bool = True


class RecommendationConfig(BaseModel):
    """Master configuration object for the recommendation engine."""

    scoring_weights: ScoringWeights = ScoringWeights()
    location: LocationConfig = LocationConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    diversity: DiversityConfig = DiversityConfig()
    max_recommendations: int = 3
    enable_rpl: bool = True
    enable_vector_search: bool = False  # disabled until pgvector is available
    similarity_threshold: float = 0.5
    asset_zero_policy: str = "redistribute"  # "redistribute" | "neutral" | "penalize"
    asset_redistribution_targets: list[str] = ["skill", "interest"]


# ── Default singleton ─────────────────────────────────────────────
default_config = RecommendationConfig()
