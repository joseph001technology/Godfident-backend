# tests/test_api.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.main import app
from app.db.database import get_db, Base


# ─── Test Database ─────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///./test_godfident.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register a test user and return auth headers."""
    register_resp = await client.post("/api/auth/register", json={
        "email": "test@godfident.app",
        "username": "testuser",
        "password": "testpass123",
        "display_name": "Test User",
    })
    # If already registered, login
    if register_resp.status_code == 400:
        login_resp = await client.post("/api/auth/login", json={
            "email": "test@godfident.app",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]
    else:
        token = register_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["app"] == "Godfident"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ─── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register(client):
    r = await client.post("/api/auth/register", json={
        "email": "newuser@godfident.app",
        "username": "newbeliever",
        "password": "secure123",
        "display_name": "New Believer",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@godfident.app"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/auth/register", json={
        "email": "dupe@godfident.app",
        "username": "dupe1",
        "password": "pass123",
    })
    r = await client.post("/api/auth/register", json={
        "email": "dupe@godfident.app",
        "username": "dupe2",
        "password": "pass123",
    })
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client, auth_headers):
    r = await client.post("/api/auth/login", json={
        "email": "test@godfident.app",
        "password": "testpass123",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    r = await client.post("/api/auth/login", json={
        "email": "test@godfident.app",
        "password": "wrongpassword",
    })
    assert r.status_code == 401


# ─── Users ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    r = await client.get("/api/users/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "test@godfident.app"


@pytest.mark.asyncio
async def test_update_me(client, auth_headers):
    r = await client.patch("/api/users/me", headers=auth_headers, json={
        "display_name": "Updated Name",
        "dark_mode": False,
    })
    assert r.status_code == 200
    assert r.json()["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_unauthorized_without_token(client):
    r = await client.get("/api/users/me")
    assert r.status_code == 401


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard(client, auth_headers):
    r = await client.get("/api/dashboard", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "user" in data
    assert "today_devotion" in data
    assert "prayer_streak" in data
    assert "bible_streak" in data
    assert "today_verse" in data
    assert "monthly_consistency" in data


# ─── Devotion ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_today_devotion(client, auth_headers):
    r = await client.get("/api/devotion/today", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "prayed" in data
    assert "read_bible" in data


@pytest.mark.asyncio
async def test_mark_as_prayed(client, auth_headers):
    r = await client.post("/api/devotion/pray", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["devotion"]["prayed"] is True
    assert data["streak"]["current_streak"] >= 1


@pytest.mark.asyncio
async def test_mark_bible_read(client, auth_headers):
    r = await client.post("/api/devotion/read", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["devotion"]["read_bible"] is True


@pytest.mark.asyncio
async def test_get_streaks(client, auth_headers):
    r = await client.get("/api/devotion/streaks", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "prayer" in data
    assert "bible" in data
    assert "focus" in data


@pytest.mark.asyncio
async def test_get_calendar(client, auth_headers):
    r = await client.get("/api/devotion/calendar", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "days" in data
    assert "consistency_percent" in data
    assert isinstance(data["days"], list)


# ─── Bible ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verse_of_day(client):
    r = await client.get("/api/bible/verse-of-day")
    assert r.status_code == 200
    data = r.json()
    assert "text" in data
    assert "reference" in data


@pytest.mark.asyncio
async def test_get_books(client):
    r = await client.get("/api/bible/books")
    assert r.status_code == 200
    data = r.json()
    assert "OT" in data
    assert "NT" in data
    assert "Psalms" in data["OT"]
    assert "John" in data["NT"]


@pytest.mark.asyncio
async def test_read_chapter(client):
    r = await client.get("/api/bible/chapter/Psalms/23")
    assert r.status_code == 200
    data = r.json()
    assert data["book"] == "Psalms"
    assert data["chapter"] == 23
    assert len(data["verses"]) > 0


@pytest.mark.asyncio
async def test_chapter_not_found(client):
    r = await client.get("/api/bible/chapter/Psalms/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_bible_search(client):
    r = await client.get("/api/bible/search?q=shepherd")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_add_bookmark(client, auth_headers):
    r = await client.post("/api/bible/bookmarks", headers=auth_headers, json={
        "book": "Psalms",
        "chapter": 23,
        "verse_number": 1,
        "verse_text": "The LORD is my shepherd; I shall not want.",
        "note": "My favourite verse",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["book"] == "Psalms"
    assert data["chapter"] == 23


@pytest.mark.asyncio
async def test_get_bookmarks(client, auth_headers):
    r = await client.get("/api/bible/bookmarks", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_add_highlight(client, auth_headers):
    r = await client.post("/api/bible/highlights", headers=auth_headers, json={
        "book": "John",
        "chapter": 3,
        "verse_number": 16,
        "verse_text": "For God so loved the world...",
        "color": "#f59e0b",
    })
    assert r.status_code == 201


# ─── Reminders ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_reminders(client, auth_headers):
    r = await client.get("/api/reminders", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_create_and_toggle_reminder(client, auth_headers):
    create_r = await client.post("/api/reminders", headers=auth_headers, json={
        "title": "Test Reminder",
        "icon": "⏰",
        "time": "08:00",
        "enabled": True,
    })
    assert create_r.status_code == 201
    rid = create_r.json()["id"]

    toggle_r = await client.patch(f"/api/reminders/{rid}/toggle", headers=auth_headers)
    assert toggle_r.status_code == 200
    assert toggle_r.json()["enabled"] is False


# ─── Journal ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_journal_entry(client, auth_headers):
    r = await client.post("/api/journal", headers=auth_headers, json={
        "title": "Morning Prayer",
        "content": "Thank You Lord for this day...",
        "mood": "peaceful",
        "category": "morning",
    })
    assert r.status_code == 201
    assert r.json()["title"] == "Morning Prayer"


@pytest.mark.asyncio
async def test_list_journal_entries(client, auth_headers):
    r = await client.get("/api/journal", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ─── Mood ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_mood(client, auth_headers):
    r = await client.post("/api/mood", headers=auth_headers, json={
        "mood": "grateful",
        "note": "Feeling blessed today",
    })
    assert r.status_code == 201
    assert r.json()["mood"] == "grateful"


@pytest.mark.asyncio
async def test_get_today_mood(client, auth_headers):
    await client.post("/api/mood", headers=auth_headers, json={"mood": "joyful"})
    r = await client.get("/api/mood/today", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_mood_summary(client, auth_headers):
    r = await client.get("/api/mood/summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "breakdown" in data


# ─── Focus ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_toggle_focus_mode(client, auth_headers):
    r = await client.post("/api/focus/mode/toggle", headers=auth_headers)
    assert r.status_code == 200
    assert "focus_mode_active" in r.json()


@pytest.mark.asyncio
async def test_add_blocked_app(client, auth_headers):
    r = await client.post("/api/focus/blocked-apps", headers=auth_headers, json={
        "app_name": "Instagram",
        "app_icon": "📸",
        "app_color": "#e1306c",
        "daily_limit_minutes": 30,
    })
    assert r.status_code == 201
    assert r.json()["app_name"] == "Instagram"


@pytest.mark.asyncio
async def test_list_blocked_apps(client, auth_headers):
    r = await client.get("/api/focus/blocked-apps", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_log_screen_time(client, auth_headers):
    r = await client.post("/api/focus/screen-time", headers=auth_headers, json={
        "app_name": "Instagram",
        "minutes_used": 45.5,
    })
    assert r.status_code == 201
    assert r.json()["minutes_used"] == 45.5


@pytest.mark.asyncio
async def test_weekly_screen_time(client, auth_headers):
    r = await client.get("/api/focus/screen-time/weekly", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "week_data" in data
    assert "focus_score" in data
    assert len(data["week_data"]) == 7


# ─── Progress ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_badges(client, auth_headers):
    r = await client.get("/api/progress/badges", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "earned" in data[0]


@pytest.mark.asyncio
async def test_progress_summary(client, auth_headers):
    r = await client.get("/api/progress/summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "prayer_streak" in data
    assert "bible_streak" in data
    assert "badges" in data
    assert "calendar" in data


# ─── AI Chat ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_chat(client, auth_headers):
    r = await client.post("/api/ai/chat", headers=auth_headers, json={
        "message": "I need encouragement today",
    })
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert "session_id" in data
    assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_ai_chat_history(client, auth_headers):
    # Start a chat first
    chat_r = await client.post("/api/ai/chat", headers=auth_headers, json={
        "message": "Help me pray",
    })
    session_id = chat_r.json()["session_id"]

    # Get history
    r = await client.get(f"/api/ai/chat/{session_id}/history", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == session_id
    assert len(data["messages"]) >= 2  # user + assistant


# ─── Prayer Requests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_prayer_request(client, auth_headers):
    r = await client.post("/api/prayer-requests", headers=auth_headers, json={
        "title": "Healing for my mother",
        "description": "Lord, please heal my mother from her illness. I trust in Your power.",
        "is_private": True,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Healing for my mother"
    assert data["is_answered"] is False


@pytest.mark.asyncio
async def test_list_prayer_requests(client, auth_headers):
    r = await client.get("/api/prayer-requests", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_mark_prayer_answered(client, auth_headers):
    create_r = await client.post("/api/prayer-requests", headers=auth_headers, json={
        "title": "Job provision",
        "description": "Praying for a new job opportunity",
    })
    pr_id = create_r.json()["id"]

    r = await client.post(
        f"/api/prayer-requests/{pr_id}/answer",
        headers=auth_headers,
        params={"answered_note": "God provided! Got the job!"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_answered"] is True
    assert data["answered_at"] is not None
