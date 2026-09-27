r"""
Stage 5 — Skill Gap Analyzer
==============================
Performs mathematical set subtraction to identify:

  Skill Gaps = Required Competencies \ Possessed Competencies

This tells the beneficiary exactly what they need to learn
in the recommended training program.
"""

from database import get_connection


async def analyze_skill_gaps(
    program: dict,
    beneficiary_skills: list[dict],
) -> tuple[list[str], list[str]]:
    """
    Determine what skills the beneficiary has vs. what the program requires.
    
    Since training_programs don't have explicit competency lists in the current schema,
    we infer required skills from:
      1. The nsqf_taxonomy table (keywords for the program's sector/sub_sector)
      2. The program name itself
    
    Returns:
        (strengths, gaps) — skills possessed and skills to learn
    """
    # Collect beneficiary's skill keywords
    ben_skill_names = set()
    ben_sub_skills = set()
    for skill in beneficiary_skills:
        name = (skill.get("skill_name") or "").lower()
        ben_skill_names.add(name)
        # Add individual words as tokens
        for word in name.split():
            if len(word) > 2:
                ben_sub_skills.add(word)
        # Add sub-skills if present
        sub_skills = skill.get("sub_skills") or []
        if isinstance(sub_skills, list):
            for ss in sub_skills:
                if isinstance(ss, str):
                    ben_sub_skills.add(ss.lower().replace("_", " "))

    # Fetch required competencies from taxonomy
    program_sector = program.get("sector") or ""
    program_sub = program.get("sub_sector") or ""
    required_keywords = set()

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT skill_name, keywords, description
                FROM nsqf_taxonomy
                WHERE LOWER(sector) = %s
                   OR LOWER(sub_sector) = %s
                """,
                (program_sector.lower(), program_sub.lower()),
            )
            rows = await cur.fetchall()

            for row in rows:
                # Add skill names from taxonomy
                skill_name = (row.get("skill_name") or "").lower()
                required_keywords.add(skill_name)
                # Add individual keywords
                keywords = row.get("keywords") or []
                if isinstance(keywords, list):
                    for kw in keywords:
                        if isinstance(kw, str) and len(kw) > 2:
                            required_keywords.add(kw.lower())
                # Add description words
                desc = row.get("description") or ""
                for word in desc.lower().split(", "):
                    word = word.strip()
                    if len(word) > 3 and word not in {"and", "the", "for", "with", "from", "basic"}:
                        required_keywords.add(word)

    # Also extract keywords from program name
    prog_name = (program.get("name") or "").lower()
    for word in prog_name.split():
        if len(word) > 3 and word not in {"and", "the", "for", "with", "from", "training"}:
            required_keywords.add(word)

    # Set operations
    all_ben_tokens = ben_skill_names | ben_sub_skills

    strengths = []
    gaps = []

    for req in required_keywords:
        req_lower = req.lower()
        # Check if the beneficiary possesses this competency
        matched = any(
            req_lower in token or token in req_lower
            for token in all_ben_tokens
        )
        if matched:
            strengths.append(req.title())
        else:
            gaps.append(req.title())

    # Deduplicate and cap
    strengths = list(dict.fromkeys(strengths))[:10]
    gaps = list(dict.fromkeys(gaps))[:10]

    return strengths, gaps
