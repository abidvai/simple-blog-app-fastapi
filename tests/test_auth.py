# pyrefly: ignore [missing-import]
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    reg_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "full_name": "Test User",
    }
    response = await client.post("/auth/register", json=reg_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert "id" in data

    login_data = {
        "username": "testuser",
        "password": "testpassword",
    }
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert profile["username"] == "testuser"

    response = await client.post("/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}

    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 401
