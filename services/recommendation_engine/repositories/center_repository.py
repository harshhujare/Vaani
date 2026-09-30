"""
Center Repository
==================
Data access layer for training centers.
"""

from __future__ import annotations

import json
from pathlib import Path

from services.recommendation_engine.models.types import TrainingCenter

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class CenterRepository:
    """Provides lookup and filtering for training centers."""

    def __init__(self, data_path: Path | None = None):
        self._centers: dict[str, TrainingCenter] = {}
        self._load(data_path or _DATA_DIR / "centers.json")

    def _load(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            c = TrainingCenter(**item)
            self._centers[c.center_id] = c

    def get(self, center_id: str) -> TrainingCenter | None:
        return self._centers.get(center_id)

    def get_all_authorized(self) -> list[TrainingCenter]:
        """Return only authorized centers."""
        return [c for c in self._centers.values() if c.authorized]

    def get_for_qualification(self, qualification_id: str) -> list[TrainingCenter]:
        """Return authorized centers supporting a specific qualification."""
        return [
            c for c in self._centers.values()
            if c.authorized and qualification_id in c.supported_qualifications
        ]

    def exists(self, center_id: str) -> bool:
        return center_id in self._centers
