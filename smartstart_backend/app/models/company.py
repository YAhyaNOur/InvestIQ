from typing import Optional
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime


class Company(Base):
    __tablename__ = "companies"

    company_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    name: Mapped[Optional[str]] = mapped_column(String(255))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry_group: Mapped[Optional[str]] = mapped_column(String(100))
    region_std: Mapped[Optional[str]] = mapped_column(String(100))

    beta: Mapped[Optional[float]] = mapped_column(Float)
    ebitda_margins: Mapped[Optional[float]] = mapped_column(Float)
    net_debt: Mapped[Optional[float]] = mapped_column(Float)
    revenue_per_employee: Mapped[Optional[float]] = mapped_column(Float)

    # ── NOUVEAUX — alimentés par le formulaire utilisateur ──
    revenue_growth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # ────────────────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="companies")
    recommendations = relationship("InvestmentRecommendation", back_populates="company")