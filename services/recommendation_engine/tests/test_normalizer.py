"""
Tests — Skill Normalizer
=========================
Covers: Hindi aliases, Marathi aliases, English aliases,
unknown skills, duplicate aliases, case differences.
"""

import pytest

from services.recommendation_engine.models.types import NormalizationSource
from services.recommendation_engine.pipeline.normalizer import SkillNormalizer
from services.recommendation_engine.repositories.skill_repository import SkillRepository


@pytest.fixture
def normalizer():
    return SkillNormalizer(SkillRepository())


class TestSkillNormalizer:
    """Test canonical skill normalization."""

    def test_english_alias(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["tailoring"])
        assert len(results) == 1
        assert results[0].canonical_id == "SK_STITCHING"
        assert results[0].confidence == 1.0
        assert results[0].source == NormalizationSource.ALIAS_TABLE

    def test_hindi_alias(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["सिलाई"])
        assert len(results) == 1
        assert results[0].canonical_id == "SK_STITCHING"

    def test_marathi_alias(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["कपडे शिवणे"])
        assert len(results) == 1
        assert results[0].canonical_id == "SK_STITCHING"

    def test_transliterated_alias(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["lakdi ka kaam"])
        assert len(results) == 1
        assert results[0].canonical_id == "SK_CARPENTRY"

    def test_unknown_skill_unresolved(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["quantum_computing"])
        assert len(results) == 1
        assert results[0].canonical_id is None
        assert results[0].source == NormalizationSource.UNRESOLVED
        assert results[0].confidence == 0.0

    def test_case_insensitive(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["TAILORING", "Carpentry"])
        assert results[0].canonical_id == "SK_STITCHING"
        assert results[1].canonical_id == "SK_CARPENTRY"

    def test_mixed_known_unknown(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["stitching", "teleportation", "welding"])
        assert results[0].canonical_id == "SK_STITCHING"
        assert results[1].canonical_id is None
        assert results[2].canonical_id == "SK_WELDING"

    def test_normalize_to_ids(self, normalizer: SkillNormalizer):
        ids = normalizer.normalize_to_ids(
            ["tailoring", "unknown_skill", "plumbing"]
        )
        assert ids == ["SK_STITCHING", "SK_PLUMBING"]

    def test_empty_input(self, normalizer: SkillNormalizer):
        results = normalizer.normalize([])
        assert results == []

    def test_exact_id_match(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["SK_STITCHING"])
        assert len(results) == 1
        assert results[0].canonical_id == "SK_STITCHING"

    def test_whitespace_handling(self, normalizer: SkillNormalizer):
        results = normalizer.normalize(["  tailoring  ", "  carpentry"])
        assert results[0].canonical_id == "SK_STITCHING"
        assert results[1].canonical_id == "SK_CARPENTRY"
