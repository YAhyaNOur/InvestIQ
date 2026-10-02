from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import jwt
import httpx

from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user
from app.models.user import User
from app.models.user_role import UserRole       

from app.schemas.auth import (
    RegisterRequest, LoginRequest,
    TokenResponse, RefreshRequest, UserOut,
)
from app.services.auth_service import (
    register_user, login_user, get_or_create_google_user, _get_user_roles,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

GOOGLE_AUTH_URL   = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL  = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO   = "https://www.googleapis.com/oauth2/v3/userinfo"


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new account and return tokens immediately."""
    user = await register_user(db, data)
    roles = [data.role]  # on se connecte avec le rôle qu'on vient de choisir
    return TokenResponse(
        access_token=create_access_token(user.user_id, roles),
        refresh_token=create_refresh_token(user.user_id),
    )


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email + password, returns JWT tokens."""
    return await login_user(db, data)


# ─── Refresh ─────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.user_id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    roles = await _get_user_roles(user)
    return TokenResponse(
        access_token=create_access_token(user.user_id, roles),
        refresh_token=create_refresh_token(user.user_id),
    )


# ─── Me ──────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserOut(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        roles=[ur.role.name for ur in current_user.user_roles if ur.role],
        avatar_url=current_user.avatar_url,
    )
