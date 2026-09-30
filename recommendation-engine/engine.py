"""
Recommendation Engine — Pipeline Orchestrator
===============================================
Executes all stages in sequence:

  1. Fetch beneficiary profile + skills from DB
  2. Retrieve candidate training programs
  3. Apply hard eligibility gates
  4. Score each eligible program (100-point model)
  5. Rank and apply diversity filter
  6. Analyze skill gaps for top picks
  7. Generate explanations

Returns a fully formed RecommendationResponse.
"""

from database import get_connection
from models import (
    BeneficiaryProfile,
    Recommendation,
    RecommendationResponse,
    NearestCenter,
)
from pipeline.retriever import retrieve_candidates
from pipeline.eligibility import filter_eligible
from pipeline.scorer import score_all
from pipeline.ranker import rank_and_diversify
from pipeline.gap_analyzer import analyze_skill_gaps
from pipeline.explainer import generate_explanation


async def fetch_beneficiary(beneficiary_id: str) -> BeneficiaryProfile | None:
    """Fetch a beneficiary and their skills from the database."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            # Get beneficiary record
            await cur.execute(
                """
                SELECT id, name, phone, district, state,
                       education_level, language
                FROM beneficiaries
                WHERE id = %s
                """,
                (beneficiary_id,),
            )
            row = await cur.fetchone()

            if not row:
                return None

            # Get their skills
            await cur.execute(
                """
                SELECT skill_name, sector, sub_sector, experience_years,
                       is_primary, nsqf_level, confidence_score, sub_skills
                FROM beneficiary_skills
                WHERE beneficiary_id = %s
                ORDER BY is_primary DESC, experience_years DESC
                """,
                (beneficiary_id,),
            )
            skill_rows = await cur.fetchall()

        skills = [dict(sr) for sr in skill_rows]

        return BeneficiaryProfile(
            id=str(row["id"]),
            name=row["name"],
            phone=row.get("phone"),
            district=row.get("district"),
            state=row.get("state"),
            education_level=row.get("education_level"),
            language=row.get("language"),
            skills=skills,
        )


async def run_recommendation(beneficiary_id: str) -> RecommendationResponse:
    """
    Execute the full recommendation pipeline for a beneficiary.
    
    Raises ValueError if beneficiary not found.
    """
    # ── Stage 0: Fetch beneficiary profile ──
    profile = await fetch_beneficiary(beneficiary_id)
    if not profile:
        raise ValueError(f"Beneficiary '{beneficiary_id}' not found")

    # Extract key attributes
    ben_sectors = list({
        s.get("sector") for s in profile.skills
        if s.get("sector")
    })
    ben_nsqf = max(
        (s.get("nsqf_level") or 0 for s in profile.skills),
        default=0,
    ) or None
    ben_experience = max(
        (s.get("experience_years") or 0 for s in profile.skills),
        default=0,
    )

    # ── Stage 1: Retrieve candidate programs ──
    candidates = await retrieve_candidates(
        beneficiary_sectors=ben_sectors,
        beneficiary_district=profile.district,
        beneficiary_state=profile.state,
    )
    total_candidates = len(candidates)

    # ── Stage 2: Apply eligibility gates ──
    eligible, rejected = filter_eligible(
        candidates=candidates,
        beneficiary_education=profile.education_level,
        beneficiary_experience_years=ben_experience,
    )
    eligible_count = len(eligible)

    # ── Stage 3: Score eligible programs ──
    scored = score_all(
        eligible_programs=eligible,
        beneficiary_skills=profile.skills,
        beneficiary_education=profile.education_level,
        beneficiary_nsqf_level=ben_nsqf,
        beneficiary_district=profile.district,
        beneficiary_state=profile.state,
    )

    # ── Stage 4: Rank and apply diversity filter ──
    ranked = rank_and_diversify(
        scored_programs=scored,
        beneficiary_nsqf_level=ben_nsqf,
        beneficiary_sectors=ben_sectors,
    )

    # ── Stage 5 & 6: Skill gaps + Explanations ──
    recommendations = []
    for program in ranked:
        # Analyze skill gaps
        strengths, gaps = await analyze_skill_gaps(
            program=program,
            beneficiary_skills=profile.skills,
        )

        # Generate explanation
        explanation = generate_explanation(
            program=program,
            matched_skills=program.get("matched_skills", []),
            skill_gaps=gaps,
            pathway_type=program.get("pathway_type", "BEST_MATCH"),
            match_score=program.get("match_score", 0),
            beneficiary_name=profile.name,
        )

        # Build recommendation object
        capacity = program.get("capacity") or 0
        enrolled = program.get("enrolled_count") or 0

        rec = Recommendation(
            rank=program["rank"],
            pathway_type=program["pathway_type"],
            program_id=str(program["id"]),
            program_name=program.get("name", ""),
            sector=program.get("sector"),
            sub_sector=program.get("sub_sector"),
            nsqf_level=program.get("nsqf_level"),
            duration_days=program.get("duration_days"),
            provider=program.get("provider"),
            certification=program.get("certification"),
            match_score=program["match_score"],
            score_breakdown=program["score_breakdown"],
            matched_skills=program.get("matched_skills", []),
            skill_gaps=gaps,
            nearest_center=NearestCenter(
                training_center=program.get("training_center", "N/A"),
                district=program.get("district", "N/A"),
                state=program.get("state", "N/A"),
                seats_available=max(0, capacity - enrolled),
            ),
            explanation_text=explanation,
        )
        recommendations.append(rec)

    return RecommendationResponse(
        beneficiary_id=profile.id,
        beneficiary_name=profile.name,
        total_candidates_evaluated=total_candidates,
        eligible_candidates=eligible_count,
        recommendations=recommendations,
        message=(
            f"Generated {len(recommendations)} recommendations from "
            f"{eligible_count} eligible programs (out of {total_candidates} evaluated)"
        ),
    )
