from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user_role import UserRole

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user", lazy="selectin")

    # Investor
    investor = relationship("Investor", back_populates="user", uselist=False)

    # Company
    companies = relationship("Company", back_populates="user")

    # Recommendations
    investment_recommendations = relationship("InvestmentRecommendation", back_populates="user")
