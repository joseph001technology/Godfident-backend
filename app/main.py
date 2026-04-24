# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
import time
import secrets

# SQLAdmin
from sqladmin import Admin, ModelView
from starlette.middleware.sessions import SessionMiddleware
from sqladmin.authentication import AuthenticationBackend

from app.config import settings
from app.db.database import init_db, engine
from app.models.models import (
    User,
    Reminder,
    JournalEntry,
    PrayerRequest,
    MoodLog,
    BlockedApp,
    ScreenTimeLog,
    DevotionLog,
    Badge,
    UserBadge,
    AIChat,
)

from app.routers import (
    auth, users, dashboard, devotion, bible,
    reminders, journal, mood, focus, progress,
    ai_chat, prayer_requests,
)

 
 


# ─────────────────────────────────────────────────────────────
# ADMIN AUTH
# ─────────────────────────────────────────────────────────────
class AdminAuth(AuthenticationBackend):
    def __init__(self):
        super().__init__(secret_key=settings.SESSION_SECRET_KEY)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if (
            username == settings.ADMIN_USERNAME
            and password == settings.ADMIN_PASSWORD
        ):
            request.session["token"] = "admin_logged_in"
            return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("token") == "admin_logged_in"


authentication_backend = AdminAuth()
# ─────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    await init_db()
    print("✅ Database initialised")
    yield
    print("👋 Shutting down...")


# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# sessions required for admin login
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY
)


# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ─────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        },
    )


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────
API = "/api"

app.include_router(auth.router, prefix=API)
app.include_router(users.router, prefix=API)
app.include_router(dashboard.router, prefix=API)
app.include_router(devotion.router, prefix=API)
app.include_router(bible.router, prefix=API)
app.include_router(reminders.router, prefix=API)
app.include_router(journal.router, prefix=API)
app.include_router(mood.router, prefix=API)
app.include_router(focus.router, prefix=API)
app.include_router(progress.router, prefix=API)
app.include_router(ai_chat.router, prefix=API)
app.include_router(prayer_requests.router, prefix=API)


# ─────────────────────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────────────────────
admin = Admin(
    app,
    engine,
    authentication_backend=authentication_backend,
    title="Godfident Admin Dashboard",
    base_url="/admin",
)


# ---------------- USERS ----------------
class UserAdmin(ModelView, model=User):
    icon = "fa-solid fa-users"
    column_list = [
        User.id,
        User.email,
        User.username,
        User.is_active,
        User.is_verified,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.username]
    column_sortable_list = [User.created_at]
    page_size = 30


# ---------------- REMINDERS ----------------
class ReminderAdmin(ModelView, model=Reminder):
    icon = "fa-solid fa-bell"
    column_list = [
        Reminder.id,
        Reminder.title,
        Reminder.time,
        Reminder.enabled,
        Reminder.created_at,
    ]


# ---------------- JOURNAL ----------------
class JournalAdmin(ModelView, model=JournalEntry):
    icon = "fa-solid fa-book"
    column_list = [
        JournalEntry.id,
        JournalEntry.title,
        JournalEntry.category,
        JournalEntry.created_at,
    ]


# ---------------- PRAYER ----------------
class PrayerAdmin(ModelView, model=PrayerRequest):
    icon = "fa-solid fa-hands-praying"
    column_list = [
        PrayerRequest.id,
        PrayerRequest.title,
        PrayerRequest.is_answered,
        PrayerRequest.created_at,
    ]


# ---------------- MOOD ----------------
class MoodAdmin(ModelView, model=MoodLog):
    icon = "fa-solid fa-face-smile"
    column_list = [MoodLog.id, MoodLog.mood, MoodLog.date]


# ---------------- BLOCKED APPS ----------------
class BlockedAppsAdmin(ModelView, model=BlockedApp):
    icon = "fa-solid fa-mobile-screen"
    column_list = [
        BlockedApp.id,
        BlockedApp.app_name,
        BlockedApp.status,
        BlockedApp.daily_limit_minutes,
    ]


# ---------------- SCREEN TIME ----------------
class ScreenTimeAdmin(ModelView, model=ScreenTimeLog):
    icon = "fa-solid fa-clock"
    column_list = [
        ScreenTimeLog.id,
        ScreenTimeLog.app_name,
        ScreenTimeLog.minutes_used,
        ScreenTimeLog.date,
    ]


# ---------------- DEVOTION ----------------
class DevotionAdmin(ModelView, model=DevotionLog):
    icon = "fa-solid fa-cross"
    column_list = [
        DevotionLog.id,
        DevotionLog.date,
        DevotionLog.prayed,
        DevotionLog.read_bible,
    ]


# ---------------- BADGES ----------------
class BadgeAdmin(ModelView, model=Badge):
    icon = "fa-solid fa-trophy"
    column_list = [Badge.id, Badge.name, Badge.requirement_value]


class UserBadgeAdmin(ModelView, model=UserBadge):
    icon = "fa-solid fa-award"
    column_list = [UserBadge.id, UserBadge.earned_at]


# ---------------- AI CHAT ----------------
class AIChatAdmin(ModelView, model=AIChat):
    icon = "fa-solid fa-robot"
    column_list = [AIChat.id, AIChat.session_id, AIChat.role, AIChat.created_at]


# register all
admin.add_view(UserAdmin)
admin.add_view(ReminderAdmin)
admin.add_view(JournalAdmin)
admin.add_view(PrayerAdmin)
admin.add_view(MoodAdmin)
admin.add_view(BlockedAppsAdmin)
admin.add_view(ScreenTimeAdmin)
admin.add_view(DevotionAdmin)
admin.add_view(BadgeAdmin)
admin.add_view(UserBadgeAdmin)
admin.add_view(AIChatAdmin)


# ─────────────────────────────────────────────────────────────
# CUSTOM DASHBOARD HOME
# ─────────────────────────────────────────────────────────────
@app.get("/admin-home")
async def admin_home():
    return RedirectResponse("/admin")


# ─────────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "admin": "/admin",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}