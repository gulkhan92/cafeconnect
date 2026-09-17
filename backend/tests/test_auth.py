import pytest

pytestmark = pytest.mark.asyncio


async def _register(client, email="new@example.com", password="SecurePass123!"):
    return await client.post(
        "/auth/register",
        json={"name": "New User", "email": email, "password": password},
    )


async def test_register_creates_customer(client):
    response = await _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "customer"
    assert "hashed_password" not in body


async def test_register_duplicate_email_is_rejected(client):
    await _register(client)
    response = await _register(client)
    assert response.status_code == 409


async def test_login_success_returns_token_pair(client):
    await _register(client, email="login@example.com", password="SecurePass123!")
    response = await client.post(
        "/auth/login", json={"email": "login@example.com", "password": "SecurePass123!"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_is_rejected(client):
    await _register(client, email="wrongpw@example.com", password="SecurePass123!")
    response = await client.post(
        "/auth/login", json={"email": "wrongpw@example.com", "password": "NotTheRightOne!"}
    )
    assert response.status_code == 401


async def test_protected_route_requires_token(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_protected_route_returns_current_user(client):
    await _register(client, email="me@example.com", password="SecurePass123!")
    login = await client.post(
        "/auth/login", json={"email": "me@example.com", "password": "SecurePass123!"}
    )
    access_token = login.json()["access_token"]

    response = await client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_refresh_rotates_token_and_revokes_old_one(client):
    await _register(client, email="refresh@example.com", password="SecurePass123!")
    login = await client.post(
        "/auth/login", json={"email": "refresh@example.com", "password": "SecurePass123!"}
    )
    old_refresh_token = login.json()["refresh_token"]

    refreshed = await client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != old_refresh_token

    reuse_attempt = await client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert reuse_attempt.status_code == 401


async def test_logout_revokes_refresh_token(client):
    await _register(client, email="logout@example.com", password="SecurePass123!")
    login = await client.post(
        "/auth/login", json={"email": "logout@example.com", "password": "SecurePass123!"}
    )
    refresh_token = login.json()["refresh_token"]

    logout_response = await client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    reuse_attempt = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_attempt.status_code == 401


async def test_staff_only_route_forbidden_for_customer(client, customer_user):
    login = await client.post("/auth/login", json=customer_user)
    access_token = login.json()["access_token"]

    response = await client.get("/admin/ping", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 403


async def test_staff_only_route_allowed_for_staff_admin(client, staff_user):
    login = await client.post("/auth/login", json=staff_user)
    access_token = login.json()["access_token"]

    response = await client.get("/admin/ping", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
