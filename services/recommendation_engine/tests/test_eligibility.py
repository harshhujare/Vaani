"""
Tests — Eligibility Gate
==========================
Covers: eligible candidate, insufficient education, insufficient experience,
inactive qualification, RPL waiver, RPL not applicable.
"""

import pytest

from services.recommendation_engine.core.config import RecommendationConfig
from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    EmploymentPreference,
    Qualification,
)
from services.recommendation_engine.pipeline.eligibility import EligibilityGate


@pytest.fixture
def gate():
    return EligibilityGate(RecommendationConfig())


@pytest.fixture
def beneficiary_ramesh():
    """Ramesh: 5th grade, 6 years experience, stitching skills."""
    return BeneficiaryProfile(
        beneficiary_id="BEN_RAMESH",
        education_level="5th",
        experience_years=6,
        skills=["SK_STITCHING"],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
    )


@pytest.fixture
def beneficiary_educated():
    """Educated beneficiary: 10th grade, 3 years experience."""
    return BeneficiaryProfile(
        beneficiary_id="BEN_EDUCATED",
        education_level="10th",
        experience_years=3,
        skills=["SK_STITCHING", "SK_PATTERN_MAKING"],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
    )


@pytest.fixture
def qual_basic():
    """Basic tailoring: 5th grade, 0 years, active."""
    return Qualification(
        qualification_id="Q_APPAR_03",
        title="Basic Tailoring",
        sector="Apparel",
        min_education="5th",
        min_experience_years=0,
        is_active=True,
        supports_rpl=True,
        rpl_min_experience_years=2,
    )


@pytest.fixture
def qual_advanced():
    """Advanced tailoring: 8th grade, 2 years, active, RPL supported."""
    return Qualification(
        qualification_id="Q_APPAR_04",
        title="Advanced Tailoring",
        sector="Apparel",
        min_education="8th",
        min_experience_years=2,
        is_active=True,
        supports_rpl=True,
        rpl_min_experience_years=5,
    )


@pytest.fixture
def qual_inactive():
    """Inactive qualification."""
    return Qualification(
        qualification_id="Q_INACTIVE_01",
        title="Legacy Course",
        sector="Apparel",
        min_education="none",
        min_experience_years=0,
        is_active=False,
    )


@pytest.fixture
def qual_no_rpl():
    """Qualification without RPL: 10th grade required, no waiver."""
    return Qualification(
        qualification_id="Q_ELEC_04",
        title="Electrical Installation",
        sector="Electronics",
        min_education="10th",
        min_experience_years=1,
        is_active=True,
        supports_rpl=False,
    )


class TestEligibilityGate:

    def test_eligible_candidate(self, gate, beneficiary_ramesh, qual_basic):
        result = gate.evaluate(beneficiary_ramesh, qual_basic)
        assert result.eligible is True
        assert result.failed_rules == []

    def test_insufficient_education_with_rpl_waiver(
        self, gate, beneficiary_ramesh, qual_advanced
    ):
        """Ramesh has 5th grade but needs 8th for advanced.
        RPL waiver should apply because he has 6 years >= 5 RPL minimum."""
        result = gate.evaluate(beneficiary_ramesh, qual_advanced)
        assert result.eligible is True
        assert result.rpl_applied is True

    def test_insufficient_education_no_rpl(
        self, gate, beneficiary_ramesh, qual_no_rpl
    ):
        """Ramesh has 5th grade but needs 10th, and no RPL available."""
        result = gate.evaluate(beneficiary_ramesh, qual_no_rpl)
        assert result.eligible is False
        assert "minimum_education_not_met" in result.failed_rules

    def test_inactive_qualification(self, gate, beneficiary_ramesh, qual_inactive):
        result = gate.evaluate(beneficiary_ramesh, qual_inactive)
        assert result.eligible is False
        assert "qualification_inactive" in result.failed_rules

    def test_insufficient_experience(self, gate, qual_advanced):
        """Beneficiary with 0 years experience for a 2-year minimum course."""
        ben = BeneficiaryProfile(
            beneficiary_id="BEN_NEW",
            education_level="10th",
            experience_years=0,
            skills=["SK_STITCHING"],
        )
        result = gate.evaluate(ben, qual_advanced)
        assert result.eligible is False
        assert "minimum_experience_not_met" in result.failed_rules

    def test_rpl_disabled_in_config(self, beneficiary_ramesh, qual_advanced):
        """RPL disabled in config — education waiver should NOT apply."""
        config = RecommendationConfig(enable_rpl=False)
        gate = EligibilityGate(config)
        result = gate.evaluate(beneficiary_ramesh, qual_advanced)
        assert result.eligible is False
        assert "minimum_education_not_met" in result.failed_rules
        assert result.rpl_applied is False

    def test_filter_eligible(self, gate, beneficiary_ramesh):
        qualifications = [
            Qualification(
                qualification_id="Q1", title="A", sector="X",
                min_education="5th", is_active=True,
            ),
            Qualification(
                qualification_id="Q2", title="B", sector="X",
                min_education="graduate", is_active=True,
            ),
            Qualification(
                qualification_id="Q3", title="C", sector="X",
                min_education="5th", is_active=False,
            ),
        ]
        eligible = gate.filter_eligible(beneficiary_ramesh, qualifications)
        assert len(eligible) == 1
        assert eligible[0][0].qualification_id == "Q1"
