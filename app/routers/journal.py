# app/routers/journal.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User, JournalEntry
from app.schemas.schemas import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryOut, MessageResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/journal", tags=["Prayer Journal"])


@router.get("", response_model=List[JournalEntryOut])
async def list_entries(
    category: Optional[str] = Query(None),
    mood: Optional[str] = Query(None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(JournalEntry).where(JournalEntry.user_id == current_user.id)
    if category:
        query = query.where(JournalEntry.category == category)
    if mood:
        query = query.where(JournalEntry.mood == mood)
    query = query.order_by(JournalEntry.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=JournalEntryOut, status_code=201)
async def create_entry(
    payload: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = JournalEntry(user_id=current_user.id, **payload.model_dump())
    db.add(entry)
    await db.flush()
    return entry


@router.get("/{entry_id}", response_model=JournalEntryOut)
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(JournalEntry).where(
            and_(JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.patch("/{entry_id}", response_model=JournalEntryOut)
async def update_entry(
    entry_id: str,
    payload: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(JournalEntry).where(
            and_(JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(entry, key, val)
    return entry


@router.delete("/{entry_id}", response_model=MessageResponse)
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(JournalEntry).where(
            and_(JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    await db.delete(entry)
    return MessageResponse(message="Entry deleted")
