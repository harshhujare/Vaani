"""
Pipeline Stage — Geospatial Matching (Haversine)
=================================================
Computes great-circle distance between two geographic coordinates.
Uses the Haversine formula — never Euclidean on lat/lon.
"""

from __future__ import annotations

import math

from services.recommendation_engine.core.constants import EARTH_RADIUS_KM
from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    Batch,
    CenterMatch,
    TrainingCenter,
)
from services.recommendation_engine.repositories.batch_repository import (
    BatchRepository,
)
from services.recommendation_engine.repositories.center_repository import (
    CenterRepository,
)


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate the great-circle distance (km) between two points.

    Uses the Haversine formula:
      d = 2r * arcsin(
          sqrt(
              sin²((φ₂ - φ₁)/2)
              + cos(φ₁) * cos(φ₂) * sin²((λ₂ - λ₁)/2)
          )
      )
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return round(EARTH_RADIUS_KM * c, 2)


DISTRICT_CENTERS: dict[str, tuple[float, float]] = {
    "ranchi": (23.3441, 85.3096),
    "sangli": (16.8524, 74.5815),
    "pune": (18.5204, 73.8567),
    "patna": (25.5941, 85.1376),
    "lucknow": (26.8467, 80.9462),
    "bhopal": (23.2599, 77.4126),
    "jaipur": (26.9124, 75.7873),
    "chennai": (13.0827, 80.2707),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
}


class GeospatialMatcher:
    """Finds the nearest authorized training center for a qualification."""

    def __init__(
        self,
        center_repo: CenterRepository,
        batch_repo: BatchRepository,
    ):
        self._center_repo = center_repo
        self._batch_repo = batch_repo

    def find_nearest(
        self,
        beneficiary: BeneficiaryProfile,
        qualification_id: str,
    ) -> CenterMatch | None:
        """Find the closest authorized center with available batches.

        Resolves coordinates from district name if latitude/longitude are omitted.
        """
        lat = beneficiary.latitude
        lon = beneficiary.longitude

        if (lat is None or lon is None) and beneficiary.district:
            d_key = beneficiary.district.strip().lower()
            if d_key in DISTRICT_CENTERS:
                lat, lon = DISTRICT_CENTERS[d_key]

        if lat is None or lon is None:
            return None

        centers = self._center_repo.get_for_qualification(qualification_id)
        if not centers:
            return None

        best: CenterMatch | None = None
        best_distance = float("inf")

        for center in centers:
            distance = haversine_distance(
                lat,
                lon,
                center.latitude,
                center.longitude,
            )

            if distance < best_distance:
                batch = self._batch_repo.get_best_batch(
                    qualification_id, center.center_id
                )
                best_distance = distance
                best = CenterMatch(
                    center_id=center.center_id,
                    name=center.name,
                    distance_km=distance,
                    seats_available=batch.seats_available if batch else None,
                    next_batch_date=batch.start_date if batch else None,
                    batch_id=batch.batch_id if batch else None,
                )

        return best
