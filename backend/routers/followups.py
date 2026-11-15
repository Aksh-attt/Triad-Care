import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import CaregiverFollowup, DoseSchedule, Medication, User
from schemas import FollowupClaim, FollowupUpdate, FollowupOut
from dependencies import (
    get_current_user,
    verify_profile_access,
    get_profile_id_for_dose,
    get_profile_id_for_followup,
)

router = APIRouter()


async def _get_followups_for_profile(profile_id: int, db: AsyncSession):
    result = await db.execute(
        select(CaregiverFollowup)
        .join(DoseSchedule)
        .join(Medication)
        .options(
            selectinload(CaregiverFollowup.dose_schedule).selectinload(DoseSchedule.medication),
            selectinload(CaregiverFollowup.caregiver),
        )
        .where(Medication.profile_id == profile_id)
        .order_by(CaregiverFollowup.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{profile_id}", response_model=list[FollowupOut])
async def list_followups(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    return await _get_followups_for_profile(profile_id, db)


@router.get("/{profile_id}/active", response_model=list[FollowupOut])
async def list_active_followups(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    result = await db.execute(
        select(CaregiverFollowup)
        .join(DoseSchedule)
        .join(Medication)
        .options(
            selectinload(CaregiverFollowup.dose_schedule).selectinload(DoseSchedule.medication),
            selectinload(CaregiverFollowup.caregiver),
        )
        .where(
            Medication.profile_id == profile_id,
            CaregiverFollowup.status.notin_(["resolved"]),
        )
        .order_by(CaregiverFollowup.created_at.desc())
    )
    return result.scalars().all()


ALLOWED_ACTIONS = {"calling", "going_to_check", "unavailable"}
ALLOWED_STATUSES = {"unassigned", "accepted", "in_progress", "resolved", "reassigned"}

VALID_TRANSITIONS = {
    "unassigned": {"accepted", "reassigned"},
    "accepted": {"in_progress", "resolved", "reassigned"},
    "in_progress": {"resolved", "reassigned"},
    "reassigned": {"accepted", "in_progress", "resolved"},
    "resolved": set(),  # Terminal state: cannot transition once resolved
}


@router.post("/claim", response_model=FollowupOut)
async def claim_followup(
    body: FollowupClaim,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{body.action}'. Must be one of: {', '.join(ALLOWED_ACTIONS)}",
        )

    # Role enforcement: Only registered caregivers can claim follow-up
    if current_user.role != "caregiver":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only registered caregivers can claim follow-up responsibility",
        )

    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_dose(body.dose_schedule_id, db)
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["caregiver"])

    # Verify dose exists
    result = await db.execute(
        select(DoseSchedule)
        .options(selectinload(DoseSchedule.medication))
        .where(DoseSchedule.id == body.dose_schedule_id)
    )
    dose = result.scalars().first()
    if not dose:
        raise HTTPException(status_code=404, detail="Dose schedule not found")

    if dose.status == "taken":
        raise HTTPException(
            status_code=400,
            detail="Invalid request: Dose has already been taken. Follow-up is only applicable to overdue or unconfirmed doses",
        )

    # Eliminate client-controlled identity: set strictly from authenticated user
    followup = CaregiverFollowup(
        dose_schedule_id=body.dose_schedule_id,
        caregiver_id=current_user.id,
        action=body.action,
        status="accepted",
        accepted_at=datetime.datetime.now(),
    )
    db.add(followup)
    await db.commit()
    await db.refresh(followup)

    # Reload with relationships
    result = await db.execute(
        select(CaregiverFollowup)
        .options(
            selectinload(CaregiverFollowup.dose_schedule).selectinload(DoseSchedule.medication),
            selectinload(CaregiverFollowup.caregiver),
        )
        .where(CaregiverFollowup.id == followup.id)
    )
    return result.scalars().first()


@router.put("/{followup_id}", response_model=FollowupOut)
async def update_followup(
    followup_id: int,
    body: FollowupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.status and body.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{body.status}'. Must be one of: {', '.join(ALLOWED_STATUSES)}",
        )

    if body.action and body.action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{body.action}'. Must be one of: {', '.join(ALLOWED_ACTIONS)}",
        )

    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_followup(followup_id, db)
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["caregiver"])

    result = await db.execute(
        select(CaregiverFollowup)
        .options(
            selectinload(CaregiverFollowup.dose_schedule).selectinload(DoseSchedule.medication),
            selectinload(CaregiverFollowup.caregiver),
        )
        .where(CaregiverFollowup.id == followup_id)
    )
    followup = result.scalars().first()
    if not followup:
        raise HTTPException(status_code=404, detail="Followup not found")

    # Only the assigned caregiver can update this follow-up
    if followup.caregiver_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You are not the caregiver assigned to this follow-up",
        )

    # State transition enforcement
    if body.status and body.status != followup.status:
        allowed_next = VALID_TRANSITIONS.get(followup.status, set())
        if body.status not in allowed_next:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state transition: Cannot transition from '{followup.status}' to '{body.status}'",
            )

    update_data = body.model_dump(exclude_unset=True)
    update_data.pop("resolved_at", None)  # Strictly reject or ignore client-supplied resolved_at

    for field, value in update_data.items():
        setattr(followup, field, value)

    # Resolution timestamps generated strictly on the server
    if body.status == "resolved":
        followup.resolved_at = datetime.datetime.now()

    await db.commit()
    await db.refresh(followup)
    return followup
