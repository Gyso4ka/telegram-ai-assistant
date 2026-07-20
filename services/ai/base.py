"""Provider-agnostic AI service interface and shared domain types.

The rest of the application depends only on :class:`AIService`, never on a
concrete provider. This keeps the AI provider replaceable (Gemini, OpenAI,
a local model, ...) without touching bot or service code.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ChatRole(enum.StrEnum):
    """Role of a message in a chat exchange."""

    USER = "user"
    ASSISTANT = "assistant"


@dataclass(slots=True, frozen=True)
class ChatMessage:
    """A single message in a conversation passed to the AI provider."""

    role: ChatRole
    content: str


class AIServiceError(Exception):
    """Raised when the AI provider fails irrecoverably."""


class AIService(ABC):
    """Abstract interface every AI provider implementation must satisfy.

    Implementations must be safe to call concurrently and must never raise
    provider-specific exceptions to callers: wrap them in
    :class:`AIServiceError` instead.
    """

    @abstractmethod
    async def generate_text(
        self,
        *,
        system_prompt: str,
        history: list[ChatMessage],
        user_message: str,
    ) -> str:
        """Generate a text reply given a system prompt and conversation.

        Args:
            system_prompt: Instruction defining assistant behaviour.
            history: Prior conversation turns, oldest first.
            user_message: The latest user message to respond to.

        Returns:
            The assistant's generated reply.

        Raises:
            AIServiceError: If generation fails.
        """

    @abstractmethod
    async def describe_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
    ) -> str:
        """Describe or analyze an image.

        Args:
            image_bytes: Raw image data.
            mime_type: The image MIME type (e.g. ``"image/jpeg"``).
            prompt: Instruction describing what to do with the image.

        Returns:
            A textual description or analysis.

        Raises:
            AIServiceError: If analysis fails.
        """

    @abstractmethod
    async def transcribe_audio(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
    ) -> str:
        """Transcribe speech in an audio clip to text.

        Args:
            audio_bytes: Raw audio data.
            mime_type: The audio MIME type (e.g. ``"audio/ogg"``).

        Returns:
            The transcribed text.

        Raises:
            AIServiceError: If transcription fails.
        """

    async def aclose(self) -> None:
        """Release any resources held by the provider. Optional override."""
        return None
