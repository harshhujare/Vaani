"""
Qualification Repository
=========================
Data access layer for NSQF qualifications/courses.
"""

from __future__ import annotations

import json
from pathlib import Path

from services.recommendation_engine.models.types import Qualification

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class QualificationRepository:
    """Provides query and filtering for qualifications."""

    def __init__(self, data_path: Path | None = None):
        self._qualifications: dict[str, Qualification] = {}
        self._load(data_path or _DATA_DIR / "qualifications.json")

    def _load(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            q = Qualification(**item)
            self._qualifications[q.qualification_id] = q

    def get(self, qualification_id: str) -> Qualification | None:
        return self._qualifications.get(qualification_id)

    def get_all(self) -> list[Qualification]:
        return list(self._qualifications.values())

    def get_active(self) -> list[Qualification]:
        """Return only active qualifications."""
        return [q for q in self._qualifications.values() if q.is_active]

    def filter_by_sector(self, sector: str) -> list[Qualification]:
        """Return active qualifications in a specific sector."""
        return [
            q for q in self._qualifications.values()
            if q.is_active and q.sector.lower() == sector.lower()
        ]

    def filter_by_skills(self, skill_ids: list[str]) -> list[Qualification]:
        """Return active qualifications whose required skills overlap with the given IDs."""
        skill_set = set(skill_ids)
        return [
            q for q in self._qualifications.values()
            if q.is_active and skill_set & set(q.required_skills)
        ]

    def exists(self, qualification_id: str) -> bool:
        return qualification_id in self._qualifications
