from typing import Optional
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime

class Investor(Base):
    __tablename__ = "investors"

    investor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    risk_profile: Mapped[Optional[str]] = mapped_column(String(20))
    preferred_sector: Mapped[Optional[str]] = mapped_column(String(100))

    min_return: Mapped[Optional[float]] = mapped_column(Float)
    max_risk: Mapped[Optional[float]] = mapped_column(Float)

    budget: Mapped[Optional[float]] = mapped_column(Float)
    region_std: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  

    portfolio_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_companies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="investor")