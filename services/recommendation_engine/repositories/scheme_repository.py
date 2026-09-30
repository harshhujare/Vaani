"""
Repository — Government Schemes
================================
Provides query access to the database of Government Welfare & Skilling Schemes.
"""

from __future__ import annotations

import json
from pathlib import Path

from services.recommendation_engine.models.types import SchemeInfo

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class SchemeDetail(SchemeInfo):
    """Detailed government scheme record stored in the database."""

    sectors: list[str] = []
    target_audience: str = ""
    min_education: str = "none"
    min_age: int = 18
    max_age: int = 65
    caste_criteria: str = "all"  # all, sc, sc_st, obc
    employment_type: str = "both"  # self_employment, wage_employment, both
    toolkit_support: str = ""
    training_provided: bool = True
    official_portal: str = ""


class SchemeRepository:
    """In-memory & SQL backed repository for government schemes."""

    def __init__(self, data_path: Path | None = None):
        self._path = data_path or (DATA_DIR / "schemes.json")
        self._schemes: dict[str, SchemeDetail] = {}
        self._load()

    def _load(self):
        if not self._path.exists():
            return

        with open(self._path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        for item in raw_list:
            detail = SchemeDetail(
                scheme_code=item["scheme_id"],
                scheme_name=item["scheme_name"],
                ministry=item.get("ministry", ""),
                benefit_summary=item.get("key_benefits", ""),
                financial_grant=item.get("financial_grant"),
                stipend_details=item.get("stipend_amount"),
                loan_subsidy=item.get("loan_subsidy"),
                sectors=item.get("sectors", ["All"]),
                target_audience=item.get("target_audience", ""),
                min_education=item.get("min_education", "none"),
                min_age=item.get("min_age", 18),
                max_age=item.get("max_age", 65),
                caste_criteria=item.get("caste_criteria", "all"),
                employment_type=item.get("employment_type", "both"),
                toolkit_support=item.get("toolkit_support", ""),
                training_provided=item.get("training_provided", True),
                official_portal=item.get("official_portal", ""),
            )
            self._schemes[detail.scheme_code] = detail

    def get(self, scheme_code: str) -> SchemeDetail | None:
        return self._schemes.get(scheme_code)

    def get_all(self) -> list[SchemeDetail]:
        return list(self._schemes.values())

    def filter_by_sector(self, sector: str) -> list[SchemeDetail]:
        return [
            s
            for s in self._schemes.values()
            if "All" in s.sectors or sector in s.sectors
        ]

    def filter_eligible(
        self,
        sector: str | None = None,
        employment_type: str = "both",
        caste: str = "all",
    ) -> list[SchemeDetail]:
        """Find all schemes eligible for a beneficiary's sector and preferences."""
        matches: list[SchemeDetail] = []
        for s in self._schemes.values():
            # Check sector match
            if sector and ("All" not in s.sectors and sector not in s.sectors):
                continue

            # Check employment match
            if (
                s.employment_type != "both"
                and employment_type != "both"
                and s.employment_type != employment_type
            ):
                continue

            # Check caste eligibility
            if s.caste_criteria == "sc" and caste not in ("sc", "all"):
                continue

            matches.append(s)

        return matches
