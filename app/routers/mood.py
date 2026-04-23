# app/routers/mood.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User, MoodLog
from app.schemas.schemas import MoodLogCreate, MoodLogOut, MessageResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/mood", tags=["Mood Tracking"])


@router.post("", response_model=MoodLogOut, status_code=201)
async def log_mood(
    payload: MoodLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today_str = payload.date or date.today().isoformat()

    # Check if mood already logged today — update if so
    result = await db.execute(
        select(MoodLog).where(
            and_(MoodLog.user_id == current_user.id, MoodLog.date == today_str)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.mood = payload.mood
        existing.note = payload.note
        return existing

    log = MoodLog(user_id=current_user.id, mood=payload.mood, note=payload.note, date=today_str)
    db.add(log)
    await db.flush()
    return log


@router.get("/today", response_model=Optional[MoodLogOut])
async def get_today_mood(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today_str = date.today().isoformat()
    result = await db.execute(
        select(MoodLog).where(
            and_(MoodLog.user_id == current_user.id, MoodLog.date == today_str)
        )
    )
    return result.scalar_one_or_none()


@router.get("/history", response_model=List[MoodLogOut])
async def get_mood_history(
    limit: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == current_user.id)
        .order_by(MoodLog.logged_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/summary")
async def get_mood_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return mood frequency breakdown for the current month."""
    first_of_month = date.today().replace(day=1).isoformat()
    result = await db.execute(
        select(MoodLog.mood, func.count(MoodLog.id).label("count"))
        .where(
            and_(
                MoodLog.user_id == current_user.id,
                MoodLog.date >= first_of_month,
            )
        )
        .group_by(MoodLog.mood)
        .order_by(func.count(MoodLog.id).desc())
    )
    rows = result.fetchall()
    total = sum(r.count for r in rows)
    return {
        "month": date.today().strftime("%B %Y"),
        "total_logs": total,
        "breakdown": [
            {"mood": r.mood, "count": r.count, "percentage": round(r.count / total * 100, 1) if total else 0}
            for r in rows
        ],
    }
