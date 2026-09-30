"""
Pipeline Stage 1 — Canonical Normalizer
========================================
Resolves raw, colloquial skill strings (in any language) to canonical
Skill IDs from the verified taxonomy. Unknown skills are marked as
unresolved, never fabricated.
"""

from __future__ import annotations

from services.recommendation_engine.models.types import (
    NormalizedSkill,
    NormalizationSource,
)
from services.recommendation_engine.repositories.skill_repository import (
    SkillRepository,
)


class SkillNormalizer:
    """Maps raw skill strings to canonical IDs using the alias table."""

    def __init__(self, skill_repo: SkillRepository):
        self._repo = skill_repo

    def normalize(self, raw_skills: list[str]) -> list[NormalizedSkill]:
        """Normalize a list of raw skill strings.

        Returns a NormalizedSkill for each input, preserving order.
        Unknown skills get canonical_id=None and source=UNRESOLVED.
        """
        results: list[NormalizedSkill] = []
        for raw in raw_skills:
            canonical_id = self._repo.resolve(raw)
            if canonical_id is not None:
                # Determine if it was an exact skill_id match or alias match
                source = (
                    NormalizationSource.EXACT_MATCH
                    if raw.strip().upper() == canonical_id
                    else NormalizationSource.ALIAS_TABLE
                )
                results.append(
                    NormalizedSkill(
                        raw_value=raw,
                        canonical_id=canonical_id,
                        confidence=1.0,
                        source=source,
                    )
                )
            else:
                results.append(
                    NormalizedSkill(
                        raw_value=raw,
                        canonical_id=None,
                        confidence=0.0,
                        source=NormalizationSource.UNRESOLVED,
                    )
                )
        return results

    def normalize_to_ids(self, raw_skills: list[str]) -> list[str]:
        """Convenience: normalize and return only resolved canonical IDs."""
        return [
            ns.canonical_id
            for ns in self.normalize(raw_skills)
            if ns.canonical_id is not None
        ]
