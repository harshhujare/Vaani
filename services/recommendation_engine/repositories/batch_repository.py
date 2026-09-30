"""
Batch Repository
=================
Data access layer for training batches.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from services.recommendation_engine.models.types import Batch

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class BatchRepository:
    """Provides query and filtering for training batches."""

    def __init__(self, data_path: Path | None = None):
        self._batches: list[Batch] = []
        self._load(data_path or _DATA_DIR / "batches.json")

    def _load(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            self._batches.append(Batch(**item))

    def get_upcoming_for_qualification_and_center(
        self, qualification_id: str, center_id: str
    ) -> list[Batch]:
        """Get upcoming batches with available seats at a specific center."""
        return [
            b for b in self._batches
            if b.qualification_id == qualification_id
            and b.center_id == center_id
            and b.status in ("upcoming", "active")
            and b.seats_available > 0
        ]

    def get_best_batch(
        self, qualification_id: str, center_id: str
    ) -> Batch | None:
        """Get the soonest upcoming batch with available seats."""
        candidates = self.get_upcoming_for_qualification_and_center(
            qualification_id, center_id
        )
        if not candidates:
            return None
        return min(candidates, key=lambda b: b.start_date)

    def get_all_for_qualification(self, qualification_id: str) -> list[Batch]:
        """Get all upcoming batches for a qualification across all centers."""
        return [
            b for b in self._batches
            if b.qualification_id == qualification_id
            and b.status in ("upcoming", "active")
            and b.seats_available > 0
        ]
