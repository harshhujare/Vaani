"""
Unit tests for the Recommendation Engine pipeline.
Tests scoring, eligibility, ranking, and diversity logic without requiring a live DB.
"""

import unittest
from config import WEIGHTS, education_rank, nsqf_fit_score, location_score, capacity_score
from pipeline.eligibility import check_eligibility, filter_eligible
from pipeline.scorer import score_program, _skill_compatibility, _education_fit
from pipeline.ranker import rank_and_diversify
from pipeline.explainer import generate_explanation


class TestEligibility(unittest.TestCase):
    def test_inactive_program_rejected(self):
        program = {"is_active": False, "capacity": 30, "enrolled_count": 5}
        eligible, reason = check_eligibility(program, "10th_pass", 2)
        self.assertFalse(eligible)
        self.assertIn("not active", reason.lower())

    def test_full_capacity_program_rejected(self):
        program = {"is_active": True, "capacity": 30, "enrolled_count": 30}
        eligible, reason = check_eligibility(program, "10th_pass", 2)
        self.assertFalse(eligible)
        self.assertIn("full", reason.lower())

    def test_education_gate_high_nsqf(self):
        program = {"is_active": True, "capacity": 30, "enrolled_count": 10, "nsqf_level": 5}
        # Below 8th pass should fail for NSQF 5+
        eligible, reason = check_eligibility(program, "5th_pass", 1)
        self.assertFalse(eligible)
        self.assertIn("requires at least 8th pass", reason.lower())

        # 8th pass or above should pass
        eligible, reason = check_eligibility(program, "8th_pass", 1)
        self.assertTrue(eligible)


class TestScoring(unittest.TestCase):
    def test_weights_sum_to_one(self):
        total_weight = sum(WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=4)

    def test_nsqf_fit_scoring(self):
        # Delta +1 is optimal (growth)
        self.assertEqual(nsqf_fit_score(3, 4), 1.0)
        # Delta 0 has good certification value
        self.assertEqual(nsqf_fit_score(4, 4), 0.8)
        # Delta +2 is stretch
        self.assertEqual(nsqf_fit_score(2, 4), 0.6)
        # Delta -1 is backward step
        self.assertEqual(nsqf_fit_score(4, 3), 0.5)

    def test_location_scoring(self):
        self.assertEqual(location_score("Ranchi", "Jharkhand", "Ranchi", "Jharkhand"), 1.0)
        self.assertEqual(location_score("Dhanbad", "Jharkhand", "Ranchi", "Jharkhand"), 0.5)
        self.assertEqual(location_score("Patna", "Bihar", "Ranchi", "Jharkhand"), 0.2)

    def test_capacity_scoring(self):
        self.assertEqual(capacity_score(100, 20), 1.0)   # < 50%
        self.assertEqual(capacity_score(100, 60), 0.6)   # 50-80%
        self.assertEqual(capacity_score(100, 90), 0.2)   # > 80%
        self.assertEqual(capacity_score(100, 100), 0.0)  # full

    def test_score_program_breakdown(self):
        program = {
            "name": "Advanced Carpentry & Furniture Design",
            "sector": "Construction",
            "sub_sector": "Carpentry",
            "nsqf_level": 4,
            "district": "Ranchi",
            "state": "Jharkhand",
            "capacity": 30,
            "enrolled_count": 12,
        }
        skills = [
            {
                "skill_name": "Carpentry",
                "sector": "Construction",
                "sub_sector": "Carpentry",
                "is_primary": True,
                "nsqf_level": 3,
                "experience_years": 5,
            }
        ]

        total, breakdown, matched = score_program(
            program=program,
            beneficiary_skills=skills,
            beneficiary_education="8th_pass",
            beneficiary_nsqf_level=3,
            beneficiary_district="Ranchi",
            beneficiary_state="Jharkhand",
        )

        # Expected score: high match
        self.assertGreater(total, 75.0)
        self.assertIn("Carpentry", matched)
        self.assertAlmostEqual(
            total,
            round(
                breakdown.skill_score
                + breakdown.nsqf_score
                + breakdown.location_score
                + breakdown.capacity_score
                + breakdown.education_score,
                2,
            ),
        )


class TestRankingAndDiversity(unittest.TestCase):
    def test_three_tier_diversity(self):
        scored = [
            {
                "id": "p1",
                "name": "Advanced Carpentry",
                "sector": "Construction",
                "nsqf_level": 4,
                "match_score": 88.0,
            },
            {
                "id": "p2",
                "name": "Master Masonry & Construction Supervisor",
                "sector": "Construction",
                "nsqf_level": 5,
                "match_score": 82.0,
            },
            {
                "id": "p3",
                "name": "Solar PV Installer",
                "sector": "Green Energy",
                "nsqf_level": 4,
                "match_score": 75.0,
            },
        ]

        ranked = rank_and_diversify(
            scored_programs=scored,
            beneficiary_nsqf_level=3,
            beneficiary_sectors=["Construction"],
        )

        self.assertEqual(len(ranked), 3)
        # First slot should be BEST_MATCH
        self.assertEqual(ranked[0]["pathway_type"], "BEST_MATCH")
        # Second slot should be GROWTH_PATH (higher NSQF)
        self.assertEqual(ranked[1]["pathway_type"], "GROWTH_PATH")
        # Third slot should be ALTERNATIVE (different sector)
        self.assertEqual(ranked[2]["pathway_type"], "ALTERNATIVE")


class TestExplanationGenerator(unittest.TestCase):
    def test_explanation_contains_context(self):
        program = {
            "name": "Advanced Carpentry & Furniture Design",
            "sector": "Construction",
            "nsqf_level": 4,
            "district": "Ranchi",
            "duration_days": 45,
            "certification": "NSDC / Skill India",
            "provider": "Jharkhand Skill Mission",
        }
        explanation = generate_explanation(
            program=program,
            matched_skills=["Carpentry"],
            skill_gaps=["Blueprint Reading", "CNC Routing"],
            pathway_type="BEST_MATCH",
            match_score=85.0,
            beneficiary_name="Ramesh Kumar",
        )

        self.assertIn("Carpentry", explanation)
        self.assertIn("Blueprint Reading", explanation)
        self.assertIn("closest match", explanation)
        self.assertIn("45-day program", explanation)


if __name__ == "__main__":
    unittest.main()
