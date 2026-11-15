"""
dependencies.py – FastAPI shared authentication & authorization dependencies.

Every protected endpoint must depend on get_current_user().
Resource endpoints additionally use verify_profile_access() and
resolve_resource_profile() to enforce care-circle membership (BOLA prevention).
"""
import os
from typing import Optional
from urllib.parse import urlparse

import jwt
from fastapi import Cookie, Depends, HTTPException, Header, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import decode_access_token
from database import get_db
from models import (
    Appointment,
    CaregiverFollowup,
    DoseSchedule,
    Medication,
    MedicationChangeRequest,
    Notification,
    PatientProfile,
    ProfileMembership,
    User,
)

# ---------------------------------------------------------------------------
# OAuth2 bearer extractor – used only for access-token extraction.
# auto_error=False so we can return a consistent 401 instead of a 403.
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Current-user dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract, validate, and return the authenticated User.

    Raises HTTP 401 for any authentication failure.
    Raises HTTP 403 if the user account is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalars().first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return user


# ---------------------------------------------------------------------------
# Profile membership check
# ---------------------------------------------------------------------------

async def verify_profile_access(
    profile_id: int,
    current_user: User,
    db: AsyncSession,
    allowed_roles: Optional[list[str]] = None,
) -> ProfileMembership:
    """Verify that current_user has an active membership in profile_id and demo isolation.

    Args:
        profile_id:    The patient profile being accessed.
        current_user:  The authenticated user.
        db:            DB session.
        allowed_roles: If provided, the membership role must be in this list.

    Returns the active ProfileMembership record.
    Raises HTTP 404 if profile does not exist.
    Raises HTTP 403 if demo boundary violated, no active membership exists, or role not allowed.
    """
    # 1. Enforce existence and demo isolation (User.is_demo == PatientProfile.is_demo)
    p_result = await db.execute(select(PatientProfile).where(PatientProfile.id == profile_id))
    profile: Optional[PatientProfile] = p_result.scalars().first()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    if bool(current_user.is_demo) != bool(profile.is_demo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-boundary access denied: demo accounts cannot access real profiles and real accounts cannot access demo profiles",
        )

    # 2. Enforce active care-circle membership
    result = await db.execute(
        select(ProfileMembership).where(
            ProfileMembership.user_id == current_user.id,
            ProfileMembership.profile_id == profile_id,
            ProfileMembership.status == "active",
        )
    )
    membership: Optional[ProfileMembership] = result.scalars().first()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not a member of this care circle",
        )
    if allowed_roles and membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: role '{membership.role}' is not permitted for this action",
        )
    return membership


# ---------------------------------------------------------------------------
# Resource → profile resolution helpers
# ---------------------------------------------------------------------------

async def get_profile_id_for_medication(medication_id: int, db: AsyncSession) -> int:
    """Return the profile_id that owns the given medication.  Raises 404 if not found."""
    result = await db.execute(
        select(Medication.profile_id).where(Medication.id == medication_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    return row[0]


async def get_profile_id_for_dose(dose_id: int, db: AsyncSession) -> int:
    """Return the profile_id that owns the given dose schedule via its medication."""
    result = await db.execute(
        select(Medication.profile_id)
        .join(DoseSchedule, DoseSchedule.medication_id == Medication.id)
        .where(DoseSchedule.id == dose_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Dose schedule not found")
    return row[0]


async def get_profile_id_for_appointment(appointment_id: int, db: AsyncSession) -> int:
    """Return the profile_id that owns the given appointment. Raises 404 if not found."""
    result = await db.execute(
        select(Appointment.profile_id).where(Appointment.id == appointment_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return row[0]


async def get_profile_id_for_followup(followup_id: int, db: AsyncSession) -> int:
    """Return the profile_id that owns the given followup via dose_schedule->medication."""
    result = await db.execute(
        select(Medication.profile_id)
        .join(DoseSchedule, DoseSchedule.medication_id == Medication.id)
        .join(CaregiverFollowup, CaregiverFollowup.dose_schedule_id == DoseSchedule.id)
        .where(CaregiverFollowup.id == followup_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Followup not found")
    return row[0]


async def get_profile_id_for_change(change_id: int, db: AsyncSession) -> int:
    """Return the profile_id that owns the given medication change request. Raises 404 if not found."""
    result = await db.execute(
        select(MedicationChangeRequest.profile_id).where(MedicationChangeRequest.id == change_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    return row[0]


async def get_profile_id_for_notification(notification_id: int, db: AsyncSession) -> int:
    """Return the profile_id that owns the given notification. Raises 404 if not found."""
    result = await db.execute(
        select(Notification.profile_id).where(Notification.id == notification_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return row[0]


# ---------------------------------------------------------------------------
# CSRF and Origin validation dependency
# ---------------------------------------------------------------------------

CSRF_HEADER = "X-CSRF-Token"
CSRF_COOKIE = "csrf_token"


def get_allowed_origins() -> set[str]:
    """Return the set of permitted frontend origins."""
    env = os.getenv("ENV", "development").lower()
    allowed = set()
    frontend_url = os.getenv("FRONTEND_URL")
    custom_origins = os.getenv("ALLOWED_ORIGINS")

    if env == "production":
        forbidden_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
        raw_origins = []
        if frontend_url and frontend_url.strip():
            raw_origins.append(frontend_url.strip())
        if custom_origins:
            for orig in custom_origins.split(","):
                if orig.strip():
                    raw_origins.append(orig.strip())

        for orig in raw_origins:
            parsed = urlparse(orig)
            hostname = (parsed.hostname or "").lower()
            if (
                parsed.scheme == "https"
                and hostname
                and hostname not in forbidden_hosts
                and not hostname.endswith(".localhost")
            ):
                allowed.add(f"{parsed.scheme}://{parsed.netloc}".rstrip("/"))
                allowed.add(orig.rstrip("/"))
    else:
        if frontend_url:
            allowed.add(frontend_url.rstrip("/"))
        if custom_origins:
            for orig in custom_origins.split(","):
                if orig.strip():
                    allowed.add(orig.strip().rstrip("/"))
        allowed.update({
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "testserver",
            "http://testserver",
        })
    return allowed


async def verify_csrf(
    request: Request,
    csrf_cookie: Optional[str] = Cookie(default=None, alias=CSRF_COOKIE),
) -> None:
    """Validate Origin/Referer and CSRF token for state-changing cookie operations.

    Must be used as a dependency on all state-changing endpoints that rely on
    cookies (refresh, logout).
    """
    # 1. Origin / Referer validation
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    allowed = get_allowed_origins()

    if origin:
        norm_origin = origin.rstrip("/")
        if norm_origin not in allowed and origin not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Origin '{origin}' is not permitted",
            )
    elif referer:
        parsed = urlparse(referer)
        ref_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        if ref_origin not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Referer origin '{ref_origin}' is not permitted",
            )
    else:
        env = os.getenv("ENV", "development").lower()
        if env == "production":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Origin or Referer header required for cookie-authenticated requests in production",
            )

    # 2. CSRF Token matching
    header_token = request.headers.get(CSRF_HEADER)
    if not header_token or not csrf_cookie or header_token != csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
