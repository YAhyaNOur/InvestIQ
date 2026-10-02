from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User
from app.models.user_role import UserRole          
from app.models.role import Role
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


async def _get_user_roles(user: User) -> list[str]:
    """Extract role names from loaded relationships."""
    return [ur.role.name for ur in user.user_roles if ur.role]

async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """
    Règle d'inscription :
    - Même email + même rôle -> 409
    - Même email + rôle différent -> autorisé
    - Même username -> autorisé
    """

    # 1. Récupérer le rôle demandé
    role_result = await db.execute(
        select(Role).where(Role.name == data.role)
    )
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le rôle '{data.role}' n'existe pas.",
        )

    # 2. Vérifier UNIQUEMENT si email + rôle existe déjà
    result = await db.execute(
        select(User)
        .join(UserRole, User.user_id == UserRole.user_id)
        .where(
            User.email == data.email,
            UserRole.role_id == role.role_id
        )
    )

    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cet email a déjà un compte {data.role}.",
        )

    # 3. Créer TOUJOURS un nouveau compte
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        password=hash_password(data.password),
        is_active=True,
    )

    db.add(user)
    await db.flush()

    # 4. Ajouter le rôle au nouveau compte
    db.add(
        UserRole(
            user_id=user.user_id,
            role_id=role.role_id
        )
    )

    await db.commit()

    # 5. Recharger avec les relations
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role)
        )
        .where(User.user_id == user.user_id)
        .execution_options(populate_existing=True)
    )

    return result.scalar_one()

async def login_user(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    # Le rôle est obligatoire car plusieurs comptes
    # peuvent avoir le même email.
    if not data.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le rôle est obligatoire pour se connecter.",
        )

    # 1. Récupérer le rôle demandé
    role_result = await db.execute(
        select(Role).where(Role.name == data.role)
    )

    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le rôle '{data.role}' n'existe pas.",
        )

    # 2. Chercher le compte avec EMAIL + RÔLE
    result = await db.execute(
        select(User)
        .join(
            UserRole,
            User.user_id == UserRole.user_id
        )
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role)
        )
        .where(
            User.email == data.email,
            UserRole.role_id == role.role_id,
        )
    )

    user = result.scalar_one_or_none()

    # 3. Vérifier le mot de passe
    if (
        not user
        or not user.password
        or not verify_password(data.password, user.password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    # 4. Vérifier que le compte est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    # 5. Créer les tokens avec le rôle choisi
    return TokenResponse(
        access_token=create_access_token(
            user.user_id,
            [data.role],
        ),
        refresh_token=create_refresh_token(
            user.user_id,
        ),
    )
async def get_or_create_google_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    full_name: str,
    avatar_url: str,
) -> User:
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.google_id == google_id)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user:
        user.google_id = google_id
        user.avatar_url = avatar_url
        await db.flush()
        return user

    username = email.split("@")[0].lower().replace(".", "_")
    check = await db.execute(select(User).where(User.username == username))
    if check.scalar_one_or_none():
        username = f"{username}_{google_id[:6]}"

    role_result = await db.execute(select(Role).where(Role.name == "STARTUPER"))
    role = role_result.scalar_one_or_none()

    new_user = User(
        username=username, email=email, full_name=full_name,
        google_id=google_id, avatar_url=avatar_url, is_active=True,
    )
    db.add(new_user)
    await db.flush()

    if role:
        db.add(UserRole(user_id=new_user.user_id, role_id=role.role_id))
        await db.flush()

    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.user_id == new_user.user_id)
    )
    return result.scalar_one()