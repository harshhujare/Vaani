"""
Stage 2 — Hard Eligibility Gate
================================
Binary pass/fail check before any scoring.
Programs that fail ANY gate are eliminated entirely.

Gates:
  1. Program must be active (is_active = true)
  2. Program must have available seats (enrolled_count < capacity)
  3. Education level must be sufficient (if program has a min requirement)

These are non-negotiable prerequisites — no score can override them.
"""

from config import education_rank


def check_eligibility(
    program: dict,
    beneficiary_education: str | None,
    beneficiary_experience_years: int | None,
) -> tuple[bool, str]:
    """
    Check if a beneficiary is eligible for a training program.
    
    Returns:
        (is_eligible, reason) — reason explains why they were rejected
    """
    # Gate 1: Program must be active
    if not program.get("is_active", False):
        return False, "Program is not active"

    # Gate 2: Seats must be available
    capacity = program.get("capacity")
    enrolled = program.get("enrolled_count", 0)
    if capacity and enrolled >= capacity:
        return False, "Program is full (no seats available)"

    # Gate 3: Education level check
    # Programs at NSQF 5+ typically require 10th pass minimum
    # Programs at NSQF 3-4 typically require 5th-8th pass
    program_nsqf = program.get("nsqf_level")
    if program_nsqf and beneficiary_education:
        ben_rank = education_rank(beneficiary_education)
        
        # Strict minimum education for higher NSQF levels
        if program_nsqf >= 5 and ben_rank < education_rank("8th_pass"):
            return False, f"NSQF level {program_nsqf} requires at least 8th pass education"
        
        if program_nsqf >= 7 and ben_rank < education_rank("12th_pass"):
            return False, f"NSQF level {program_nsqf} requires at least 12th pass education"

    # All gates passed
    return True, "Eligible"


def filter_eligible(
    candidates: list[dict],
    beneficiary_education: str | None,
    beneficiary_experience_years: int | None,
) -> tuple[list[dict], list[dict]]:
    """
    Filter candidates through eligibility gates.
    
    Returns:
        (eligible_programs, rejected_programs)
    """
    eligible = []
    rejected = []

    for program in candidates:
        is_eligible, reason = check_eligibility(
            program, beneficiary_education, beneficiary_experience_years
        )
        if is_eligible:
            eligible.append(program)
        else:
            rejected.append({**program, "rejection_reason": reason})

    return eligible, rejected
