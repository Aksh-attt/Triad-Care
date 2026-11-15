from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import PatientProfile, ProfileMembership, User
from schemas import PatientProfileOut, PatientProfileUpdate, MembershipOut
from dependencies import get_current_user, verify_profile_access

router = APIRouter()


@router.get("/{profile_id}", response_model=PatientProfileOut)
async def get_patient(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    result = await db.execute(select(PatientProfile).where(PatientProfile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=PatientProfileOut)
async def update_patient(
    profile_id: int,
    body: PatientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only elderly patient can edit patient profile per permission matrix
    await verify_profile_access(profile_id, current_user, db, allowed_roles=["elderly"])
    result = await db.execute(select(PatientProfile).where(PatientProfile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/{profile_id}/members", response_model=list[MembershipOut])
async def get_members(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_profile_access(profile_id, current_user, db)
    result = await db.execute(
        select(ProfileMembership)
        .options(selectinload(ProfileMembership.user))
        .where(ProfileMembership.profile_id == profile_id)
    )
    members = result.scalars().all()
    return members
