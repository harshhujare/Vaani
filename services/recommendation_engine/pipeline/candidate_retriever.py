"""
Pipeline Stage 2 — Candidate Retriever
========================================
Dual-funnel retrieval: SQL-like filtering + optional vector semantic search.
Merges and deduplicates into a candidate pool of 50–100 qualifications.
"""

from __future__ import annotations

from services.recommendation_engine.core.config import RecommendationConfig
from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    Qualification,
)
from services.recommendation_engine.repositories.qualification_repository import (
    QualificationRepository,
)
from services.recommendation_engine.repositories.skill_repository import (
    SkillRepository,
)


class CandidateRetriever:
    """Retrieves a candidate pool of qualifications for scoring."""

    def __init__(
        self,
        qualification_repo: QualificationRepository,
        skill_repo: SkillRepository,
        config: RecommendationConfig,
    ):
        self._qual_repo = qualification_repo
        self._skill_repo = skill_repo
        self._config = config

    def retrieve(self, profile: BeneficiaryProfile) -> list[Qualification]:
        """Retrieve candidate qualifications using dual-funnel strategy.

        1. SQL Retrieval: filter by sector overlap with beneficiary skills
        2. Vector Retrieval: (when enabled) semantic similarity search
        3. Merge and deduplicate
        """
        sql_candidates = self._sql_retrieve(profile)
        vector_candidates = self._vector_retrieve(profile)

        # Merge and deduplicate by qualification_id
        seen: set[str] = set()
        merged: list[Qualification] = []
        for q in sql_candidates + vector_candidates:
            if q.qualification_id not in seen:
                seen.add(q.qualification_id)
                merged.append(q)

        # Cap at max pool size
        return merged[: self._config.retrieval.max_candidate_pool]

    def _sql_retrieve(self, profile: BeneficiaryProfile) -> list[Qualification]:
        """Retrieve by sector and skill overlap (relational filtering)."""
        if not profile.skills:
            # If no skills, return all active qualifications as candidates
            return self._qual_repo.get_active()[: self._config.retrieval.sql_top_k]

        # Get sectors from the beneficiary's skills
        sectors: set[str] = set()
        for skill_id in profile.skills:
            skill = self._skill_repo.get(skill_id)
            if skill:
                sectors.add(skill.sector)

        # Retrieve by skill overlap first (primary)
        skill_matches = self._qual_repo.filter_by_skills(profile.skills)

        # Retrieve by sector (secondary, for breadth)
        sector_matches: list[Qualification] = []
        for sector in sectors:
            sector_matches.extend(self._qual_repo.filter_by_sector(sector))

        # Merge (skill matches first, then sector, deduped)
        seen: set[str] = set()
        result: list[Qualification] = []
        for q in skill_matches + sector_matches:
            if q.qualification_id not in seen:
                seen.add(q.qualification_id)
                result.append(q)

        # Ensure sufficient candidate pool size for 3-way diversity ranking (at least 10 candidates)
        if len(result) < 10:
            for active_q in self._qual_repo.get_active():
                if active_q.qualification_id not in seen:
                    seen.add(active_q.qualification_id)
                    result.append(active_q)
                if len(result) >= self._config.retrieval.sql_top_k:
                    break

        return result[: self._config.retrieval.sql_top_k]

    def _vector_retrieve(self, profile: BeneficiaryProfile) -> list[Qualification]:
        """Semantic vector retrieval using pgvector (cosine similarity).

        Currently returns empty list when vector search is disabled.
        When pgvector is available, this will query qualification embeddings
        against a profile embedding using cosine similarity.
        """
        if not self._config.enable_vector_search:
            return []

        # Placeholder for pgvector integration:
        # 1. Generate embedding for beneficiary profile text
        # 2. Query pgvector for top-K similar qualifications
        # 3. Filter by similarity threshold
        # 4. Return matched qualifications
        return []
