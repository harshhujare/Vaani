"""
Tests — API Routes & FastAPI Integration
========================================
Validates REST endpoints:
  - GET  /
  - GET  /api/v1/health
  - POST /api/v1/recommendations (flat payload)
  - POST /api/v1/recommend (nested SIH specification payload)
"""

import pytest
from fastapi.testclient import TestClient

from services.recommendation_engine.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data
    assert "engine_version" in data


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["engine_version"] == "1.0.0"


def test_recommendations_flat_payload(client):
    """Test recommendations with flat payload format."""
    payload = {
        "beneficiary_id": "BEN-TEST-001",
        "name": "Ramesh",
        "language": "hi",
        "district": "Ranchi",
        "state": "Jharkhand",
        "latitude": 23.3441,
        "longitude": 85.3096,
        "education_level": "8th",
        "experience_years": 4.0,
        "skills": ["लकड़ी का काम", "furniture assembly"],
        "interests": ["carpentry"],
        "assets": ["AST_CARP_BASIC"],
        "employment_preference": "self_employment",
    }

    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["beneficiary_id"] == "BEN-TEST-001"
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0

    top_rec = data["recommendations"][0]
    assert "qualification_id" in top_rec
    assert "qualification_title" in top_rec
    assert "nsqf_level" in top_rec
    assert "final_score" in top_rec
    assert 0 <= top_rec["final_score"] <= 100
    assert "score_breakdown" in top_rec
    assert "matched_skills" in top_rec
    assert "skill_gaps" in top_rec
    assert "explanation" in top_rec
    assert len(top_rec["explanation"]) > 0


def test_recommend_nested_payload(client):
    """Test recommendations with nested SIH specification payload (/api/v1/recommend)."""
    payload = {
        "beneficiary_id": "BEN-2026-091",
        "language": "mr",
        "location": {
            "district": "Sangli",
            "block": "Miraj",
            "latitude": 16.8524,
            "longitude": 74.5815,
        },
        "livelihood_profile": {
            "current_occupation": "tailoring",
            "experience_years": 5.0,
            "education_level": "10th",
            "employment_preference": "self_employment",
            "canonical_skill_ids": ["SK001", "SK004"],
            "asset_ids": ["AST_SEW_01"],
            "interest_tags": ["dress_designing"],
        },
    }

    response = client.post("/api/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["beneficiary_id"] == "BEN-2026-091"
    assert len(data["recommendations"]) >= 1

    top_rec = data["recommendations"][0]
    assert top_rec["pathway_type"] in ["BEST_MATCH", "GROWTH_PATH", "ALTERNATIVE_OPTION"]
    assert top_rec["training_center"] is not None
    assert top_rec["training_center"]["distance_km"] >= 0


def test_zero_skills_recommendation(client):
    """Test that a candidate with zero skills still receives a valid response."""
    payload = {
        "beneficiary_id": "BEN-ZERO-001",
        "language": "hi",
        "education_level": "8th",
        "experience_years": 0.0,
        "skills": [],
        "interests": ["carpentry"],
    }

    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["beneficiary_id"] == "BEN-ZERO-001"
    assert isinstance(data["recommendations"], list)
