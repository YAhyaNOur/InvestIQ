from pydantic import BaseModel, Field
from typing import Optional


class CompanyBase(BaseModel):
    company_id: Optional[int] = None
    name: Optional[str] = None

    sector: Optional[str] = None
    industry_group: Optional[str] = None
    region_std: Optional[str] = None

    beta: Optional[float] = None
    net_debt: Optional[float] = None
    revenue_per_employee: Optional[float] = None
    ebitda_margins: Optional[float] = None

    # ── NOUVEAUX ──────────────────────────────────────────
    revenue_growth: Optional[float] = Field(
        None,
        description="Taux de croissance du revenu. Ex: 0.12 pour 12%"
    )
    current_ratio: Optional[float] = Field(
        None,
        description="Actifs court terme / Passifs court terme"
    )
    debt_to_equity: Optional[float] = Field(
        None,
        description="Dette totale / Capitaux propres"
    )
    # ──────────────────────────────────────────────────────


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    company_id: int

    model_config = {"from_attributes": True}