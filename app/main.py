# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.config import settings
from app.db.database import init_db
from app.routers import (
    auth, users, dashboard, devotion, bible,
    reminders, journal, mood, focus, progress,
    ai_chat, prayer_requests,
)


# ─── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    await init_db()
    print("✅ Database initialised")
    yield
    # Shutdown
    print("👋 Shutting down...")


# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="""
## ✦ Godfident — Spiritual Discipline & Digital Wellness API

A full-featured backend for the **Godfident** Christian app.

### Features
- 🔐 **Auth** — JWT-based register/login
- 📖 **Bible** — Verse of the Day, chapter reader, search, bookmarks, highlights
- 🙏 **Devotion** — Prayer & Bible reading check-ins with automatic streak tracking
- 🏆 **Progress** — Streaks, badges, calendar, monthly consistency
- 🎯 **Focus** — App blocking, screen time logging, weekly analytics
- 📓 **Journal** — Prayer journal CRUD
- 😊 **Mood** — Daily mood tracking and monthly breakdown
- 🤖 **AI Chat** — Scripture-grounded encouragement via Anthropic Claude
- 🙏 **Prayer Requests** — Manage and mark answered prayers
- 🔔 **Reminders** — Configurable prayer/reading reminders

### Quick Start
1. `POST /api/auth/register` — create account
2. Use the `access_token` as `Bearer` in all subsequent requests
3. `GET /api/dashboard` — full home screen data in one call
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Timing Middleware ─────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ─── Global Exception Handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred", "type": type(exc).__name__},
    )


# ─── Routes ────────────────────────────────────────────────────────────────────

API = "/api"

app.include_router(auth.router,             prefix=API)
app.include_router(users.router,            prefix=API)
app.include_router(dashboard.router,        prefix=API)
app.include_router(devotion.router,         prefix=API)
app.include_router(bible.router,            prefix=API)
app.include_router(reminders.router,        prefix=API)
app.include_router(journal.router,          prefix=API)
app.include_router(mood.router,             prefix=API)
app.include_router(focus.router,            prefix=API)
app.include_router(progress.router,         prefix=API)
app.include_router(ai_chat.router,          prefix=API)
app.include_router(prayer_requests.router,  prefix=API)


# ─── Health / Root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "message": "✦ Walk with God today",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "app": settings.APP_NAME}
