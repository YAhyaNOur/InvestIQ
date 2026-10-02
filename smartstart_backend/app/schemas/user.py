from typing import Optional
from pydantic import BaseModel, EmailStr


class UserProfileOut(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = {"from_attributes": True}
