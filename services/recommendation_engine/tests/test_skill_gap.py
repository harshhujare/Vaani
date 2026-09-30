"""
Tests — Skill Gap Analysis
============================
Covers: empty required, empty possessed, partial overlap, complete overlap.
"""

import pytest

from services.recommendation_engine.models.types import Qualification
from services.recommendation_engine.pipeline.skill_gap import compute_skill_gap


class TestSkillGap:

    def test_complete_overlap(self):
        qual = Qualification(
            qualification_id="Q1", title="A", sector="X",
            required_skills=["SK_A", "SK_B"],
        )
        result = compute_skill_gap(["SK_A", "SK_B", "SK_C"], qual)
        assert result.matched_skills == ["SK_A", "SK_B"]
        assert result.skill_gaps == []

    def test_partial_overlap(self):
        qual = Qualification(
            qualification_id="Q1", title="A", sector="X",
            required_skills=["SK_A", "SK_B", "SK_C"],
        )
        result = compute_skill_gap(["SK_A"], qual)
        assert result.matched_skills == ["SK_A"]
        assert set(result.skill_gaps) == {"SK_B", "SK_C"}

    def test_no_overlap(self):
        qual = Qualification(
            qualification_id="Q1", title="A", sector="X",
            required_skills=["SK_A", "SK_B"],
        )
        result = compute_skill_gap(["SK_X", "SK_Y"], qual)
        assert result.matched_skills == []
        assert set(result.skill_gaps) == {"SK_A", "SK_B"}

    def test_empty_required_skills(self):
        qual = Qualification(
            qualification_id="Q1", title="A", sector="X",
            required_skills=[],
        )
        result = compute_skill_gap(["SK_A"], qual)
        assert result.matched_skills == []
        assert result.skill_gaps == []

    def test_empty_possessed_skills(self):
        qual = Qualification(
            qualification_id="Q1", title="A", sector="X",
            required_skills=["SK_A", "SK_B"],
        )
        result = compute_skill_gap([], qual)
        assert result.matched_skills == []
        assert set(result.skill_gaps) == {"SK_A", "SK_B"}

    def test_both_empty(self):
        qual = Qualification(
            qualification_id="Q1", title="A", sector="X",
            required_skills=[],
        )
        result = compute_skill_gap([], qual)
        assert result.matched_skills == []
        assert result.skill_gaps == []
