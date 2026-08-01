"""
Telegram update handlers. This is where your bot's conversational
logic lives -- replace these example handlers with your own commands.
"""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="core")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "👋 Hello! This is a boilerplate FastAPI + Telegram bot.\n"
        "Replace this handler with your own business logic in app/bot/handlers.py."
    )


@router.message(F.text)
async def echo_text(message: Message) -> None:
    """Fallback echo handler -- delete once you add real commands."""
    await message.answer(f"You said: {message.text}")
