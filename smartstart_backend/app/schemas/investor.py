from pydantic import BaseModel
from typing import Optional


class InvestorBase(BaseModel):
    risk_profile: Optional[str] = "medium"
    preferred_sector: Optional[str] = None
    region_std: Optional[str] = None 
    budget: Optional[float] = 0
    min_return: Optional[float] = None
    max_risk: Optional[float] = None


class InvestorCreate(InvestorBase):
    portfolio_value: Optional[float] = None
    active_companies: Optional[int] = None
    pass


class InvestorUpdate(InvestorBase):
    pass


class InvestorOut(InvestorBase):
    investor_id: int
    user_id: int
    model_config = {"from_attributes": True}