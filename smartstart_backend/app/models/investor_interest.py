from sqlalchemy import Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime


class InvestorInterest(Base):
    __tablename__ = "investor_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False
    )

    interested: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    company = relationship("Company")