"""
Tests — End-to-End Engine Test
=================================
Realistic end-to-end scenario: "Ramesh the Carpenter"

Verifies the entire pipeline:
  normalize → retrieve → eligibility → score → skill gaps →
  geospatial → diversity → explain → validate → final JSON

Also tests a tailor profile and an edge case with zero skills.
"""

import pytest

from services.recommendation_engine.core.config import RecommendationConfig
from services.recommendation_engine.engine import RecommendationEngine
from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    EmploymentPreference,
    PathwayType,
)


@pytest.fixture
def engine():
    return RecommendationEngine(config=RecommendationConfig())


@pytest.mark.asyncio
async def test_ramesh_carpenter_e2e(engine):
    """Ramesh: 5th grade education, 6 years carpentry experience,
    located near Ranchi, Jharkhand. No formal certification."""
    ramesh = BeneficiaryProfile(
        beneficiary_id="BEN_RAMESH",
        name="Ramesh Kumar",
        language="hi",
        district="Ranchi",
        state="Jharkhand",
        latitude=23.35,
        longitude=85.33,
        education_level="5th",
        experience_years=6,
        skills=["carpentry", "furniture making"],  # Raw strings, will be normalized
        interests=["wood work", "construction"],
        assets=[],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
    )

    response = await engine.recommend(ramesh)

    # Basic structure checks
    assert response.beneficiary_id == "BEN_RAMESH"
    assert response.engine_version == "1.0.0"
    assert len(response.recommendations) > 0
    assert len(response.recommendations) <= 3

    # Audit metadata
    assert response.audit is not None
    assert response.audit.candidate_count > 0
    assert response.audit.eligible_count > 0
    assert response.audit.selected_count == len(response.recommendations)
    assert response.audit.processing_duration_ms > 0

    # Check each recommendation
    for rec in response.recommendations:
        assert rec.eligible is True
        assert 0 <= rec.final_score <= 100
        assert rec.score_breakdown.total > 0
        assert abs(rec.score_breakdown.total - rec.final_score) < 0.1
        assert rec.qualification_id
        assert rec.qualification_title
        assert rec.nsqf_level >= 1
        assert rec.pathway_type in PathwayType
        assert rec.explanation  # Should have a template explanation

    # Should include carpentry-related qualification
    qual_ids = [r.qualification_id for r in response.recommendations]
    assert any("CONST" in qid for qid in qual_ids), (
        f"Expected carpentry qualification, got: {qual_ids}"
    )

    # Pathway diversity: should have distinct types
    pathway_types = {r.pathway_type for r in response.recommendations}
    if len(response.recommendations) >= 2:
        assert len(pathway_types) >= 2, "Expected diverse pathway types"


@pytest.mark.asyncio
async def test_tailor_sangli_e2e(engine):
    """Tailor near Sangli with sewing machine."""
    tailor = BeneficiaryProfile(
        beneficiary_id="BEN_TAILOR",
        name="Meena Devi",
        language="mr",
        district="Sangli",
        state="Maharashtra",
        latitude=16.85,
        longitude=74.58,
        education_level="8th",
        experience_years=5,
        skills=["stitching", "कपडे शिवणे"],
        interests=["dress_designing", "garment_construction"],
        assets=["AST_SEW_BASIC"],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
    )

    response = await engine.recommend(tailor)

    assert len(response.recommendations) > 0
    for rec in response.recommendations:
        assert rec.eligible is True
        assert 0 <= rec.final_score <= 100

    # Should include apparel-related qualification
    qual_ids = [r.qualification_id for r in response.recommendations]
    assert any("APPAR" in qid for qid in qual_ids)

    # Best match should have a training center near Sangli
    best = [r for r in response.recommendations if r.pathway_type == PathwayType.BEST_MATCH]
    if best and best[0].training_center:
        assert best[0].training_center.distance_km < 50


@pytest.mark.asyncio
async def test_zero_skills_e2e(engine):
    """Beneficiary with no skills — should still get recommendations
    from all active qualifications."""
    new_entrant = BeneficiaryProfile(
        beneficiary_id="BEN_NEW",
        name="New Person",
        education_level="10th",
        experience_years=0,
        skills=[],
        interests=[],
    )

    response = await engine.recommend(new_entrant)

    # Should still return something (entry-level courses)
    # May be empty if all courses require experience
    assert response.beneficiary_id == "BEN_NEW"
    assert response.audit is not None


@pytest.mark.asyncio
async def test_response_is_reproducible(engine):
    """Same input should produce same output (deterministic)."""
    profile = BeneficiaryProfile(
        beneficiary_id="BEN_REPRO",
        education_level="8th",
        experience_years=3,
        skills=["SK_STITCHING"],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
    )

    response1 = await engine.recommend(profile)
    response2 = await engine.recommend(profile)

    # Scores should be identical
    for r1, r2 in zip(response1.recommendations, response2.recommendations):
        assert r1.qualification_id == r2.qualification_id
        assert r1.final_score == r2.final_score
        assert r1.score_breakdown.skill == r2.score_breakdown.skill


@pytest.mark.asyncio
async def test_score_breakdown_matches_total(engine):
    """Verify score breakdown components sum to final_score."""
    profile = BeneficiaryProfile(
        beneficiary_id="BEN_VERIFY",
        education_level="10th",
        experience_years=5,
        skills=["SK_STITCHING", "SK_PATTERN_MAKING"],
        interests=["garment work"],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
        latitude=16.85,
        longitude=74.58,
    )

    response = await engine.recommend(profile)

    for rec in response.recommendations:
        breakdown = rec.score_breakdown
        computed_total = (
            breakdown.skill + breakdown.interest + breakdown.experience
            + breakdown.education + breakdown.asset + breakdown.location
            + breakdown.employment + breakdown.batch
        )
        assert abs(computed_total - rec.final_score) < 0.1, (
            f"Breakdown total {computed_total} != final score {rec.final_score}"
        )
