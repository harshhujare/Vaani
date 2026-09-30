"""
Pipeline Helper — Government Schemes & Related Skills Resolver
==============================================================
Maps beneficiary profile and recommended course to:
  1. At least 3 related core/adjacent skills taught in this pathway
  2. At least 3 eligible government welfare & skilling schemes:
     - PM-AJAY GIA (Grants-in-Aid for Skilling & Toolkit)
     - PM Vishwakarma Yojana (Traditional Artisans & Craftspeople)
     - PMKVY 4.0 (Skill India Short-Term Training)
     - PMMY Mudra Yojana (Collateral-Free Micro Enterprise Credit)
     - DDU-GKY (Rural Placement-Linked Skilling)
"""

from __future__ import annotations

from services.recommendation_engine.models.types import (
    BeneficiaryProfile,
    EmploymentPreference,
    Qualification,
    SchemeInfo,
)
from services.recommendation_engine.repositories.skill_repository import (
    SkillRepository,
)

# Standard sector fallbacks to ensure at least 3 rich related skills
SECTOR_RELATED_SKILLS: dict[str, list[str]] = {
    "Apparel": [
        "Pattern Drafting & Cutting",
        "Industrial Sewing Machine Operation",
        "Garment Alteration & Finishing",
        "Surface Embroidery & Zari Work",
        "Measurement & Quality Control",
    ],
    "Construction": [
        "Wood Joinery & Assembly",
        "Surface Polishing & Finishing",
        "Modular Furniture Installation",
        "Blueprint & Measurement Reading",
        "Workshop Tool Maintenance",
    ],
    "Automotive": [
        "Engine Overhaul & Tuning",
        "Auto Electrical & Battery Care",
        "Brake & Suspension Servicing",
        "Fuel Injection Diagnostics",
        "Workshop Safety & Tool Handling",
    ],
    "Healthcare": [
        "Patient Vital Signs Monitoring",
        "First Aid & Emergency Response",
        "Bedside Hygiene & Mobility Assistance",
        "Elderly & Geriatric Rehabilitation",
        "Medication Scheduling & Caregiving",
    ],
    "Renewable Energy": [
        "Rooftop Solar PV Mounting",
        "DC Wiring & Inverter Integration",
        "Solar Efficiency Testing & Cleaning",
        "Site Assessment & Shadow Analysis",
        "Safety Earthing & Grid Synchronization",
    ],
    "Electronics": [
        "PCB Micro-Soldering & Component Repair",
        "Display & Charging Port Replacement",
        "Appliance Circuit Diagnostics",
        "CCTV IP Configuration & Cabling",
        "Power Supply Troubleshooting",
    ],
    "Agriculture": [
        "Organic Composting & Bio-Pesticides",
        "Micro-Drip Irrigation Assembly",
        "Dairy Hygiene & Cattle Nutrition",
        "Soil Moisture Testing & Crop Rotation",
        "Post-Harvest Grading & Packaging",
    ],
    "Beauty": [
        "Professional Hair Styling & Cutting",
        "Therapeutic Skin Care & Facials",
        "Bridal Makeup & Draping Artistry",
        "Manicure, Pedicure & Sanitation",
        "Salon Client Consultation",
    ],
    "IT-ITeS": [
        "High-Speed Data Entry & Verification",
        "Spreadsheet Automation & Reporting",
        "Tally Prime & GST Billing Operations",
        "Operating System & Network Support",
        "Online Citizen Portal Services",
    ],
    "Retail": [
        "Point of Sale (POS) & Barcode Billing",
        "Customer Service & Product Demos",
        "Store Merchandising & Shelf Layout",
        "Inventory Stock Reconciliation",
        "Digital Payments Handling (UPI/Card)",
    ],
    "Logistics": [
        "Barcode Scanning & Consignment Picking",
        "Secure Carton Packaging & Labelling",
        "Pallet Stacking & Forklift Assistance",
        "Dispatch Manifest Verification",
        "Warehouse Safety & Spill Protocol",
    ],
    "Capital Goods": [
        "Shielded Metal Arc Welding (SMAW)",
        "Oxy-Fuel Gas Cutting & Bevelling",
        "Precision Bench Fitting & Tapping",
        "Joint Inspection & Grinding",
        "Industrial Workshop Safety Standards",
    ],
}
from services.recommendation_engine.repositories.scheme_repository import (
    SchemeRepository,
)


class SchemeResolver:
    """Resolves at least 3 related skills and at least 3 government schemes from the database."""

    def __init__(
        self,
        skill_repo: SkillRepository | None = None,
        scheme_repo: SchemeRepository | None = None,
    ):
        self._skill_repo = skill_repo or SkillRepository()
        self._scheme_repo = scheme_repo or SchemeRepository()

    def resolve_related_skills(self, qualification: Qualification) -> list[str]:
        """Return at least 3 related competencies/skills taught in this course."""
        skills: list[str] = []

        # 1. Collect names from required skills
        for sid in qualification.required_skills:
            skill_obj = self._skill_repo.get(sid)
            name = skill_obj.name if skill_obj else sid.replace("SK_", "").replace("_", " ").title()
            if name not in skills:
                skills.append(name)

        # 2. Collect names from optional skills
        for sid in qualification.optional_skills:
            skill_obj = self._skill_repo.get(sid)
            name = skill_obj.name if skill_obj else sid.replace("SK_", "").replace("_", " ").title()
            if name not in skills:
                skills.append(name)

        # 3. If fewer than 3, supplement from sector curated skills
        sector_defaults = SECTOR_RELATED_SKILLS.get(qualification.sector, [
            "Trade Quality Standards",
            "Workshop Tool Operation",
            "Health & Occupational Safety",
        ])
        for default_skill in sector_defaults:
            if len(skills) >= 3:
                break
            if default_skill not in skills:
                skills.append(default_skill)

        return skills[:4]

    def resolve_eligible_schemes(
        self,
        beneficiary: BeneficiaryProfile,
        qualification: Qualification,
    ) -> list[SchemeInfo]:
        """Query the schemes database and return at least 3 eligible PM-AJAY & converged schemes."""
        matched: list[SchemeInfo] = []
        is_self_employed = beneficiary.employment_preference in (
            EmploymentPreference.SELF_EMPLOYMENT,
            EmploymentPreference.BOTH,
            EmploymentPreference.UNKNOWN,
        )

        def add_scheme_by_id(scheme_id: str):
            if any(m.scheme_code == scheme_id for m in matched):
                return
            s = self._scheme_repo.get(scheme_id)
            if s:
                matched.append(SchemeInfo(
                    scheme_code=s.scheme_code,
                    scheme_name=s.scheme_name,
                    ministry=s.ministry,
                    benefit_summary=s.benefit_summary,
                    financial_grant=s.financial_grant,
                    stipend_details=s.stipend_details,
                    loan_subsidy=s.loan_subsidy,
                ))

        # 1. Primary PM-AJAY GIA Skilling Training (Free NSQF Course + ₹1,500/mo)
        add_scheme_by_id("SCHEME_PM_AJAY_GIA_SKILL")

        # 2. If experienced and RPL supported -> PM-AJAY RPL Certification
        if qualification.supports_rpl and beneficiary.experience_years >= 1.0:
            add_scheme_by_id("SCHEME_PM_AJAY_RPL")

        # 3. PM-AJAY Toolkit Grant (up to ₹50,000 for self-employment / tool assets)
        if is_self_employed or qualification.required_assets:
            add_scheme_by_id("SCHEME_PM_AJAY_GIA_TOOLKIT")

        # 4. PM Vishwakarma for traditional artisan/craft/technical trades
        is_traditional_trade = qualification.sector in (
            "Apparel", "Construction", "Automotive", "Beauty", "Capital Goods", "Electronics", "Handicrafts", "Leather"
        )
        if is_traditional_trade:
            add_scheme_by_id("SCHEME_PM_VISHWAKARMA")

        # 5. PM-AJAY Special Central Assistance (SCA) Credit Subsidy
        if is_self_employed:
            add_scheme_by_id("SCHEME_PM_AJAY_SCA_CREDIT")

        # 6. PM-AJAY Common Facility Centre (CFC) Tool Bank for cluster trades
        if qualification.sector in ("Apparel", "Handicrafts", "Leather", "Capital Goods"):
            add_scheme_by_id("SCHEME_PM_AJAY_CFC_TOOLBANK")

        # 7. PMKVY 4.0 Skill India Digital convergence
        add_scheme_by_id("SCHEME_PMKVY_4_0")

        # 8. MUDRA Shishu Loan
        if is_self_employed:
            add_scheme_by_id("SCHEME_PMMY_MUDRA_SHISHU")

        # 9. NSFDC Term Loan for Scheduled Castes
        add_scheme_by_id("SCHEME_NSFDC_LOAN")

        # Fallback to any remaining schemes if still fewer than 3
        if len(matched) < 3:
            for s in self._scheme_repo.get_all():
                add_scheme_by_id(s.scheme_code)
                if len(matched) >= 3:
                    break

        return matched[:3]
