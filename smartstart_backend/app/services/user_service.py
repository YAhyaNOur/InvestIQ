from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User 
from app.schemas.user import UserProfileUpdate

def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserProfileUpdate

async def update_user_profile(db: AsyncSession, user: User, update_data: UserProfileUpdate) -> User:
    """Met à jour les champs fournis du profil utilisateur."""
    update_dict = update_data.dict(exclude_unset=True)  
    for field, value in update_dict.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user