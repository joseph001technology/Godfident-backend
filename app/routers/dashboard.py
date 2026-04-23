# app/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date

from app.db.database import get_db
from app.models.models import User, Streak, Reminder, UserBadge, Badge, MoodLog, ScreenTimeLog
from app.schemas.schemas import DashboardResponse, UserOut, DevotionLogOut, StreakOut, ReminderOut
from app.services.auth_service import get_current_user
from app.services.bible_service import get_verse_of_day
from app.services.streak_service import (
    get_or_create_streak, get_or_create_today_log, get_monthly_consistency
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Today's devotion log
    today_log = await get_or_create_today_log(current_user.id, db)

    # Streaks
    prayer_streak = await get_or_create_streak(current_user.id, "prayer", db)
    bible_streak = await get_or_create_streak(current_user.id, "bible", db)
    focus_streak = await get_or_create_streak(current_user.id, "focus", db)

    # Today's verse
    verse = get_verse_of_day()

    # Monthly consistency
    consistency = await get_monthly_consistency(current_user.id, db)

    # Focus score (simple calc based on focus streak)
    focus_score = min(100.0, 60.0 + (focus_streak.current_streak * 2))

    # Recent mood
    mood_result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == current_user.id)
        .order_by(MoodLog.logged_at.desc())
        .limit(1)
    )
    recent_mood_obj = mood_result.scalar_one_or_none()
    recent_mood = recent_mood_obj.mood if recent_mood_obj else None

    # Active reminders
    reminders_result = await db.execute(
        select(Reminder)
        .where(and_(Reminder.user_id == current_user.id, Reminder.enabled == True))
        .order_by(Reminder.time)
        .limit(4)
    )
    reminders = reminders_result.scalars().all()

    # Badge count
    total_badges_result = await db.execute(select(Badge))
    total_badges = len(total_badges_result.scalars().all())

    earned_result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == current_user.id)
    )
    earned_count = len(earned_result.scalars().all())

    # Time saved today (mock based on blocked apps)
    time_saved = 45.0 + (prayer_streak.current_streak * 3)

    return DashboardResponse(
        user=UserOut.model_validate(current_user),
        today_devotion=DevotionLogOut.model_validate(today_log),
        prayer_streak=StreakOut.model_validate(prayer_streak),
        bible_streak=StreakOut.model_validate(bible_streak),
        focus_streak=StreakOut.model_validate(focus_streak),
        today_verse=verse,
        monthly_consistency=consistency,
        focus_score=focus_score,
        time_saved_today=time_saved,
        recent_mood=recent_mood,
        active_reminders=[ReminderOut.model_validate(r) for r in reminders],
        badges_earned=earned_count,
        total_badges=total_badges,
    )
