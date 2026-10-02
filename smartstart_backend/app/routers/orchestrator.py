

import httpx
import joblib
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.company import Company
from app.models.investment_recommendation import InvestmentRecommendation
from app.models.investor_interest import InvestorInterest
from app.core.deps import get_current_user
from app.core.features import compute_all_features

# ── Chargement des modèles ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # smartstart_backend
MODELS_DIR = BASE_DIR.parent / "Service_ml" / "models3" / "models"

try:
    growth_package  = joblib.load(str(Path(MODELS_DIR) / "growth_score_model.joblib"))
    growth_model    = growth_package["model"]
    FEATURES_MODEL_1 = growth_package["features"]
    print(" Growth model chargé")
except Exception as e:
    print(f" Growth model FAILED: {e}")
    growth_model     = None
    FEATURES_MODEL_1 = []

try:
    risk_package    = joblib.load(str(Path(MODELS_DIR) / "risk_model.joblib"))
    risk_model      = risk_package["model"]
    FEATURES_MODEL_2 = risk_package["features"]
    print(" Risk model chargé")
except Exception as e:
    print(f" Risk model FAILED: {e}")
    risk_model       = None
    FEATURES_MODEL_2 = []

router = APIRouter(prefix="/predict-all", tags=["Orchestrator"])

N8N_WEBHOOK = "http://localhost:5678/webhook-test/investor-interest"


@router.post("/{company_id}")
async def predict_all(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. GET COMPANY
    result = await db.execute(
        select(Company).where(Company.company_id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # ── 2. VÉRIFIER SI DÉJÀ ANALYSÉ ────────────────────────────────────────
    existing_interest = await db.execute(
        select(InvestorInterest).where(
            InvestorInterest.user_id   == current_user.user_id,
            InvestorInterest.company_id == company_id,
            InvestorInterest.interested == True
        )
    )
    already_interested = existing_interest.scalar_one_or_none()

    if already_interested:
        # Récupérer l'analyse existante
        # Par — prendre seulement la première (la plus récente)
        existing_rec = await db.execute(
            select(InvestmentRecommendation).where(
                InvestmentRecommendation.user_id    == current_user.user_id,
                InvestmentRecommendation.company_id == company_id
            ).order_by(InvestmentRecommendation.created_at.desc()).limit(1)
        )
        rec = existing_rec.scalar_one_or_none()

        # Retourner sans recalculer ni renvoyer d'email
        return {
            "status":        "already_analyzed",
            "company_name":  company.name,
            "investor_name": current_user.username,
            "growth_score":  round((rec.ml_score       or 0) * 100, 1) if rec else 0,
            "risk_score":    round((rec.business_score  or 0) * 100, 1) if rec else 0,
            "final_score":   round((rec.final_score     or 0) * 100, 1) if rec else 0,
            "decision":      rec.decision if rec else "N/A",
            "sector":        company.sector,
            "region":        company.region_std,
            "beta":          company.beta,
            "ebitda":        company.ebitda_margins,
        }
    # ────────────────────────────────────────────────────────────────────────

    # 3. RAW DATA — brancher les vraies valeurs
    raw_data = {
        "sector":         company.sector         or "Other",
        "region":         company.region_std      or "Other",
        "industry":       company.industry_group  or "Other",
        "beta":           company.beta            or 0.0,
        "total_debt":     company.net_debt        or 0.0,
        "total_cash":     0.0,
        "revenue_growth": company.revenue_growth  or 0.0,
        "current_ratio":  company.current_ratio   or 0.0,
        "debt_to_equity": company.debt_to_equity  or 0.0,
        "revenue":        0.0,
        "employees":      0.0,
    }

    # 4. FEATURES
    try:
        features_dict = compute_all_features(raw_data, sector_stats={})
        df = pd.DataFrame([features_dict])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature error: {e}")

    # 5. PREDICTIONS
    if not growth_model or not risk_model:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        def prepare(frame, cols):
            X = frame[cols].copy()
            for col in X.select_dtypes(include="object").columns:
                X[col] = X[col].astype(str)
            return X

        growth_prob = float(growth_model.predict_proba(prepare(df, FEATURES_MODEL_1))[0][1])
        risk_prob   = float(risk_model.predict_proba(prepare(df, FEATURES_MODEL_2))[0][1])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    # 6. DECISION
    final_score = round((growth_prob * 0.6) - (risk_prob * 0.4), 4)
    final_score = max(0.0, final_score)
    decision    = "INVEST" if growth_prob > 0.6 and risk_prob < 0.5 else "REJECT"

    # 7. SAVE InvestorInterest
    interest = InvestorInterest(
        user_id=current_user.user_id,
        company_id=company_id,
        interested=True
    )
    db.add(interest)

    # 8. SAVE InvestmentRecommendation
    rec = InvestmentRecommendation(
        user_id=current_user.user_id,
        company_id=company_id,
        ml_score=growth_prob,
        business_score=risk_prob,
        final_score=final_score,
        decision=decision
    )
    db.add(rec)
    await db.commit()

    # 9. PAYLOAD
    payload = {
        "status":         "success",
        "company_name":   company.name,
        "investor_name":  current_user.username,
        "investor_email": current_user.email,
        "growth_score":   round(growth_prob  * 100, 1),
        "risk_score":     round(risk_prob    * 100, 1),
        "final_score":    round(final_score  * 100, 1),
        "decision":       decision,
        "sector":         company.sector,
        "region":         company.region_std,
        "beta":           company.beta,
        "ebitda":         company.ebitda_margins,
    }

    # 10. N8N WEBHOOK — email envoyé seulement pour une nouvelle analyse
    try:
        async with httpx.AsyncClient() as client:
            await client.post(N8N_WEBHOOK, json=payload, timeout=3.0)
            print(f" N8N notifié: {payload}")
    except Exception as e:
        print(f"N8N webhook failed: {e}")

    return payload


# ── GET — récupérer les intérêts de l'utilisateur ──────────────────────────
@router.get("/my-interests")
async def get_my_interests(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Retourne la liste des company_id déjà marqués comme intéressants."""
    result = await db.execute(
        select(InvestorInterest.company_id).where(
            InvestorInterest.user_id    == current_user.user_id,
            InvestorInterest.interested == True
        )
    )
    ids = [row[0] for row in result.fetchall()]
    return {"interested_company_ids": ids}