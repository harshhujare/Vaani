"""
Tests — 100-Point Scoring Engine
==================================
Tests exact mathematical outputs for each scoring component.
Verifies total weight = 100.
Tests zero, partial, and maximum scores.
"""

import pytest
from datetime import date

from services.recommendation_engine.core.config import (
    RecommendationConfig,
    ScoringWeights,
)
from services.recommendation_engine.models.types import (
    Batch,
    BeneficiaryProfile,
    CenterMatch,
    EmploymentPreference,
    Qualification,
)
from services.recommendation_engine.pipeline.scoring import (
    ScoringEngine,
    score_skill_compatibility,
    score_interest_alignment,
    score_experience_relevance,
    score_education_match,
    score_asset_compatibility,
    score_location_proximity,
    score_employment_preference,
    score_batch_availability,
)


class TestScoringWeightsValidation:
    """Verify scoring weight constraints."""

    def test_default_weights_sum_to_100(self):
        weights = ScoringWeights()
        total = (
            weights.skill + weights.interest + weights.experience
            + weights.education + weights.asset + weights.location
            + weights.employment + weights.batch
        )
        assert total == 100.0

    def test_invalid_weights_rejected(self):
        with pytest.raises(ValueError, match="must sum to 100"):
            ScoringWeights(skill=50, interest=50)  # all others default


class TestSkillCompatibility:

    def test_full_match(self):
        score, matched, missing = score_skill_compatibility(
            ["SK_A", "SK_B"], ["SK_A", "SK_B"], [], 30.0
        )
        assert score == 27.0  # 100% * 30 * 0.9 = 27
        assert matched == ["SK_A", "SK_B"]
        assert missing == []

    def test_partial_match(self):
        score, matched, missing = score_skill_compatibility(
            ["SK_A"], ["SK_A", "SK_B"], [], 30.0
        )
        assert matched == ["SK_A"]
        assert missing == ["SK_B"]
        assert 0 < score < 27.0

    def test_no_match(self):
        score, matched, missing = score_skill_compatibility(
            ["SK_X"], ["SK_A", "SK_B"], [], 30.0
        )
        assert score == 0.0
        assert matched == []
        assert missing == ["SK_A", "SK_B"]

    def test_no_required_skills(self):
        score, matched, missing = score_skill_compatibility(
            ["SK_A"], [], [], 30.0
        )
        assert score == 30.0
        assert matched == []
        assert missing == []

    def test_optional_skills_bonus(self):
        # Full required + some optional -> above 90% base
        score_without_opt, _, _ = score_skill_compatibility(
            ["SK_A"], ["SK_A"], [], 30.0
        )
        score_with_opt, _, _ = score_skill_compatibility(
            ["SK_A", "SK_OPT"], ["SK_A"], ["SK_OPT"], 30.0
        )
        assert score_with_opt > score_without_opt


class TestInterestAlignment:

    def test_matching_interest(self):
        score = score_interest_alignment(
            ["tailoring"], "Apparel", "Tailor", ["self_employment"], 20.0
        )
        assert score > 0

    def test_no_interests_neutral(self):
        score = score_interest_alignment(
            [], "Apparel", "Tailor", [], 20.0
        )
        assert score == 10.0  # 50% of max

    def test_no_match(self):
        score = score_interest_alignment(
            ["quantum_physics"], "Apparel", "Tailor", [], 20.0
        )
        assert score == 0.0


class TestExperienceRelevance:

    def test_zero_experience(self):
        score = score_experience_relevance(0, 2, 15.0)
        assert score == 0.0

    def test_meets_minimum(self):
        score = score_experience_relevance(2, 2, 15.0)
        assert score == 10.5  # 70% of max

    def test_exceeds_minimum(self):
        score = score_experience_relevance(6, 2, 15.0)
        assert score == 15.0  # >= 2x minimum = max

    def test_below_minimum(self):
        score = score_experience_relevance(1, 2, 15.0)
        assert 0 < score < 10.5

    def test_no_minimum_requirement(self):
        score = score_experience_relevance(3, 0, 15.0)
        assert score > 0  # Any experience counts


class TestEducationMatch:

    def test_meets_requirement(self):
        score = score_education_match("10th", "8th", 10.0)
        assert score == 10.0

    def test_below_requirement(self):
        score = score_education_match("5th", "10th", 10.0)
        assert 0 < score < 10.0

    def test_no_requirement(self):
        score = score_education_match("5th", "none", 10.0)
        assert score == 10.0


class TestAssetCompatibility:

    def test_no_asset_requirements(self):
        score, info = score_asset_compatibility([], [], [], 10.0, "redistribute")
        assert score == 10.0
        assert info.asset_gap is False

    def test_zero_assets_redistribute_policy(self):
        score, info = score_asset_compatibility(
            [], ["AST_TOOL"], [], 10.0, "redistribute"
        )
        assert score == 5.0  # 50% of max under redistribute
        assert info.asset_gap is True
        assert info.suggested_support == "TOOLKIT_GRANT"

    def test_zero_assets_neutral_policy(self):
        score, info = score_asset_compatibility(
            [], ["AST_TOOL"], [], 10.0, "neutral"
        )
        assert score == 10.0
        assert info.asset_gap is True

    def test_zero_assets_penalize_policy(self):
        score, info = score_asset_compatibility(
            [], ["AST_TOOL"], [], 10.0, "penalize"
        )
        assert score == 0.0
        assert info.asset_gap is True

    def test_has_required_assets(self):
        score, info = score_asset_compatibility(
            ["AST_TOOL"], ["AST_TOOL"], [], 10.0, "redistribute"
        )
        assert score == 10.0
        assert info.asset_gap is False


class TestLocationProximity:

    def test_within_full_score_range(self):
        score = score_location_proximity(3.0, 5.0, 5.0, 30.0)
        assert score == 5.0

    def test_beyond_zero_range(self):
        score = score_location_proximity(35.0, 5.0, 5.0, 30.0)
        assert score == 0.0

    def test_linear_decay_midpoint(self):
        # Midpoint between 5 and 30 = 17.5 -> 50% decay
        score = score_location_proximity(17.5, 5.0, 5.0, 30.0)
        assert abs(score - 2.5) < 0.1

    def test_unknown_location_neutral(self):
        score = score_location_proximity(None, 5.0, 5.0, 30.0)
        assert score == 2.5  # 50% of max

    def test_exact_boundary_5km(self):
        score = score_location_proximity(5.0, 5.0, 5.0, 30.0)
        assert score == 5.0

    def test_exact_boundary_30km(self):
        score = score_location_proximity(30.0, 5.0, 5.0, 30.0)
        assert score == 0.0


class TestEmploymentPreference:

    def test_matching_preference(self):
        score = score_employment_preference(
            "self_employment", ["self_employment"], 5.0
        )
        assert score == 5.0

    def test_mismatched_preference(self):
        score = score_employment_preference(
            "self_employment", ["wage_employment"], 5.0
        )
        assert score == 0.0

    def test_unknown_preference_neutral(self):
        score = score_employment_preference(
            "unknown", ["self_employment"], 5.0
        )
        assert score == 2.5


class TestBatchAvailability:

    def test_no_batch(self):
        score = score_batch_availability(None, 5.0)
        assert score == 0.0

    def test_full_batch_no_seats(self):
        batch = Batch(
            batch_id="B1", qualification_id="Q1", center_id="C1",
            start_date=date(2026, 10, 1), capacity=30, seats_available=0,
        )
        score = score_batch_availability(batch, 5.0)
        assert score == 0.0

    def test_available_seats(self):
        batch = Batch(
            batch_id="B1", qualification_id="Q1", center_id="C1",
            start_date=date(2026, 10, 1), capacity=30, seats_available=15,
        )
        score = score_batch_availability(batch, 5.0)
        assert score > 0

    def test_many_seats_full_score(self):
        batch = Batch(
            batch_id="B1", qualification_id="Q1", center_id="C1",
            start_date=date(2026, 10, 1), capacity=30, seats_available=30,
        )
        score = score_batch_availability(batch, 5.0)
        assert score == 5.0


class TestScoringEngineIntegration:
    """Test the full scoring engine produces valid breakdowns."""

    def test_full_score_within_bounds(self):
        config = RecommendationConfig()
        scorer = ScoringEngine(config)

        beneficiary = BeneficiaryProfile(
            beneficiary_id="BEN1",
            education_level="10th",
            experience_years=5,
            skills=["SK_STITCHING"],
            interests=["tailoring"],
            assets=["AST_SEW_BASIC"],
            employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
            latitude=16.85,
            longitude=74.58,
        )

        qualification = Qualification(
            qualification_id="Q_APPAR_03",
            title="Basic Tailoring",
            sector="Apparel",
            occupation="Tailor",
            required_skills=["SK_STITCHING"],
            min_education="5th",
            nsqf_level=3,
            employment_types=["self_employment"],
        )

        center = CenterMatch(
            center_id="TC_SANGLI_01",
            name="Test Center",
            distance_km=4.0,
        )

        batch = Batch(
            batch_id="B1", qualification_id="Q_APPAR_03",
            center_id="TC_SANGLI_01",
            start_date=date(2026, 10, 15),
            capacity=30, seats_available=18,
        )

        breakdown, matched, missing, asset_info = scorer.score(
            beneficiary, qualification, center, batch
        )

        assert 0 <= breakdown.total <= 100
        assert breakdown.skill >= 0
        assert breakdown.interest >= 0
        assert breakdown.experience >= 0
        assert breakdown.education >= 0
        assert breakdown.asset >= 0
        assert breakdown.location >= 0
        assert breakdown.employment >= 0
        assert breakdown.batch >= 0
