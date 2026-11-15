from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import User, ProfileMembership
from schemas import LoginRequest, LoginResponse, UserOut, MembershipOut

router = APIRouter()


@router.get("/demo-users", response_model=list[UserOut])
async def get_demo_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.passcode == body.passcode))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid passcode")

    mem_result = await db.execute(
        select(ProfileMembership)
        .options(selectinload(ProfileMembership.user))
        .where(ProfileMembership.user_id == user.id)
    )
    memberships = mem_result.scalars().all()

    return LoginResponse(
        user=UserOut.model_validate(user),
        memberships=[MembershipOut.model_validate(m) for m in memberships]
    )
