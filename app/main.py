from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bot.bot import remove_webhook, set_webhook
from app.core.config import settings
from app.routers import auth, telegram, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await set_webhook()
    yield
    # --- Shutdown ---
    await remove_webhook()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# Tighten allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(telegram.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
