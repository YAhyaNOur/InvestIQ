import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.investor_interest import InvestorInterest
from app.models.company import Company
from app.core.deps import get_current_user

router = APIRouter(prefix="/interest", tags=["Investor Interest"])

N8N_WEBHOOK = "http://localhost:5678/webhook-test/investor-interest"

@router.post("/{company_id}")
async def mark_interest(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Sauvegarder l'intérêt
    interest = InvestorInterest(
        user_id=current_user.user_id,
        company_id=company_id,
        interested=True
    )
    db.add(interest)
    await db.commit()

    # Récupérer la company
    result = await db.execute(select(Company).where(Company.company_id == company_id))
    company = result.scalar_one_or_none()

    # Appeler les modèles ML
    growth_score = 0
    risk_score = 0

    try:
        async with httpx.AsyncClient() as ml_client:
            # Growth model
            growth_resp = await ml_client.post(
                "http://localhost:8000/growth/predict",
                json={
                    "Sector": company.sector or "Unknown",
                    "Beta": float(company.beta or 0),
                    "Region_std": company.region_std or "Unknown",
                    "Net_Debt": float(company.net_debt or 0),
                    "Revenue_Growth": float(company.revenue_growth or 0)
                },
                timeout=5.0
            )
            growth_score = round(growth_resp.json().get("score", 0) * 100, 1)

            # Risk model
            risk_resp = await ml_client.post(
                "http://localhost:8000/risk/predict_risk",
                json={
                    "Sector": company.sector or "Unknown",
                    "Region_std": company.region_std or "Unknown",
                    "Debt_To_Equity": float(company.debt_to_equity or 0),
                    "Total_Debt_M": float(company.net_debt or 0),
                    "Current_Ratio": float(company.current_ratio or 1),
                    "Employees_Sector_Z": 0
                },
                timeout=5.0
            )
            risk_score = risk_resp.json().get("analysis", {}).get("risk_score", 0)

    except Exception as e:
        print(f"⚠️ ML models failed: {e}")

    # Déclencher n8n avec toutes les données
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                N8N_WEBHOOK,
                json={
                    "user_id": current_user.user_id,
                    "company_id": company_id,
                    "action": "interested",
                    "company_name": company.name if company else "Unknown",
                    "investor_name": getattr(current_user, 'full_name', 'Investor'),
                    "investor_email": getattr(current_user, 'email', ''),
                    "sector": company.sector if company else "N/A",
                    "region": company.region_std if company else "N/A",
                    "beta": float(company.beta) if company and company.beta else 0,
                    "net_debt": float(company.net_debt) if company and company.net_debt else 0,
                    "revenue_growth": float(company.revenue_growth) if company and company.revenue_growth else 0,
                    "debt_to_equity": float(company.debt_to_equity) if company and company.debt_to_equity else 0,
                    "current_ratio": float(company.current_ratio) if company and company.current_ratio else 0,
                    "ebitda": str(round(company.ebitda_margins * 100, 1)) + "%" if company and company.ebitda_margins else "N/A",
                    "growth_score": growth_score,
                    "risk_score": risk_score,
                },
                timeout=3.0
            )
    except Exception as e:
        print(f"⚠️ N8N failed: {e}")

    return {"message": "Interest saved", "company_id": company_id}


@router.get("/my-interests")
async def get_my_interests(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(InvestorInterest).where(
            InvestorInterest.user_id == current_user.user_id,
            InvestorInterest.interested == True
        )
    )
    interests = result.scalars().all()
    ids = [i.company_id for i in interests]
    return {"interested_company_ids": ids}


@router.get("/my-interests-full")
async def get_my_interests_full(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    from sqlalchemy import select
    from app.models.company import Company

    result = await db.execute(
        select(InvestorInterest, Company)
        .join(Company, Company.company_id == InvestorInterest.company_id)
        .where(
            InvestorInterest.user_id == current_user.user_id,
            InvestorInterest.interested == True
        )
        .order_by(InvestorInterest.created_at.desc())
    )
    rows = result.all()
    interests = []
    for interest, company in rows:
        interests.append({
            "company_id": company.company_id,
            "name": company.name,
            "sector": company.sector,
            "region": company.region_std,
            "final_score": 0,
            "created_at": interest.created_at.isoformat()
        })
    return {"interests": interests}