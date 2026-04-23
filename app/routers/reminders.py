# app/routers/reminders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.db.database import get_db
from app.models.models import User, Reminder
from app.schemas.schemas import ReminderCreate, ReminderUpdate, ReminderOut, MessageResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.get("", response_model=List[ReminderOut])
async def list_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == current_user.id)
        .order_by(Reminder.time)
    )
    return result.scalars().all()


@router.post("", response_model=ReminderOut, status_code=201)
async def create_reminder(
    payload: ReminderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = Reminder(user_id=current_user.id, **payload.model_dump())
    db.add(reminder)
    await db.flush()
    return reminder


@router.get("/{reminder_id}", response_model=ReminderOut)
async def get_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return r


@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: str,
    payload: ReminderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(r, key, val)
    return r


@router.delete("/{reminder_id}", response_model=MessageResponse)
async def delete_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await db.delete(r)
    return MessageResponse(message="Reminder deleted")


@router.patch("/{reminder_id}/toggle", response_model=ReminderOut)
async def toggle_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    r.enabled = not r.enabled
    return r
