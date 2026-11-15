import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import Medication, DoseSchedule, User
from schemas import MedicationCreate, MedicationUpdate, MedicationOut, DoseScheduleOut
from dependencies import (
    get_current_user,
    verify_profile_access,
    get_profile_id_for_medication,
)

router = APIRouter()


@router.get("/{profile_id}", response_model=list[MedicationOut])
async def list_medications(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    result = await db.execute(
        select(Medication).where(
            Medication.profile_id == profile_id,
            Medication.is_active == True,
        )
    )
    return result.scalars().all()


@router.post("/{profile_id}", response_model=MedicationOut)
async def add_medication(
    profile_id: int,
    body: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Medication sovereignty: only elderly patient can directly add active medications
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["elderly"])
    data = body.model_dump()
    data["added_by_user_id"] = current_user.id

    med = Medication(profile_id=profile_id, **data)
    db.add(med)
    await db.commit()
    await db.refresh(med)

    # Generate today's dose schedules for the new medication
    today = datetime.date.today()
    slot_times = {
        "morning": datetime.time(8, 0),
        "afternoon": datetime.time(13, 0),
        "evening": datetime.time(19, 0),
        "bedtime": datetime.time(21, 0),
    }
    slots = med.timing_slots or ["morning"]
    for slot in slots:
        slot_key = slot.lower()
        t = slot_times.get(slot_key, datetime.time(9, 0))
        sched_time = datetime.datetime.combine(today, t)
        dose = DoseSchedule(
            medication_id=med.id,
            scheduled_time=sched_time,
            status="pending",
        )
        db.add(dose)
    await db.commit()

    return med


@router.put("/{medication_id}", response_model=MedicationOut)
async def update_medication(
    medication_id: int,
    body: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_medication(medication_id, db)
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["elderly"])

    result = await db.execute(select(Medication).where(Medication.id == medication_id))
    med = result.scalars().first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(med, field, value)

    await db.commit()
    await db.refresh(med)
    return med


@router.delete("/{medication_id}")
async def delete_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_medication(medication_id, db)
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["elderly"])

    result = await db.execute(select(Medication).where(Medication.id == medication_id))
    med = result.scalars().first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    med.is_active = False
    await db.commit()
    return {"message": "Medication deactivated"}


@router.get("/{profile_id}/schedule/today", response_model=list[DoseScheduleOut])
async def today_schedule(
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
