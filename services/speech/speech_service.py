"""Speech service: voice message transcription.

Wraps the AI provider's audio capability. Converting speech to text is kept
here so handlers only deal with Telegram I/O.
"""

from __future__ import annotations

from services.ai.base import AIService


class SpeechService:
    """Transcribes voice/audio messages via the configured AI provider."""

    def __init__(self, *, ai: AIService) -> None:
        """Store the AI provider."""
        self._ai = ai

    async def transcribe(self, *, audio_bytes: bytes, mime_type: str) -> str:
        """Transcribe an audio clip to text.

        Args:
            audio_bytes: Raw audio data.
            mime_type: Audio MIME type (e.g. ``"audio/ogg"``).

        Returns:
            The transcribed text.
        """
        return await self._ai.transcribe_audio(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
        )
