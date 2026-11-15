from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Notification
from schemas import NotificationOut

router = APIRouter()


@router.get("/{profile_id}", response_model=list[NotificationOut])
async def list_notifications(profile_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification)
        .where(Notification.profile_id == profile_id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return notif


@router.put("/{profile_id}/read-all")
async def mark_all_read(profile_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(
            Notification.profile_id == profile_id,
            Notification.is_read == False
        )
    )
    notifications = result.scalars().all()
    for n in notifications:
        n.is_read = True
    await db.commit()
    return {"message": f"Marked {len(notifications)} notifications as read"}
