from sqlalchemy import Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime


class InvestmentRecommendation(Base):
    __tablename__ = "investment_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False
    )

    ml_score: Mapped[float] = mapped_column(Float)
    business_score: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float] = mapped_column(Float)

    decision: Mapped[str] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    company = relationship("Company")