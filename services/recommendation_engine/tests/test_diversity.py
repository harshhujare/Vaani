"""
Tests — Diversity Pathway Ranking
===================================
Tests that three near-duplicate courses don't become three pathways
unless they actually meet structural constraints.
"""

import pytest

from services.recommendation_engine.core.config import RecommendationConfig
from services.recommendation_engine.models.types import (
    EligibilityResult,
    PathwayType,
    Recommendation,
    ScoreBreakdown,
)
from services.recommendation_engine.pipeline.diversity import DiversityRanker


def _make_rec(qid: str, nsqf: int, score: float, sector_prefix: str = "APPAR") -> Recommendation:
    return Recommendation(
        pathway_type=PathwayType.BEST_MATCH,  # placeholder
        qualification_id=f"Q_{sector_prefix}_{qid}",
        qualification_title=f"Course {qid}",
        nsqf_level=nsqf,
        final_score=score,
        score_breakdown=ScoreBreakdown(
            skill=score * 0.3, interest=score * 0.2,
            experience=score * 0.15, education=score * 0.1,
            asset=score * 0.1, location=score * 0.05,
            employment=score * 0.05, batch=score * 0.05,
        ),
        eligibility_result=EligibilityResult(
            qualification_id=f"Q_{sector_prefix}_{qid}", eligible=True,
        ),
    )


@pytest.fixture
def ranker():
    return DiversityRanker(RecommendationConfig())


class TestDiversityRanker:

    def test_three_distinct_pathways(self, ranker):
        candidates = [
            _make_rec("03", nsqf=3, score=85),
            _make_rec("04", nsqf=4, score=70),
            _make_rec("CONST_03", nsqf=3, score=50, sector_prefix="CONST"),
        ]
        result = ranker.rank(candidates, beneficiary_nsqf_estimate=3, beneficiary_sectors={"Apparel"})
        assert len(result) == 3
        pathway_types = {r.pathway_type for r in result}
        assert PathwayType.BEST_MATCH in pathway_types

    def test_best_match_is_highest_at_current_level(self, ranker):
        """Best match allows ±1 NSQF delta, so the highest scoring
        candidate within that range wins (NSQF 4, score 90)."""
        candidates = [
            _make_rec("03", nsqf=3, score=85),
            _make_rec("04", nsqf=4, score=90),
        ]
        result = ranker.rank(candidates, beneficiary_nsqf_estimate=3, beneficiary_sectors={"Apparel"})
        best = [r for r in result if r.pathway_type == PathwayType.BEST_MATCH]
        assert len(best) == 1
        # Both NSQF 3 and 4 are within ±1 of estimate 3; higher score wins
        assert best[0].final_score == 90.0

    def test_growth_path_higher_nsqf(self, ranker):
        candidates = [
            _make_rec("03", nsqf=3, score=85),
            _make_rec("04", nsqf=4, score=70),
            _make_rec("05", nsqf=5, score=60),
        ]
        result = ranker.rank(candidates, beneficiary_nsqf_estimate=3, beneficiary_sectors={"Apparel"})
        growth = [r for r in result if r.pathway_type == PathwayType.GROWTH_PATH]
        assert len(growth) == 1
        assert growth[0].nsqf_level > 3

    def test_empty_candidates(self, ranker):
        result = ranker.rank([], beneficiary_nsqf_estimate=3, beneficiary_sectors=set())
        assert result == []

    def test_single_candidate(self, ranker):
        candidates = [_make_rec("03", nsqf=3, score=85)]
        result = ranker.rank(candidates, beneficiary_nsqf_estimate=3, beneficiary_sectors={"Apparel"})
        assert len(result) == 1

    def test_no_duplicate_qualifications(self, ranker):
        candidates = [
            _make_rec("03", nsqf=3, score=85),
            _make_rec("04", nsqf=4, score=70),
            _make_rec("05", nsqf=5, score=60),
            _make_rec("06", nsqf=3, score=55),
        ]
        result = ranker.rank(candidates, beneficiary_nsqf_estimate=3, beneficiary_sectors={"Apparel"})
        qids = [r.qualification_id for r in result]
        assert len(qids) == len(set(qids))  # No duplicates
