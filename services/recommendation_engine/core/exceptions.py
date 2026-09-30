"""
Recommendation Engine — Custom Exceptions
==========================================
Structured error hierarchy for the recommendation pipeline.
Each stage has its own exception type for clear error handling.
"""


class RecommendationEngineError(Exception):
    """Base exception for all recommendation engine errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NormalizationError(RecommendationEngineError):
    """Raised when skill normalization fails."""
    pass


class RetrievalError(RecommendationEngineError):
    """Raised when candidate retrieval fails."""
    pass


class EligibilityError(RecommendationEngineError):
    """Raised when eligibility evaluation encounters an error."""
    pass


class ScoringError(RecommendationEngineError):
    """Raised when the scoring engine encounters invalid data."""
    pass


class GeospatialError(RecommendationEngineError):
    """Raised when geographic calculations fail (e.g., invalid coordinates)."""
    pass


class ExplanationError(RecommendationEngineError):
    """Raised when the LLM explainer produces invalid output."""
    pass


class ValidationError(RecommendationEngineError):
    """Raised when input or output schema validation fails."""
    pass
