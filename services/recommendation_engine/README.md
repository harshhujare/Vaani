# 🧠 VaniSetu Recommendation Engine

**Layer 2: Data Processing & Intelligence Core**  
**Problem Statement:** SIH26097 — AI Voice Assistant for Livelihood Mapping & NSQF-Aligned Skilling (PM-AJAY GIA)  

> **Core Architectural Law:** *AI Understands. Structured Data & Rules Decide.*

---

## 1. Architectural Boundary & Core Principles

```
  ┌──────────────────────────────────────────────┐
  │                   AI LAYER                   │
  │  • Speech-to-Text (ASR)                      │
  │  • Unstructured Profile Extraction           │
  │  • Semantic Normalization                    │
  │  • Natural-Language Explanation Generation   │
  └──────────────────────┬───────────────────────┘
                         │ Structured Facts Only
                         ▼
  ┌──────────────────────────────────────────────┐
  │             DETERMINISTIC ENGINE             │
  │  • Hard Eligibility Gates (Pass / Fail)      │
  │  • 100-Point Heuristic Scoring Formula       │
  │  • Multi-Tier Ranking & Diversity Filters    │
  │  • Skill Gap Set Subtraction                 │
  │  • Geospatial Distance Matching              │
  └──────────────────────────────────────────────┘
```

1. **No Black-Box Decisions:** An LLM does not choose courses or assign scores.
2. **Traceable & Auditable:** Every recommendation generates an explicit mathematical breakdown for jury and government audits.
3. **Grounded Facts:** Qualification metadata, eligibility rules, and center rosters are queried strictly from structured seed repositories / PostgreSQL, never hallucinated by an LLM.

---

## 2. 9-Stage Pipeline Workflow

1. **Skill Normalization (`pipeline/normalizer.py`):** Maps colloquial / multilingual phrases (Hindi, Marathi, English) into Canonical Skill IDs (`SK_*`).
2. **Candidate Retrieval (`pipeline/candidate_retriever.py`):** Dual-funnel retrieval combining SQL relational filtering with pgvector semantic search (configurable fallback).
3. **Hard Eligibility Gate (`pipeline/eligibility.py`):** Binary prerequisite gate evaluating minimum education level, experience, active status, and RPL (Recognition of Prior Learning) pathways.
4. **100-Point Heuristic Scoring (`pipeline/scoring.py`):** Multi-factor weighted evaluation ensuring deterministic output between 0 and 100.
5. **Skill Gap Set Subtraction (`pipeline/skill_gap.py`):** Mathematical set difference (`Required \ Possessed`) classifying competencies into Strengths vs Gaps.
6. **Haversine Geospatial Matching (`pipeline/geospatial.py`):** Great-circle distance calculation to find nearest authorized PMKK/training centers with active seats.
7. **Diversity Pathway Ranking (`pipeline/diversity.py`):** Stratifies top candidates into 3 distinct pathways:
   - `BEST_MATCH`: Closest fit to current skills and profile.
   - `GROWTH_PATH`: Slightly higher NSQF level aligned with future interests.
   - `ALTERNATIVE_OPTION`: Viable lateral sector/trade pathway.
8. **Guardrailed Explainer (`pipeline/explainer.py`):** Supplies pre-computed facts only to generate 2-sentence plain-language summaries (with fallback `TemplateExplainer`).
9. **Response Validator (`pipeline/validator.py`):** Ensures all returned qualification IDs and training centers exist in records, and scores match mathematical constraints.

---

## 3. 100-Point Scoring Model

$$\text{Final Score} = \sum (\text{Component Score} \times \text{Weight})$$

| Component | Weight | Measurement Basis |
|---|---|---|
| **Skill Compatibility** | 30% | Weighted overlap between user skills and required course standards |
| **Interest Alignment** | 20% | Alignment between user interest tags and qualification trade/sector |
| **Experience Relevance** | 15% | Working years compared against course prerequisite baseline |
| **Education Match** | 10% | Direct baseline compliance with educational prerequisites |
| **Asset Compatibility** | 10% | Ownership of necessary functional tools (e.g., sewing machine, basic kit) |
| **Location / Accessibility** | 5% | Distance scale (100 pts for <5 km, linearly decaying to 0 at 30 km) |
| **Employment Preference** | 5% | Match for Self-Employment vs Wage Employment |
| **Batch Availability** | 5% | Active seat capacity in upcoming batches |

---

## 4. API Endpoints

### `GET /api/v1/health`
Health check and version info.

### `POST /api/v1/recommend` or `POST /api/v1/recommendations`
Accepts either flat or nested payload formats.

#### Sample Request (Nested SIH Spec):
```json
{
  "beneficiary_id": "BEN-2026-091",
  "language": "mr",
  "location": {
    "district": "Sangli",
    "block": "Miraj",
    "latitude": 16.8524,
    "longitude": 74.5815
  },
  "livelihood_profile": {
    "current_occupation": "tailoring",
    "experience_years": 5,
    "education_level": "10th",
    "employment_preference": "self_employment",
    "canonical_skill_ids": ["SK_STITCHING", "SK_GARMENT_ALTERATION"],
    "asset_ids": ["AST_SEW_BASIC"],
    "interest_tags": ["dress_designing"]
  }
}
```

#### Sample Response:
```json
{
  "beneficiary_id": "BEN-2026-091",
  "engine_version": "1.0.0",
  "recommendations": [
    {
      "pathway_type": "BEST_MATCH",
      "qualification_id": "Q_APPAR_04",
      "qualification_title": "Advanced Tailoring & Garment Construction",
      "nsqf_level": 4,
      "eligible": true,
      "final_score": 90.25,
      "score_breakdown": {
        "skill": 27.0,
        "interest": 20.0,
        "experience": 14.25,
        "education": 10.0,
        "asset": 10.0,
        "location": 4.0,
        "employment": 5.0,
        "batch": 5.0
      },
      "matched_skills": ["Stitching", "Garment Alteration"],
      "skill_gaps": ["Pattern Making", "Industrial Machine Operation"],
      "training_center": {
        "center_id": "TC_SANGLI_01",
        "name": "PMKK Miraj Training Centre",
        "distance_km": 6.4,
        "seats_available": 18
      },
      "suggested_gia_intervention": null,
      "explanation": "Based on your profile, Advanced Tailoring & Garment Construction (NSQF Level 4) is recommended as your best match..."
    }
  ],
  "audit": {
    "decision_id": "DEC_A1B2C3D4E5F6",
    "candidate_count": 8,
    "eligible_count": 6,
    "selected_count": 3,
    "processing_duration_ms": 12.4
  }
}
```

---

## 5. Running & Testing

### Running Locally
```bash
uvicorn services.recommendation_engine.main:app --reload --port 8000
```
Interactive Swagger docs available at: `http://localhost:8000/docs`

### Running the Test Suite
```bash
python -m pytest services/recommendation_engine/tests/ -v
```
All 89 unit and integration tests validate the full pipeline end-to-end.
