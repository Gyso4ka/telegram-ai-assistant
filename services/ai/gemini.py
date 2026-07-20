"""Google Gemini implementation of :class:`AIService`.

Uses the ``google-genai`` SDK. Network calls are wrapped with retry logic
(via ``tenacity``) and provider errors are translated into
:class:`AIServiceError` so callers stay provider-agnostic.
"""

from __future__ import annotations

import asyncio
from typing import Any

from google import genai
from google.genai import types
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.ai.base import AIService, AIServiceError, ChatMessage, ChatRole
from utils.logging import get_logger
from utils.security import sanitize_external_text

logger = get_logger(__name__)

# Exceptions worth retrying: transient network/5xx style failures. We retry on
# the broad genai error base to keep coupling low.
_RETRYABLE = (genai.errors.APIError,)


class GeminiService(AIService):
    """AI provider backed by Google Gemini models."""

    def __init__(
        self,
        *,
        api_key: str,
        text_model: str,
        vision_model: str,
        audio_model: str,
    ) -> None:
        """Create the Gemini client.

        Args:
            api_key: Gemini API key (never logged).
            text_model: Model name for text generation.
            vision_model: Model name for image understanding.
            audio_model: Model name for audio transcription.
        """
        self._client = genai.Client(api_key=api_key)
        self._text_model = text_model
        self._vision_model = vision_model
        self._audio_model = audio_model

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def _generate(
        self,
        *,
        model: str,
        contents: Any,
        system_instruction: str | None = None,
    ) -> str:
        """Call the Gemini API off the event loop and return response text."""
        config = (
            types.GenerateContentConfig(system_instruction=system_instruction)
            if system_instruction
            else None
        )
        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=model,
            contents=contents,
            config=config,
        )
        text = response.text or ""
        return sanitize_external_text(text)

    async def generate_text(
        self,
        *,
        system_prompt: str,
        history: list[ChatMessage],
        user_message: str,
    ) -> str:
        """See :meth:`AIService.generate_text`."""
        contents = self._build_contents(history, user_message)
        try:
            return await self._generate(
                model=self._text_model,
                contents=contents,
                system_instruction=system_prompt,
            )
        except Exception as exc:  # noqa: BLE001 - translated to domain error
            logger.error("gemini_generate_text_failed", error=type(exc).__name__)
            raise AIServiceError("Failed to generate a text response.") from exc

    async def describe_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
    ) -> str:
        """See :meth:`AIService.describe_image`."""
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            return await self._generate(
                model=self._vision_model,
                contents=[prompt, image_part],
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("gemini_describe_image_failed", error=type(exc).__name__)
            raise AIServiceError("Failed to analyze the image.") from exc

    async def transcribe_audio(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
    ) -> str:
        """See :meth:`AIService.transcribe_audio`."""
        try:
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            return await self._generate(
                model=self._audio_model,
                contents=[
                    "Transcribe the spoken content of this audio verbatim. "
                    "Return only the transcription text.",
                    audio_part,
                ],
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("gemini_transcribe_audio_failed", error=type(exc).__name__)
            raise AIServiceError("Failed to transcribe the audio.") from exc

    @staticmethod
    def _build_contents(history: list[ChatMessage], user_message: str) -> list[types.Content]:
        """Convert domain messages into Gemini ``Content`` turns."""
        role_map = {ChatRole.USER: "user", ChatRole.ASSISTANT: "model"}
        contents: list[types.Content] = [
            types.Content(
                role=role_map[msg.role],
                parts=[types.Part.from_text(text=msg.content)],
            )
            for msg in history
        ]
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )
        return contents

    async def aclose(self) -> None:
        """No persistent resources to release for the Gemini client."""
        return None
