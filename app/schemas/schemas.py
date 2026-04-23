# app/schemas/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────
class MoodEnum(str, Enum):
    joyful = "joyful"
    peaceful = "peaceful"
    hopeful = "hopeful"
    low = "low"
    on_fire = "on_fire"
    grateful = "grateful"


class JournalCategoryEnum(str, Enum):
    morning = "morning"
    evening = "evening"
    gratitude = "gratitude"
    intercession = "intercession"
    confession = "confession"
    personal = "personal"


class BlockStatusEnum(str, Enum):
    active = "active"
    locked = "locked"
    paused = "paused"


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
class UserOut(BaseModel):
    id: str
    email: str
    username: str
    display_name: Optional[str]
    avatar_emoji: str
    is_active: bool
    dark_mode: bool
    notifications_enabled: bool
    daily_verse_enabled: bool
    focus_mode_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_emoji: Optional[str] = None
    dark_mode: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    daily_verse_enabled: Optional[bool] = None
    focus_mode_active: Optional[bool] = None


# ─────────────────────────────────────────────
# STREAK
# ─────────────────────────────────────────────
class StreakOut(BaseModel):
    id: str
    type: str
    current_streak: int
    longest_streak: int
    last_completed_date: Optional[datetime]
    total_completions: int

    model_config = {"from_attributes": True}


class StreaksResponse(BaseModel):
    prayer: Optional[StreakOut] = None
    bible: Optional[StreakOut] = None
    focus: Optional[StreakOut] = None


# ─────────────────────────────────────────────
# DEVOTION LOG
# ─────────────────────────────────────────────
class DevotionLogOut(BaseModel):
    id: str
    date: str
    prayed: bool
    read_bible: bool
    prayed_at: Optional[datetime]
    read_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DevotionUpdate(BaseModel):
    prayed: Optional[bool] = None
    read_bible: Optional[bool] = None
    notes: Optional[str] = None


class ProgressResponse(BaseModel):
    today: DevotionLogOut
    prayer_streak: StreakOut
    bible_streak: StreakOut
    monthly_consistency: float
    total_prayers: int
    total_bible_reads: int
    focus_score: float


# ─────────────────────────────────────────────
# REMINDER
# ─────────────────────────────────────────────
class ReminderCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: str = "🔔"
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    enabled: bool = True
    days_of_week: List[int] = [0, 1, 2, 3, 4, 5, 6]


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    time: Optional[str] = None
    enabled: Optional[bool] = None
    days_of_week: Optional[List[int]] = None


class ReminderOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    icon: str
    time: str
    enabled: bool
    days_of_week: List[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# JOURNAL
# ─────────────────────────────────────────────
class JournalEntryCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field(..., min_length=1)
    mood: Optional[MoodEnum] = None
    category: JournalCategoryEnum = JournalCategoryEnum.personal
    is_private: bool = True


class JournalEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[MoodEnum] = None
    category: Optional[JournalCategoryEnum] = None
    is_private: Optional[bool] = None


class JournalEntryOut(BaseModel):
    id: str
    title: str
    content: str
    mood: Optional[str]
    category: str
    is_private: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# MOOD
# ─────────────────────────────────────────────
class MoodLogCreate(BaseModel):
    mood: MoodEnum
    note: Optional[str] = None
    date: Optional[str] = None  # defaults to today


class MoodLogOut(BaseModel):
    id: str
    mood: str
    note: Optional[str]
    date: str
    logged_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BLOCKED APPS
# ─────────────────────────────────────────────
class BlockedAppCreate(BaseModel):
    app_name: str = Field(..., max_length=100)
    app_icon: str = "📱"
    app_color: str = "#888888"
    daily_limit_minutes: Optional[int] = None
    block_during_prayer: bool = True
    block_during_study: bool = True


class BlockedAppUpdate(BaseModel):
    daily_limit_minutes: Optional[int] = None
    status: Optional[BlockStatusEnum] = None
    block_during_prayer: Optional[bool] = None
    block_during_study: Optional[bool] = None


class BlockedAppOut(BaseModel):
    id: str
    app_name: str
    app_icon: str
    app_color: str
    daily_limit_minutes: Optional[int]
    status: str
    block_during_prayer: bool
    block_during_study: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# SCREEN TIME
# ─────────────────────────────────────────────
class ScreenTimeCreate(BaseModel):
    date: Optional[str] = None
    app_name: str
    minutes_used: float = Field(..., ge=0)


class ScreenTimeOut(BaseModel):
    id: str
    date: str
    app_name: str
    minutes_used: float
    logged_at: datetime

    model_config = {"from_attributes": True}


class ScreenTimeSummary(BaseModel):
    date: str
    total_minutes: float
    total_hours: float
    by_app: List[dict]


class WeeklyScreenTime(BaseModel):
    week_data: List[dict]
    average_daily_hours: float
    most_used_app: str
    focus_score: float
    time_saved_minutes: float


# ─────────────────────────────────────────────
# BIBLE (static data)
# ─────────────────────────────────────────────
class VerseOut(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str
    testament: str


class ChapterOut(BaseModel):
    book: str
    chapter: int
    testament: str
    verses: List[VerseOut]


class VerseOfDay(BaseModel):
    text: str
    reference: str
    book: str
    chapter: int
    verse: int
    theme: str


class BibleSearchResult(BaseModel):
    results: List[VerseOut]
    total: int
    query: str


# ─────────────────────────────────────────────
# BOOKMARKS
# ─────────────────────────────────────────────
class BookmarkCreate(BaseModel):
    book: str
    chapter: int
    verse_number: int
    verse_text: Optional[str] = None
    note: Optional[str] = None


class BookmarkOut(BaseModel):
    id: str
    book: str
    chapter: int
    verse_number: int
    verse_text: Optional[str]
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# HIGHLIGHTS
# ─────────────────────────────────────────────
class HighlightCreate(BaseModel):
    book: str
    chapter: int
    verse_number: int
    verse_text: Optional[str] = None
    color: str = "#f59e0b"


class HighlightOut(BaseModel):
    id: str
    book: str
    chapter: int
    verse_number: int
    verse_text: Optional[str]
    color: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BADGES
# ─────────────────────────────────────────────
class BadgeOut(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    requirement_type: str
    requirement_value: int
    earned: bool
    earned_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# AI CHAT
# ─────────────────────────────────────────────
class AIChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None


class AIChatResponse(BaseModel):
    session_id: str
    response: str
    role: str = "assistant"
    created_at: datetime


class AIChatHistory(BaseModel):
    session_id: str
    messages: List[dict]


# ─────────────────────────────────────────────
# PRAYER REQUEST
# ─────────────────────────────────────────────
class PrayerRequestCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., min_length=1)
    is_private: bool = True


class PrayerRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_answered: Optional[bool] = None
    answered_note: Optional[str] = None
    is_private: Optional[bool] = None


class PrayerRequestOut(BaseModel):
    id: str
    title: str
    description: str
    is_answered: bool
    answered_note: Optional[str]
    answered_at: Optional[datetime]
    is_private: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
class DashboardResponse(BaseModel):
    user: UserOut
    today_devotion: DevotionLogOut
    prayer_streak: StreakOut
    bible_streak: StreakOut
    focus_streak: StreakOut
    today_verse: VerseOfDay
    monthly_consistency: float
    focus_score: float
    time_saved_today: float
    recent_mood: Optional[str]
    active_reminders: List[ReminderOut]
    badges_earned: int
    total_badges: int


# ─────────────────────────────────────────────
# GENERIC
# ─────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


Token.model_rebuild()
