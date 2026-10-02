from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.company import Company
from app.models.investment_recommendation import InvestmentRecommendation

from service.recommendation import hybrid_recommend_final
from service.similar_user import get_similar_investors
from service.investor_profile import build_profile

from app.core.deps import get_current_user

import pandas as pd


router = APIRouter(prefix="/company-recommendation", tags=["Company Recommendation"])


@router.get("/my-recommendations")
async def get_my_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(InvestmentRecommendation, Company)
        .join(
            Company,
            Company.company_id == InvestmentRecommendation.company_id
        )
        .where(
            InvestmentRecommendation.user_id == current_user.user_id
        )
        .order_by(
            InvestmentRecommendation.final_score.desc()
        )
    )

    rows = result.all()

    recommendations = []

    for rec, company in rows:
        recommendations.append({
            "id": rec.id,
            "company_id": company.company_id,
            "company_name": company.name,
            "sector": company.sector,
            "region": company.region_std,
            "ml_score": rec.ml_score,
            "business_score": rec.business_score,
            "final_score": rec.final_score,
            "decision": rec.decision,
            "created_at": rec.created_at.isoformat()
        })

    return {
        "recommendations": recommendations
    }

@router.get("/{company_id}")
async def recommend_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # ─────────────────────────────
    # 1. GET COMPANY
    # ─────────────────────────────
    result = await db.execute(
        select(Company).where(Company.company_id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # ─────────────────────────────
    # 2. BUILD DATAFRAME (IMPORTANT)
    # ─────────────────────────────
    df_companies = pd.DataFrame([{
        "company_id": company.company_id,
        "Sector": company.sector,
        "Region_std": company.region_std,
        "Beta": company.beta,
        "Net_Debt": company.net_debt,
        "Revenue_per_Employee": company.revenue_per_employee,
        "EBITDA Margins": company.ebitda_margins,
    }])

    # ─────────────────────────────
    # 3. GET INVESTOR PROFILE
    # ─────────────────────────────
    investor_query = await db.execute(
        select(current_user.__class__).where(current_user.__class__.user_id == current_user.user_id)
    )
    investor = investor_query.scalar_one_or_none()

    profile = {
        "risk": getattr(investor, "risk_profile", "medium"),
        "sector": getattr(investor, "preferred_sector", None),
        "min_return": getattr(investor, "min_return", 0),
        "max_risk": getattr(investor, "max_risk", 1),
        "budget": getattr(investor, "budget", 0),
    }

    # ─────────────────────────────
    # 4. SIMILAR USERS
    # ─────────────────────────────
    try:
        similar_df = get_similar_investors(current_user.user_id, df_companies)
    except Exception:
        similar_df = pd.DataFrame()

    # ─────────────────────────────
    # 5. ML ENGINE
    # ─────────────────────────────
    result_df = hybrid_recommend_final(
        df_companies=df_companies,
        investor_profile=profile,
        similar_df=similar_df,
        user_id=current_user.user_id
    )

    row = result_df.iloc[0]

    # ─────────────────────────────
    # 6. SAVE RECOMMENDATION
    # ─────────────────────────────
    rec = InvestmentRecommendation(
        user_id=current_user.user_id,
        company_id=company_id,
        ml_score=row["ml_score"],
        business_score=row["business_score_final"],
        final_score=row["final_score"],
        decision=row["decision"]
    )

    db.add(rec)
    await db.commit()

    # ─────────────────────────────
    # 7. RETURN RESULT
    # ─────────────────────────────
    return row.to_dict()