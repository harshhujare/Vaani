"""
Tests — Response Validator
===========================
Validates qualification existence, center existence, score ranges,
and breakdown consistency.
"""

import pytest

from services.recommendation_engine.core.exceptions import ValidationError
from services.recommendation_engine.models.types import (
    CenterMatch,
    EligibilityResult,
    PathwayType,
    Recommendation,
    RecommendationResponse,
    ScoreBreakdown,
)
from services.recommendation_engine.pipeline.validator import ResponseValidator
from services.recommendation_engine.repositories.center_repository import CenterRepository
from services.recommendation_engine.repositories.qualification_repository import QualificationRepository


@pytest.fixture
def validator():
    return ResponseValidator(QualificationRepository(), CenterRepository())


def _make_valid_rec() -> Recommendation:
    breakdown = ScoreBreakdown(
        skill=27.0, interest=18.0, experience=13.5,
        education=10.0, asset=8.0, location=4.0,
        employment=5.0, batch=4.5,
    )
    return Recommendation(
        pathway_type=PathwayType.BEST_MATCH,
        qualification_id="Q_APPAR_03",
        qualification_title="Basic Tailoring",
        nsqf_level=3,
        final_score=90.0,
        score_breakdown=breakdown,
        eligibility_result=EligibilityResult(
            qualification_id="Q_APPAR_03", eligible=True,
        ),
        training_center=CenterMatch(
            center_id="TC_SANGLI_01",
            name="PMKK Miraj",
            distance_km=5.0,
        ),
    )


class TestResponseValidator:

    def test_valid_response_passes(self, validator):
        rec = _make_valid_rec()
        response = RecommendationResponse(
            beneficiary_id="BEN1",
            engine_version="1.0.0",
            recommendations=[rec],
        )
        result = validator.validate(response)
        assert len(result.recommendations) == 1

    def test_invalid_qualification_fails(self, validator):
        rec = _make_valid_rec()
        rec.qualification_id = "Q_NONEXISTENT"
        response = RecommendationResponse(
            beneficiary_id="BEN1",
            engine_version="1.0.0",
            recommendations=[rec],
        )
        with pytest.raises(ValidationError):
            validator.validate(response)

    def test_invalid_center_fails(self, validator):
        rec = _make_valid_rec()
        rec.training_center = CenterMatch(
            center_id="FAKE_CENTER",
            name="Nonexistent",
            distance_km=10.0,
        )
        response = RecommendationResponse(
            beneficiary_id="BEN1",
            engine_version="1.0.0",
            recommendations=[rec],
        )
        with pytest.raises(ValidationError):
            validator.validate(response)

    def test_score_out_of_range_fails(self, validator):
        rec = _make_valid_rec()
        rec.final_score = 150.0
        response = RecommendationResponse(
            beneficiary_id="BEN1",
            engine_version="1.0.0",
            recommendations=[rec],
        )
        with pytest.raises(ValidationError):
            validator.validate(response)
