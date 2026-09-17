import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import TokenError, create_access_token, create_refresh_token, decode_token
from app.core.limiter import limiter
from app.core.refresh_store import (
    is_refresh_token_active,
    revoke_refresh_token,
    store_refresh_token,
)
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_token_pair(user: User) -> TokenResponse:
    access_token = create_access_token(user.id, user.role.value)
    refresh_token, jti = create_refresh_token(user.id, user.role.value)
    await store_refresh_token(user.id, jti)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.customer,
        phone=payload.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    return await _issue_token_pair(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    invalid_token_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
    )

    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise invalid_token_error from exc

    jti = claims["jti"]

    try:
        user_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise invalid_token_error from exc

    if not await is_refresh_token_active(user_id, jti):
        raise invalid_token_error

    user = await db.get(User, user_id)
    if user is None:
        raise invalid_token_error

    # Rotate: the old refresh token is single-use.
    await revoke_refresh_token(user_id, jti)
    return await _issue_token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest) -> None:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError:
        # Logout is idempotent: an already-invalid token is not an error.
        return None

    await revoke_refresh_token(claims["sub"], claims["jti"])
    return None
