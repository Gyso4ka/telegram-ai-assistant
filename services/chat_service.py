"""High-level chat orchestration service.

Combines the memory service and the AI provider to answer a user message:
builds personalized context, calls the provider, and records the exchange.
"""

from __future__ import annotations

from database.models.user import User
from services.ai.base import AIService
from services.memory.memory_service import MemoryService
from utils.security import neutralize_injection


class ChatService:
    """Orchestrates a single text conversation turn end to end."""

    def __init__(self, *, ai: AIService, memory: MemoryService) -> None:
        """Store the AI provider and memory service.

        Args:
            ai: Provider-agnostic AI service.
            memory: User memory service.
        """
        self._ai = ai
        self._memory = memory

    async def reply(self, *, user: User, message: str) -> str:
        """Produce and persist an assistant reply to a user message.

        Args:
            user: The user asking the question.
            message: The sanitized user message.

        Returns:
            The assistant's reply text.
        """
        safe_message = neutralize_injection(message)
        context = await self._memory.build_context(user)
        reply = await self._ai.generate_text(
            system_prompt=context.system_prompt,
            history=context.history,
            user_message=safe_message,
        )
        await self._memory.record_exchange(user=user, user_message=message, assistant_message=reply)
        return reply
