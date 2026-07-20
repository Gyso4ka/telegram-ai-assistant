"""AI provider abstraction layer.

Exposes the provider-agnostic interface and a factory. Concrete provider
modules (e.g. :mod:`services.ai.gemini`) are imported lazily by the factory.
"""

from services.ai.base import (
    AIService,
    AIServiceError,
    ChatMessage,
    ChatRole,
)
from services.ai.factory import UnknownProviderError, create_ai_service

__all__ = [
    "AIService",
    "AIServiceError",
    "ChatMessage",
    "ChatRole",
    "create_ai_service",
    "UnknownProviderError",
]
