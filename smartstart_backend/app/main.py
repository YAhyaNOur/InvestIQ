import sys
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

SERVICE_CODE_PATH = r"C:\Users\user\Desktop\BIIA\BiAi\Service_ml\models3\code"
if SERVICE_CODE_PATH not in sys.path:
    sys.path.append(SERVICE_CODE_PATH)
    print(f"[DEBUG] SERVICE_CODE_PATH added: {SERVICE_CODE_PATH}")

from app.core.config import settings
from app.db.session import engine
from app.routers import startup_dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[SmartStart] Starting in {settings.app_env} mode")
    yield
    await engine.dispose()
    print("[SmartStart] Shutdown complete")


app = FastAPI(
    title="SmartStart API",
    version="1.0.0",
    description="AI-powered startup & investor matching platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Exception Handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    print(f"[ERROR] {request.method} {request.url}\n{error_detail}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


def include_router_safe(import_path, prefix="", tags=None):
    try:
        module = __import__(import_path, fromlist=['router'])
        app.include_router(module.router, prefix=prefix, tags=tags or [])
        print(f"[OK] Router: {import_path}")
    except Exception as e:
        print(f"[ERROR] Router FAILED {import_path}: {e}")


# ─── CORE ROUTERS ─────────────────────────────────────────────────────────────
include_router_safe("app.routers.auth")
include_router_safe("app.routers.users")


# ─── ONBOARDING ───────────────────────────────────────────────────────────────
include_router_safe("app.routers.onboarding.investor_onboarding")
include_router_safe("app.routers.onboarding.company_onboarding")

# ─── COMPANY ──────────────────────────────────────────────────────────────────
include_router_safe("app.routers.company")
include_router_safe("app.routers.company_recommendation")

# ─── INVESTOR ─────────────────────────────────────────────────────────────────
include_router_safe("app.routers.investor_interest")
include_router_safe("app.routers.orchestrator")

# ─── STARTUP DASHBOARD ────────────────────────────────────────────────────────
app.include_router(startup_dashboard.router)

# ─── ML ROUTERS ───────────────────────────────────────────────────────────────
try:
    from api.api_growth import router as profit_router
    from api.api_risk import router as risk_router
    from api.api_hybride import router as hybrid_router
    from service.api import router as service_router

    app.include_router(profit_router, prefix="/growth", tags=["Growth Analysis"])
    app.include_router(risk_router, prefix="/risk", tags=["Risk Analysis"])
    app.include_router(hybrid_router, prefix="/score", tags=["Hybrid Analysis"])
    app.include_router(service_router, prefix="/data", tags=["Data Service"])
    print("[OK] ML routers inclus")
except Exception as e:
    print(f"[ERROR] ML routers FAILED: {e}")

# ─── HEALTH ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

# ─── YFINANCE ─────────────────────────────────────────────────────────────────
try:
    from app.routers import yfinance_analysis
    app.include_router(yfinance_analysis.router)
    print("[OK] YFinance router loaded")
except Exception as e:
    print(f"[ERROR] YFinance FAILED: {e}")

# ─── CRYPTO ───────────────────────────────────────────────────────────────────
from app.routers.crypto import router as crypto_router

app.include_router(crypto_router, prefix="/api/crypto", tags=["Crypto"])
print("[OK] Crypto router loaded")


# ─── INVESTIQ ─────────────────────────────────────────────────────────────────

class ProjectInput(BaseModel):
    description: str

class AnalysisResult(BaseModel):
    score: int
    sector: str
    project_type: str
    keywords: list[str]
    market_potential: int
    innovation_score: int
    risk_level: int
    advantages: list[str]
    disadvantages: list[str]
    recommendation: str
    funding_potential: str
    target_market: str

@app.post("/analyze", tags=["InvestIQ"], response_model=AnalysisResult)
async def analyze_project(payload: ProjectInput):
    if len(payload.description.strip()) < 50:
        raise HTTPException(status_code=422, detail="Description trop courte (minimum 50 caractères).")
    try:
        from app.services.nlp_service import extract_sector_and_keywords
        from app.services.scoring_service import compute_scores
        from app.services.llm_service import generate_llm_analysis

        nlp_result = extract_sector_and_keywords(payload.description)
        scores = compute_scores(payload.description, nlp_result)
        llm_output = await generate_llm_analysis(payload.description, nlp_result, scores)

        return AnalysisResult(
            score=scores["global_score"],
            sector=nlp_result["sector"],
            project_type=nlp_result["project_type"],
            keywords=nlp_result["keywords"],
            market_potential=scores["market_potential"],
            innovation_score=scores["innovation_score"],
            risk_level=scores["risk_level"],
            advantages=llm_output["advantages"],
            disadvantages=llm_output["disadvantages"],
            recommendation=llm_output["recommendation"],
            funding_potential=llm_output["funding_potential"],
            target_market=nlp_result["target_market"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse InvestIQ: {str(e)}")