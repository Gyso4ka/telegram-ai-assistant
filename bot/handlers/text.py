"""Text message handler.

Receives plain text messages, validates them, delegates to the chat service
and returns the assistant's reply. No business logic lives here.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from database.models.user import User
from services.ai.base import AIServiceError
from services.chat_service import ChatService
from utils.logging import get_logger
from utils.security import InputValidationError, sanitize_text

logger = get_logger(__name__)

router = Router(name="text")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(
    message: Message,
    user: User,
    chat_service: ChatService,
    max_input_chars: int,
) -> None:
    """Answer a free-form text message from the user.

    Args:
        message: The incoming Telegram message.
        user: The resolved application user (injected by middleware).
        chat_service: Orchestration service for a conversation turn.
        max_input_chars: Maximum accepted input length.
    """
    try:
        text = sanitize_text(message.text or "", max_chars=max_input_chars)
    except InputValidationError as exc:
        await message.answer(f"I couldn't process that: {exc}")
        return

    assert message.bot is not None  # noqa: S101 - always set for incoming updates
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        reply = await chat_service.reply(user=user, message=text)
    except AIServiceError:
        logger.error("text_reply_failed")
        await message.answer("Sorry, I couldn't generate a response right now. Please try again.")
        return

    await message.answer(reply)
