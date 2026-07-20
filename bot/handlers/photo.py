"""Photo message handler.

Downloads the largest available photo, sends it to the vision service and
returns the analysis. Optionally uses the caption as a specific question.
"""

from __future__ import annotations

import io

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from database.models.user import User
from services.ai.base import AIServiceError
from services.memory.memory_service import MemoryService
from services.vision.vision_service import VisionService
from utils.logging import get_logger
from utils.security import sanitize_text

logger = get_logger(__name__)

router = Router(name="photo")

# Telegram photos are always served as JPEG.
_PHOTO_MIME = "image/jpeg"


@router.message(F.photo)
async def handle_photo(
    message: Message,
    user: User,
    vision_service: VisionService,
    memory: MemoryService,
    max_input_chars: int,
) -> None:
    """Analyze an incoming photo and reply with a description or answer.

    Args:
        message: The incoming Telegram message containing photo sizes.
        user: The resolved application user.
        vision_service: Service that performs image understanding.
        memory: Memory service used to record the exchange.
        max_input_chars: Maximum accepted caption length.
    """
    if not message.photo:
        return

    question: str | None = None
    if message.caption:
        try:
            question = sanitize_text(message.caption, max_chars=max_input_chars)
        except Exception:  # noqa: BLE001 - caption is optional, ignore if invalid
            question = None

    assert message.bot is not None  # noqa: S101
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    # The last PhotoSize is the highest resolution.
    photo = message.photo[-1]
    buffer = io.BytesIO()
    await message.bot.download(photo, destination=buffer)

    try:
        result = await vision_service.analyze(
            image_bytes=buffer.getvalue(),
            mime_type=_PHOTO_MIME,
            question=question,
        )
    except AIServiceError:
        logger.error("photo_analyze_failed")
        await message.answer("Sorry, I couldn't analyze that image right now. Please try again.")
        return

    await memory.record_exchange(
        user=user,
        user_message=f"[sent an image] {question or ''}".strip(),
        assistant_message=result,
    )
    await message.answer(result)
