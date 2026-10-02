from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user_role import UserRole

class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role", lazy="selectin")