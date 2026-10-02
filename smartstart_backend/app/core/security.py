from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
import bcrypt

from app.core.config import settings


# ─── Password ───────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─── JWT ────────────────────────────────────────────────────────────────────

def _create_token(
    subject: str,
    kind: Literal["access", "refresh"],
    extra: dict | None = None,
) -> str:
    if kind == "access":
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

    payload = {
        "sub":  str(subject),
        "type": kind,
        "exp":  expire,
        "iat":  datetime.now(timezone.utc),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: int, roles: list[str]) -> str:
    return _create_token(
        subject=str(user_id),
        kind="access",
        extra={"roles": roles},
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(subject=str(user_id), kind="refresh")


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError if invalid or expired."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])