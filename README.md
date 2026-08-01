# FastAPI · PostgreSQL · Telegram Bot Boilerplate

A production-ready, batteries-included starting point for building backends that combine a **FastAPI** REST API, an **async PostgreSQL** database (SQLAlchemy 2.0), and a **Telegram Bot** running in webhook mode — all inside a single deployable service.

This repository contains **no business logic**. It's pure infrastructure: clean architecture, async DB sessions, JWT auth with Role-Based Access Control (RBAC), a working Telegram webhook wired to [aiogram](https://docs.aiogram.dev/), Docker Compose for local development, and Alembic migrations — ready for you to build on top of.

---

## ✨ Features

- **FastAPI** app factory with lifespan-managed startup/shutdown
- **Async SQLAlchemy 2.0** engine + session-per-request dependency
- **Alembic** configured for async autogenerate migrations
- **JWT authentication** (access tokens) with **RBAC** via a reusable dependency factory (`require_role(...)`)
- **Telegram Bot** (aiogram 3.x) integrated as a FastAPI webhook route, with secret-token verification
- **Clean architecture**: routers / schemas / models / core / db are fully separated
- **Docker Compose** stack (API + PostgreSQL) for one-command local dev
- **Pytest** test suite scaffold using `httpx.AsyncClient`
- Sensible `.env`-based configuration via `pydantic-settings`

---

## 🧱 Tech Stack

| Layer          | Technology                                  |
|----------------|----------------------------------------------|
| API framework  | FastAPI, Uvicorn                              |
| Database       | PostgreSQL, SQLAlchemy 2.0 (async), asyncpg   |
| Migrations     | Alembic (async engine)                        |
| Auth           | python-jose (JWT), passlib (bcrypt)           |
| Telegram Bot   | aiogram 3.x (webhook mode)                    |
| Config         | pydantic-settings                             |
| Testing        | pytest, pytest-asyncio, httpx                 |
| Containers     | Docker, Docker Compose                        |

---

## 📁 Project Structure

```
.
├── app/
│   ├── main.py                # FastAPI app factory, lifespan, router registration
│   ├── core/
│   │   ├── config.py          # pydantic-settings: env vars, computed DB URI
│   │   └── security.py        # password hashing, JWT create/decode
│   ├── db/
│   │   ├── database.py        # async engine, session factory, get_db() dependency
│   │   ├── base.py            # shared SQLAlchemy DeclarativeBase
│   │   └── base_all.py        # imports every model — used only by Alembic autogenerate
│   ├── models/
│   │   └── user.py            # User ORM model (email, hashed_password, role, telegram_id)
│   ├── schemas/
│   │   ├── user.py            # Pydantic request/response models
│   │   └── token.py           # Token / TokenPayload schemas
│   ├── routers/
│   │   ├── auth.py            # POST /auth/register, /auth/login
│   │   ├── users.py           # GET /users/me, RBAC-protected example route
│   │   └── telegram.py        # POST /telegram/webhook
│   ├── bot/
│   │   ├── bot.py             # aiogram Bot/Dispatcher singletons + webhook lifecycle
│   │   └── handlers.py        # Telegram message/command handlers
│   └── middleware/
│       └── auth.py            # get_current_user + require_role() RBAC dependencies
├── alembic/
│   ├── env.py                 # async-aware Alembic environment
│   └── versions/               # generated migration scripts
├── tests/
│   ├── conftest.py            # async test client fixture
│   └── test_health.py
├── docker-compose.yml          # API + PostgreSQL stack
├── Dockerfile
├── Makefile                    # shortcuts: run, migrate, test, docker-up, ...
├── requirements.txt
├── requirements-dev.txt
├── alembic.ini
├── .env.example
└── README.md
```

**Why dependency-injected auth instead of raw ASGI middleware?**
FastAPI's `Depends()` system lets you protect routes selectively (per-router or per-route), shows up correctly in the OpenAPI docs, and is trivial to override in tests via `app.dependency_overrides`. A blanket `BaseHTTPMiddleware` can't easily express "this route needs `ADMIN`, that one needs any authenticated user." `app/middleware/auth.py` therefore exposes composable dependencies (`get_current_user`, `require_role(...)`) rather than a global middleware — this is the pattern FastAPI itself recommends for auth.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ (or use the provided Docker Compose setup)
- Docker & Docker Compose (optional, but recommended)
- A Telegram Bot token from [@BotFather](https://t.me/BotFather) (optional, only needed for the bot)
- A public HTTPS URL for the webhook in dev — e.g. [ngrok](https://ngrok.com/) (optional)

### 1. Clone & configure environment

```bash
git clone https://github.com/<your-org>/fastapi-postgres-telegram-boilerplate.git
cd fastapi-postgres-telegram-boilerplate
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable                   | Description                                                        |
|-----------------------------|----------------------------------------------------------------------|
| `SECRET_KEY`                | Random secret for signing JWTs — generate with `openssl rand -hex 32` |
| `POSTGRES_*`                | Database credentials (used to build the connection string)          |
| `TELEGRAM_BOT_TOKEN`        | Token from @BotFather                                                |
| `TELEGRAM_WEBHOOK_SECRET`   | Any random string — verifies incoming webhook calls are from Telegram |
| `TELEGRAM_WEBHOOK_BASE_URL` | Your public HTTPS URL (e.g. ngrok URL). Leave blank to skip the bot. |

### 2. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

This starts the API on `http://localhost:8000` and PostgreSQL on `localhost:5432`. Then, in another shell, apply migrations:

```bash
docker compose exec api alembic upgrade head
```

### 3. Or run locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Make sure PostgreSQL is running and matches your .env, then:
alembic upgrade head
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`, with interactive docs at:

- Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`

---

## 🗄️ Database Migrations

Migrations are managed with Alembic, configured for SQLAlchemy's async engine.

```bash
# Generate a new migration after changing models in app/models/
alembic revision --autogenerate -m "add users table"

# Apply migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1
```

> When you add a new model, remember to import it in `app/db/base_all.py` so Alembic's autogenerate can detect it.

---

## 🔐 Authentication & RBAC

- `POST /api/v1/auth/register` — create a user
- `POST /api/v1/auth/login` — OAuth2-password-flow login, returns a JWT access token
- `GET /api/v1/users/me` — example route requiring any authenticated user
- `GET /api/v1/users/admin-area` — example route requiring the `admin` role

To protect your own routes:

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user, require_role
from app.models.user import UserRole

router = APIRouter()

@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": str(user.id)}

@router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def admin_only():
    return {"message": "admins only"}
```

---

## 🤖 Telegram Bot Setup

The bot runs in **webhook mode** (not polling), sharing the same FastAPI process — no separate worker needed.

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token into `TELEGRAM_BOT_TOKEN`.
2. Expose your local server publicly, e.g. with ngrok:
   ```bash
   ngrok http 8000
   ```
3. Set `TELEGRAM_WEBHOOK_BASE_URL` in `.env` to the ngrok HTTPS URL.
4. Start the app — on startup, `app/bot/bot.py::set_webhook()` automatically registers `<TELEGRAM_WEBHOOK_BASE_URL>/api/v1/telegram/webhook` with Telegram, using `TELEGRAM_WEBHOOK_SECRET` to verify incoming requests.
5. Message your bot on Telegram — you should get a reply from the example handler in `app/bot/handlers.py`.

Add your own commands and logic in `app/bot/handlers.py`, and register additional routers on `dp` in `app/bot/bot.py`.

---

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest -v
```

The included `tests/conftest.py` spins up an async `httpx` client against the FastAPI app via `ASGITransport` — no live server required. Extend it with a test database fixture as your models grow.

---

## 🛠️ Useful Commands (via Makefile)

```bash
make run           # uvicorn --reload locally
make docker-up      # docker compose up --build
make docker-down     # docker compose down
make migrate         # alembic upgrade head
make revision m="add users table"   # alembic revision --autogenerate
make format           # ruff format .
make lint             # ruff check .
make test              # pytest -v
```

---

## 🗺️ Suggested Next Steps

This boilerplate deliberately stops at infrastructure. Common extensions:

- Add refresh tokens / token revocation
- Add a `telegram_id` linking flow (bot command that binds a Telegram account to a registered user)
- Add rate limiting (e.g. `slowapi`) on public endpoints
- Add structured logging and request IDs
- Add a CI workflow (lint + test) via GitHub Actions
- Swap `allow_origins=["*"]` in `app/main.py` for an explicit CORS allow-list before production

---

## 🤝 Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a PR. Run `make lint` and `make test` before pushing.

## 📄 License

Released under the [MIT License](LICENSE).
