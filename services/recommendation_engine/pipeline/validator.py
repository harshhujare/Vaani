"""
Pipeline Stage — Response Validator
=====================================
Final validation gate before returning the API response.
Ensures all recommendations reference real, verified data.
"""

from __future__ import annotations

from services.recommendation_engine.core.exceptions import ValidationError
from services.recommendation_engine.models.types import (
    Recommendation,
    RecommendationResponse,
)
from services.recommendation_engine.repositories.center_repository import (
    CenterRepository,
)
from services.recommendation_engine.repositories.qualification_repository import (
    QualificationRepository,
)


class ResponseValidator:
    """Validates the final recommendation response against source data."""

    def __init__(
        self,
        qualification_repo: QualificationRepository,
        center_repo: CenterRepository,
    ):
        self._qual_repo = qualification_repo
        self._center_repo = center_repo

    def validate(self, response: RecommendationResponse) -> RecommendationResponse:
        """Validate all recommendations in the response.

        Raises ValidationError if any recommendation references
        non-existent qualifications or centers.
        """
        errors: list[str] = []

        for rec in response.recommendations:
            # Verify qualification exists
            if not self._qual_repo.exists(rec.qualification_id):
                errors.append(
                    f"Qualification {rec.qualification_id} does not exist in repository."
                )

            # Verify center exists (if referenced)
            if rec.training_center and not self._center_repo.exists(
                rec.training_center.center_id
            ):
                errors.append(
                    f"Center {rec.training_center.center_id} does not exist in repository."
                )

            # Verify score is within valid range
            if rec.final_score < 0 or rec.final_score > 100:
                errors.append(
                    f"Score {rec.final_score} for {rec.qualification_id} is out of range [0, 100]."
                )

            # Verify score breakdown sums to final score
            breakdown_total = rec.score_breakdown.total
            if abs(breakdown_total - rec.final_score) > 0.1:
                errors.append(
                    f"Score breakdown total {breakdown_total} != final score "
                    f"{rec.final_score} for {rec.qualification_id}."
                )

        if errors:
            raise ValidationError(
                message="Response validation failed.",
                details={"errors": errors},
            )

        return response
