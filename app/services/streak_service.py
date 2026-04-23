# app/services/streak_service.py
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.models import Streak, DevotionLog, UserBadge, Badge, User


BADGE_DEFINITIONS = [
    {"name": "First Prayer", "icon": "🙏", "description": "Completed your first prayer session", "requirement_type": "prayer_total", "requirement_value": 1},
    {"name": "Week Warrior", "icon": "⚔️", "description": "7-day prayer streak", "requirement_type": "prayer_streak", "requirement_value": 7},
    {"name": "Scripture Scholar", "icon": "📖", "description": "14-day Bible reading streak", "requirement_type": "bible_streak", "requirement_value": 14},
    {"name": "Focus Master", "icon": "🎯", "description": "Used Focus mode for 7 days", "requirement_type": "focus_streak", "requirement_value": 7},
    {"name": "Overcomer", "icon": "👑", "description": "30-day prayer streak", "requirement_type": "prayer_streak", "requirement_value": 30},
    {"name": "Holy Month", "icon": "✨", "description": "100% consistency for a full month", "requirement_type": "monthly_consistency", "requirement_value": 100},
    {"name": "Faithful One", "icon": "🌟", "description": "50 total prayers", "requirement_type": "prayer_total", "requirement_value": 50},
    {"name": "Word Walker", "icon": "📚", "description": "50 Bible reading sessions", "requirement_type": "bible_total", "requirement_value": 50},
]


async def ensure_badges_exist(db: AsyncSession):
    """Seed badge definitions if not present."""
    for b in BADGE_DEFINITIONS:
        result = await db.execute(select(Badge).where(Badge.name == b["name"]))
        if not result.scalar_one_or_none():
            db.add(Badge(**b))
    await db.flush()


async def get_or_create_streak(user_id: str, streak_type: str, db: AsyncSession) -> Streak:
    result = await db.execute(
        select(Streak).where(and_(Streak.user_id == user_id, Streak.type == streak_type))
    )
    streak = result.scalar_one_or_none()
    if not streak:
        streak = Streak(user_id=user_id, type=streak_type)
        db.add(streak)
        await db.flush()
    return streak


async def get_or_create_today_log(user_id: str, db: AsyncSession) -> DevotionLog:
    today_str = date.today().isoformat()
    result = await db.execute(
        select(DevotionLog).where(
            and_(DevotionLog.user_id == user_id, DevotionLog.date == today_str)
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        log = DevotionLog(user_id=user_id, date=today_str)
        db.add(log)
        await db.flush()
    return log


def _is_yesterday(dt: Optional[datetime]) -> bool:
    if not dt:
        return False
    yesterday = date.today() - timedelta(days=1)
    return dt.date() == yesterday


def _is_today(dt: Optional[datetime]) -> bool:
    if not dt:
        return False
    return dt.date() == date.today()


async def record_prayer(user_id: str, db: AsyncSession) -> tuple[DevotionLog, Streak]:
    log = await get_or_create_today_log(user_id, db)
    streak = await get_or_create_streak(user_id, "prayer", db)

    now = datetime.now(timezone.utc)

    if not log.prayed:
        log.prayed = True
        log.prayed_at = now
        streak.total_completions += 1

        if _is_yesterday(streak.last_completed_date):
            streak.current_streak += 1
        elif not _is_today(streak.last_completed_date):
            streak.current_streak = 1

        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_completed_date = now

        await _check_and_award_badges(user_id, streak, db)

    return log, streak


async def record_bible_read(user_id: str, db: AsyncSession) -> tuple[DevotionLog, Streak]:
    log = await get_or_create_today_log(user_id, db)
    streak = await get_or_create_streak(user_id, "bible", db)

    now = datetime.now(timezone.utc)

    if not log.read_bible:
        log.read_bible = True
        log.read_at = now
        streak.total_completions += 1

        if _is_yesterday(streak.last_completed_date):
            streak.current_streak += 1
        elif not _is_today(streak.last_completed_date):
            streak.current_streak = 1

        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_completed_date = now

        await _check_and_award_badges(user_id, streak, db)

    return log, streak


async def _check_and_award_badges(user_id: str, streak: Streak, db: AsyncSession):
    """Award badges when conditions are met."""
    await ensure_badges_exist(db)

    # Get all badge definitions
    result = await db.execute(select(Badge))
    all_badges = result.scalars().all()

    # Get already earned badge IDs
    earned_result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
    )
    earned_ids = {row[0] for row in earned_result.fetchall()}

    for badge in all_badges:
        if badge.id in earned_ids:
            continue

        should_award = False
        rt = badge.requirement_type
        rv = badge.requirement_value

        if rt == "prayer_streak" and streak.type == "prayer" and streak.current_streak >= rv:
            should_award = True
        elif rt == "bible_streak" and streak.type == "bible" and streak.current_streak >= rv:
            should_award = True
        elif rt == "prayer_total" and streak.type == "prayer" and streak.total_completions >= rv:
            should_award = True
        elif rt == "bible_total" and streak.type == "bible" and streak.total_completions >= rv:
            should_award = True

        if should_award:
            db.add(UserBadge(user_id=user_id, badge_id=badge.id))

    await db.flush()


async def get_monthly_consistency(user_id: str, db: AsyncSession) -> float:
    """Return the percentage of days this month the user completed devotion."""
    today = date.today()
    first_of_month = today.replace(day=1).isoformat()
    today_str = today.isoformat()

    result = await db.execute(
        select(DevotionLog).where(
            and_(
                DevotionLog.user_id == user_id,
                DevotionLog.date >= first_of_month,
                DevotionLog.date <= today_str,
            )
        )
    )
    logs = result.scalars().all()

    days_passed = today.day
    if days_passed == 0:
        return 0.0

    completed = sum(1 for log in logs if log.prayed or log.read_bible)
    return round((completed / days_passed) * 100, 1)


async def get_calendar_data(user_id: str, year: int, month: int, db: AsyncSession) -> List[dict]:
    """Return day-by-day devotion status for a month."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    result = await db.execute(
        select(DevotionLog).where(
            and_(
                DevotionLog.user_id == user_id,
                DevotionLog.date >= first_day.isoformat(),
                DevotionLog.date <= last_day.isoformat(),
            )
        )
    )
    logs = {log.date: log for log in result.scalars().all()}
    today = date.today()

    calendar = []
    for day_num in range(1, last_day.day + 1):
        d = date(year, month, day_num)
        log = logs.get(d.isoformat())
        if d > today:
            status = "future"
        elif log and (log.prayed or log.read_bible):
            status = "done"
        elif d == today:
            status = "today"
        else:
            status = "missed"

        calendar.append({
            "day": day_num,
            "date": d.isoformat(),
            "status": status,
            "prayed": log.prayed if log else False,
            "read_bible": log.read_bible if log else False,
        })

    return calendar
