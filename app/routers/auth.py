# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.models import User, Streak, Reminder
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut, MessageResponse
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

DEFAULT_REMINDERS = [
    {"title": "Morning Prayer", "icon": "🙏", "time": "06:00", "description": "Start your day with God", "enabled": True},
    {"title": "Read Scripture", "icon": "📖", "time": "07:00", "description": "Daily Bible reading", "enabled": True},
    {"title": "Midday Prayer", "icon": "☀️", "time": "12:00", "description": "Pause and pray", "enabled": False},
    {"title": "Evening Devotion", "icon": "🌙", "time": "20:00", "description": "End your day with gratitude", "enabled": True},
]


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name or payload.username.title(),
    )
    db.add(user)
    await db.flush()

    # Create default streaks
    for streak_type in ["prayer", "bible", "focus"]:
        db.add(Streak(user_id=user.id, type=streak_type))

    # Create default reminders
    for r in DEFAULT_REMINDERS:
        db.add(Reminder(user_id=user.id, **r))

    await db.flush()

    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
async def logout():
    # JWT is stateless; client deletes token. Optionally maintain a blocklist.
    return MessageResponse(message="Logged out successfully")
