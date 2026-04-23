# app/routers/focus.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date, timedelta
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User, BlockedApp, ScreenTimeLog
from app.schemas.schemas import (
    BlockedAppCreate, BlockedAppUpdate, BlockedAppOut,
    ScreenTimeCreate, ScreenTimeOut, ScreenTimeSummary,
    WeeklyScreenTime, MessageResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/focus", tags=["Focus & Screen Time"])


# ─── Focus Mode ─────────────────────────────────────────

@router.post("/mode/toggle", response_model=dict)
async def toggle_focus_mode(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.focus_mode_active = not current_user.focus_mode_active
    await db.flush()
    return {
        "focus_mode_active": current_user.focus_mode_active,
        "message": "Focus mode activated 🛡️" if current_user.focus_mode_active else "Focus mode deactivated",
    }


@router.get("/mode/status")
async def get_focus_status(current_user: User = Depends(get_current_user)):
    return {"focus_mode_active": current_user.focus_mode_active}


# ─── Blocked Apps ────────────────────────────────────────

@router.get("/blocked-apps", response_model=List[BlockedAppOut])
async def list_blocked_apps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BlockedApp)
        .where(BlockedApp.user_id == current_user.id)
        .order_by(BlockedApp.created_at.desc())
    )
    return result.scalars().all()


@router.post("/blocked-apps", response_model=BlockedAppOut, status_code=201)
async def add_blocked_app(
    payload: BlockedAppCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Prevent duplicates
    result = await db.execute(
        select(BlockedApp).where(
            and_(
                BlockedApp.user_id == current_user.id,
                BlockedApp.app_name == payload.app_name,
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"{payload.app_name} is already in your blocked list")

    app = BlockedApp(user_id=current_user.id, **payload.model_dump())
    db.add(app)
    await db.flush()
    return app


@router.patch("/blocked-apps/{app_id}", response_model=BlockedAppOut)
async def update_blocked_app(
    app_id: str,
    payload: BlockedAppUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BlockedApp).where(
            and_(BlockedApp.id == app_id, BlockedApp.user_id == current_user.id)
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Blocked app not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(app, key, val)
    return app


@router.delete("/blocked-apps/{app_id}", response_model=MessageResponse)
async def remove_blocked_app(
    app_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BlockedApp).where(
            and_(BlockedApp.id == app_id, BlockedApp.user_id == current_user.id)
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Blocked app not found")
    await db.delete(app)
    return MessageResponse(message="App removed from blocked list")


@router.patch("/blocked-apps/{app_id}/lock", response_model=BlockedAppOut)
async def lock_app(
    app_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BlockedApp).where(
            and_(BlockedApp.id == app_id, BlockedApp.user_id == current_user.id)
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Blocked app not found")
    app.status = "locked"
    return app


# ─── Screen Time ─────────────────────────────────────────

@router.post("/screen-time", response_model=ScreenTimeOut, status_code=201)
async def log_screen_time(
    payload: ScreenTimeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today_str = payload.date or date.today().isoformat()

    # If entry for this app+date exists, update it
    result = await db.execute(
        select(ScreenTimeLog).where(
            and_(
                ScreenTimeLog.user_id == current_user.id,
                ScreenTimeLog.date == today_str,
                ScreenTimeLog.app_name == payload.app_name,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.minutes_used = payload.minutes_used
        return existing

    log = ScreenTimeLog(
        user_id=current_user.id,
        date=today_str,
        app_name=payload.app_name,
        minutes_used=payload.minutes_used,
    )
    db.add(log)
    await db.flush()
    return log


@router.get("/screen-time/today", response_model=ScreenTimeSummary)
async def get_today_screen_time(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today_str = date.today().isoformat()
    result = await db.execute(
        select(ScreenTimeLog)
        .where(and_(ScreenTimeLog.user_id == current_user.id, ScreenTimeLog.date == today_str))
        .order_by(ScreenTimeLog.minutes_used.desc())
    )
    logs = result.scalars().all()
    total_minutes = sum(l.minutes_used for l in logs)
    return ScreenTimeSummary(
        date=today_str,
        total_minutes=round(total_minutes, 1),
        total_hours=round(total_minutes / 60, 2),
        by_app=[{"app": l.app_name, "minutes": round(l.minutes_used, 1)} for l in logs],
    )


@router.get("/screen-time/weekly", response_model=WeeklyScreenTime)
async def get_weekly_screen_time(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    week_ago = today - timedelta(days=6)

    result = await db.execute(
        select(
            ScreenTimeLog.date,
            func.sum(ScreenTimeLog.minutes_used).label("total_minutes"),
        )
        .where(
            and_(
                ScreenTimeLog.user_id == current_user.id,
                ScreenTimeLog.date >= week_ago.isoformat(),
            )
        )
        .group_by(ScreenTimeLog.date)
        .order_by(ScreenTimeLog.date)
    )
    daily_rows = result.fetchall()
    daily_map = {r.date: r.total_minutes for r in daily_rows}

    # Most-used app this week
    top_result = await db.execute(
        select(ScreenTimeLog.app_name, func.sum(ScreenTimeLog.minutes_used).label("total"))
        .where(
            and_(
                ScreenTimeLog.user_id == current_user.id,
                ScreenTimeLog.date >= week_ago.isoformat(),
            )
        )
        .group_by(ScreenTimeLog.app_name)
        .order_by(func.sum(ScreenTimeLog.minutes_used).desc())
        .limit(1)
    )
    top_app_row = top_result.first()
    most_used = top_app_row.app_name if top_app_row else "None"

    # Build 7-day array (fill missing days with 0)
    week_data = []
    total_weekly_minutes = 0
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.isoformat()
        mins = daily_map.get(d_str, 0)
        total_weekly_minutes += mins
        week_data.append({
            "date": d_str,
            "day": d.strftime("%a"),
            "total_minutes": round(mins, 1),
            "total_hours": round(mins / 60, 2),
        })

    avg_daily = total_weekly_minutes / 7
    # Focus score: lower screen time = higher score
    focus_score = max(0, min(100, round(100 - (avg_daily / 6 * 100), 1)))
    time_saved = max(0, round((360 - avg_daily), 1))  # baseline 6hrs

    return WeeklyScreenTime(
        week_data=week_data,
        average_daily_hours=round(avg_daily / 60, 2),
        most_used_app=most_used,
        focus_score=focus_score,
        time_saved_minutes=time_saved,
    )


@router.get("/screen-time/history", response_model=List[ScreenTimeOut])
async def get_screen_time_history(
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = (date.today() - timedelta(days=days)).isoformat()
    result = await db.execute(
        select(ScreenTimeLog)
        .where(
            and_(
                ScreenTimeLog.user_id == current_user.id,
                ScreenTimeLog.date >= since,
            )
        )
        .order_by(ScreenTimeLog.date.desc(), ScreenTimeLog.minutes_used.desc())
    )
    return result.scalars().all()
