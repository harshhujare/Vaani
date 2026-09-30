"""
Beneficiary Models & Location Adapters
======================================
Provides BeneficiaryProfile and LocationCoordinates for convenient importing.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    EmploymentPreference,
    RawCandidateProfile,
)


class LocationCoordinates(BaseModel):
    """Geographic location specification for a beneficiary."""

    latitude: float | None = None
    longitude: float | None = None
    district: str = ""
    block: str = ""
    state: str = ""


__all__ = [
    "BeneficiaryProfile",
    "EmploymentPreference",
    "LocationCoordinates",
    "RawCandidateProfile",
]
