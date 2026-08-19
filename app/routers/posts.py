import json
import re

import redis.asyncio as aioredis  # pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db, get_redis
from app.models.category import Category
from app.models.comment import Comment
from app.models.post import Like, Post
from app.models.user import User
from app.schemas.post import PaginatedPosts, PostCreate, PostListOut, PostOut, PostUpdate

router = APIRouter(prefix="/posts", tags=["Posts"])

CACHE_TTL = 300


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug


async def _get_like_count(post_id: int, db: AsyncSession, redis: aioredis.Redis) -> int:
    cached = await redis.get(f"likes:post:{post_id}")
    if cached is not None:
        return int(cached)
    result = await db.execute(select(func.count()).where(Like.post_id == post_id))
    count = result.scalar() or 0
    await redis.setex(f"likes:post:{post_id}", CACHE_TTL, count)
    return count


@router.get("", response_model=PaginatedPosts)
async def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    published_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    cache_key = f"posts:list:p{page}:s{size}:search={search}:pub={published_only}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    query = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.categories),
    )
    count_query = select(func.count()).select_from(Post)

    if published_only:
        query = query.where(Post.is_published == True)
        count_query = count_query.where(Post.is_published == True)

    if search:
        query = query.where(Post.title.ilike(f"%{search}%"))
        count_query = count_query.where(Post.title.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * size
    posts = (await db.execute(query.offset(offset).limit(size).order_by(Post.created_at.desc()))).scalars().all()

    results = []
    for post in posts:
        like_count = await _get_like_count(post.id, db, redis)
        comment_count_res = await db.execute(
            select(func.count()).where(Comment.post_id == post.id)
        )
        comment_count = comment_count_res.scalar() or 0
        item = PostListOut.model_validate(post)
        item.like_count = like_count
        item.comment_count = comment_count
        results.append(item)

    response = PaginatedPosts(total=total, page=page, size=size, results=results)
    await redis.setex(cache_key, CACHE_TTL, response.model_dump_json())
    return response


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slug = _slugify(post_in.title)
    existing = (await db.execute(select(Post).where(Post.slug == slug))).scalar_one_or_none()
    if existing:
        slug = f"{slug}-{current_user.id}"

    categories = []
    if post_in.category_ids:
        result = await db.execute(select(Category).where(Category.id.in_(post_in.category_ids)))
        categories = list(result.scalars().all())

    post = Post(
        title=post_in.title,
        slug=slug,
        content=post_in.content,
        excerpt=post_in.excerpt,
        is_published=post_in.is_published,
        author_id=current_user.id,
        categories=categories,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post, ["author", "categories"])
    return PostOut.model_validate(post)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.categories))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like_count = await _get_like_count(post.id, db, redis)
    comment_count = (
        await db.execute(select(func.count()).where(Comment.post_id == post.id))
    ).scalar() or 0

    out = PostOut.model_validate(post)
    out.like_count = like_count
    out.comment_count = comment_count
    return out


@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    result = await db.execute(
        select(Post).options(selectinload(Post.author), selectinload(Post.categories)).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if post_update.title is not None:
        post.title = post_update.title
        post.slug = _slugify(post_update.title)
    if post_update.content is not None:
        post.content = post_update.content
    if post_update.excerpt is not None:
        post.excerpt = post_update.excerpt
    if post_update.is_published is not None:
        post.is_published = post_update.is_published
    if post_update.category_ids is not None:
        cats = (await db.execute(select(Category).where(Category.id.in_(post_update.category_ids)))).scalars().all()
        post.categories = list(cats)

    await db.commit()
    await db.refresh(post, ["author", "categories"])

    await redis.delete(f"likes:post:{post_id}")

    return PostOut.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(post)
    await db.commit()
    await redis.delete(f"likes:post:{post_id}")


@router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
async def toggle_like(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_like = (
        await db.execute(select(Like).where(Like.post_id == post_id, Like.user_id == current_user.id))
    ).scalar_one_or_none()

    if existing_like:
        await db.delete(existing_like)
        await db.commit()
        await redis.decr(f"likes:post:{post_id}")
        return {"liked": False, "message": "Like removed"}
    else:
        like = Like(post_id=post_id, user_id=current_user.id)
        db.add(like)
        await db.commit()
        await redis.incr(f"likes:post:{post_id}")
        await redis.expire(f"likes:post:{post_id}", CACHE_TTL)
        return {"liked": True, "message": "Post liked"}

