from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from jwt import InvalidTokenError

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.models.user_role import UserRole  

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 🔥 TOKEN
    if not credentials:
        print("❌ NO CREDENTIALS")
        raise credentials_exception

    token = credentials.credentials
    print("🔥 TOKEN:", token)

    try:
        payload = decode_token(token)

        print("🔥 PAYLOAD:", payload)

        # ❌ decode failed
        if payload is None:
            print("❌ PAYLOAD IS NONE")
            raise credentials_exception

        if payload.get("type") != "access":
            print("❌ INVALID TOKEN TYPE")
            raise credentials_exception

        user_id = payload.get("sub")
        print("🔥 USER_ID RAW:", user_id)

        if user_id is None:
            print("❌ NO USER ID")
            raise credentials_exception

        try:
            user_id = int(user_id)
        except Exception:
            print("❌ USER ID NOT INT")
            raise credentials_exception

    except InvalidTokenError as e:
        print("🔥 JWT INVALID:", e)
        raise credentials_exception

    except Exception as e:
        print("🔥 AUTH ERROR:", e)
        raise credentials_exception

    # 🔥 DB QUERY
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.user_id == user_id)
    )

    user = result.scalar_one_or_none()

    print("🔥 USER FOUND:", user)

    if not user or not user.is_active:
        print("❌ USER NOT FOUND OR INACTIVE")
        raise credentials_exception

    return user