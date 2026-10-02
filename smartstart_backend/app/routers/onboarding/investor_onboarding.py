"""from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import pandas as pd

from app.db.session import get_db
from app.models.investor import Investor
from app.models.company import Company
from app.models.investment_recommendation import InvestmentRecommendation
from app.schemas.investor import InvestorCreate
from app.core.deps import get_current_user

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# ─────────────────────────
# QUESTIONS 
# ─────────────────────────
@router.get("/questions")
def get_questions():
    return {
        "sectors": ["Technology", "Finance", "Healthcare", "Industrials", "Consumer", "Real_Estate"],
        "regions": ["US", "EU", "AS", "AF"]
    }

# ─────────────────────────
# SUBMIT : Uniquement Secteur et Région
# ─────────────────────────
@router.post("/submit")
async def submit_onboarding(
    data: InvestorCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. Mise à jour du profil de l'investisseur
    result = await db.execute(
        select(Investor).where(Investor.user_id == current_user.user_id)
    )
    investor = result.scalar_one_or_none()

    if not investor:
        investor = Investor(user_id=current_user.user_id)

    # On ne stocke que ce qui est demandé
    investor.preferred_sector = data.preferred_sector
    investor.region_std = data.region_std 

    db.add(investor)
    await db.commit()
    await db.refresh(investor)

    # 2. Recherche simple d'entreprises correspondantes
    # On cherche les entreprises qui ont le même secteur ET la même région
    query = select(Company).where(
        Company.sector == investor.preferred_sector,
        Company.region_std == investor.region_std
    )
    
    companies_result = await db.execute(query)
    matching_companies = companies_result.scalars().all()

    # 3. Nettoyage des anciennes recommandations
    await db.execute(
        delete(InvestmentRecommendation).where(
            InvestmentRecommendation.user_id == current_user.user_id
        )
    )

    # 4. Sauvegarde des nouveaux résultats (Top 10 max)
    recommendations_to_return = []
    for c in matching_companies[:10]:
        rec = InvestmentRecommendation(
            user_id=current_user.user_id,
            company_id=c.company_id,
            final_score=1.0, # Score simple par défaut
            decision="Match"
        )
        db.add(rec)
        
        # Préparation de la réponse pour le frontend
        recommendations_to_return.append({
            "company_id": c.company_id,
            "name": c.name,
            "sector": c.sector,
            "region": c.region_std,
            "final_score": 1.0
        })

    await db.commit()

    return {
        "status": "success",
        "investor": {
            "sector": investor.preferred_sector,
            "region": investor.region_std
        },
        "recommendations": recommendations_to_return
    }"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import pandas as pd

from app.db.session import get_db
from app.models.investor import Investor
from app.models.company import Company
from app.models.investment_recommendation import InvestmentRecommendation
from app.schemas.investor import InvestorCreate
from app.core.deps import get_current_user

from service.investor_profile import build_profile
from service.similar_user import get_similar_investors
from service.ml_model import get_ml_score
from service.scoring import business_score

import joblib
from pathlib import Path

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# ── Charger le modèle ────────────────────────────────────────────────────────
MODELS_DIR = Path(r"C:\Users\user\Desktop\BIIA\BiAi\Service_ml\models3\models")
_package = joblib.load(MODELS_DIR / "model_recommendation.joblib")
_model = _package["model"]
_FEATURES = _package["features"]
_CAT_FEATURES = _package["cat_features"]
_ALLOWED = _package.get("allowed_values", {})


@router.get("/status")
async def onboarding_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(Investor).where(Investor.user_id == current_user.user_id)
    )
    investor = result.scalar_one_or_none()
    return {
        "completed": investor is not None and investor.preferred_sector is not None
    }


@router.get("/questions")
def get_questions():
    return {
        "sectors": ["Technology", "Finance", "Healthcare", "Industrials", "Consumer", "Energy", "Education"],
        "regions": ["US", "EU", "AS", "AF"],
        "risk": ["low", "medium", "high"]
    }


@router.post("/submit")
async def submit_onboarding(
    data: InvestorCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. SAVE INVESTOR
    result = await db.execute(
        select(Investor).where(Investor.user_id == current_user.user_id)
    )
    investor = result.scalar_one_or_none()

    if not investor:
        investor = Investor(user_id=current_user.user_id)

    investor.preferred_sector = data.preferred_sector
    investor.region_std = getattr(data, "region_std", None)
    investor.risk_profile = getattr(data, "risk", "medium")
    investor.portfolio_value = data.portfolio_value
    investor.active_companies = data.active_companies

    db.add(investor)
    await db.commit()
    await db.refresh(investor)

    # 2. PROFILE
    profile = build_profile({
        "preferred_sector": investor.preferred_sector,
        "region_std": investor.region_std,
        "risk": investor.risk_profile or "medium"
    })

    # 3. LOAD COMPANIES
    companies_result = await db.execute(select(Company))
    companies = companies_result.scalars().all()

    df_companies = pd.DataFrame([{
        "company_id": c.company_id,
        "name": c.name,
        "Sector": c.sector,
        "Industry_Group": c.industry_group,
        "Region_std": c.region_std,
        "Beta": c.beta or 0,
        "EBITDA Margins": c.ebitda_margins or 0,
        "Revenue_Per_Employee": c.revenue_per_employee or 0,
        "Net_Debt": c.net_debt or 0,
    } for c in companies])

    if df_companies.empty:
        return {"status": "no_companies", "recommendations": []}

    # 4. SIMILAR INVESTORS
    investors_result = await db.execute(select(Investor))
    investors = investors_result.scalars().all()

    df_users = pd.DataFrame([{
        "investor_id": i.user_id,
        "preferred_sector": i.preferred_sector or "Other",
        "region_std": getattr(i, "region_std", "Other") or "Other",
    } for i in investors])

    try:
        similar_df = get_similar_investors(
            current_id=current_user.user_id,
            df=df_users,
            top_n=5
        )
    except Exception as e:
        print(f"Similar users error: {e}")
        similar_df = pd.DataFrame()

    # 5. ML SCORE
    try:
        df_ml = df_companies.copy()
        # Préparer les features pour le modèle
        for col in _CAT_FEATURES:
            if col in df_ml.columns:
                df_ml[col] = df_ml[col].astype(str)
                if col in _ALLOWED:
                    df_ml[col] = df_ml[col].apply(
                        lambda x: x if x in _ALLOWED[col] else "Unknown"
                    )
        df_companies["ml_score"] = get_ml_score(_model, df_ml, _FEATURES)
    except Exception as e:
        print(f"ML score error: {e}")
        df_companies["ml_score"] = 0.5

    # 6. BUSINESS SCORE
    df_companies["business_score"] = df_companies.apply(
        lambda r: business_score(r.to_dict(), profile), axis=1
    )

    # Normaliser business score
    min_b = df_companies["business_score"].min()
    max_b = df_companies["business_score"].max()
    if max_b - min_b > 0:
        df_companies["business_score"] = (
            df_companies["business_score"] - min_b
        ) / (max_b - min_b)
    else:
        df_companies["business_score"] = 0.5

    # 7. USER-USER SCORE
    def uu_score(row):
        if similar_df is None or similar_df.empty:
            return 0.0
        sector_match = (similar_df.get("preferred_sector", pd.Series()) == row["Sector"])
        region_match = (similar_df.get("region_std", pd.Series()) == row["Region_std"])
        if sector_match.any():
            return float(similar_df[sector_match]["sim_score"].mean()) * 0.8
        if region_match.any():
            return float(similar_df[region_match]["sim_score"].mean()) * 0.4
        return 0.0

    df_companies["user_user_score"] = df_companies.apply(uu_score, axis=1)

    # 8. FINAL SCORE
    df_companies["final_score"] = (
        0.40 * df_companies["ml_score"] +
        0.25 * df_companies["business_score"] +
        0.20 * df_companies["user_user_score"] +
        0.15 * df_companies.apply(
            lambda r: 0.5 + (0.5 if r["Sector"] == profile["sector"] else 0) +
                      (0.3 if r["Region_std"] == profile["region"] else 0),
            axis=1
        ).clip(0, 1)
    ).clip(0, 1)

    # 9. DECISION
    df_companies["decision"] = df_companies["final_score"].apply(lambda x:
        "STRONG BUY" if x > 0.75 else
        "BUY"        if x > 0.55 else
        "HOLD"       if x > 0.35 else
        "AVOID"
    )

    # 10. CLEAN OLD RECS
    await db.execute(
        delete(InvestmentRecommendation).where(
            InvestmentRecommendation.user_id == current_user.user_id
        )
    )

    # 11. SAVE NEW RECS
    recommendations = []
    top_recs = df_companies.sort_values("final_score", ascending=False).head(10)

    for _, row in top_recs.iterrows():
        rec = InvestmentRecommendation(
            user_id=current_user.user_id,
            company_id=int(row["company_id"]),
            ml_score=float(row["ml_score"]),
            business_score=float(row["business_score"]),
            final_score=float(row["final_score"]),
            decision=str(row["decision"])
        )
        db.add(rec)
        recommendations.append({
            "company_id": int(row["company_id"]),
            "name": row.get("name"),
            "sector": row.get("Sector"),
            "region": row.get("Region_std"),
            "ml_score": round(float(row["ml_score"]), 3),
            "business_score": round(float(row["business_score"]), 3),
            "final_score": round(float(row["final_score"]), 3),
            "decision": row["decision"]
        })

    await db.commit()

    return {
        "status": "success",
        "investor": profile,
        "recommendations": recommendations,
        "portfolio_value": investor.portfolio_value,
        "active_companies": investor.active_companies,
    }