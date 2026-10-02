from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import jwt

from app.db.session import get_db
from app.schemas.user import UserProfileOut, UserProfileUpdate
from app.services.user_service import update_user_profile
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/profile", tags=["Profile"])
security = HTTPBearer()

# --- Get current user from JWT token ---
import logging

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        logging.info(f"JWT payload: {payload}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as e:
        logging.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        result = await db.execute(select(User).where(User.user_id  == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except Exception as e:
        logging.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return user
# --- Read profile ---
@router.get("", response_model=UserProfileOut)
async def read_profile(current_user: User = Depends(get_current_user)):
    return current_user

# --- Update profile ---
@router.patch("/update", response_model=UserProfileOut)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await update_user_profile(db, current_user, profile_update)
    return updated_user