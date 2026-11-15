"""
dependencies.py – FastAPI shared authentication & authorization dependencies.

Every protected endpoint must depend on get_current_user().
Resource endpoints additionally use verify_profile_access() and
resolve_resource_profile() to enforce care-circle membership (BOLA prevention).
"""
from typing import Optional

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
    """Verify that current_user has an active membership in profile_id.

    Args:
        profile_id:    The patient profile being accessed.
        current_user:  The authenticated user.
        db:            DB session.
        allowed_roles: If provided, the membership role must be in this list.

    Returns the active ProfileMembership record.
    Raises HTTP 403 if no active membership exists (or role not allowed).
    """
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
# CSRF validation dependency (for cookie-dependent mutating endpoints)
# ---------------------------------------------------------------------------

CSRF_HEADER = "X-CSRF-Token"
CSRF_COOKIE = "csrf_token"


async def verify_csrf(
    request: Request,
    csrf_cookie: Optional[str] = Cookie(default=None, alias=CSRF_COOKIE),
) -> None:
    """Verify that the X-CSRF-Token header matches the csrf_token cookie.

    Must be used as a dependency on all state-changing endpoints that also
    rely on the HttpOnly refresh cookie (refresh, logout).
    """
    header_token = request.headers.get(CSRF_HEADER)
    if not header_token or not csrf_cookie or header_token != csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
