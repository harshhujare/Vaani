"""
Stage 1 — Candidate Retriever
==============================
Fetches candidate training programs from the database.
Uses a dual-funnel approach:
  1. Sector match: programs in the same sector as beneficiary skills
  2. Broad fallback: active programs in the same state/district

Returns a candidate pool of up to MAX_CANDIDATES programs.
"""

from database import get_connection
from config import MAX_CANDIDATES


async def retrieve_candidates(
    beneficiary_sectors: list[str],
    beneficiary_district: str | None,
    beneficiary_state: str | None,
) -> list[dict]:
    """
    Pull candidate programs from the database.
    
    Strategy:
    - First: fetch all active programs in matching sectors
    - Then: fetch remaining active programs in same district/state
    - Merge and deduplicate
    - Cap at MAX_CANDIDATES
    """
    async with get_connection() as conn:
        candidates = {}

        # ── Funnel 1: Sector-matched programs ──
        if beneficiary_sectors:
            sectors_lower = [s.lower() for s in beneficiary_sectors]
            # Use ANY() for IN-clause with psycopg
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        id, name, sector, sub_sector, nsqf_level,
                        duration_days, district, state, training_center,
                        provider, capacity, enrolled_count, start_date,
                        end_date, is_active, certification, scheme
                    FROM training_programs
                    WHERE is_active = true
                      AND LOWER(sector) = ANY(%s)
                    ORDER BY name
                    LIMIT %s
                    """,
                    (sectors_lower, MAX_CANDIDATES),
                )
                rows = await cur.fetchall()
                for row in rows:
                    candidates[str(row["id"])] = dict(row)

        # ── Funnel 2: Location-based fallback ──
        conditions = []
        params = []

        if beneficiary_district:
            conditions.append("LOWER(district) = %s")
            params.append(beneficiary_district.lower())

        if beneficiary_state:
            conditions.append("LOWER(state) = %s")
            params.append(beneficiary_state.lower())

        if conditions:
            location_filter = " OR ".join(conditions)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT
                        id, name, sector, sub_sector, nsqf_level,
                        duration_days, district, state, training_center,
                        provider, capacity, enrolled_count, start_date,
                        end_date, is_active, certification, scheme
                    FROM training_programs
                    WHERE is_active = true
                      AND ({location_filter})
                    ORDER BY name
                    LIMIT %s
                    """,
                    (*params, MAX_CANDIDATES),
                )
                rows = await cur.fetchall()
                for row in rows:
                    pid = str(row["id"])
                    if pid not in candidates:
                        candidates[pid] = dict(row)

        # ── Funnel 3: If still under threshold, grab any active program ──
        if len(candidates) < 5:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        id, name, sector, sub_sector, nsqf_level,
                        duration_days, district, state, training_center,
                        provider, capacity, enrolled_count, start_date,
                        end_date, is_active, certification, scheme
                    FROM training_programs
                    WHERE is_active = true
                    ORDER BY name
                    LIMIT %s
                    """,
                    (MAX_CANDIDATES,),
                )
                rows = await cur.fetchall()
                for row in rows:
                    pid = str(row["id"])
                    if pid not in candidates:
                        candidates[pid] = dict(row)

        # Return as list, capped
        result = list(candidates.values())[:MAX_CANDIDATES]
        return result
