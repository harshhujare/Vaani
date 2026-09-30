"""
VaniSetu Recommendation Engine
==============================
AI Understands. Rules Decide.

A modular, auditable, deterministic recommendation engine for
matching PM-AJAY GIA beneficiaries to NSQF-aligned skilling programs.
"""

__version__ = "1.0.0"

from services.recommendation_engine.engine import RecommendationEngine

__all__ = ["RecommendationEngine", "__version__"]
