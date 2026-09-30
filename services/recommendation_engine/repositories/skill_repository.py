"""
Skill Repository
================
Data access layer for the canonical skill taxonomy and alias dictionary.
Loads from JSON seed files. Can be swapped for PostgreSQL later.
"""

from __future__ import annotations

import json
from pathlib import Path

from services.recommendation_engine.models.types import Skill

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class SkillRepository:
    """Provides lookup and normalization services for canonical skills."""

    def __init__(self, data_path: Path | None = None):
        self._skills: dict[str, Skill] = {}
        self._alias_index: dict[str, str] = {}
        self._load(data_path or _DATA_DIR / "skills.json")

    def _load(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            skill = Skill(**item)
            self._skills[skill.skill_id] = skill
            # Index the canonical name itself as a lookup key
            self._alias_index[skill.name.lower().strip()] = skill.skill_id
            self._alias_index[skill.skill_id.lower().strip()] = skill.skill_id
            for alias in skill.aliases:
                self._alias_index[alias.lower().strip()] = skill.skill_id

    def resolve(self, raw_value: str) -> str | None:
        """Resolve a raw skill string to a canonical skill ID.
        Returns None if no match found."""
        return self._alias_index.get(raw_value.lower().strip())

    def get(self, skill_id: str) -> Skill | None:
        """Get a skill by its canonical ID."""
        return self._skills.get(skill_id)

    def get_all(self) -> list[Skill]:
        """Return all canonical skills."""
        return list(self._skills.values())

    def exists(self, skill_id: str) -> bool:
        """Check if a canonical skill ID exists."""
        return skill_id in self._skills
