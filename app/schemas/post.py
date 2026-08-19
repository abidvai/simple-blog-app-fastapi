from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    content: str = Field(..., min_length=10)
    excerpt: str | None = Field(None, max_length=500)
    is_published: bool = False
    category_ids: list[int] = []


class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=255)
    content: str | None = Field(None, min_length=10)
    excerpt: str | None = Field(None, max_length=500)
    is_published: bool | None = None
    category_ids: list[int] | None = None


class PostOut(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str | None
    is_published: bool
    author: UserPublic
    categories: list[CategoryOut]
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostListOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str | None
    is_published: bool
    author: UserPublic
    categories: list[CategoryOut]
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}



class PaginatedPosts(BaseModel):
    total: int
    page: int
    size: int
    results: list[PostListOut]
