"""
VaniSetu — Instant Scheme & Course Suggestion Tool
=================================================
Once a person enters/speaks their details (occupation, skills, education, location, assets, preference),
this tool queries the database of 50+ NSQF Courses and Government Schemes to produce
tailored, deterministic recommendations and plain-language explanations.

Usage:
  1. Interactive mode (prompts for details):
     python services/recommendation_engine/suggest.py

  2. Pre-filled sample run:
     python services/recommendation_engine/suggest.py --sample carpenter
     python services/recommendation_engine/suggest.py --sample tailor
     python services/recommendation_engine/suggest.py --sample solar

  3. Custom JSON profile:
     python services/recommendation_engine/suggest.py --json '{"name": "Ramesh", "skills": ["carpentry"], "education_level": "8th", "district": "Ranchi"}'
"""

from __future__ import annotations

import argparse
import json
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
from services.recommendation_engine.models.beneficiary import BeneficiaryProfile

SAMPLE_PERSONAS = {
    "carpenter": {
        "beneficiary_id": "PERSON_CARPENTER",
        "name": "Ramesh Kumar",
        "language": "hi",
        "district": "Ranchi",
        "state": "Jharkhand",
        "latitude": 23.3441,
        "longitude": 85.3096,
        "education_level": "8th",
        "experience_years": 4.0,
        "skills": ["लकड़ी का काम", "furniture assembly"],
        "interests": ["carpentry", "furniture making"],
        "assets": ["AST_CARP_BASIC"],
        "employment_preference": "self_employment",
    },
    "tailor": {
        "beneficiary_id": "PERSON_TAILOR",
        "name": "Meena Devi",
        "language": "mr",
        "district": "Sangli",
        "state": "Maharashtra",
        "latitude": 16.8524,
        "longitude": 74.5815,
        "education_level": "5th",
        "experience_years": 5.0,
        "skills": ["कपडे शिवणे", "stitching"],
        "interests": ["dress_designing", "garment_construction"],
        "assets": ["AST_SEW_BASIC"],
        "employment_preference": "self_employment",
    },
    "solar": {
        "beneficiary_id": "PERSON_SOLAR",
        "name": "Ravi Solanki",
        "language": "hi",
        "district": "Jaipur",
        "state": "Rajasthan",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "education_level": "10th",
        "experience_years": 1.5,
        "skills": ["solar panel fitting", "wiring"],
        "interests": ["renewable energy", "solar water pump"],
        "assets": ["AST_SOLAR_TOOLS"],
        "employment_preference": "both",
    },
    "electrician": {
        "beneficiary_id": "PERSON_ELEC",
        "name": "Dinesh Sharma",
        "language": "hi",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "education_level": "10th",
        "experience_years": 2.0,
        "skills": ["बिजली का काम", "wiring"],
        "interests": ["house wiring", "industrial electrical"],
        "assets": ["AST_ELEC_KIT"],
        "employment_preference": "self_employment",
    },
}


def print_suggestions(person: BeneficiaryProfile, response):
    print("\n" + "=" * 88)
    print("🎯 VANISETU RECOMMENDATIONS: COURSES & GOVERNMENT SCHEMES")
    print("=" * 88)
    print(f"👤 Person: {person.name or 'Beneficiary'} (Location: {person.district}, {person.state})")
    print(f"🎓 Education: {person.education_level.upper()} | Experience: {person.experience_years} years")
    print(f"🛠️ Possessed Skills: {', '.join(person.skills) if person.skills else 'None entered'}")
    print(f"💼 Work Preference: {person.employment_preference.value.replace('_', ' ').title()}")
    print("-" * 88)

    if not response.recommendations:
        print("\n⚠️ No matching courses found that satisfy minimum eligibility criteria.")
        return

    sorted_recs = sorted(response.recommendations, key=lambda r: r.final_score, reverse=True)
    for i, rec in enumerate(sorted_recs, 1):
        center_str = (
            f"{rec.training_center.name} ({rec.training_center.distance_km} km away, "
            f"{rec.training_center.seats_available} open seats)"
            if rec.training_center
            else "Nearest center being mapped"
        )

        print("━" * 88)
        print(f"📌 OPTION #{i}: [{rec.pathway_type.value}] {rec.qualification_title} (NSQF Level {rec.nsqf_level})")
        print(f"   • Overall Match Score: {rec.final_score:.1f} / 100")
        print(f"   • Nearest Training Center: {center_str}")

        # 3 Related Skills
        print(f"\n   📚 3 Related Competencies You Will Learn in this Course:")
        for s_idx, skill in enumerate(rec.related_skills[:3], 1):
            print(f"      {s_idx}. {skill}")

        # 3 Eligible Schemes
        print(f"\n   🏛️ 3 Eligible Government Welfare & Financial Schemes You Can Claim:")
        for sc_idx, scheme in enumerate(rec.eligible_schemes[:3], 1):
            grant_str = f" | Grant: {scheme.financial_grant}" if scheme.financial_grant else ""
            stipend_str = f" | Stipend: {scheme.stipend_details}" if scheme.stipend_details else ""
            loan_str = f" | Credit: {scheme.loan_subsidy}" if scheme.loan_subsidy else ""
            print(f"      {sc_idx}. {scheme.scheme_name}")
            print(f"         • Ministry: {scheme.ministry}")
            print(f"         • Benefits: {scheme.benefit_summary}{grant_str}{stipend_str}{loan_str}")

        # Explanation
        print(f"\n   💡 Plain-Language Rationale:")
        print(f"      \"{rec.explanation}\"\n")

    print("=" * 88)


def main():
    parser = argparse.ArgumentParser(description="Suggest Courses and Schemes for a Person")
    parser.add_argument("--sample", choices=["carpenter", "tailor", "solar", "electrician"], help="Run sample persona")
    parser.add_argument("--json", type=str, help="JSON string with person's data")
    args = parser.parse_args()

    engine = RecommendationEngine()

    if args.sample:
        data = SAMPLE_PERSONAS[args.sample]
        person = BeneficiaryProfile(**data)
    elif args.json:
        data = json.loads(args.json)
        data.setdefault("beneficiary_id", "PERSON_CLI")
        person = BeneficiaryProfile(**data)
    else:
        # Interactive Mode
        print("=" * 88)
        print("📋 VANISETU — ENTER PERSON DETAILS FOR SCHEME & COURSE SUGGESTIONS")
        print("=" * 88)
        name = input("Enter Name [Default: Person]: ").strip() or "Person"
        district = input("Enter District [Default: Ranchi]: ").strip() or "Ranchi"
        state = input("Enter State [Default: Jharkhand]: ").strip() or "Jharkhand"
        edu = input("Enter Education Level (none, 5th, 8th, 10th, 12th, iti) [Default: 8th]: ").strip() or "8th"
        exp = float(input("Enter Experience in Years [Default: 2]: ").strip() or "2")
        skills_raw = input("Enter Skills (comma-separated, e.g. silai, stitching) [Default: लकड़ी का काम]: ").strip() or "लकड़ी का काम"
        pref = input("Enter Employment Preference (self_employment / wage_employment / both) [Default: self_employment]: ").strip() or "self_employment"

        person = BeneficiaryProfile(
            beneficiary_id="PERSON_INPUT",
            name=name,
            district=district,
            state=state,
            education_level=edu,
            experience_years=exp,
            skills=[s.strip() for s in skills_raw.split(",") if s.strip()],
            employment_preference=pref,
        )

    print("\n[*] Querying database of 50+ NSQF Courses and Government Schemes...")
    response = engine.recommend_sync(person)
    print_suggestions(person, response)


if __name__ == "__main__":
    main()
