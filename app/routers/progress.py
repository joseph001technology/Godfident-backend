# app/routers/progress.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from typing import List

from app.db.database import get_db
from app.models.models import User, Badge, UserBadge
from app.schemas.schemas import BadgeOut
from app.services.auth_service import get_current_user
from app.services.streak_service import (
    ensure_badges_exist, get_or_create_streak,
    get_monthly_consistency, get_calendar_data
)

router = APIRouter(prefix="/progress", tags=["Progress & Badges"])


@router.get("/badges", response_model=List[BadgeOut])
async def get_all_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_badges_exist(db)

    # All badge defs
    badges_result = await db.execute(select(Badge))
    all_badges = badges_result.scalars().all()

    # User earned badges
    earned_result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == current_user.id)
    )
    earned = {ub.badge_id: ub.earned_at for ub in earned_result.scalars().all()}

    return [
        BadgeOut(
            id=b.id,
            name=b.name,
            description=b.description,
            icon=b.icon,
            requirement_type=b.requirement_type,
            requirement_value=b.requirement_value,
            earned=b.id in earned,
            earned_at=earned.get(b.id),
        )
        for b in all_badges
    ]


@router.get("/summary")
async def get_progress_summary(
    year: int = Query(default=None),
    month: int = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    y = year or today.year
    m = month or today.month

    prayer_streak = await get_or_create_streak(current_user.id, "prayer", db)
    bible_streak = await get_or_create_streak(current_user.id, "bible", db)
    focus_streak = await get_or_create_streak(current_user.id, "focus", db)
    consistency = await get_monthly_consistency(current_user.id, db)
    calendar = await get_calendar_data(current_user.id, y, m, db)

    # Badge counts
    await ensure_badges_exist(db)
    total_result = await db.execute(select(Badge))
    total_badges = len(total_result.scalars().all())
    earned_result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == current_user.id)
    )
    earned_count = len(earned_result.scalars().all())

    focus_score = min(100.0, 50.0 + (focus_streak.current_streak * 2.5))

    return {
        "prayer_streak": {
            "current": prayer_streak.current_streak,
            "longest": prayer_streak.longest_streak,
            "total": prayer_streak.total_completions,
        },
        "bible_streak": {
            "current": bible_streak.current_streak,
            "longest": bible_streak.longest_streak,
            "total": bible_streak.total_completions,
        },
        "focus_streak": {
            "current": focus_streak.current_streak,
            "longest": focus_streak.longest_streak,
        },
        "monthly_consistency": consistency,
        "focus_score": focus_score,
        "badges": {"earned": earned_count, "total": total_badges},
        "calendar": {
            "year": y,
            "month": m,
            "days": calendar,
        },
        "quick_stats": {
            "total_prayers": prayer_streak.total_completions,
            "total_bible_reads": bible_streak.total_completions,
            "best_prayer_streak": prayer_streak.longest_streak,
            "best_bible_streak": bible_streak.longest_streak,
        },
    }
