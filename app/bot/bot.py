"""
Telegram Bot instance and webhook lifecycle, built on aiogram 3.x.

The Bot/Dispatcher live here as singletons; app/routers/telegram.py
feeds incoming webhook payloads into `dp.feed_update(...)`, and
app/main.py calls set_webhook()/remove_webhook() during the FastAPI
application lifespan.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings

bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Register all routers/handlers here.
from app.bot.handlers import router as core_router  # noqa: E402

dp.include_router(core_router)


async def set_webhook() -> None:
    """Registers the FastAPI webhook URL with Telegram. Called on app startup."""
    if not settings.TELEGRAM_WEBHOOK_BASE_URL:
        # No public URL configured (e.g. local dev without ngrok) -- skip silently.
        return

    webhook_url = f"{settings.TELEGRAM_WEBHOOK_BASE_URL}{settings.API_V1_PREFIX}/telegram/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
        drop_pending_updates=True,
    )


async def remove_webhook() -> None:
    """Tears down the webhook and closes the bot's HTTP session. Called on shutdown."""
    await bot.delete_webhook()
    await bot.session.close()
