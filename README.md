# ✦ Godfident — Python Backend API

A production-ready **FastAPI** backend for the Godfident spiritual discipline app.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd godfident-backend
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to something random
```

### 3. Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. (Optional) Seed demo data
```bash
python -m app.db.seed
```
This creates a demo user:
- **Email:** `demo@godfident.app`
- **Password:** `password123`

### 5. View API docs
Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive Swagger UI.

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```

All 40+ tests run against an in-memory SQLite database.

---

## 🗂️ Project Structure

```
godfident-backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, middleware, route registration
│   ├── config.py            # Pydantic settings (reads .env)
│   ├── db/
│   │   ├── database.py      # SQLAlchemy async engine & session
│   │   └── seed.py          # Demo data seeder
│   ├── models/
│   │   └── models.py        # All SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py       # All Pydantic request/response schemas
│   ├── services/
│   │   ├── auth_service.py  # JWT creation, hashing, get_current_user
│   │   ├── bible_service.py # Static Bible data & verse logic
│   │   ├── streak_service.py# Streak calculation & badge awarding
│   │   └── ai_service.py    # Anthropic Claude integration + fallbacks
│   └── routers/
│       ├── auth.py          # POST /register, /login, /logout
│       ├── users.py         # GET/PATCH /users/me
│       ├── dashboard.py     # GET /dashboard (home screen data)
│       ├── devotion.py      # Prayer/Bible check-ins, streaks, calendar
│       ├── bible.py         # Verse of day, chapter reader, bookmarks
│       ├── reminders.py     # CRUD reminders + toggle
│       ├── journal.py       # Prayer journal CRUD
│       ├── mood.py          # Mood logging & monthly summary
│       ├── focus.py         # App blocking, screen time, focus mode
│       ├── progress.py      # Badges, progress summary
│       ├── ai_chat.py       # AI encouragement chat
│       └── prayer_requests.py # Prayer request CRUD + mark answered
├── tests/
│   └── test_api.py          # Full test suite (40+ tests)
├── requirements.txt
├── pytest.ini
├── alembic.ini
├── .env.example
└── README.md
```

---

## 📡 API Reference

All routes are prefixed with `/api`.

### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account → returns JWT |
| POST | `/api/auth/login` | Login → returns JWT |
| POST | `/api/auth/logout` | Logout (client deletes token) |

### 👤 Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/me` | Get current user profile |
| PATCH | `/api/users/me` | Update profile / settings |
| DELETE | `/api/users/me` | Deactivate account |

### 🏠 Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Full home screen data (streaks, verse, devotion, reminders) |

### 🙏 Devotion & Streaks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devotion/today` | Today's devotion log |
| POST | `/api/devotion/pray` | Mark prayer done → updates streak |
| POST | `/api/devotion/read` | Mark Bible reading done → updates streak |
| PATCH | `/api/devotion/today` | Update notes |
| GET | `/api/devotion/streaks` | All 3 streaks (prayer, bible, focus) |
| GET | `/api/devotion/progress` | Full progress summary |
| GET | `/api/devotion/calendar` | Monthly calendar `?year=&month=` |
| GET | `/api/devotion/history` | Past 30 devotion logs |

### 📖 Bible
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/bible/verse-of-day` | Daily rotating verse |
| GET | `/api/bible/inspiration` | Random inspirational verse |
| GET | `/api/bible/books` | OT & NT book lists |
| GET | `/api/bible/chapter/{book}/{chapter}` | Read a chapter |
| GET | `/api/bible/search?q=` | Search scripture |
| GET | `/api/bible/bookmarks` | List bookmarks |
| POST | `/api/bible/bookmarks` | Add bookmark |
| DELETE | `/api/bible/bookmarks/{id}` | Remove bookmark |
| GET | `/api/bible/highlights` | List highlights `?book=&chapter=` |
| POST | `/api/bible/highlights` | Add highlight |
| DELETE | `/api/bible/highlights/{id}` | Remove highlight |

### 🔔 Reminders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reminders` | List all reminders |
| POST | `/api/reminders` | Create reminder |
| GET | `/api/reminders/{id}` | Get single reminder |
| PATCH | `/api/reminders/{id}` | Update reminder |
| DELETE | `/api/reminders/{id}` | Delete reminder |
| PATCH | `/api/reminders/{id}/toggle` | Toggle enabled/disabled |

### 📓 Journal
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/journal` | List entries `?category=&mood=` |
| POST | `/api/journal` | Create entry |
| GET | `/api/journal/{id}` | Get entry |
| PATCH | `/api/journal/{id}` | Update entry |
| DELETE | `/api/journal/{id}` | Delete entry |

### 😊 Mood
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mood` | Log today's mood |
| GET | `/api/mood/today` | Get today's mood |
| GET | `/api/mood/history` | Past 30 mood logs |
| GET | `/api/mood/summary` | Monthly mood breakdown |

### 🎯 Focus & Screen Time
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/focus/mode/toggle` | Toggle focus mode |
| GET | `/api/focus/mode/status` | Get focus mode status |
| GET | `/api/focus/blocked-apps` | List blocked apps |
| POST | `/api/focus/blocked-apps` | Add app to block list |
| PATCH | `/api/focus/blocked-apps/{id}` | Update limit/status |
| DELETE | `/api/focus/blocked-apps/{id}` | Remove from list |
| PATCH | `/api/focus/blocked-apps/{id}/lock` | Lock app entirely |
| POST | `/api/focus/screen-time` | Log screen time for an app |
| GET | `/api/focus/screen-time/today` | Today's screen time summary |
| GET | `/api/focus/screen-time/weekly` | 7-day chart data + focus score |
| GET | `/api/focus/screen-time/history` | Historical screen time |

### 🏆 Progress & Badges
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/progress/badges` | All badges with earned status |
| GET | `/api/progress/summary` | Full progress summary with calendar |

### 🤖 AI Encouragement
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/chat` | Send message, receive encouragement |
| GET | `/api/ai/chat/sessions` | List chat sessions |
| GET | `/api/ai/chat/{session_id}/history` | Get session history |

### 🙏 Prayer Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prayer-requests` | List `?answered=true/false` |
| POST | `/api/prayer-requests` | Create request |
| GET | `/api/prayer-requests/{id}` | Get single request |
| PATCH | `/api/prayer-requests/{id}` | Update request |
| POST | `/api/prayer-requests/{id}/answer` | Mark as answered |
| DELETE | `/api/prayer-requests/{id}` | Delete |

---

## 🔑 Authentication

All protected routes require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

Tokens are valid for **7 days** by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

## 🌍 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing secret — **change in production** |
| `DATABASE_URL` | `sqlite+aiosqlite:///./godfident.db` | Database connection string |
| `ANTHROPIC_API_KEY` | *(optional)* | Enables real Claude AI responses |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | JWT expiry |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS origins |

---

## 🐳 Production Deployment

### With PostgreSQL
```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/godfident
```

### Install asyncpg driver
```bash
pip install asyncpg
```

### Run with gunicorn
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## ✦ "Seek first His kingdom and His righteousness" — Matthew 6:33
