"""
Recommendation Engine — Master Orchestrator
=============================================
Coordinates all pipeline stages in the correct order.
This is the single entry point for generating recommendations.

Pipeline Order:
  1. Normalize skills
  2. Retrieve candidates (dual-funnel)
  3. Hard eligibility gate
  4. Score each eligible candidate (100-point)
  5. Compute skill gaps
  6. Find nearest training centers (Haversine)
  7. Apply diversity ranking
  8. Generate explanations
  9. Validate response
"""

from __future__ import annotations

import logging
import time
import uuid

from services.recommendation_engine.core.config import (
    RecommendationConfig,
    default_config,
)
from services.recommendation_engine.core.constants import (
    ENGINE_VERSION,
    SCORING_VERSION,
)
from services.recommendation_engine.models.types import (
    AuditMetadata,
    BeneficiaryProfile,
    EligibilityResult,
    EmploymentPreference,
    PathwayType,
    Recommendation,
    RecommendationResponse,
)
from services.recommendation_engine.pipeline.candidate_retriever import (
    CandidateRetriever,
)
from services.recommendation_engine.pipeline.diversity import DiversityRanker
from services.recommendation_engine.pipeline.eligibility import EligibilityGate
from services.recommendation_engine.pipeline.explainer import (
    RecommendationExplainer,
    TemplateExplainer,
)
from services.recommendation_engine.pipeline.geospatial import GeospatialMatcher
from services.recommendation_engine.pipeline.normalizer import SkillNormalizer
from services.recommendation_engine.pipeline.scheme_resolver import SchemeResolver
from services.recommendation_engine.pipeline.scoring import ScoringEngine
from services.recommendation_engine.pipeline.skill_gap import compute_skill_gap
from services.recommendation_engine.pipeline.validator import ResponseValidator
from services.recommendation_engine.repositories.batch_repository import (
    BatchRepository,
)
from services.recommendation_engine.repositories.center_repository import (
    CenterRepository,
)
from services.recommendation_engine.repositories.qualification_repository import (
    QualificationRepository,
)
from services.recommendation_engine.repositories.skill_repository import (
    SkillRepository,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Master orchestrator for the recommendation pipeline.

    Coordinates: normalization → retrieval → eligibility → scoring →
    skill gaps → geospatial → diversity → explanation → validation.
    """

    def __init__(
        self,
        config: RecommendationConfig | None = None,
        explainer: RecommendationExplainer | None = None,
        skill_repo: SkillRepository | None = None,
        qualification_repo: QualificationRepository | None = None,
        center_repo: CenterRepository | None = None,
        batch_repo: BatchRepository | None = None,
    ):
        self._config = config or default_config
        self._skill_repo = skill_repo or SkillRepository()
        self._qual_repo = qualification_repo or QualificationRepository()
        self._center_repo = center_repo or CenterRepository()
        self._batch_repo = batch_repo or BatchRepository()

        # Pipeline stages
        self._normalizer = SkillNormalizer(self._skill_repo)
        self._retriever = CandidateRetriever(
            self._qual_repo, self._skill_repo, self._config
        )
        self._eligibility = EligibilityGate(self._config)
        self._scorer = ScoringEngine(self._config)
        self._geo = GeospatialMatcher(self._center_repo, self._batch_repo)
        self._diversity = DiversityRanker(self._config)
        self._validator = ResponseValidator(self._qual_repo, self._center_repo)
        self._scheme_resolver = SchemeResolver(self._skill_repo)
        self._explainer = explainer or TemplateExplainer()

    def recommend_sync(
        self, beneficiary: BeneficiaryProfile
    ) -> RecommendationResponse:
        """Synchronously execute the full recommendation pipeline.

        Convenience wrapper around async recommend() that safely manages
        event loops in both synchronous scripts and existing asyncio contexts.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, self.recommend(beneficiary)).result()
        else:
            return asyncio.run(self.recommend(beneficiary))

    def recommend_for_person(
        self, person_data: dict | BeneficiaryProfile
    ) -> dict:
        """Recommend the best 3 NSQF courses and PM-AJAY Yojana schemes for a person.

        Accepts either a BeneficiaryProfile or a plain dictionary containing person data.
        Returns a clean, structured dictionary with the top 3 recommended packages.
        """
        if isinstance(person_data, BeneficiaryProfile):
            profile = person_data
        else:
            skills = list(person_data.get("skills", []))
            occupation = person_data.get("occupation") or person_data.get("trade") or ""
            if occupation and occupation not in skills:
                skills.append(occupation)

            emp_pref_str = str(person_data.get("employment_preference", "unknown")).lower().strip()
            try:
                emp_pref = EmploymentPreference(emp_pref_str)
            except ValueError:
                emp_pref = EmploymentPreference.UNKNOWN

            lat = person_data.get("latitude")
            lon = person_data.get("longitude")
            district = str(person_data.get("district", "")).strip()
            from services.recommendation_engine.pipeline.geospatial import DISTRICT_CENTERS
            if (lat is None or lon is None) and district.lower() in DISTRICT_CENTERS:
                lat, lon = DISTRICT_CENTERS[district.lower()]

            profile = BeneficiaryProfile(
                beneficiary_id=person_data.get("beneficiary_id") or f"PERSON_{uuid.uuid4().hex[:8].upper()}",
                name=person_data.get("name", "Applicant"),
                language=person_data.get("language", "hi"),
                district=district,
                state=person_data.get("state", ""),
                latitude=lat,
                longitude=lon,
                education_level=person_data.get("education_level", "none"),
                experience_years=float(person_data.get("experience_years", 0.0)),
                skills=skills,
                interests=person_data.get("interests", [occupation] if occupation else []),
                assets=person_data.get("assets", []),
                employment_preference=emp_pref,
            )

        response = self.recommend_sync(profile)

        # Build clean, high-level summary of top 3 courses and PM-AJAY schemes
        # Strictly sort recommendations by match score descending (Score 1 >= Score 2 >= Score 3)
        sorted_recs = sorted(response.recommendations, key=lambda r: r.final_score, reverse=True)
        recommendations_out = []
        for rank, rec in enumerate(sorted_recs[:3], start=1):
            primary_scheme = rec.eligible_schemes[0] if rec.eligible_schemes else None
            recommendations_out.append({
                "rank": rank,
                "pathway_type": rec.pathway_type.value,
                "course": {
                    "course_id": rec.qualification_id,
                    "title": rec.qualification_title,
                    "nsqf_level": rec.nsqf_level,
                },
                "pm_ajay_scheme": {
                    "scheme_name": primary_scheme.scheme_name if primary_scheme else "PM-AJAY: GIA Comprehensive Skilling Component",
                    "scheme_code": primary_scheme.scheme_code if primary_scheme else "SCHEME_PM_AJAY_GIA_SKILL",
                    "financial_grant": primary_scheme.financial_grant if primary_scheme else "100% Free NSQF Skilling + ₹50,000 Toolkit Grant",
                    "stipend": primary_scheme.stipend_details if primary_scheme else "₹1,500/month training conveyance allowance",
                    "loan_subsidy": primary_scheme.loan_subsidy if primary_scheme else "Special Central Assistance (SCA) Credit Subsidy Linkage",
                    "key_benefits": primary_scheme.benefit_summary if primary_scheme else "100% Free Course + Certificate + ₹50,000 Toolkit Grant",
                } if primary_scheme else None,
                "all_eligible_pm_ajay_schemes": [s.model_dump() for s in rec.eligible_schemes],
                "related_skills": rec.related_skills,
                "training_center": {
                    "center_name": rec.training_center.name if rec.training_center else "Accredited PM-AJAY Training Center / ITI",
                    "distance_km": rec.training_center.distance_km if rec.training_center else 0.0,
                    "seats_available": rec.training_center.seats_available if rec.training_center else None,
                    "next_batch_date": str(rec.training_center.next_batch_date) if rec.training_center and rec.training_center.next_batch_date else "Upcoming",
                } if rec.training_center else None,
                "match_score": rec.final_score,
                "explanation": rec.explanation,
            })

        return {
            "person": {
                "name": profile.name,
                "district": profile.district,
                "state": profile.state,
                "education": profile.education_level,
                "experience_years": profile.experience_years,
                "skills_input": profile.skills,
                "employment_preference": profile.employment_preference.value,
            },
            "recommendations_count": len(recommendations_out),
            "recommendations": recommendations_out,
            "decision_id": response.audit.decision_id if response.audit else None,
        }


    async def recommend_batch(
        self, beneficiaries: list[BeneficiaryProfile]
    ) -> list[RecommendationResponse]:
        """Concurrently execute the recommendation pipeline for multiple beneficiaries."""
        import asyncio

        tasks = [self.recommend(b) for b in beneficiaries]
        return await asyncio.gather(*tasks)

    def recommend_batch_sync(
        self, beneficiaries: list[BeneficiaryProfile]
    ) -> list[RecommendationResponse]:
        """Synchronously execute recommendations for a batch of beneficiaries."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    asyncio.run, self.recommend_batch(beneficiaries)
                ).result()
        else:
            return asyncio.run(self.recommend_batch(beneficiaries))

    async def recommend(
        self, beneficiary: BeneficiaryProfile
    ) -> RecommendationResponse:
        """Execute the full recommendation pipeline.

        This is the single entry point. Returns a validated,
        auditable RecommendationResponse.
        """
        start_time = time.time()
        decision_id = f"DEC_{uuid.uuid4().hex[:12].upper()}"

        logger.info(
            "Starting recommendation pipeline",
            extra={
                "decision_id": decision_id,
                "beneficiary_id": beneficiary.beneficiary_id,
            },
        )

        # ── Stage 1: Normalize skills ────────────────────────────
        # If the beneficiary's skills are raw strings, normalize them.
        # If they're already canonical IDs (from a prior extraction step),
        # the normalizer will resolve them via exact match.
        normalized_ids = self._normalizer.normalize_to_ids(beneficiary.skills)
        if normalized_ids:
            beneficiary = beneficiary.model_copy(
                update={"skills": normalized_ids}
            )

        logger.info(
            f"Normalized {len(beneficiary.skills)} skills: {beneficiary.skills}"
        )

        # ── Stage 2: Retrieve candidates ─────────────────────────
        candidates = self._retriever.retrieve(beneficiary)
        candidate_count = len(candidates)
        logger.info(f"Retrieved {candidate_count} candidate qualifications.")

        # ── Stage 3: Hard eligibility gate ────────────────────────
        eligible_pairs = self._eligibility.filter_eligible(
            beneficiary, candidates
        )
        eligible_count = len(eligible_pairs)
        logger.info(
            f"Eligibility gate: {eligible_count}/{candidate_count} eligible."
        )

        if not eligible_pairs:
            # No eligible candidates — return empty response
            duration_ms = (time.time() - start_time) * 1000
            return RecommendationResponse(
                beneficiary_id=beneficiary.beneficiary_id,
                engine_version=ENGINE_VERSION,
                recommendations=[],
                audit=AuditMetadata(
                    decision_id=decision_id,
                    engine_version=ENGINE_VERSION,
                    scoring_version=SCORING_VERSION,
                    candidate_count=candidate_count,
                    eligible_count=0,
                    selected_count=0,
                    retrieval_method="sql",
                    processing_duration_ms=round(duration_ms, 2),
                ),
            )

        # ── Stages 4-6: Score + skill gaps + geospatial ──────────
        scored_recommendations: list[Recommendation] = []

        for qualification, elig_result in eligible_pairs:
            # Find nearest center
            center_match = self._geo.find_nearest(
                beneficiary, qualification.qualification_id
            )

            # Find best batch
            batch = None
            if center_match and center_match.batch_id:
                # Batch info already populated by geospatial matcher
                batches = self._batch_repo.get_all_for_qualification(
                    qualification.qualification_id
                )
                batch = next(
                    (b for b in batches if b.batch_id == center_match.batch_id),
                    None,
                )

            # Score
            breakdown, matched_skills, missing_skills, asset_info = (
                self._scorer.score(
                    beneficiary, qualification, center_match, batch
                )
            )

            # Skill gap
            gap_result = compute_skill_gap(
                beneficiary.skills, qualification
            )

            # Determine GIA intervention
            gia_intervention = None
            if asset_info.asset_gap and asset_info.suggested_support:
                gia_intervention = f"SKILL_TRAINING_WITH_{asset_info.suggested_support}"

            # Resolve at least 3 related skills and at least 3 eligible government schemes
            related_skills = self._scheme_resolver.resolve_related_skills(qualification)
            eligible_schemes = self._scheme_resolver.resolve_eligible_schemes(
                beneficiary, qualification
            )

            rec = Recommendation(
                pathway_type=PathwayType.BEST_MATCH,  # placeholder, set by diversity ranker
                qualification_id=qualification.qualification_id,
                qualification_title=qualification.title,
                nsqf_level=qualification.nsqf_level,
                eligible=True,
                final_score=round(breakdown.total, 2),
                score_breakdown=breakdown,
                eligibility_result=elig_result,
                matched_skills=gap_result.matched_skills,
                skill_gaps=gap_result.skill_gaps,
                related_skills=related_skills,
                eligible_schemes=eligible_schemes,
                training_center=center_match,
                asset_info=asset_info,
                suggested_gia_intervention=gia_intervention,
            )
            scored_recommendations.append(rec)

        # ── Stage 7: Diversity ranking ────────────────────────────
        # Estimate beneficiary's current NSQF level from their skills/experience
        beneficiary_nsqf = self._estimate_nsqf_level(beneficiary)

        # Get sectors from beneficiary skills
        beneficiary_sectors: set[str] = set()
        for skill_id in beneficiary.skills:
            skill = self._skill_repo.get(skill_id)
            if skill:
                beneficiary_sectors.add(skill.sector)

        ranked = self._diversity.rank(
            scored_recommendations,
            beneficiary_nsqf,
            beneficiary_sectors,
        )

        # ── Stage 8: Generate explanations ────────────────────────
        for rec in ranked:
            try:
                explanation = await self._explainer.explain(beneficiary, rec)
                rec.explanation = explanation
            except Exception as e:
                logger.warning(f"Explanation generation failed: {e}")
                # Fallback is handled inside the explainer, but just in case:
                rec.explanation = (
                    f"{rec.qualification_title} (NSQF Level {rec.nsqf_level}) "
                    f"matches your profile with a score of {rec.final_score:.1f}/100."
                )

        # ── Stage 9: Validate response ────────────────────────────
        duration_ms = (time.time() - start_time) * 1000

        response = RecommendationResponse(
            beneficiary_id=beneficiary.beneficiary_id,
            engine_version=ENGINE_VERSION,
            recommendations=ranked,
            audit=AuditMetadata(
                decision_id=decision_id,
                engine_version=ENGINE_VERSION,
                scoring_version=SCORING_VERSION,
                candidate_count=candidate_count,
                eligible_count=eligible_count,
                selected_count=len(ranked),
                retrieval_method="sql",
                processing_duration_ms=round(duration_ms, 2),
                config_snapshot=self._config.model_dump(),
            ),
        )

        # Validate against source data
        validated_response = self._validator.validate(response)

        logger.info(
            "Recommendation pipeline complete",
            extra={
                "decision_id": decision_id,
                "beneficiary_id": beneficiary.beneficiary_id,
                "selected_count": len(ranked),
                "processing_ms": round(duration_ms, 2),
            },
        )

        return validated_response

    def _estimate_nsqf_level(self, beneficiary: BeneficiaryProfile) -> int:
        """Estimate the beneficiary's current NSQF level from experience.

        Simple heuristic:
          0-1 years  -> Level 1
          1-3 years  -> Level 2
          3-5 years  -> Level 3
          5-10 years -> Level 4
          10+ years  -> Level 5
        """
        exp = beneficiary.experience_years
        if exp >= 10:
            return 5
        elif exp >= 5:
            return 4
        elif exp >= 3:
            return 3
        elif exp >= 1:
            return 2
        return 1
