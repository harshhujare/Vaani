# 🧠 VaniSetu Recommendation Engine

**Deterministic, auditable training program recommendation service**  
_Part of the VaniSetu PM-AJAY GIA AI Voice Assistant Platform_

## Architecture

```
Python FastAPI Microservice
├── Connects to same Neon PostgreSQL as Node.js backend
├── Stateless — all data lives in the shared database
├── No LLM in scoring loop — AI understands, structured rules decide
└── Full mathematical audit trail on every recommendation
```

## 6-Stage Pipeline

| Stage | Module | Purpose |
|-------|--------|---------|
| 1 | `pipeline/retriever.py` | Fetch candidates (sector + location dual-funnel) |
| 2 | `pipeline/eligibility.py` | Hard gates (active, seats, education) |
| 3 | `pipeline/scorer.py` | 100-point multi-factor scoring |
| 4 | `pipeline/ranker.py` | Sort + diversity filter (3 pathways) |
| 5 | `pipeline/gap_analyzer.py` | Skill gap set subtraction |
| 6 | `pipeline/explainer.py` | Plain-language explanations |

## Scoring Formula

```
Final Score = Σ (Component × Weight × 100)

  Skill Compatibility  × 0.30  (keyword overlap)
+ NSQF Level Fit       × 0.25  (level alignment)
+ Location Match       × 0.20  (district/state proximity)
+ Capacity Available   × 0.15  (seat availability)
+ Education Match      × 0.10  (education level fit)
= Total (0–100)
```

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Neon PostgreSQL DATABASE_URL

# 4. Run the server
python main.py
# or: uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/recommend/{beneficiary_id}` | Get top 3 recommendations |
| `GET` | `/api/v1/scoring-config` | View scoring formula (audit) |

## Example Response

```json
{
  "beneficiary_id": "uuid-here",
  "beneficiary_name": "Ramesh Kumar",
  "total_candidates_evaluated": 5,
  "eligible_candidates": 4,
  "recommendations": [
    {
      "rank": 1,
      "pathway_type": "BEST_MATCH",
      "program_name": "Advanced Carpentry & Furniture Design",
      "match_score": 82.5,
      "score_breakdown": {
        "skill_score": 30.0,
        "nsqf_score": 25.0,
        "location_score": 20.0,
        "capacity_score": 15.0,
        "education_score": 8.5
      },
      "matched_skills": ["Carpentry - Furniture Making"],
      "skill_gaps": ["Pattern Design", "Wood Selection"],
      "explanation_text": "Based on existing skills in Carpentry..."
    }
  ]
}
```

## Integration with Node.js Backend

The Node.js backend can call this service via HTTP:

```javascript
// In Node.js backend
const response = await fetch(
  `http://localhost:8000/api/v1/recommend/${beneficiaryId}`
);
const data = await response.json();
```

---

> **Core Law:** AI Understands. Structured Data & Rules Decide.
