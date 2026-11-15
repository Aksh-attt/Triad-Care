from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Appointment
from schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
import datetime

router = APIRouter()


@router.get("/{profile_id}", response_model=list[AppointmentOut])
async def list_appointments(profile_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.profile_id == profile_id,
            Appointment.date_time >= datetime.datetime.now()
        )
        .order_by(Appointment.date_time.asc())
    )
    return result.scalars().all()


@router.post("/{profile_id}", response_model=AppointmentOut)
async def add_appointment(profile_id: int, body: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    appt = Appointment(profile_id=profile_id, **body.model_dump())
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt


@router.put("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(appointment_id: int, body: AppointmentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(appt, field, value)

    await db.commit()
    await db.refresh(appt)
    return appt


@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await db.delete(appt)
    await db.commit()
    return {"message": "Appointment deleted"}
