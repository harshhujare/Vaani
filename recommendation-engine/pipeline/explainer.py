"""
Stage 6 — Explanation Generator
================================
Generates a plain-language explanation for each recommendation.
This is a DETERMINISTIC template-based generator — no LLM calls.

For the hackathon prototype, we use templates instead of an LLM.
This keeps the engine fully auditable and avoids hallucination risks.
In production, this stage would call a guardrailed LLM with
strict context injection (as per the spec).
"""


def generate_explanation(
    program: dict,
    matched_skills: list[str],
    skill_gaps: list[str],
    pathway_type: str,
    match_score: float,
    beneficiary_name: str | None = None,
) -> str:
    """
    Generate a human-readable explanation for why this program was recommended.
    """
    name = beneficiary_name or "the beneficiary"
    prog_name = program.get("name", "this program")
    sector = program.get("sector", "")
    nsqf = program.get("nsqf_level", "")
    district = program.get("district", "")
    duration = program.get("duration_days", "")
    certification = program.get("certification", "")
    provider = program.get("provider", "")

    # Build skill context
    if matched_skills:
        skill_text = f"Based on existing skills in {', '.join(matched_skills[:3])}"
    else:
        skill_text = "Based on the beneficiary's profile"

    # Build gap context
    if skill_gaps:
        gap_text = f"This training will build competencies in {', '.join(skill_gaps[:3])}"
    else:
        gap_text = "This training will reinforce and certify existing skills"

    # Pathway-specific framing
    if pathway_type == "BEST_MATCH":
        pathway_text = "this is the closest match to current experience"
    elif pathway_type == "GROWTH_PATH":
        pathway_text = "this offers upward mobility to a higher skill level"
    else:
        pathway_text = "this provides a practical alternative career pathway"

    # Duration and cert info
    details = []
    if duration:
        details.append(f"{duration}-day program")
    if district:
        details.append(f"in {district}")
    if certification:
        details.append(f"with {certification}")
    if provider:
        details.append(f"by {provider}")
    detail_text = ", ".join(details) if details else ""

    # Compose
    explanation = (
        f"{skill_text}, {pathway_text}. "
        f"{gap_text}. "
        f"{prog_name} is a {detail_text}."
    )

    return explanation.strip()
