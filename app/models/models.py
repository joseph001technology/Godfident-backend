# app/models/models.py
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float,
    ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────
class MoodEnum(str, enum.Enum):
    joyful = "joyful"
    peaceful = "peaceful"
    hopeful = "hopeful"
    low = "low"
    on_fire = "on_fire"
    grateful = "grateful"


class JournalCategoryEnum(str, enum.Enum):
    morning = "morning"
    evening = "evening"
    gratitude = "gratitude"
    intercession = "intercession"
    confession = "confession"
    personal = "personal"


class BlockStatusEnum(str, enum.Enum):
    active = "active"
    locked = "locked"
    paused = "paused"


class TestamentEnum(str, enum.Enum):
    OT = "OT"
    NT = "NT"


# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    avatar_emoji = Column(String, default="👤")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Settings
    dark_mode = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    daily_verse_enabled = Column(Boolean, default=True)
    focus_mode_active = Column(Boolean, default=False)

    # Relationships
    streaks = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    mood_logs = relationship("MoodLog", back_populates="user", cascade="all, delete-orphan")
    blocked_apps = relationship("BlockedApp", back_populates="user", cascade="all, delete-orphan")
    screen_time_logs = relationship("ScreenTimeLog", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("VerseBookmark", back_populates="user", cascade="all, delete-orphan")
    highlights = relationship("VerseHighlight", back_populates="user", cascade="all, delete-orphan")
    devotion_logs = relationship("DevotionLog", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    ai_chats = relationship("AIChat", back_populates="user", cascade="all, delete-orphan")
    prayer_requests = relationship("PrayerRequest", back_populates="user", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# STREAK
# ─────────────────────────────────────────────
class Streak(Base):
    __tablename__ = "streaks"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # "prayer" | "bible" | "focus"
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_completed_date = Column(DateTime(timezone=True), nullable=True)
    total_completions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="streaks")


# ─────────────────────────────────────────────
# DEVOTION LOG (daily prayer/bible check-in)
# ─────────────────────────────────────────────
class DevotionLog(Base):
    __tablename__ = "devotion_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    prayed = Column(Boolean, default=False)
    read_bible = Column(Boolean, default=False)
    prayed_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="devotion_logs")


# ─────────────────────────────────────────────
# REMINDER
# ─────────────────────────────────────────────
class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, default="🔔")
    time = Column(String, nullable=False)  # "HH:MM" 24hr
    enabled = Column(Boolean, default=True)
    days_of_week = Column(JSON, default=lambda: [0, 1, 2, 3, 4, 5, 6])  # 0=Sun, 6=Sat
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="reminders")


# ─────────────────────────────────────────────
# JOURNAL ENTRY
# ─────────────────────────────────────────────
class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(Enum(MoodEnum), nullable=True)
    category = Column(Enum(JournalCategoryEnum), default=JournalCategoryEnum.personal)
    is_private = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="journal_entries")


# ─────────────────────────────────────────────
# MOOD LOG
# ─────────────────────────────────────────────
class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    mood = Column(Enum(MoodEnum), nullable=False)
    note = Column(Text, nullable=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="mood_logs")


# ─────────────────────────────────────────────
# BLOCKED APPS
# ─────────────────────────────────────────────
class BlockedApp(Base):
    __tablename__ = "blocked_apps"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    app_name = Column(String, nullable=False)
    app_icon = Column(String, default="📱")
    app_color = Column(String, default="#888888")
    daily_limit_minutes = Column(Integer, nullable=True)  # null = blocked entirely
    status = Column(Enum(BlockStatusEnum), default=BlockStatusEnum.active)
    block_during_prayer = Column(Boolean, default=True)
    block_during_study = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="blocked_apps")


# ─────────────────────────────────────────────
# SCREEN TIME LOG
# ─────────────────────────────────────────────
class ScreenTimeLog(Base):
    __tablename__ = "screen_time_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    app_name = Column(String, nullable=False)
    minutes_used = Column(Float, default=0.0)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="screen_time_logs")


# ─────────────────────────────────────────────
# VERSE BOOKMARK
# ─────────────────────────────────────────────
class VerseBookmark(Base):
    __tablename__ = "verse_bookmarks"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    book = Column(String, nullable=False)
    chapter = Column(Integer, nullable=False)
    verse_number = Column(Integer, nullable=False)
    verse_text = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookmarks")


# ─────────────────────────────────────────────
# VERSE HIGHLIGHT
# ─────────────────────────────────────────────
class VerseHighlight(Base):
    __tablename__ = "verse_highlights"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    book = Column(String, nullable=False)
    chapter = Column(Integer, nullable=False)
    verse_number = Column(Integer, nullable=False)
    verse_text = Column(Text, nullable=True)
    color = Column(String, default="#f59e0b")  # gold default
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="highlights")


# ─────────────────────────────────────────────
# BADGE
# ─────────────────────────────────────────────
class Badge(Base):
    __tablename__ = "badges"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)
    requirement_type = Column(String, nullable=False)  # prayer_streak, bible_streak, focus_days, etc.
    requirement_value = Column(Integer, nullable=False)

    users = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    badge_id = Column(String, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="users")


# ─────────────────────────────────────────────
# AI CHAT
# ─────────────────────────────────────────────
class AIChat(Base):
    __tablename__ = "ai_chats"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="ai_chats")


# ─────────────────────────────────────────────
# PRAYER REQUEST
# ─────────────────────────────────────────────
class PrayerRequest(Base):
    __tablename__ = "prayer_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_answered = Column(Boolean, default=False)
    answered_note = Column(Text, nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    is_private = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="prayer_requests")
