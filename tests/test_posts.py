# pyrefly: ignore [missing-import]
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


@pytest.mark.asyncio
async def test_posts_flow(client: AsyncClient, db_session: AsyncSession):
    reg_data = {
        "username": "author1",
        "email": "author1@example.com",
        "password": "authorpassword",
    }
    await client.post("/auth/register", json=reg_data)

    login_data = {"username": "author1", "password": "authorpassword"}
    login_resp = await client.post("/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    category = Category(name="Tech", slug="tech")
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    post_data = {
        "title": "My first FastAPI post",
        "content": "This is the content of my first blog post.",
        "excerpt": "Excerpt of post",
        "is_published": True,
        "category_ids": [category.id],
    }
    post_resp = await client.post("/posts", json=post_data, headers=headers)
    assert post_resp.status_code == 201
    post = post_resp.json()
    assert post["title"] == "My first FastAPI post"
    assert post["author"]["username"] == "author1"
    assert len(post["categories"]) == 1
    assert post["categories"][0]["name"] == "Tech"
    post_id = post["id"]

    get_resp = await client.get(f"/posts/{post_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "My first FastAPI post"

    like_resp = await client.post(f"/posts/{post_id}/like", headers=headers)
    assert like_resp.status_code == 200
    assert like_resp.json()["liked"] is True

    get_resp = await client.get(f"/posts/{post_id}")
    assert get_resp.json()["like_count"] == 1

    unlike_resp = await client.post(f"/posts/{post_id}/like", headers=headers)
    assert unlike_resp.status_code == 200
    assert unlike_resp.json()["liked"] is False

    get_resp = await client.get(f"/posts/{post_id}")
    assert get_resp.json()["like_count"] == 0

    comment_data = {"content": "This is a comment"}
    comment_resp = await client.post(f"/posts/{post_id}/comments", json=comment_data, headers=headers)
    assert comment_resp.status_code == 201
    comment = comment_resp.json()
    assert comment["content"] == "This is a comment"
    assert comment["author"]["username"] == "author1"
    comment_id = comment["id"]

    comments_list_resp = await client.get(f"/posts/{post_id}/comments")
    assert comments_list_resp.status_code == 200
    assert len(comments_list_resp.json()) == 1

    del_comment_resp = await client.delete(f"/posts/{post_id}/comments/{comment_id}", headers=headers)
    assert del_comment_resp.status_code == 204

    comments_list_resp = await client.get(f"/posts/{post_id}/comments")
    assert len(comments_list_resp.json()) == 0
