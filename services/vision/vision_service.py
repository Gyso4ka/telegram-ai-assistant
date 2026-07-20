"""Vision service: image understanding.

Wraps the AI provider's image capability with the vision prompt and any
caller-supplied question. Keeps handlers free of AI/domain logic.
"""

from __future__ import annotations

from services.ai.base import AIService
from services.ai.prompts import get_prompt
from utils.security import neutralize_injection


class VisionService:
    """Analyzes images via the configured AI provider."""

    def __init__(self, *, ai: AIService) -> None:
        """Store the AI provider."""
        self._ai = ai

    async def analyze(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        question: str | None = None,
    ) -> str:
        """Describe or answer a question about an image.

        Args:
            image_bytes: Raw image data.
            mime_type: Image MIME type (e.g. ``"image/jpeg"``).
            question: Optional user question about the image.

        Returns:
            A textual description or answer.
        """
        prompt = get_prompt("vision")
        if question:
            prompt = f"{prompt}\n\nUser question: {neutralize_injection(question)}"
        return await self._ai.describe_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            prompt=prompt,
        )
