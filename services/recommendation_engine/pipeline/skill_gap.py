"""
Pipeline Stage — Skill Gap Analysis
=====================================
Deterministic set subtraction: Required - Possessed.
No LLM involvement. Pure mathematical set operations.
"""

from __future__ import annotations

from services.recommendation_engine.models.types import (
    Qualification,
    SkillGapResult,
)


def compute_skill_gap(
    possessed_skills: list[str],
    qualification: Qualification,
) -> SkillGapResult:
    """Compute skill gaps via set subtraction.

    Skill Gaps    = Required Skills \\ Possessed Skills
    Matched Skills = Required Skills ∩ Possessed Skills
    """
    possessed = set(possessed_skills)
    required = set(qualification.required_skills)

    matched = sorted(required & possessed)
    gaps = sorted(required - possessed)

    return SkillGapResult(
        matched_skills=matched,
        skill_gaps=gaps,
    )
