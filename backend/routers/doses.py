import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import DoseSchedule, Medication
from schemas import DoseScheduleOut, DoseConfirm, DoseReason

router = APIRouter()


@router.get("/{profile_id}/today", response_model=list[DoseScheduleOut])
async def get_today_doses(profile_id: int, db: AsyncSession = Depends(get_db)):
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
async def confirm_dose(dose_id: int, body: DoseConfirm, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DoseSchedule)
        .options(selectinload(DoseSchedule.medication))
        .where(DoseSchedule.id == dose_id)
    )
    dose = result.scalars().first()
    if not dose:
        raise HTTPException(status_code=404, detail="Dose not found")

    dose.status = "taken"
    dose.confirmed_by_user_id = body.confirmed_by_user_id
    dose.confirmed_at = datetime.datetime.now()
    # NEVER touches followup status per business rules

    await db.commit()
    await db.refresh(dose)
    return dose


@router.post("/{dose_id}/reason", response_model=DoseScheduleOut)
async def record_reason(dose_id: int, body: DoseReason, db: AsyncSession = Depends(get_db)):
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
    dose.confirmed_by_user_id = body.confirmed_by_user_id
    dose.confirmed_at = datetime.datetime.now()

    await db.commit()
    await db.refresh(dose)
    return dose


@router.get("/{profile_id}/history", response_model=list[DoseScheduleOut])
async def dose_history(profile_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DoseSchedule)
        .join(Medication)
        .options(selectinload(DoseSchedule.medication))
        .where(Medication.profile_id == profile_id)
        .order_by(DoseSchedule.scheduled_time.desc())
    )
    return result.scalars().all()
