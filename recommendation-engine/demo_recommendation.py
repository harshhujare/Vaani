"""
VaniSetu Recommendation Engine — Standalone Demo / Verification Script
========================================================================
Runs the full 6-stage recommendation pipeline on sample beneficiary
data (Ramesh Kumar from the seed script) to verify and demonstrate
all calculations, scoring breakdowns, diversity tiers, and explanations.

Usage:
    python demo_recommendation.py
"""

import sys
import json
from config import WEIGHTS
from pipeline.eligibility import filter_eligible
from pipeline.scorer import score_all
from pipeline.ranker import rank_and_diversify
from pipeline.explainer import generate_explanation

# Configure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_demo():
    print("=" * 65)
    print("   VaniSetu PM-AJAY GIA Recommendation Engine — Prototype Demo")
    print("   Deterministic, Auditable Multi-Factor Scoring Pipeline")
    print("=" * 65)

    # 1. Beneficiary Profile (Ramesh Kumar from seed.js)
    beneficiary = {
        "id": "b0000001-0000-0000-0000-000000000001",
        "name": "Ramesh Kumar",
        "district": "Ranchi",
        "state": "Jharkhand",
        "education_level": "8th_pass",
        "skills": [
            {
                "skill_name": "Carpentry - Furniture Making",
                "sector": "Construction",
                "sub_sector": "Woodwork",
                "experience_years": 15,
                "is_primary": True,
                "nsqf_level": 4,
            },
            {
                "skill_name": "Basic Plumbing Repair",
                "sector": "Construction",
                "sub_sector": "Plumbing",
                "experience_years": 3,
                "is_primary": False,
                "nsqf_level": 3,
            },
        ],
    }

    # 2. Available Training Programs (from seed.js)
    programs = [
        {
            "id": "p0000001-0000-0000-0000-000000000001",
            "name": "Advanced Carpentry & Furniture Design",
            "sector": "Construction",
            "sub_sector": "Carpentry",
            "nsqf_level": 5,
            "duration_days": 90,
            "district": "Ranchi",
            "state": "Jharkhand",
            "training_center": "PM-AJAY Skill Center, Ranchi",
            "provider": "National Skill Development Corporation",
            "capacity": 30,
            "enrolled_count": 10,
            "is_active": True,
            "certification": "NSQF Level 5 Certificate - Carpentry",
            "keywords": ["furniture", "lakdi", "wood", "carpenter", "finishing", "cnc", "cad"],
        },
        {
            "id": "p0000002-0000-0000-0000-000000000002",
            "name": "Organic Farming Techniques",
            "sector": "Agriculture",
            "sub_sector": "Organic Farming",
            "nsqf_level": 4,
            "duration_days": 45,
            "district": "Ranchi",
            "state": "Jharkhand",
            "training_center": "Krishi Vigyan Kendra, Ranchi",
            "provider": "Ministry of Agriculture",
            "capacity": 40,
            "enrolled_count": 15,
            "is_active": True,
            "certification": "NSQF Level 4 Certificate - Organic Farming",
            "keywords": ["organic", "kheti", "jaivik", "compost", "soil", "pest_control"],
        },
        {
            "id": "p0000003-0000-0000-0000-000000000003",
            "name": "Mobile Phone Repair Technician",
            "sector": "Electronics",
            "sub_sector": "Mobile Repair",
            "nsqf_level": 4,
            "duration_days": 60,
            "district": "Patna",
            "state": "Bihar",
            "training_center": "ITI Patna",
            "provider": "Samsung Electronics India",
            "capacity": 25,
            "enrolled_count": 8,
            "is_active": True,
            "certification": "NSQF Level 4 - Mobile Repair Technician",
            "keywords": ["mobile", "pcb", "soldering", "hardware", "diagnostics"],
        },
        {
            "id": "p0000004-0000-0000-0000-000000000004",
            "name": "Handloom Weaving - Advanced Patterns",
            "sector": "Textiles",
            "sub_sector": "Weaving",
            "nsqf_level": 5,
            "duration_days": 120,
            "district": "Varanasi",
            "state": "Uttar Pradesh",
            "training_center": "Weavers Service Centre, Varanasi",
            "provider": "Ministry of Textiles",
            "capacity": 20,
            "enrolled_count": 20,  # FULL!
            "is_active": True,
            "certification": "NSQF Level 5 - Handloom Weaving",
            "keywords": ["weaving", "bunai", "jacquard", "loom"],
        },
    ]

    print(f"\n[BENEFICIARY PROFILE]")
    print(f"  Name:       {beneficiary['name']}")
    print(f"  Location:   {beneficiary['district']}, {beneficiary['state']}")
    print(f"  Education:  {beneficiary['education_level']}")
    print(f"  Primary:    {beneficiary['skills'][0]['skill_name']} (NSQF {beneficiary['skills'][0]['nsqf_level']}, {beneficiary['skills'][0]['experience_years']} yrs exp)")
    print(f"  Secondary:  {beneficiary['skills'][1]['skill_name']} (NSQF {beneficiary['skills'][1]['nsqf_level']}, {beneficiary['skills'][1]['experience_years']} yrs exp)")

    # ── Stage 2: Eligibility Filtering ──
    print(f"\n[STAGE 2: HARD ELIGIBILITY GATES]")
    eligible, rejected = filter_eligible(
        candidates=programs,
        beneficiary_education=beneficiary["education_level"],
        beneficiary_experience_years=15,
    )
    print(f"  Total Candidates Evaluated: {len(programs)}")
    print(f"  Eligible Programs:          {len(eligible)}")
    for r in rejected:
        print(f"  [X] Rejected: '{r['name']}' -> Reason: {r['rejection_reason']}")

    # ── Stage 3: Multi-Factor Scoring ──
    print(f"\n[STAGE 3: 100-POINT HEURISTIC SCORER]")
    scored = score_all(
        eligible_programs=eligible,
        beneficiary_skills=beneficiary["skills"],
        beneficiary_education=beneficiary["education_level"],
        beneficiary_nsqf_level=4,
        beneficiary_district=beneficiary["district"],
        beneficiary_state=beneficiary["state"],
    )

    for p in scored:
        b = p["score_breakdown"]
        print(f"\n  Program: {p['name']} (NSQF {p['nsqf_level']}, {p['district']})")
        print(f"  Final Score: {p['match_score']}/100")
        print(f"    - Skill Compatibility (30% max): {b.skill_score} pts (Matched: {p['matched_skills']})")
        print(f"    - NSQF Level Fit      (25% max): {b.nsqf_score} pts")
        print(f"    - Location Match      (20% max): {b.location_score} pts")
        print(f"    - Capacity Available  (15% max): {b.capacity_score} pts")
        print(f"    - Education Match     (10% max): {b.education_score} pts")

    # ── Stage 4: Ranker & Diversity Filter ──
    print(f"\n[STAGE 4: DIVERSITY PATHWAY FILTERING]")
    ranked = rank_and_diversify(
        scored_programs=scored,
        beneficiary_nsqf_level=4,
        beneficiary_sectors=["Construction"],
    )

    print(f"\n{'Rank':<5} {'Pathway':<15} {'Score':<8} {'Program Name':<40} {'District'}")
    print("-" * 80)
    for r in ranked:
        print(f"#{r['rank']:<4} {r['pathway_type']:<15} {r['match_score']:<8} {r['name'][:38]:<40} {r['district']}")

    # ── Stage 5 & 6: Explanations & Output ──
    print(f"\n[STAGE 5 & 6: SKILL GAPS & AUDITABLE EXPLANATIONS]")
    for r in ranked:
        # Mock gap computation from keywords
        required_keywords = r.get("keywords", [])
        possessed = {"furniture", "lakdi", "wood", "carpenter", "finishing"} if r["sector"] == "Construction" else set()
        gaps = [k for k in required_keywords if k not in possessed]

        explanation = generate_explanation(
            program=r,
            matched_skills=r["matched_skills"],
            skill_gaps=gaps,
            pathway_type=r["pathway_type"],
            match_score=r["match_score"],
            beneficiary_name=beneficiary["name"],
        )

        print(f"\n--- Recommendation #{r['rank']} [{r['pathway_type']}] ---")
        print(f"Program: {r['name']}")
        print(f"Target Skill Gaps: {', '.join(gaps) if gaps else 'None (refinement)'}")
        print(f"Explanation: \"{explanation}\"")

    print("\n" + "=" * 65)
    print("  [SUCCESS] All pipeline stages executed deterministically!")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()
