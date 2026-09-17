import jwt
import pytest

from app.core.config import Settings, assert_production_secrets_are_safe
from app.core.jwt import TokenError, create_access_token, decode_token
from tests.conftest import get_access_token


def _settings(**overrides) -> Settings:
    return Settings(**{"database_url": "x", "redis_url": "x", **overrides})


def test_production_startup_refuses_default_jwt_secret():
    # Explicit, not omitted: conftest sets a JWT_SECRET env var for the whole
    # test session (so real JWTs work in tests), which would otherwise get
    # picked up here instead of the insecure class default we're testing for.
    with pytest.raises(RuntimeError, match="insecure/missing JWT_SECRET"):
        assert_production_secrets_are_safe(
            _settings(env="production", jwt_secret="change-me-to-a-long-random-value")
        )


def test_production_startup_refuses_short_jwt_secret():
    with pytest.raises(RuntimeError):
        assert_production_secrets_are_safe(_settings(env="production", jwt_secret="short"))


def test_production_startup_accepts_strong_jwt_secret():
    strong = "x" * 40
    assert_production_secrets_are_safe(_settings(env="production", jwt_secret=strong))


def test_development_startup_does_not_check_jwt_secret():
    # The default/weak secret is fine in development — only production is guarded.
    assert_production_secrets_are_safe(_settings(env="development"))


async def test_tampered_token_signature_is_rejected():
    import uuid

    token = create_access_token(uuid.uuid4(), "customer")
    header, payload, _signature = token.split(".")
    forged = f"{header}.{payload}.forged-signature"

    with pytest.raises(TokenError):
        decode_token(forged, expected_type="access")


async def test_token_signed_with_wrong_secret_is_rejected():
    import uuid

    bad_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "role": "staff_admin", "type": "access"},
        "a-completely-different-secret",
        algorithm="HS256",
    )
    with pytest.raises(TokenError):
        decode_token(bad_token, expected_type="access")


async def test_expired_access_token_is_rejected():
    import datetime
    import uuid

    expired_payload = {
        "sub": str(uuid.uuid4()),
        "role": "customer",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2),
        "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
    }
    from app.core.config import settings as live_settings

    expired_token = jwt.encode(
        expired_payload, live_settings.jwt_secret, algorithm=live_settings.jwt_algorithm
    )

    with pytest.raises(TokenError):
        decode_token(expired_token, expected_type="access")


async def test_login_endpoint_actually_rate_limits(client, customer_user):
    # 5/minute is the configured limit (see app/api/auth.py); the 6th attempt
    # in the same window must be rejected regardless of credentials.
    responses = []
    for _ in range(6):
        response = await client.post(
            "/auth/login", json={"email": customer_user["email"], "password": "wrong-password"}
        )
        responses.append(response.status_code)

    assert responses[:5] == [401] * 5
    assert responses[5] == 429


async def test_staff_only_routes_reject_customer_token_everywhere(client, customer_user):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    staff_only_get_routes = [
        "/admin/ping",
        "/bookings",
        "/orders",
        "/analytics/summary",
        "/analytics/revenue",
        "/analytics/top-items",
        "/analytics/table-utilization",
        "/analytics/conversion",
    ]
    for path in staff_only_get_routes:
        response = await client.get(path, headers=headers)
        assert response.status_code == 403, f"{path} should reject a customer token"
