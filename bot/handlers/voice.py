"""Voice message handler.

Downloads the voice clip, transcribes it via the speech service, then feeds
the transcription through the chat service so the user gets a real answer.
"""

from __future__ import annotations

import io

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from database.models.user import User
from services.ai.base import AIServiceError
from services.chat_service import ChatService
from services.speech.speech_service import SpeechService
from utils.logging import get_logger
from utils.security import InputValidationError, sanitize_text

logger = get_logger(__name__)

router = Router(name="voice")

# Telegram voice messages are OGG/Opus.
_VOICE_MIME = "audio/ogg"


@router.message(F.voice)
async def handle_voice(
    message: Message,
    user: User,
    speech_service: SpeechService,
    chat_service: ChatService,
    max_input_chars: int,
) -> None:
    """Transcribe a voice message and answer it.

    Args:
        message: The incoming Telegram message containing a voice clip.
        user: The resolved application user.
        speech_service: Service that transcribes audio to text.
        chat_service: Service that produces the assistant reply.
        max_input_chars: Maximum accepted transcription length.
    """
    if not message.voice:
        return

    assert message.bot is not None  # noqa: S101
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    buffer = io.BytesIO()
    await message.bot.download(message.voice, destination=buffer)

    try:
        transcript = await speech_service.transcribe(
            audio_bytes=buffer.getvalue(),
            mime_type=_VOICE_MIME,
        )
    except AIServiceError:
        logger.error("voice_transcribe_failed")
        await message.answer("Sorry, I couldn't understand that voice message. Please try again.")
        return

    try:
        clean_transcript = sanitize_text(transcript, max_chars=max_input_chars)
    except InputValidationError:
        await message.answer("I couldn't detect any speech in that message.")
        return

    await message.answer(f'You said: "{clean_transcript}"')

    try:
        reply = await chat_service.reply(user=user, message=clean_transcript)
    except AIServiceError:
        logger.error("voice_reply_failed")
        await message.answer("Sorry, something went wrong generating a response. Please try again.")
        return

    await message.answer(reply)
