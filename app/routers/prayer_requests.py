# app/routers/prayer_requests.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timezone
from typing import List

from app.db.database import get_db
from app.models.models import User, PrayerRequest
from app.schemas.schemas import (
    PrayerRequestCreate, PrayerRequestUpdate, PrayerRequestOut, MessageResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/prayer-requests", tags=["Prayer Requests"])


@router.get("", response_model=List[PrayerRequestOut])
async def list_prayer_requests(
    answered: bool = Query(None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PrayerRequest).where(PrayerRequest.user_id == current_user.id)
    if answered is not None:
        query = query.where(PrayerRequest.is_answered == answered)
    query = query.order_by(PrayerRequest.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=PrayerRequestOut, status_code=201)
async def create_prayer_request(
    payload: PrayerRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pr = PrayerRequest(user_id=current_user.id, **payload.model_dump())
    db.add(pr)
    await db.flush()
    return pr


@router.get("/{request_id}", response_model=PrayerRequestOut)
async def get_prayer_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PrayerRequest).where(
            and_(PrayerRequest.id == request_id, PrayerRequest.user_id == current_user.id)
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Prayer request not found")
    return pr


@router.patch("/{request_id}", response_model=PrayerRequestOut)
async def update_prayer_request(
    request_id: str,
    payload: PrayerRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PrayerRequest).where(
            and_(PrayerRequest.id == request_id, PrayerRequest.user_id == current_user.id)
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Prayer request not found")

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(pr, key, val)

    if payload.is_answered and not pr.answered_at:
        pr.answered_at = datetime.now(timezone.utc)

    return pr


@router.post("/{request_id}/answer", response_model=PrayerRequestOut)
async def mark_answered(
    request_id: str,
    answered_note: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PrayerRequest).where(
            and_(PrayerRequest.id == request_id, PrayerRequest.user_id == current_user.id)
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Prayer request not found")

    pr.is_answered = True
    pr.answered_note = answered_note
    pr.answered_at = datetime.now(timezone.utc)
    return pr


@router.delete("/{request_id}", response_model=MessageResponse)
async def delete_prayer_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PrayerRequest).where(
            and_(PrayerRequest.id == request_id, PrayerRequest.user_id == current_user.id)
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Prayer request not found")
    await db.delete(pr)
    return MessageResponse(message="Prayer request deleted")
