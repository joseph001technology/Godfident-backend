# app/db/seed.py
"""
Seed the database with sample data for development/demo purposes.
Run: python -m app.db.seed
"""
import asyncio
from datetime import date, timedelta
from app.db.database import AsyncSessionLocal, init_db
from app.models.models import (
    User, Streak, DevotionLog, Reminder, JournalEntry,
    MoodLog, BlockedApp, ScreenTimeLog, Badge, UserBadge
)
from app.services.auth_service import hash_password
from app.services.streak_service import ensure_badges_exist

SAMPLE_USER = {
    "email": "demo@godfident.app",
    "username": "faithwarrior",
    "hashed_password": hash_password("password123"),
    "display_name": "Faith Warrior",
    "avatar_emoji": "🙏",
    "dark_mode": True,
    "notifications_enabled": True,
    "daily_verse_enabled": True,
}

DEFAULT_REMINDERS = [
    {"title": "Morning Prayer", "icon": "🙏", "time": "06:00", "description": "Start your day with God", "enabled": True},
    {"title": "Read Scripture", "icon": "📖", "time": "07:00", "description": "Daily Bible reading", "enabled": True},
    {"title": "Midday Prayer", "icon": "☀️", "time": "12:00", "description": "Pause and pray", "enabled": False},
    {"title": "Evening Devotion", "icon": "🌙", "time": "20:00", "description": "End your day with gratitude", "enabled": True},
]

SAMPLE_JOURNAL = [
    {
        "title": "Morning Prayer",
        "content": "Lord, thank You for this new day. Guide my steps and let Your light shine through me. Help me to stay focused on what matters — Your kingdom and Your righteousness.",
        "mood": "peaceful",
        "category": "morning",
    },
    {
        "title": "Gratitude Prayer",
        "content": "Father, I am grateful for the blessings You pour upon my life. For health, family, and Your unending grace. Thank You for never leaving me.",
        "mood": "grateful",
        "category": "gratitude",
    },
    {
        "title": "Intercession for Family",
        "content": "Lord, I lift up my family and friends. Cover them with Your protection, peace, and provision. Let Your favour surround them like a shield.",
        "mood": "hopeful",
        "category": "intercession",
    },
]

SAMPLE_BLOCKED_APPS = [
    {"app_name": "Instagram", "app_icon": "📸", "app_color": "#e1306c", "daily_limit_minutes": 30, "status": "active"},
    {"app_name": "YouTube", "app_icon": "▶️", "app_color": "#ff0000", "daily_limit_minutes": 60, "status": "active"},
    {"app_name": "TikTok", "app_icon": "🎵", "app_color": "#555555", "daily_limit_minutes": 20, "status": "locked"},
]

SAMPLE_SCREEN_TIME = [
    ("Instagram", 84),
    ("YouTube", 58),
    ("WhatsApp", 42),
    ("TikTok", 38),
    ("Twitter", 22),
    ("Games", 8),
]

SAMPLE_MOODS = [
    ("peaceful", "Started the day in prayer"),
    ("grateful", "God is so faithful"),
    ("hopeful", "Trusting His plan"),
    ("on_fire", "Word hit different today"),
    ("joyful", "Family time was a blessing"),
    ("peaceful", "Evening devotion was restorative"),
]


async def seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # Check if already seeded
        result = await db.execute(select(User).where(User.email == SAMPLE_USER["email"]))
        if result.scalar_one_or_none():
            print("✓ Database already seeded.")
            return

        print("🌱 Seeding database...")

        # Create demo user
        user = User(**SAMPLE_USER)
        db.add(user)
        await db.flush()
        print(f"  ✓ User created: {user.email}")

        # Create streaks with realistic values
        prayer_streak = Streak(user_id=user.id, type="prayer", current_streak=7, longest_streak=21, total_completions=127)
        bible_streak = Streak(user_id=user.id, type="bible", current_streak=14, longest_streak=30, total_completions=84)
        focus_streak = Streak(user_id=user.id, type="focus", current_streak=5, longest_streak=10, total_completions=45)
        db.add_all([prayer_streak, bible_streak, focus_streak])
        print("  ✓ Streaks created")

        # Create reminders
        for r in DEFAULT_REMINDERS:
            db.add(Reminder(user_id=user.id, **r))
        print("  ✓ Reminders created")

        # Create devotion logs for past 22 days (most days completed)
        completed_days = {1,2,3,4,5,7,8,9,10,12,13,14,15,16,17,18,19,21,22}
        for i in range(22, -1, -1):
            d = date.today() - timedelta(days=i)
            done = (22 - i + 1) in completed_days
            log = DevotionLog(
                user_id=user.id,
                date=d.isoformat(),
                prayed=done,
                read_bible=done,
            )
            db.add(log)
        print("  ✓ Devotion logs created (22 days)")

        # Create journal entries
        for j in SAMPLE_JOURNAL:
            db.add(JournalEntry(user_id=user.id, **j))
        print("  ✓ Journal entries created")

        # Create blocked apps
        for app in SAMPLE_BLOCKED_APPS:
            db.add(BlockedApp(user_id=user.id, **app))
        print("  ✓ Blocked apps created")

        # Create screen time for last 7 days
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            for app_name, base_mins in SAMPLE_SCREEN_TIME:
                variation = (i * 7 + len(app_name)) % 20 - 10
                mins = max(0, base_mins + variation)
                db.add(ScreenTimeLog(
                    user_id=user.id,
                    date=d.isoformat(),
                    app_name=app_name,
                    minutes_used=float(mins),
                ))
        print("  ✓ Screen time logs created (7 days)")

        # Create mood logs for last 6 days
        for i, (mood, note) in enumerate(SAMPLE_MOODS):
            d = date.today() - timedelta(days=len(SAMPLE_MOODS) - 1 - i)
            db.add(MoodLog(user_id=user.id, mood=mood, note=note, date=d.isoformat()))
        print("  ✓ Mood logs created")

        # Seed badges and award some to demo user
        await ensure_badges_exist(db)
        result = await db.execute(select(Badge))
        all_badges = result.scalars().all()
        earned_names = {"First Prayer", "Week Warrior", "Scripture Scholar", "Focus Master"}
        for badge in all_badges:
            if badge.name in earned_names:
                db.add(UserBadge(user_id=user.id, badge_id=badge.id))
        print(f"  ✓ Badges seeded, {len(earned_names)} awarded to demo user")

        await db.commit()
        print("\n✅ Seeding complete!")
        print(f"\n📱 Demo login credentials:")
        print(f"   Email:    {SAMPLE_USER['email']}")
        print(f"   Password: password123")


if __name__ == "__main__":
    asyncio.run(seed())
