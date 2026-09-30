"""
VaniSetu Recommendation Engine — FastAPI Application
=====================================================
Production-ready HTTP server hosting the NSQF-aligned recommendation engine.

Run locally:
    uvicorn services.recommendation_engine.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.recommendation_engine import __version__
from services.recommendation_engine.api.routes import router as recommendations_router
from services.recommendation_engine.core.constants import (
    ENGINE_VERSION,
    SCORING_VERSION,
)
from services.recommendation_engine.core.exceptions import (
    RecommendationEngineError,
    ValidationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("recommendation_engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown hooks."""
    logger.info(
        f"Starting VaniSetu Recommendation Engine v{__version__} "
        f"(Engine: {ENGINE_VERSION}, Scoring: {SCORING_VERSION})"
    )
    yield
    logger.info("Shutting down Recommendation Engine service.")


def create_app() -> FastAPI:
    """Application factory for the Recommendation Engine."""
    app = FastAPI(
        title="VaniSetu Recommendation Engine",
        description=(
            "Layer 2 Data Processing & Intelligence Core for PM-AJAY GIA. "
            "Implements deterministic 100-point scoring, multi-tier diversity ranking, "
            "Haversine spatial matching, competency set subtraction, and guardrailed explanations."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(recommendations_router)

    # Custom Exception Handlers
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": exc.message, "details": exc.details},
        )

    @app.exception_handler(RecommendationEngineError)
    async def engine_exception_handler(request: Request, exc: RecommendationEngineError):
        return JSONResponse(
            status_code=500,
            content={"error": exc.message, "details": exc.details},
        )

    @app.get("/", tags=["system"])
    async def root():
        return {
            "name": "VaniSetu Recommendation Engine",
            "version": __version__,
            "engine_version": ENGINE_VERSION,
            "scoring_version": SCORING_VERSION,
            "status": "online",
            "docs_url": "/docs",
        }

    return app


app = create_app()
