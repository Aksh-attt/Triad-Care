import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import MedicationChangeRequest, Medication, User
from schemas import ChangeRequestCreate, ChangeRequestUpdate, ChangeRequestOut
from dependencies import (
    get_current_user,
    verify_profile_access,
    get_profile_id_for_change,
)

router = APIRouter()


@router.get("/{profile_id}", response_model=list[ChangeRequestOut])
async def list_changes(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    result = await db.execute(
        select(MedicationChangeRequest)
        .options(
            selectinload(MedicationChangeRequest.requested_by_user),
            selectinload(MedicationChangeRequest.medication),
        )
        .where(MedicationChangeRequest.profile_id == profile_id)
        .order_by(MedicationChangeRequest.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{profile_id}", response_model=ChangeRequestOut)
async def create_change(
    profile_id: int,
    body: ChangeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Any member of the care circle can propose changes
    await verify_profile_access(profile_id, current_user, db)

    # Cross-profile ownership validation: Medication must belong to this patient profile
    if body.medication_id is not None:
        med_res = await db.execute(select(Medication).where(Medication.id == body.medication_id))
        med = med_res.scalars().first()
        if not med:
            raise HTTPException(status_code=404, detail="Medication not found")
        if med.profile_id != profile_id:
            raise HTTPException(
                status_code=400,
                detail="Medication does not belong to this patient profile",
            )

    data = body.model_dump()
    # Eliminate client-controlled identity: set strictly from authenticated user
    data["requested_by_user_id"] = current_user.id

    req = MedicationChangeRequest(
        profile_id=profile_id,
        **data,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    result = await db.execute(
        select(MedicationChangeRequest)
        .options(
            selectinload(MedicationChangeRequest.requested_by_user),
            selectinload(MedicationChangeRequest.medication),
        )
        .where(MedicationChangeRequest.id == req.id)
    )
    return result.scalars().first()


@router.put("/{change_id}", response_model=ChangeRequestOut)
@router.put("/{change_id}/review", response_model=ChangeRequestOut)
async def review_change(
    change_id: int,
    body: ChangeRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status: must be 'approved' or 'rejected'")

    # Resolve real parent profile (BOLA/IDOR protection)
    profile_id = await get_profile_id_for_change(change_id, db)

    # Role enforcement: Only the elderly patient for this profile can review changes
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["elderly"])
    if current_user.role != "elderly":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only the elderly patient can approve or reject medication changes per clinical safety policy",
        )

    result = await db.execute(
        select(MedicationChangeRequest)
        .options(
            selectinload(MedicationChangeRequest.requested_by_user),
            selectinload(MedicationChangeRequest.medication),
        )
        .where(MedicationChangeRequest.id == change_id)
    )
    req = result.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Change request not found")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot review change request: already {req.status}")

    req.status = body.status
    # Eliminate client-controlled identity: set strictly from authenticated user
    req.reviewed_by_user_id = current_user.id
    req.reviewed_at = datetime.datetime.now()

    # If approved, verify medication ownership again before applying change
    if body.status == "approved" and req.medication_id is not None:
        m_res = await db.execute(select(Medication).where(Medication.id == req.medication_id))
        med = m_res.scalars().first()
        if not med or med.profile_id != req.profile_id:
            raise HTTPException(
                status_code=400,
                detail="Security violation: Medication does not belong to this patient profile",
            )

    # If approved, apply change to medication
    if body.status == "approved" and req.proposed_details:
        details = req.proposed_details
        if req.change_type == "dosage_change" and req.medication_id:
            m_res = await db.execute(select(Medication).where(Medication.id == req.medication_id))
            med = m_res.scalars().first()
            if med:
                if "new_dosage" in details:
                    med.dosage = str(details["new_dosage"])
                if "dosage" in details:
                    med.dosage = str(details["dosage"])
                if "unit" in details:
                    med.unit = str(details["unit"])
        elif req.change_type == "discontinue" and req.medication_id:
            m_res = await db.execute(select(Medication).where(Medication.id == req.medication_id))
            med = m_res.scalars().first()
            if med:
                med.is_active = False
        elif req.change_type == "new_medicine":
            new_med = Medication(
                profile_id=req.profile_id,
                name=details.get("name", "New Medication"),
                dosage=str(details.get("dosage", "1")),
                unit=details.get("unit", "tablet"),
                frequency=details.get("frequency", "once_daily"),
                timing_slots=details.get("timing_slots", ["morning"]),
                start_date=datetime.date.today(),
                instructions=details.get("instructions", ""),
                is_active=True,
                added_by_user_id=current_user.id,
            )
            db.add(new_med)

    await db.commit()
    res = await db.execute(
        select(MedicationChangeRequest)
        .options(
            selectinload(MedicationChangeRequest.requested_by_user),
            selectinload(MedicationChangeRequest.medication),
        )
        .where(MedicationChangeRequest.id == change_id)
    )
    return res.scalars().first()
