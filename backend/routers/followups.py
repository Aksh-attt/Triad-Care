import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import CaregiverFollowup, DoseSchedule, Medication, User
from schemas import FollowupClaim, FollowupUpdate, FollowupOut

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
async def list_followups(profile_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_followups_for_profile(profile_id, db)


@router.get("/{profile_id}/active", response_model=list[FollowupOut])
async def list_active_followups(profile_id: int, db: AsyncSession = Depends(get_db)):
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
            CaregiverFollowup.status.notin_(["resolved"])
        )
        .order_by(CaregiverFollowup.created_at.desc())
    )
    return result.scalars().all()


ALLOWED_ACTIONS = {"calling", "going_to_check", "unavailable"}
ALLOWED_STATUSES = {"unassigned", "accepted", "in_progress", "resolved", "reassigned"}


@router.post("/claim", response_model=FollowupOut)
async def claim_followup(body: FollowupClaim, db: AsyncSession = Depends(get_db)):
    if body.action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{body.action}'. Must be one of: {', '.join(ALLOWED_ACTIONS)}",
        )

    # Role enforcement: verify user exists and has role 'caregiver'
    u_res = await db.execute(select(User).where(User.id == body.caregiver_id))
    user = u_res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Caregiver user not found")
    if user.role != "caregiver":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only registered caregivers can claim follow-up responsibility",
        )

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

    # CRITICAL: MUST NOT change dose status
    followup = CaregiverFollowup(
        dose_schedule_id=body.dose_schedule_id,
        caregiver_id=body.caregiver_id,
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
async def update_followup(followup_id: int, body: FollowupUpdate, db: AsyncSession = Depends(get_db)):
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

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(followup, field, value)

    if body.status == "resolved" and not followup.resolved_at:
        followup.resolved_at = datetime.datetime.now()

    await db.commit()
    await db.refresh(followup)
    return followup
