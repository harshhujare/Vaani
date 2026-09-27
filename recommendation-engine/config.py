"""
Recommendation Engine — Configuration & Scoring Weights
========================================================
All tunable parameters live here so the jury can see
exactly how scores are calculated. No black-box decisions.
"""

# ══════════════════════════════════════════
# SCORING WEIGHTS (must sum to 1.0)
# ══════════════════════════════════════════

WEIGHTS = {
    "skill_compatibility": 0.30,   # Keyword overlap between user skills and program
    "nsqf_level_fit":      0.25,   # How well the NSQF levels align
    "location_match":      0.20,   # District / state proximity
    "capacity_available":  0.15,   # Seats remaining in the program
    "education_match":     0.10,   # Education level alignment
}

# ══════════════════════════════════════════
# EDUCATION HIERARCHY (ordinal ranking)
# ══════════════════════════════════════════
# Higher index = higher education level
EDUCATION_LEVELS = [
    "illiterate",
    "below_5th",
    "5th_pass",
    "8th_pass",
    "10th_pass",
    "12th_pass",
    "iti",
    "diploma",
    "graduate",
    "post_graduate",
]

def education_rank(level: str | None) -> int:
    """Return ordinal rank for an education level string."""
    if not level:
        return 0
    normalized = level.strip().lower().replace(" ", "_").replace("-", "_")
    try:
        return EDUCATION_LEVELS.index(normalized)
    except ValueError:
        # Fuzzy fallback — check if any keyword is contained
        for i, edu in enumerate(EDUCATION_LEVELS):
            if edu in normalized or normalized in edu:
                return i
        return 0

# ══════════════════════════════════════════
# NSQF LEVEL SCORING RULES
# ══════════════════════════════════════════
# program_level - beneficiary_level = delta
# Best fit: program is exactly 1 level above current

def nsqf_fit_score(beneficiary_level: int | None, program_level: int | None) -> float:
    """
    Score how well a program's NSQF level fits the beneficiary.
    Returns 0.0 – 1.0.
    """
    if not beneficiary_level or not program_level:
        return 0.5  # neutral if unknown

    delta = program_level - beneficiary_level

    if delta == 1:
        return 1.0    # ideal: one step up
    elif delta == 0:
        return 0.80   # same level — still valuable for certification
    elif delta == -1:
        return 0.50   # slightly below — review course, less growth
    elif delta == 2:
        return 0.60   # stretch — achievable with effort
    elif delta >= 3:
        return 0.20   # too high — likely to struggle
    else:
        return 0.30   # program is well below current level

# ══════════════════════════════════════════
# LOCATION SCORING
# ══════════════════════════════════════════

def location_score(ben_district: str | None, ben_state: str | None,
                   prog_district: str | None, prog_state: str | None) -> float:
    """
    Score proximity between beneficiary and training program.
    Returns 0.0 – 1.0.
    """
    if not ben_district or not prog_district:
        return 0.3  # unknown — neutral-low

    bd = ben_district.strip().lower()
    pd = prog_district.strip().lower()
    bs = (ben_state or "").strip().lower()
    ps = (prog_state or "").strip().lower()

    if bd == pd:
        return 1.0   # same district — ideal
    elif bs and ps and bs == ps:
        return 0.5   # same state, different district
    else:
        return 0.2   # different state

# ══════════════════════════════════════════
# CAPACITY SCORING
# ══════════════════════════════════════════

def capacity_score(capacity: int | None, enrolled_count: int | None) -> float:
    """
    Score based on remaining seats.
    Returns 0.0 – 1.0.
    """
    if not capacity or capacity <= 0:
        return 0.5  # unknown capacity

    enrolled = enrolled_count or 0
    fill_ratio = enrolled / capacity

    if fill_ratio < 0.50:
        return 1.0   # plenty of room
    elif fill_ratio < 0.80:
        return 0.6   # filling up
    elif fill_ratio < 1.0:
        return 0.2   # almost full
    else:
        return 0.0   # full — should be caught by eligibility gate

# ══════════════════════════════════════════
# DIVERSITY PATHWAY TYPES
# ══════════════════════════════════════════

PATHWAY_BEST_MATCH = "BEST_MATCH"
PATHWAY_GROWTH     = "GROWTH_PATH"
PATHWAY_ALTERNATIVE = "ALTERNATIVE"

# ══════════════════════════════════════════
# ENGINE LIMITS
# ══════════════════════════════════════════

MAX_CANDIDATES = 100       # max programs to pull from DB
TOP_N_RESULTS  = 3         # final recommendations to return
MIN_SCORE_THRESHOLD = 10   # minimum score to be considered
