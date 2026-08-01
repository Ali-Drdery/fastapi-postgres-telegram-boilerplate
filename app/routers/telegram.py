from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.bot.bot import bot, dp
from app.core.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    """
    Receives updates pushed by Telegram and feeds them into the aiogram
    Dispatcher. Protected by the secret token Telegram echoes back in the
    `X-Telegram-Bot-Api-Secret-Token` header (set via `set_webhook`).
    """
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret token")

    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}
