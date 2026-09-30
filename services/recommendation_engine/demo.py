"""
Demonstration Script — Dynamic Recommendations for Courses & PM-AJAY Yojana Schemes
====================================================================================
1. Verifies that the SQLite database (data/vanisetu.db) contains ZERO person records
   and stores strictly NSQF Courses, Government Schemes under PM-AJAY Yojana,
   Skills, and Training Centers.
2. Demonstrates that when a living person provides their real-time profile
   (trade, skills, experience, education, district, preference), the engine
   evaluates the master database and recommends the BEST 3 Courses and PM-AJAY Schemes.

Run with:
  python services/recommendation_engine/demo.py
"""

from __future__ import annotations

import io
import json
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# UTF-8 terminal safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.recommendation_engine.engine import RecommendationEngine


def verify_database():
    """Verify that the SQLite database has ZERO person data."""
    db_path = Path(__file__).resolve().parent / "data" / "vanisetu.db"
    print("=" * 88)
    print("🔍 STEP 1: DATABASE INTEGRITY VERIFICATION (vanisetu.db)")
    print("=" * 88)

    if not db_path.exists():
        print(f"[!] Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"[*] Found {len(tables)} Master Tables in Database: {', '.join(tables)}")

    # Check for any person / beneficiary tables
    person_tables = [t for t in tables if any(kw in t.lower() for kw in ["person", "beneficiar", "user"])]
    if person_tables:
        print(f"[!] Warning: Person tables found: {person_tables}")
    else:
        print("[✓] CONFIRMED: Database contains ZERO person/beneficiary tables.")

    # Table breakdown
    for t in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        if t == "courses":
            print(f"    • {t}: {count} NSQF Courses registered under PM-AJAY trade sectors")
        elif t == "schemes":
            print(f"    • {t}: {count} Government Schemes under PM-AJAY Yojana & official convergences")
        elif t == "skills":
            print(f"    • {t}: {count} Canonical Skills in the multilingual skill taxonomy")
        elif t == "training_centers":
            print(f"    • {t}: {count} Accredited PM-AJAY / NSDC Training Centers")
        elif t == "batches":
            print(f"    • {t}: {count} Scheduled Training Batches with live seat counts")
        else:
            print(f"    • {t}: {count} rows")

    conn.close()
    print("-" * 88)


def main():
    verify_database()

    engine = RecommendationEngine()

    print("\n" + "=" * 88)
    print("🧠 STEP 2: DYNAMIC ON-THE-FLY RECOMMENDATIONS FOR LIVING PERSONS")
    print("=" * 88)
    print("Rule: Person enters data at runtime -> Engine evaluates DB -> Recommends Top 3 Courses & Schemes\n")

    test_persons = [
        {
            "name": "Ramesh Kumar",
            "occupation": "carpenter",
            "experience_years": 4.0,
            "education_level": "8th",
            "district": "Ranchi",
            "state": "Jharkhand",
            "skills": ["लकड़ी का काम", "furniture assembly"],
            "employment_preference": "self_employment",
            "assets": ["AST_CARP_BASIC"],
            "caste_category": "SC",
        },
        {
            "name": "Meena Devi",
            "occupation": "tailor",
            "experience_years": 5.0,
            "education_level": "5th",
            "district": "Sangli",
            "state": "Maharashtra",
            "skills": ["कपडे शिवणे", "stitching"],
            "employment_preference": "self_employment",
            "assets": ["AST_SEW_BASIC"],
            "caste_category": "SC",
        },
        {
            "name": "Akash Gaikwad",
            "occupation": "two wheeler mechanic",
            "experience_years": 2.0,
            "education_level": "8th",
            "district": "Pune",
            "state": "Maharashtra",
            "skills": ["bike repair", "मोटरसाइकिल मरम्मत"],
            "employment_preference": "self_employment",
            "assets": ["AST_AUTO_KIT"],
            "caste_category": "SC",
        },
    ]

    for p_idx, person in enumerate(test_persons, 1):
        print("━" * 88)
        print(f"👤 PERSON #{p_idx} ENTERS DATA:")
        print(f"   Name: {person['name']} | District: {person['district']}, {person['state']}")
        print(f"   Trade/Skills: {', '.join(person['skills'])} | Experience: {person['experience_years']} yrs")
        print(f"   Education: {person['education_level'].upper()} | Preference: {person['employment_preference']}")
        print("━" * 88)

        # Call engine.recommend_for_person
        result = engine.recommend_for_person(person)

        print(f"🎯 TOP 3 RECOMMENDED NSQF COURSES & PM-AJAY YOJANA SCHEMES:\n")

        for rec in result["recommendations"]:
            rank = rec["rank"]
            pathway = rec["pathway_type"]
            course = rec["course"]
            scheme = rec["pm_ajay_scheme"]
            center = rec["training_center"]

            print(f"  [{rank}] {pathway} — {course['title']} (NSQF Level {course['nsqf_level']})")
            print(f"      • Match Score: {rec['match_score']:.1f}/100")
            if scheme:
                print(f"      • PM-AJAY Yojana Scheme: {scheme['scheme_name']}")
                print(f"        - Financial Grant: {scheme['financial_grant']}")
                print(f"        - Stipend / Hostel: {scheme['stipend']}")
                if scheme.get("loan_subsidy"):
                    print(f"        - Credit / Margin Subsidy: {scheme['loan_subsidy']}")
            print(f"      • 3 Related Skills Learned: {', '.join(rec['related_skills'][:3])}")
            if center:
                print(f"      • Nearest Center: {center['center_name']} ({center['distance_km']} km away, {center['seats_available']} seats open, starts {center['next_batch_date']})")
            print(f"      • Rationale: \"{rec['explanation']}\"\n")


if __name__ == "__main__":
    main()

