"""
Stage 4 — Ranker & Diversity Filter
=====================================
Sorts scored programs in descending order and assigns each
to one of three diversity pathway tiers:

  1. BEST_MATCH    — Highest score, closest to current skills
  2. GROWTH_PATH   — Higher NSQF level, aligned with growth
  3. ALTERNATIVE   — Different sector, practical lateral pathway

This ensures the beneficiary gets varied, actionable options
instead of 3 programs from the same exact sector.
"""

from config import (
    PATHWAY_BEST_MATCH,
    PATHWAY_GROWTH,
    PATHWAY_ALTERNATIVE,
    TOP_N_RESULTS,
    MIN_SCORE_THRESHOLD,
)


def rank_and_diversify(
    scored_programs: list[dict],
    beneficiary_nsqf_level: int | None,
    beneficiary_sectors: list[str],
) -> list[dict]:
    """
    Sort by score, then assign diversity tiers.
    Returns at most TOP_N_RESULTS programs.
    """
    # Filter out programs below minimum threshold
    viable = [p for p in scored_programs if p["match_score"] >= MIN_SCORE_THRESHOLD]

    # Sort by score descending
    viable.sort(key=lambda p: p["match_score"], reverse=True)

    if not viable:
        return []

    ben_sectors = {s.lower() for s in beneficiary_sectors}
    ben_nsqf = beneficiary_nsqf_level or 0

    result = []
    used_sectors = set()
    assigned_types = set()

    for program in viable:
        if len(result) >= TOP_N_RESULTS:
            break

        prog_sector = (program.get("sector") or "").lower()
        prog_nsqf = program.get("nsqf_level") or 0

        # Determine pathway type
        if PATHWAY_BEST_MATCH not in assigned_types:
            # First slot always goes to the highest scorer
            pathway = PATHWAY_BEST_MATCH
        elif PATHWAY_GROWTH not in assigned_types:
            # Second slot: prefer a program with higher NSQF level
            if prog_nsqf > ben_nsqf:
                pathway = PATHWAY_GROWTH
            elif prog_sector not in used_sectors:
                pathway = PATHWAY_ALTERNATIVE
            else:
                pathway = PATHWAY_GROWTH  # fallback
        elif PATHWAY_ALTERNATIVE not in assigned_types:
            # Third slot: prefer a different sector
            if prog_sector not in used_sectors:
                pathway = PATHWAY_ALTERNATIVE
            else:
                pathway = PATHWAY_ALTERNATIVE  # assign anyway
        else:
            # All three types assigned, just fill remaining slots
            pathway = PATHWAY_BEST_MATCH

        program["pathway_type"] = pathway
        program["rank"] = len(result) + 1
        assigned_types.add(pathway)
        used_sectors.add(prog_sector)
        result.append(program)

    # If we couldn't fill all 3 from the diversity logic, fill from the rest
    if len(result) < TOP_N_RESULTS:
        for program in viable:
            if len(result) >= TOP_N_RESULTS:
                break
            pid = str(program.get("id", ""))
            if pid not in {str(r.get("id", "")) for r in result}:
                # Assign whichever type is still missing
                for ptype in [PATHWAY_BEST_MATCH, PATHWAY_GROWTH, PATHWAY_ALTERNATIVE]:
                    if ptype not in assigned_types:
                        program["pathway_type"] = ptype
                        assigned_types.add(ptype)
                        break
                else:
                    program["pathway_type"] = PATHWAY_ALTERNATIVE

                program["rank"] = len(result) + 1
                result.append(program)

    return result
