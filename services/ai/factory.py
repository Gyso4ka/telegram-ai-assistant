"""Factory for constructing the configured :class:`AIService`.

Selecting a provider happens in exactly one place. Adding a new provider
means adding a branch here plus a new implementation module — no other code
needs to change.
"""

from __future__ import annotations

from config.settings import Settings
from services.ai.base import AIService


class UnknownProviderError(ValueError):
    """Raised when the configured AI provider is not supported."""


def create_ai_service(settings: Settings) -> AIService:
    """Build the AI service selected by configuration.

    Args:
        settings: Application settings holding the provider selection.

    Returns:
        A ready-to-use :class:`AIService` implementation.

    Raises:
        UnknownProviderError: If ``AI_PROVIDER`` is not recognized.
    """
    provider = settings.ai_provider.strip().lower()

    if provider == "gemini":
        # Imported lazily so provider SDKs are only required when selected.
        from services.ai.gemini import GeminiService

        return GeminiService(
            api_key=settings.gemini_api_key.get_secret_value(),
            text_model=settings.gemini_text_model,
            vision_model=settings.gemini_vision_model,
            audio_model=settings.gemini_audio_model,
        )

    raise UnknownProviderError(f"Unsupported AI provider: {settings.ai_provider!r}")
