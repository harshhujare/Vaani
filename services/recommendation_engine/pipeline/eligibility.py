"""
Pipeline Stage 3 — Hard Eligibility Gate
==========================================
Binary pass/fail evaluation BEFORE scoring.
Checks education, experience, active status, and RPL waivers.
No ineligible candidate may ever receive a positive score.
"""

from __future__ import annotations

from services.recommendation_engine.core.config import RecommendationConfig
from services.recommendation_engine.core.constants import EDUCATION_LEVELS
from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    EligibilityResult,
    Qualification,
)


def _education_rank(level: str) -> int:
    """Convert an education level string to its numeric rank."""
    return EDUCATION_LEVELS.get(level.lower().strip(), 0)


class EligibilityGate:
    """Deterministic binary eligibility evaluator."""

    def __init__(self, config: RecommendationConfig):
        self._config = config

    def evaluate(
        self,
        beneficiary: BeneficiaryProfile,
        qualification: Qualification,
    ) -> EligibilityResult:
        """Evaluate whether a beneficiary is eligible for a qualification.

        Rules (all must pass):
        1. Qualification must be active.
        2. Beneficiary education >= qualification min_education
           (unless RPL waiver applies).
        3. Beneficiary experience >= qualification min_experience.
        """
        failed_rules: list[str] = []
        reasons: list[str] = []
        rpl_applied = False

        # Rule 1: Active qualification
        if not qualification.is_active:
            failed_rules.append("qualification_inactive")
            reasons.append(
                f"Qualification {qualification.qualification_id} is not active."
            )

        # Rule 2: Education requirement
        beneficiary_edu_rank = _education_rank(beneficiary.education_level)
        required_edu_rank = _education_rank(qualification.min_education)

        education_met = beneficiary_edu_rank >= required_edu_rank

        if not education_met:
            # Check RPL waiver
            if (
                self._config.enable_rpl
                and qualification.supports_rpl
                and beneficiary.experience_years
                >= qualification.rpl_min_experience_years
            ):
                education_met = True
                rpl_applied = True
                reasons.append(
                    f"Education waiver via RPL: {beneficiary.experience_years} years "
                    f"experience >= {qualification.rpl_min_experience_years} RPL minimum."
                )
            else:
                failed_rules.append("minimum_education_not_met")
                reasons.append(
                    f"Education {beneficiary.education_level} (rank {beneficiary_edu_rank}) "
                    f"< required {qualification.min_education} (rank {required_edu_rank})."
                )

        # Rule 3: Experience requirement
        if beneficiary.experience_years < qualification.min_experience_years:
            failed_rules.append("minimum_experience_not_met")
            reasons.append(
                f"Experience {beneficiary.experience_years} years "
                f"< required {qualification.min_experience_years} years."
            )

        eligible = len(failed_rules) == 0

        return EligibilityResult(
            qualification_id=qualification.qualification_id,
            eligible=eligible,
            reasons=reasons,
            failed_rules=failed_rules,
            rpl_applied=rpl_applied,
        )

    def filter_eligible(
        self,
        beneficiary: BeneficiaryProfile,
        qualifications: list[Qualification],
    ) -> list[tuple[Qualification, EligibilityResult]]:
        """Filter a list of qualifications, returning only eligible ones
        along with their eligibility results."""
        results: list[tuple[Qualification, EligibilityResult]] = []
        for q in qualifications:
            result = self.evaluate(beneficiary, q)
            if result.eligible:
                results.append((q, result))
        return results
