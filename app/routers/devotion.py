# app/routers/devotion.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from typing import List

from app.db.database import get_db
from app.models.models import User, DevotionLog, Streak
from app.schemas.schemas import (
    DevotionLogOut, DevotionUpdate, StreaksResponse, StreakOut,
    ProgressResponse, MessageResponse
)
from app.services.auth_service import get_current_user
from app.services.streak_service import (
    record_prayer, record_bible_read, get_or_create_streak,
    get_or_create_today_log, get_monthly_consistency, get_calendar_data
)

router = APIRouter(prefix="/devotion", tags=["Devotion & Streaks"])


@router.get("/today", response_model=DevotionLogOut)
async def get_today_devotion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = await get_or_create_today_log(current_user.id, db)
    return log


@router.post("/pray", response_model=dict)
async def mark_as_prayed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark today's prayer as done and update streak."""
    log, streak = await record_prayer(current_user.id, db)
    return {
        "success": True,
        "already_done": not log.prayed,
        "message": "Prayer recorded! 🙏" if log.prayed else "Already prayed today!",
        "devotion": DevotionLogOut.model_validate(log),
        "streak": StreakOut.model_validate(streak),
    }


@router.post("/read", response_model=dict)
async def mark_bible_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark today's Bible reading as done and update streak."""
    log, streak = await record_bible_read(current_user.id, db)
    return {
        "success": True,
        "message": "Bible reading recorded! 📖" if log.read_bible else "Already read today!",
        "devotion": DevotionLogOut.model_validate(log),
        "streak": StreakOut.model_validate(streak),
    }


@router.patch("/today", response_model=DevotionLogOut)
async def update_today_devotion(
    payload: DevotionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = await get_or_create_today_log(current_user.id, db)
    if payload.notes is not None:
        log.notes = payload.notes
    return log


@router.get("/streaks", response_model=StreaksResponse)
async def get_streaks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prayer = await get_or_create_streak(current_user.id, "prayer", db)
    bible = await get_or_create_streak(current_user.id, "bible", db)
    focus = await get_or_create_streak(current_user.id, "focus", db)
    return StreaksResponse(
        prayer=StreakOut.model_validate(prayer),
        bible=StreakOut.model_validate(bible),
        focus=StreakOut.model_validate(focus),
    )


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = await get_or_create_today_log(current_user.id, db)
    prayer_streak = await get_or_create_streak(current_user.id, "prayer", db)
    bible_streak = await get_or_create_streak(current_user.id, "bible", db)
    consistency = await get_monthly_consistency(current_user.id, db)

    # Focus score calc
    focus_score = min(100.0, 50.0 + (prayer_streak.current_streak * 2.5))

    return ProgressResponse(
        today=DevotionLogOut.model_validate(today),
        prayer_streak=StreakOut.model_validate(prayer_streak),
        bible_streak=StreakOut.model_validate(bible_streak),
        monthly_consistency=consistency,
        total_prayers=prayer_streak.total_completions,
        total_bible_reads=bible_streak.total_completions,
        focus_score=focus_score,
    )


@router.get("/calendar")
async def get_calendar(
    year: int = Query(default=None),
    month: int = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    calendar = await get_calendar_data(current_user.id, y, m, db)
    consistency = await get_monthly_consistency(current_user.id, db)
    return {
        "year": y,
        "month": m,
        "days": calendar,
        "consistency_percent": consistency,
    }


@router.get("/history", response_model=List[DevotionLogOut])
async def get_history(
    limit: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DevotionLog)
        .where(DevotionLog.user_id == current_user.id)
        .order_by(DevotionLog.date.desc())
        .limit(limit)
    )
    return result.scalars().all()
