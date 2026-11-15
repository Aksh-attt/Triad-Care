import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import DoseSchedule, Medication, User
from schemas import DoseScheduleOut, DoseConfirm, DoseReason
from dependencies import (
    get_current_user,
    verify_profile_access,
    get_profile_id_for_dose,
)

router = APIRouter()


@router.get("/{profile_id}/today", response_model=list[DoseScheduleOut])
async def get_today_doses(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    today = datetime.date.today()
    start = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)

    result = await db.execute(
        select(DoseSchedule)
        .join(Medication)
        .options(selectinload(DoseSchedule.medication))
        .where(
            Medication.profile_id == profile_id,
            Medication.is_active == True,
            DoseSchedule.scheduled_time >= start,
            DoseSchedule.scheduled_time <= end,
        )
    )
    return result.scalars().all()


@router.post("/{dose_id}/confirm", response_model=DoseScheduleOut)
async def confirm_dose(
    dose_id: int,
    body: DoseConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_dose(dose_id, db)
    await verify_profile_access(profile_id, current_user, db)

    # Permission matrix check: family members cannot confirm doses
    if current_user.role == "family":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Family members cannot confirm medication doses per permission matrix",
        )

    result = await db.execute(
        select(DoseSchedule)
        .options(selectinload(DoseSchedule.medication))
        .where(DoseSchedule.id == dose_id)
    )
    dose = result.scalars().first()
    if not dose:
        raise HTTPException(status_code=404, detail="Dose not found")

    # Determine confirmation method based on role and payload
    if current_user.role == "elderly":
        method = "patient_confirmed"
    elif current_user.role == "caregiver":
        method = body.confirmation_method if body.confirmation_method in ["caregiver_observed", "caregiver_reported"] else "caregiver_observed"
    else:
        method = "patient_confirmed"

    dose.confirmation_method = method
    if method == "caregiver_reported":
        # Healthcare safety: caregiver-reported intake is NOT automatically marked taken
        pass
    else:
        dose.status = "taken"

    # Eliminate client-controlled identity: set strictly from authenticated user
    dose.confirmed_by_user_id = current_user.id
    dose.confirmed_at = datetime.datetime.now()

    await db.commit()
    await db.refresh(dose)
    return dose


@router.post("/{dose_id}/reason", response_model=DoseScheduleOut)
async def record_reason(
    dose_id: int,
    body: DoseReason,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_dose(dose_id, db)
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["elderly", "caregiver"])

    result = await db.execute(
        select(DoseSchedule)
        .options(selectinload(DoseSchedule.medication))
        .where(DoseSchedule.id == dose_id)
    )
    dose = result.scalars().first()
    if not dose:
        raise HTTPException(status_code=404, detail="Dose not found")

    dose.reason_not_taken = body.reason
    dose.reason_notes = body.notes
    # Eliminate client-controlled identity: set strictly from authenticated user
    dose.confirmed_by_user_id = current_user.id
    dose.confirmed_at = datetime.datetime.now()

    await db.commit()
    await db.refresh(dose)
    return dose


@router.get("/{profile_id}/history", response_model=list[DoseScheduleOut])
async def dose_history(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    result = await db.execute(
        select(DoseSchedule)
        .join(Medication)
        .options(selectinload(DoseSchedule.medication))
        .where(Medication.profile_id == profile_id)
        .order_by(DoseSchedule.scheduled_time.desc())
    )
    return result.scalars().all()
