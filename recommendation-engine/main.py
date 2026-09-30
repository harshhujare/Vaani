"""
VaniSetu Recommendation Engine — FastAPI Application
=====================================================
A deterministic, auditable recommendation service that matches
PM-AJAY GIA beneficiaries to NSQF-aligned training programs.

Architecture:
  - Separate Python microservice (FastAPI + asyncpg)
  - Connects to the same Neon PostgreSQL as the Node.js backend
  - Stateless — all state lives in the database
  - No LLM in the scoring loop — AI understands, rules decide

Endpoints:
  GET  /health                           → Health check
  GET  /api/v1/recommend/{beneficiary_id} → Get recommendations
  POST /api/v1/recommend                 → Get recommendations (with body)
"""

import sys
import uuid
import time
from contextlib import asynccontextmanager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
    try:
        import uvicorn.loops.asyncio
        uvicorn.loops.asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import init_pool, close_pool, settings
from models import RecommendationResponse, ErrorResponse
from engine import run_recommendation


# ══════════════════════════════════════════
# APP LIFECYCLE
# ══════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("\n  ===============================================")
    print("    VaniSetu Recommendation Engine")
    print(f"    Starting on: http://localhost:{settings.port}")
    print(f"    Environment: {settings.env}")
    print("  ===============================================\n")

    try:
        await init_pool()
        print("  [OK] Database pool initialized")
    except Exception as e:
        print(f"  [WARN] Database connection warning: {e}")
        print("  [WARN] Server is running, but database-dependent endpoints will return 503 until a valid DATABASE_URL is configured in .env\n")

    yield

    # Shutdown
    try:
        await close_pool()
        print("  [OK] Database pool closed")
    except Exception:
        pass


# ══════════════════════════════════════════
# FASTAPI APP
# ══════════════════════════════════════════

app = FastAPI(
    title="VaniSetu Recommendation Engine",
    description=(
        "Deterministic, auditable recommendation service for matching "
        "PM-AJAY GIA beneficiaries to NSQF-aligned training programs."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Node.js backend and frontend to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "service": "VaniSetu Recommendation Engine",
        "version": "1.0.0",
        "status": "healthy",
    }


# ══════════════════════════════════════════
# RECOMMENDATION ENDPOINTS
# ══════════════════════════════════════════

@app.get(
    "/api/v1/recommend/{beneficiary_id}",
    response_model=RecommendationResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get training program recommendations for a beneficiary",
    description=(
        "Runs the full 6-stage recommendation pipeline:\n"
        "1. Retrieve candidate programs (sector + location match)\n"
        "2. Apply hard eligibility gates (education, capacity, active)\n"
        "3. Score each program (100-point multi-factor model)\n"
        "4. Rank and apply diversity filter (3 distinct pathways)\n"
        "5. Analyze skill gaps (set subtraction)\n"
        "6. Generate plain-language explanations\n\n"
        "Returns top 3 recommendations with full score breakdowns."
    ),
)
async def get_recommendations(beneficiary_id: str):
    """Get recommendations for a beneficiary by UUID."""
    start_time = time.time()

    # Validate UUID format
    try:
        uuid.UUID(beneficiary_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid beneficiary ID format: '{beneficiary_id}'. Expected UUID.",
        )

    try:
        result = await run_recommendation(beneficiary_id)
        elapsed = round((time.time() - start_time) * 1000, 2)
        print(f"  [OK] Recommendation generated in {elapsed}ms for {beneficiary_id}")
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"  [ERROR] Engine error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation engine error: {str(e)}",
        )


@app.post(
    "/api/v1/recommend",
    response_model=RecommendationResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get recommendations (POST variant)",
    description="Same as GET but accepts beneficiary_id in the request body.",
)
async def post_recommendations(beneficiary_id: str = Query(..., description="Beneficiary UUID")):
    """POST variant — same pipeline, accepts query param."""
    return await get_recommendations(beneficiary_id)


# ══════════════════════════════════════════
# SCORING CONFIG ENDPOINT (for transparency)
# ══════════════════════════════════════════

@app.get(
    "/api/v1/scoring-config",
    summary="View the scoring weights and configuration",
    description="Returns the current scoring formula and weights for audit transparency.",
)
async def get_scoring_config():
    """Expose the scoring config so the jury can verify the formula."""
    from config import WEIGHTS, EDUCATION_LEVELS, TOP_N_RESULTS, MIN_SCORE_THRESHOLD

    return {
        "success": True,
        "scoring_formula": "Final Score = Σ (Component Score × Weight × 100)",
        "weights": WEIGHTS,
        "education_hierarchy": EDUCATION_LEVELS,
        "max_recommendations": TOP_N_RESULTS,
        "min_score_threshold": MIN_SCORE_THRESHOLD,
        "nsqf_fit_rules": {
            "delta_+1": "1.0 (ideal — one step up)",
            "delta_0":  "0.8 (same level — certification value)",
            "delta_-1": "0.5 (below current — less growth)",
            "delta_+2": "0.6 (stretch — achievable)",
            "delta_+3+": "0.2 (too high — likely to struggle)",
        },
        "location_rules": {
            "same_district": 1.0,
            "same_state": 0.5,
            "different_state": 0.2,
        },
        "capacity_rules": {
            "under_50_percent": 1.0,
            "50_to_80_percent": 0.6,
            "80_to_100_percent": 0.2,
            "full": 0.0,
        },
    }


# ══════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.env == "development"),
        loop="asyncio",
    )
