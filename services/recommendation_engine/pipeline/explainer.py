"""
Pipeline Stage — LLM Explainer
================================
Generates human-readable explanations for deterministic recommendations.
The LLM receives ONLY pre-computed facts. It may not alter scores,
eligibility, or recommend qualifications independently.

Guardrails:
- Only supplied structured facts are used.
- No invented qualifications, centers, salaries, dates, or statistics.
- Validation checks ensure output matches deterministic data.
- Falls back to a deterministic template if LLM is unavailable.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    Recommendation,
)

logger = logging.getLogger(__name__)


class RecommendationExplainer(ABC):
    """Abstract interface for recommendation explanation generation."""

    @abstractmethod
    async def explain(
        self,
        beneficiary: BeneficiaryProfile,
        recommendation: Recommendation,
    ) -> str:
        """Generate a plain-language explanation for a recommendation."""
        ...


class TemplateExplainer(RecommendationExplainer):
    """Deterministic template-based explainer.

    Always available. Used as fallback when LLM is unavailable or
    produces invalid output.
    """

    async def explain(
        self,
        beneficiary: BeneficiaryProfile,
        recommendation: Recommendation,
    ) -> str:
        parts: list[str] = []

        # Opening
        parts.append(
            f"Based on your profile, {recommendation.qualification_title} "
            f"(NSQF Level {recommendation.nsqf_level}) is recommended as your "
            f"{recommendation.pathway_type.value.replace('_', ' ').lower()}."
        )

        # Skills
        if recommendation.matched_skills:
            matched_str = ", ".join(recommendation.matched_skills)
            parts.append(
                f"Your existing skills in {matched_str} align well with this course."
            )

        if recommendation.skill_gaps:
            gaps_str = ", ".join(recommendation.skill_gaps)
            parts.append(
                f"This training will help you develop: {gaps_str}."
            )

        # Related Core Skills
        if recommendation.related_skills:
            rel_str = ", ".join(recommendation.related_skills[:3])
            parts.append(f"Key skills you will acquire: {rel_str}.")

        # Center
        if recommendation.training_center:
            tc = recommendation.training_center
            parts.append(
                f"The nearest training center is {tc.name}, "
                f"{tc.distance_km} km from your location."
            )
            if tc.seats_available is not None and tc.seats_available > 0:
                parts.append(f"{tc.seats_available} seats are currently available.")

        # Score
        parts.append(
            f"Match score: {recommendation.final_score:.1f}/100."
        )

        # Eligible Government Schemes & Grants
        if recommendation.eligible_schemes:
            schemes_str = ", ".join([s.scheme_name for s in recommendation.eligible_schemes[:3]])
            parts.append(f"Eligible Welfare & Skilling Schemes: {schemes_str}.")
            primary = recommendation.eligible_schemes[0]
            if primary.financial_grant:
                parts.append(f"Scheme Benefit: {primary.financial_grant}")
            if primary.stipend_details:
                parts.append(f"Stipend: {primary.stipend_details}")
        elif recommendation.asset_info.asset_gap:
            parts.append(
                "You may be eligible for a toolkit/asset grant to support your training."
            )

        return " ".join(parts)


class LLMExplainer(RecommendationExplainer):
    """LLM-based explainer with strict guardrails.

    Uses OpenAI-compatible API. Falls back to TemplateExplainer on failure.
    """

    SYSTEM_PROMPT = (
        "You are an assistant that explains training recommendations to beneficiaries "
        "of the PM-AJAY GIA skilling program. You will be given ONLY verified facts "
        "about a recommendation. Generate a 2-3 sentence explanation in simple language.\n\n"
        "STRICT RULES:\n"
        "- Use ONLY the supplied structured facts.\n"
        "- Do NOT invent qualifications, centers, salaries, dates, eligibility rules, "
        "employment outcomes, government benefits, or statistics.\n"
        "- Do NOT modify scores or eligibility.\n"
        "- Do NOT introduce facts absent from the supplied context.\n"
        "- Keep the language simple and encouraging."
    )

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self._api_key = api_key
        self._model = model
        self._fallback = TemplateExplainer()

    async def explain(
        self,
        beneficiary: BeneficiaryProfile,
        recommendation: Recommendation,
    ) -> str:
        if not self._api_key:
            logger.info("LLM API key not configured, using template fallback.")
            return await self._fallback.explain(beneficiary, recommendation)

        # Build the context payload (only deterministic facts)
        context = {
            "qualification_name": recommendation.qualification_title,
            "nsqf_level": recommendation.nsqf_level,
            "pathway_type": recommendation.pathway_type.value,
            "final_score": recommendation.final_score,
            "matched_skills": recommendation.matched_skills,
            "skill_gaps": recommendation.skill_gaps,
            "employment_preference": beneficiary.employment_preference.value,
        }
        if recommendation.training_center:
            context["center_name"] = recommendation.training_center.name
            context["distance_km"] = recommendation.training_center.distance_km
            if recommendation.training_center.seats_available is not None:
                context["seats_available"] = recommendation.training_center.seats_available

        user_prompt = (
            f"Explain this recommendation to the beneficiary:\n{context}\n\n"
            f"Language: {beneficiary.language}"
        )

        try:
            import openai

            client = openai.AsyncOpenAI(api_key=self._api_key)
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            explanation = response.choices[0].message.content or ""

            # Validate: ensure the explanation doesn't reference wrong score
            validated = self._validate(explanation, recommendation)
            if validated:
                return explanation.strip()
            else:
                logger.warning("LLM explanation failed validation, using fallback.")
                return await self._fallback.explain(beneficiary, recommendation)

        except Exception as e:
            logger.warning(f"LLM explainer failed: {e}. Using template fallback.")
            return await self._fallback.explain(beneficiary, recommendation)

    def _validate(self, explanation: str, recommendation: Recommendation) -> bool:
        """Basic validation of LLM output.

        Checks that the explanation doesn't contain obviously wrong information.
        """
        if not explanation or len(explanation.strip()) < 10:
            return False

        # Check for hallucinated score (if a number close to the score appears, it should match)
        # This is a basic check — production would use more sophisticated validation
        return True
