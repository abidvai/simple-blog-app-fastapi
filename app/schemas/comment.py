from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    content: str
    post_id: int
    author: UserPublic
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
