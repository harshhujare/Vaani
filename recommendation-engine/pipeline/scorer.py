"""
Stage 3 — 100-Point Heuristic Scorer
=====================================
Every eligible program is scored from 0 to 100 using a
deterministic, weighted formula.

Formula:
  Final Score = Σ (Component Score × Weight × 100)

Components:
  - Skill Compatibility  (30%) — keyword overlap
  - NSQF Level Fit       (25%) — level alignment
  - Location Match       (20%) — district/state proximity
  - Capacity Available   (15%) — seat availability
  - Education Match      (10%) — education level fit

Every score generates an explicit mathematical breakdown
for jury and government audit purposes.
"""

from config import (
    WEIGHTS,
    nsqf_fit_score,
    location_score as calc_location_score,
    capacity_score as calc_capacity_score,
    education_rank,
)
from models import ScoreBreakdown


def _skill_compatibility(
    beneficiary_skills: list[dict],
    program: dict,
) -> tuple[float, list[str]]:
    """
    Calculate skill overlap between beneficiary and program.
    Returns (score 0-1, list of matched skill names).
    """
    if not beneficiary_skills:
        return 0.0, []

    program_sector = (program.get("sector") or "").lower()
    program_sub = (program.get("sub_sector") or "").lower()
    program_name = (program.get("name") or "").lower()

    matched = []
    total_weight = 0
    match_weight = 0

    for skill in beneficiary_skills:
        skill_name = (skill.get("skill_name") or "").lower()
        skill_sector = (skill.get("sector") or "").lower()
        skill_sub = (skill.get("sub_sector") or "").lower()
        is_primary = skill.get("is_primary", False)

        # Weight primary skills higher
        weight = 2.0 if is_primary else 1.0
        total_weight += weight

        # Check for sector match
        sector_match = (
            (skill_sector and skill_sector == program_sector)
            or (skill_sub and skill_sub == program_sub)
        )

        # Check for keyword overlap in program name
        skill_words = set(skill_name.split())
        program_words = set(program_name.split())
        keyword_overlap = len(skill_words & program_words) > 0

        # Check sub-sector alignment
        sub_sector_match = (
            skill_sub and program_sub and
            (skill_sub in program_sub or program_sub in skill_sub)
        )

        if sector_match or keyword_overlap or sub_sector_match:
            match_weight += weight
            matched.append(skill.get("skill_name", "Unknown"))

    if total_weight == 0:
        return 0.0, []

    return match_weight / total_weight, matched


def _education_fit(
    beneficiary_education: str | None,
    program_nsqf: int | None,
) -> float:
    """
    Score how well the beneficiary's education fits the program.
    Returns 0.0 – 1.0.
    """
    ben_rank = education_rank(beneficiary_education)

    if not program_nsqf:
        return 0.5  # neutral

    # Map NSQF levels to typical education requirements
    # NSQF 1-3: 5th pass+, NSQF 4-5: 8th pass+, NSQF 6-7: 10th/12th+
    required_rank_map = {
        1: education_rank("below_5th"),
        2: education_rank("5th_pass"),
        3: education_rank("5th_pass"),
        4: education_rank("8th_pass"),
        5: education_rank("8th_pass"),
        6: education_rank("10th_pass"),
        7: education_rank("12th_pass"),
        8: education_rank("graduate"),
    }

    required_rank = required_rank_map.get(program_nsqf, 0)

    if ben_rank >= required_rank + 2:
        return 1.0   # well above minimum
    elif ben_rank >= required_rank:
        return 0.85  # meets or exceeds
    elif ben_rank == required_rank - 1:
        return 0.50  # borderline
    else:
        return 0.20  # significantly below


def score_program(
    program: dict,
    beneficiary_skills: list[dict],
    beneficiary_education: str | None,
    beneficiary_nsqf_level: int | None,
    beneficiary_district: str | None,
    beneficiary_state: str | None,
) -> tuple[float, ScoreBreakdown, list[str]]:
    """
    Score a single program against a beneficiary profile.
    
    Returns:
        (total_score, breakdown, matched_skills)
    """
    # Component 1: Skill Compatibility (30%)
    skill_raw, matched_skills = _skill_compatibility(beneficiary_skills, program)
    skill_points = round(skill_raw * WEIGHTS["skill_compatibility"] * 100, 2)

    # Component 2: NSQF Level Fit (25%)
    nsqf_raw = nsqf_fit_score(beneficiary_nsqf_level, program.get("nsqf_level"))
    nsqf_points = round(nsqf_raw * WEIGHTS["nsqf_level_fit"] * 100, 2)

    # Component 3: Location Match (20%)
    loc_raw = calc_location_score(
        beneficiary_district, beneficiary_state,
        program.get("district"), program.get("state"),
    )
    loc_points = round(loc_raw * WEIGHTS["location_match"] * 100, 2)

    # Component 4: Capacity Available (15%)
    cap_raw = calc_capacity_score(program.get("capacity"), program.get("enrolled_count"))
    cap_points = round(cap_raw * WEIGHTS["capacity_available"] * 100, 2)

    # Component 5: Education Match (10%)
    edu_raw = _education_fit(beneficiary_education, program.get("nsqf_level"))
    edu_points = round(edu_raw * WEIGHTS["education_match"] * 100, 2)

    # Total
    total = round(skill_points + nsqf_points + loc_points + cap_points + edu_points, 2)

    breakdown = ScoreBreakdown(
        skill_score=skill_points,
        nsqf_score=nsqf_points,
        location_score=loc_points,
        capacity_score=cap_points,
        education_score=edu_points,
    )

    return total, breakdown, matched_skills


def score_all(
    eligible_programs: list[dict],
    beneficiary_skills: list[dict],
    beneficiary_education: str | None,
    beneficiary_nsqf_level: int | None,
    beneficiary_district: str | None,
    beneficiary_state: str | None,
) -> list[dict]:
    """
    Score all eligible programs and attach results.
    Returns list of programs with 'match_score', 'score_breakdown', 'matched_skills'.
    """
    scored = []

    for program in eligible_programs:
        total, breakdown, matched = score_program(
            program,
            beneficiary_skills,
            beneficiary_education,
            beneficiary_nsqf_level,
            beneficiary_district,
            beneficiary_state,
        )
        scored.append({
            **program,
            "match_score": total,
            "score_breakdown": breakdown,
            "matched_skills": matched,
        })

    return scored
