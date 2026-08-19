from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = Field(None, max_length=100)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None
    bio: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    id: int
    username: str
    full_name: str | None
    bio: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

