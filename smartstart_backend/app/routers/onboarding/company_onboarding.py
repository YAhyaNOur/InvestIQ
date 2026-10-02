from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate
from app.core.deps import get_current_user

router = APIRouter(prefix="/onboarding/company", tags=["Company Onboarding"])


# ─────────────────────────────
# CHECK IF COMPANY EXISTS
# ─────────────────────────────
@router.get("/status")
async def company_onboarding_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Company).where(Company.user_id == current_user.user_id)
    )
    company = result.scalar_one_or_none()
    return {"completed": company is not None}


# ─────────────────────────────
# CREATE COMPANY (ONBOARDING)
# ─────────────────────────────
@router.post("/submit")
async def submit_company_onboarding(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Company).where(Company.user_id == current_user.user_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {"message": "Company already exists", "company_id": existing.company_id}

    company = Company(
        user_id=current_user.user_id,
        name=data.name,
        sector=data.sector,
        industry_group=data.industry_group,
        region_std=data.region_std,
        beta=data.beta,
        ebitda_margins=data.ebitda_margins,
        revenue_per_employee=data.revenue_per_employee,
        net_debt=data.net_debt,
        # ── NOUVEAUX ──
        revenue_growth=data.revenue_growth,
        current_ratio=data.current_ratio,
        debt_to_equity=data.debt_to_equity,
    )

    db.add(company)
    await db.commit()
    await db.refresh(company)

    return {
        "message": "Company onboarding completed",
        "company": company
    }


# ─────────────────────────────
# UPDATE COMPANY (ONBOARDING)
# ─────────────────────────────
@router.put("/submit")
async def update_company_onboarding(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Company).where(Company.user_id == current_user.user_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        return {"error": "Company not found"}

    company.name = data.name
    company.sector = data.sector
    company.industry_group = data.industry_group
    company.region_std = data.region_std
    company.beta = data.beta
    company.ebitda_margins = data.ebitda_margins
    company.revenue_per_employee = data.revenue_per_employee
    company.net_debt = data.net_debt
    # ── NOUVEAUX ──
    company.revenue_growth = data.revenue_growth
    company.current_ratio = data.current_ratio
    company.debt_to_equity = data.debt_to_equity

    await db.commit()
    await db.refresh(company)

    return {
        "message": "Company updated",
        "company": company
    }