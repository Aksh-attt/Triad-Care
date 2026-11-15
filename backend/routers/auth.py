"""
routers/auth.py – Triad Care authentication endpoints (Security Upgrade v2).

Endpoints:
  POST /api/auth/login            – Argon2id login → access JWT + HttpOnly refresh cookie
  POST /api/auth/demo-login       – Demo persona login (DEMO_MODE=true only)
  POST /api/auth/refresh          – Atomic refresh-token rotation (CSRF + cookie)
  POST /api/auth/logout           – Family-wide token revocation (CSRF + cookie)
  GET  /api/auth/me               – Authenticated user info and memberships
  GET  /api/auth/csrf-bootstrap   – Issue CSRF token for session restoration
  GET  /api/auth/demo-users       – Public demo user list (no passcodes/hashes returned)
"""
import os
from datetime import datetime, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_utils import (
    create_access_token,
    decode_access_token,
    generate_csrf_token,
    generate_refresh_token,
    hash_refresh_token,
    new_family_id,
    refresh_token_expires_at,
    verify_password,
)
from database import get_db
from dependencies import get_current_user, verify_csrf
from models import ProfileMembership, RefreshToken, User
from schemas import LoginRequest, LoginResponse, MembershipOut, UserOut
from pydantic import BaseModel


class DemoLoginRequest(BaseModel):
    role: str   # elderly | caregiver | family


router = APIRouter()

DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
SECURE_COOKIE: bool = os.getenv("ENV", "development").lower() == "production"
REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_refresh_cookie(response: Response, plain_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=plain_token,
        httponly=True,
        samesite="lax",
        secure=SECURE_COOKIE,
        path="/api/auth",
        max_age=7 * 24 * 60 * 60,
    )


def _set_csrf_cookie(response: Response, csrf_token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,     # Must be readable by JS so it can be sent as a header
        samesite="lax",
        secure=SECURE_COOKIE,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/auth")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")


async def _build_login_response(
    user: User,
    db: AsyncSession,
    response: Response,
) -> LoginResponse:
    """Create tokens, set cookies, return LoginResponse."""
    access_token = create_access_token(user.id)
    plain_refresh, refresh_hash = generate_refresh_token()
    csrf_token = generate_csrf_token()
    family = new_family_id()

    new_rt = RefreshToken(
        user_id=user.id,
        family_id=family,
        token_hash=refresh_hash,
        expires_at=refresh_token_expires_at(),
    )
    db.add(new_rt)
    await db.commit()

    _set_refresh_cookie(response, plain_refresh)
    _set_csrf_cookie(response, csrf_token)

    mem_result = await db.execute(
        select(ProfileMembership)
        .options(selectinload(ProfileMembership.user))
        .where(ProfileMembership.user_id == user.id, ProfileMembership.status == "active")
    )
    memberships = mem_result.scalars().all()

    return LoginResponse(
        user=UserOut.model_validate(user),
        memberships=[MembershipOut.model_validate(m) for m in memberships],
        access_token=access_token,
        csrf_token=csrf_token,
    )


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@router.get("/demo-users", response_model=list[UserOut])
async def get_demo_users(db: AsyncSession = Depends(get_db)):
    """Return all demo users (no credentials in response)."""
    result = await db.execute(select(User).where(User.is_demo == True))  # noqa: E712
    return result.scalars().all()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Authenticate with username + password or legacy/demo passcode (Argon2id).

    Returns an access JWT in the body and sets an HttpOnly refresh cookie.
    """
    invalid_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user: Optional[User] = None

    if body.passcode:
        # Check against users whose Argon2id hashed_password matches the passcode
        result = await db.execute(select(User).where(User.hashed_password != None))  # noqa: E711
        candidates = result.scalars().all()
        for candidate in candidates:
            if candidate.hashed_password and verify_password(candidate.hashed_password, body.passcode):
                user = candidate
                break
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid passcode")
    elif body.username and body.password:
        # Look up by name or email – supports both "Meera Sharma" and email
        result = await db.execute(
            select(User).where(
                (User.name == body.username) | (User.email == body.username)
            )
        )
        user = result.scalars().first()
        if not user or not user.hashed_password or not verify_password(user.hashed_password, body.password):
            raise invalid_exc
    else:
        raise invalid_exc

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return await _build_login_response(user, db, response)


@router.post("/demo-login", response_model=LoginResponse)
async def demo_login(body: "DemoLoginRequest", response: Response, db: AsyncSession = Depends(get_db)):
    """Authenticate as a demo persona by role.  Only active when DEMO_MODE=true."""
    if not DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    result = await db.execute(
        select(User).where(User.role == body.role, User.is_demo == True)  # noqa: E712
    )
    user: Optional[User] = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo user not found")

    return await _build_login_response(user, db, response)


# ---------------------------------------------------------------------------
# Token management (require CSRF verification)
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=LoginResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_cookie: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    _csrf: None = Depends(verify_csrf),
):
    """Rotate the refresh token and issue a new access JWT.

    Implements single-successor enforcement and replay detection.
    """
    invalid_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    if not refresh_cookie:
        raise invalid_exc

    token_hash = hash_refresh_token(refresh_cookie)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt: Optional[RefreshToken] = result.scalars().first()

    if rt is None:
        raise invalid_exc

    # Replay detection: if token already revoked, revoke entire family
    if rt.revoked_at is not None:
        await _revoke_family(rt.family_id, db)
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected – session revoked. Please log in again.",
        )

    if rt.expires_at.replace(tzinfo=timezone.utc) < now:
        raise invalid_exc

    # Revoke old token and create single successor in one transaction
    rt.revoked_at = now

    plain_new, hash_new = generate_refresh_token()
    new_rt = RefreshToken(
        user_id=rt.user_id,
        family_id=rt.family_id,
        token_hash=hash_new,
        parent_token_id=rt.id,
        expires_at=refresh_token_expires_at(),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_rt)
    await db.flush()
    rt.replaced_by_token_id = new_rt.id
    await db.commit()

    # Fetch user
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user: Optional[User] = user_result.scalars().first()
    if not user or not user.is_active:
        raise invalid_exc

    access_token = create_access_token(user.id)
    csrf_token = generate_csrf_token()

    _set_refresh_cookie(response, plain_new)
    _set_csrf_cookie(response, csrf_token)

    mem_result = await db.execute(
        select(ProfileMembership)
        .options(selectinload(ProfileMembership.user))
        .where(ProfileMembership.user_id == user.id, ProfileMembership.status == "active")
    )
    memberships = mem_result.scalars().all()

    return LoginResponse(
        user=UserOut.model_validate(user),
        memberships=[MembershipOut.model_validate(m) for m in memberships],
        access_token=access_token,
        csrf_token=csrf_token,
    )


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_cookie: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    _csrf: None = Depends(verify_csrf),
):
    """Revoke all refresh tokens in the family and clear cookies.

    Succeeds even if the access JWT has expired (no get_current_user dependency here).
    """
    if refresh_cookie:
        token_hash = hash_refresh_token(refresh_cookie)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        rt: Optional[RefreshToken] = result.scalars().first()
        if rt:
            await _revoke_family(rt.family_id, db)

    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/csrf-bootstrap")
async def csrf_bootstrap(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_cookie: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """Issue a fresh CSRF token for browser session restoration.

    Validates that an active (non-expired, non-revoked) refresh token is present
    but does NOT rotate it.  The frontend should follow up with /refresh.
    """
    if not refresh_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")

    token_hash = hash_refresh_token(refresh_cookie)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at == None,  # noqa: E711
        )
    )
    rt: Optional[RefreshToken] = result.scalars().first()
    if not rt or rt.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    csrf_token = generate_csrf_token()
    _set_csrf_cookie(response, csrf_token)
    return {"csrf_token": csrf_token}


@router.get("/me", response_model=LoginResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile and active memberships."""
    mem_result = await db.execute(
        select(ProfileMembership)
        .options(selectinload(ProfileMembership.user))
        .where(ProfileMembership.user_id == current_user.id, ProfileMembership.status == "active")
    )
    memberships = mem_result.scalars().all()
    return LoginResponse(
        user=UserOut.model_validate(current_user),
        memberships=[MembershipOut.model_validate(m) for m in memberships],
        access_token=None,
        csrf_token=None,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _revoke_family(family_id: str, db: AsyncSession) -> None:
    """Revoke all active tokens in a refresh-token family."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at == None,  # noqa: E711
        )
    )
    for rt in result.scalars().all():
        rt.revoked_at = now
    await db.commit()
