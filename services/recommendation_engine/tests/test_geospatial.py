"""
Tests — Geospatial (Haversine)
================================
Tests known coordinate pairs, same coordinates, short/large distances,
and boundary conditions at 5 km and 30 km.
"""

import pytest

from services.recommendation_engine.pipeline.geospatial import haversine_distance


class TestHaversineDistance:

    def test_same_coordinates_zero_distance(self):
        d = haversine_distance(20.0, 77.0, 20.0, 77.0)
        assert d == 0.0

    def test_known_pair_mumbai_pune(self):
        """Mumbai (19.0760, 72.8777) to Pune (18.5204, 73.8567).
        Expected ~120 km."""
        d = haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
        assert 115 < d < 125

    def test_known_pair_delhi_mumbai(self):
        """Delhi (28.7041, 77.1025) to Mumbai (19.0760, 72.8777).
        Expected ~1148 km."""
        d = haversine_distance(28.7041, 77.1025, 19.0760, 72.8777)
        assert 1140 < d < 1160

    def test_short_distance(self):
        """Two points ~1 km apart (approximately)."""
        # 0.01 degrees latitude ≈ 1.11 km
        d = haversine_distance(20.0, 77.0, 20.01, 77.0)
        assert 1.0 < d < 1.2

    def test_large_distance(self):
        """Ranchi to Sangli (~1200+ km)."""
        d = haversine_distance(23.35, 85.33, 16.85, 74.62)
        assert d > 1000

    def test_symmetry(self):
        """Distance A->B should equal B->A."""
        d1 = haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
        d2 = haversine_distance(18.5204, 73.8567, 19.0760, 72.8777)
        assert d1 == d2

    def test_boundary_under_5km(self):
        """Points within ~3 km should be < 5 km."""
        # ~0.027 degrees ≈ 3 km
        d = haversine_distance(20.0, 77.0, 20.027, 77.0)
        assert d < 5.0

    def test_boundary_over_30km(self):
        """Points ~35 km apart should be > 30 km."""
        # ~0.32 degrees ≈ 35 km
        d = haversine_distance(20.0, 77.0, 20.32, 77.0)
        assert d > 30.0
