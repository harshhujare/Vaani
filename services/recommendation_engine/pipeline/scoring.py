"""
Pipeline Stage 4 — 100-Point Deterministic Scoring Engine
==========================================================
Pure mathematical scoring. No LLM, no black box.
Each component is independently testable and returns its own sub-score.

Weights (default, configurable):
  Skill:       30 pts
  Interest:    20 pts
  Experience:  15 pts
  Education:   10 pts
  Asset:       10 pts
  Location:     5 pts
  Employment:   5 pts
  Batch:        5 pts
  TOTAL:      100 pts
"""

from __future__ import annotations

from services.recommendation_engine.core.config import RecommendationConfig
from services.recommendation_engine.core.constants import EDUCATION_LEVELS
from services.recommendation_engine.models.types import (
    AssetGapInfo,
    Batch,
    BeneficiaryProfile,
    CenterMatch,
    Qualification,
    ScoreBreakdown,
)
from services.recommendation_engine.pipeline.geospatial import haversine_distance


# ── Individual Component Scorers (pure functions) ──────────────────


def score_skill_compatibility(
    beneficiary_skills: list[str],
    required_skills: list[str],
    optional_skills: list[str],
    max_points: float,
) -> tuple[float, list[str], list[str]]:
    """Calculate skill compatibility using weighted overlap.

    Required skills count fully; optional skills add bonus.
    Returns (score, matched_skills, missing_skills).
    """
    if not required_skills:
        # If the qualification requires no specific skills, full score
        return max_points, [], []

    ben_set = set(beneficiary_skills)
    req_set = set(required_skills)
    opt_set = set(optional_skills)

    matched_required = ben_set & req_set
    missing_required = req_set - ben_set
    matched_optional = ben_set & opt_set

    # Core score: proportion of required skills matched
    required_ratio = len(matched_required) / len(req_set) if req_set else 1.0

    # Optional bonus: up to 10% extra of max_points
    optional_bonus = 0.0
    if opt_set and matched_optional:
        optional_bonus = 0.1 * max_points * (len(matched_optional) / len(opt_set))

    score = required_ratio * max_points * 0.9 + optional_bonus
    score = min(score, max_points)

    matched = sorted(matched_required | matched_optional)
    missing = sorted(missing_required)

    return round(score, 2), matched, missing


def score_interest_alignment(
    beneficiary_interests: list[str],
    qualification_sector: str,
    qualification_occupation: str,
    qualification_employment_types: list[str],
    max_points: float,
) -> float:
    """Score interest alignment using keyword overlap.

    Simple deterministic matching: check if any beneficiary interest
    keywords appear in the qualification sector/occupation.
    """
    if not beneficiary_interests:
        # No interests stated = neutral score (50% of max)
        return round(max_points * 0.5, 2)

    # Build a set of qualification descriptors for matching
    qual_terms = {
        qualification_sector.lower(),
        qualification_occupation.lower(),
    }
    for et in qualification_employment_types:
        qual_terms.add(et.lower())

    # Check overlap
    interest_lower = {i.lower() for i in beneficiary_interests}

    matches = 0
    for interest in interest_lower:
        for term in qual_terms:
            if interest in term or term in interest:
                matches += 1
                break

    ratio = min(matches / len(interest_lower), 1.0)
    return round(ratio * max_points, 2)


def score_experience_relevance(
    beneficiary_experience_years: float,
    qualification_min_experience: float,
    max_points: float,
) -> float:
    """Score experience relevance.

    0 years relevant experience -> 0 points.
    Meets minimum -> 70% of max.
    Exceeds minimum by 2x or more -> 100% of max.
    """
    if beneficiary_experience_years <= 0:
        return 0.0

    if qualification_min_experience <= 0:
        # No minimum required; any experience is bonus
        # Scale: 1yr=30%, 3yr=60%, 5yr+=100%
        ratio = min(beneficiary_experience_years / 5.0, 1.0)
        return round(ratio * max_points, 2)

    ratio = beneficiary_experience_years / qualification_min_experience
    if ratio >= 2.0:
        return max_points
    elif ratio >= 1.0:
        # 70% to 100% linearly between 1x and 2x the minimum
        score = 0.7 + 0.3 * (ratio - 1.0)
        return round(score * max_points, 2)
    else:
        # Below minimum but still has some experience
        score = ratio * 0.7
        return round(score * max_points, 2)


def score_education_match(
    beneficiary_education: str,
    qualification_min_education: str,
    max_points: float,
) -> float:
    """Score education match.

    Meets requirement -> full score.
    Below requirement -> proportional score.
    """
    ben_rank = EDUCATION_LEVELS.get(beneficiary_education.lower().strip(), 0)
    req_rank = EDUCATION_LEVELS.get(qualification_min_education.lower().strip(), 0)

    if req_rank == 0:
        # No education requirement
        return max_points

    if ben_rank >= req_rank:
        return max_points

    # Partial credit
    ratio = ben_rank / req_rank if req_rank > 0 else 0.0
    return round(ratio * max_points, 2)


def score_asset_compatibility(
    beneficiary_assets: list[str],
    required_assets: list[str],
    preferred_assets: list[str],
    max_points: float,
    zero_asset_policy: str,
) -> tuple[float, AssetGapInfo]:
    """Score asset compatibility with fairness for zero-asset beneficiaries.

    Policies:
    - 'redistribute': Beneficiaries with no required assets get neutral score
      (points redistributed to other components by the caller).
    - 'neutral': Beneficiaries with no relevant asset requirements get full score.
    - 'penalize': Strict scoring based on possession.
    """
    has_no_assets = len(beneficiary_assets) == 0
    no_requirements = len(required_assets) == 0 and len(preferred_assets) == 0

    ben_set = set(beneficiary_assets)
    req_set = set(required_assets)
    pref_set = set(preferred_assets)

    missing_assets: list[str] = []
    suggested_support: str | None = None

    # Case 1: No asset requirements at all
    if no_requirements:
        return max_points, AssetGapInfo(asset_gap=False)

    # Case 2: Beneficiary has no assets
    if has_no_assets:
        missing_assets = sorted(req_set | pref_set)

        if required_assets:
            suggested_support = "TOOLKIT_GRANT"

        if zero_asset_policy == "redistribute":
            # Neutral score — caller will redistribute these points
            return round(max_points * 0.5, 2), AssetGapInfo(
                asset_gap=True,
                missing_assets=missing_assets,
                suggested_support=suggested_support,
            )
        elif zero_asset_policy == "neutral":
            return max_points, AssetGapInfo(
                asset_gap=True,
                missing_assets=missing_assets,
                suggested_support=suggested_support,
            )
        else:  # penalize
            return 0.0, AssetGapInfo(
                asset_gap=True,
                missing_assets=missing_assets,
                suggested_support=suggested_support,
            )

    # Case 3: Beneficiary has some assets — score based on coverage
    matched_required = ben_set & req_set
    matched_preferred = ben_set & pref_set
    missing_required = req_set - ben_set
    missing_preferred = pref_set - ben_set
    missing_assets = sorted(missing_required | missing_preferred)

    if missing_required:
        suggested_support = "TOOLKIT_GRANT"

    req_score = 0.0
    if req_set:
        req_score = (len(matched_required) / len(req_set)) * 0.8
    else:
        req_score = 0.8  # No required assets = full required portion

    pref_score = 0.0
    if pref_set:
        pref_score = (len(matched_preferred) / len(pref_set)) * 0.2
    else:
        pref_score = 0.2

    score = (req_score + pref_score) * max_points

    return round(score, 2), AssetGapInfo(
        asset_gap=len(missing_assets) > 0,
        missing_assets=missing_assets,
        suggested_support=suggested_support,
    )


def score_location_proximity(
    distance_km: float | None,
    max_points: float,
    full_score_km: float,
    zero_score_km: float,
) -> float:
    """Score location proximity using distance.

    < full_score_km         -> 100%
    full_score_km to zero_score_km -> linear decay
    >= zero_score_km        -> 0%
    """
    if distance_km is None:
        # Unknown location — neutral score
        return round(max_points * 0.5, 2)

    if distance_km <= full_score_km:
        return max_points

    if distance_km >= zero_score_km:
        return 0.0

    # Linear decay
    range_km = zero_score_km - full_score_km
    ratio = 1.0 - (distance_km - full_score_km) / range_km
    return round(ratio * max_points, 2)


def score_employment_preference(
    beneficiary_preference: str,
    qualification_employment_types: list[str],
    max_points: float,
) -> float:
    """Score employment preference alignment."""
    pref = beneficiary_preference.lower().strip()

    if pref in ("unknown", "both", ""):
        return round(max_points * 0.5, 2)

    qual_types = {t.lower() for t in qualification_employment_types}

    if not qual_types:
        return round(max_points * 0.5, 2)

    if pref in qual_types:
        return max_points

    return 0.0


def score_batch_availability(
    batch: Batch | None,
    max_points: float,
) -> float:
    """Score batch availability based on seat availability.

    No batch available -> 0 points.
    Seats available -> scaled by capacity ratio.
    """
    if batch is None:
        return 0.0

    if batch.seats_available <= 0:
        return 0.0

    # Score based on availability ratio
    ratio = batch.seats_available / batch.capacity if batch.capacity > 0 else 0.0
    # At least 50% score if any seats are available
    score = max(0.5, ratio) * max_points
    return round(min(score, max_points), 2)


# ── Master Scorer ──────────────────────────────────────────────────


class ScoringEngine:
    """Orchestrates all 8 scoring components into a single ScoreBreakdown."""

    def __init__(self, config: RecommendationConfig):
        self._config = config
        self._weights = config.scoring_weights

    def score(
        self,
        beneficiary: BeneficiaryProfile,
        qualification: Qualification,
        center_match: CenterMatch | None,
        batch: Batch | None,
    ) -> tuple[ScoreBreakdown, list[str], list[str], AssetGapInfo]:
        """Calculate the full 100-point score breakdown.

        Returns (breakdown, matched_skills, missing_skills, asset_info).
        """
        # 1. Skill Compatibility (30 pts)
        skill_score, matched_skills, missing_skills = score_skill_compatibility(
            beneficiary.skills,
            qualification.required_skills,
            qualification.optional_skills,
            self._weights.skill,
        )

        # 2. Interest Alignment (20 pts)
        interest_score = score_interest_alignment(
            beneficiary.interests,
            qualification.sector,
            qualification.occupation,
            qualification.employment_types,
            self._weights.interest,
        )

        # 3. Experience Relevance (15 pts)
        experience_score = score_experience_relevance(
            beneficiary.experience_years,
            qualification.min_experience_years,
            self._weights.experience,
        )

        # 4. Education Match (10 pts)
        education_score = score_education_match(
            beneficiary.education_level,
            qualification.min_education,
            self._weights.education,
        )

        # 5. Asset Compatibility (10 pts)
        asset_score, asset_info = score_asset_compatibility(
            beneficiary.assets,
            qualification.required_assets,
            qualification.preferred_assets,
            self._weights.asset,
            self._config.asset_zero_policy,
        )

        # 6. Location / Proximity (5 pts)
        distance_km = center_match.distance_km if center_match else None
        location_score = score_location_proximity(
            distance_km,
            self._weights.location,
            self._config.location.full_score_km,
            self._config.location.zero_score_km,
        )

        # 7. Employment Preference (5 pts)
        employment_score = score_employment_preference(
            beneficiary.employment_preference.value,
            qualification.employment_types,
            self._weights.employment,
        )

        # 8. Batch Availability (5 pts)
        batch_score = score_batch_availability(batch, self._weights.batch)

        breakdown = ScoreBreakdown(
            skill=skill_score,
            interest=interest_score,
            experience=experience_score,
            education=education_score,
            asset=asset_score,
            location=location_score,
            employment=employment_score,
            batch=batch_score,
        )

        return breakdown, matched_skills, missing_skills, asset_info
