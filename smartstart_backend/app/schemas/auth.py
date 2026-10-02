from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    password: str
    role: str = "STARTUPER"  # STARTUPER | INVESTOR

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username: letters, numbers, underscores only")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a digit")
        return v

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        allowed = {"STARTUPER", "INVESTOR"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None  # STARTUPER | INVESTOR (obligatoire si le compte a les deux rôles)

    @field_validator("role")
    @classmethod
    def login_role_valid(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        v = v.upper()
        if v not in {"STARTUPER", "INVESTOR"}:
            raise ValueError("Role must be STARTUPER or INVESTOR")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    roles: list[str]
    avatar_url: str | None = None

    model_config = {"from_attributes": True}