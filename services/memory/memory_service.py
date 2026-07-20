"""User memory service.

Owns everything about a user's persistent memory: identity, conversation
history and durable facts. It builds the personalized context (system prompt
plus recent turns) that the AI provider needs and persists new turns.
"""

from __future__ import annotations

from dataclasses import dataclass

from database.models.message import MessageRole
from database.models.user import User
from database.repositories.fact_repository import FactRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.user_repository import UserRepository
from services.ai.base import ChatMessage, ChatRole
from services.ai.prompts import get_prompt


@dataclass(slots=True, frozen=True)
class ConversationContext:
    """Everything the AI needs to answer a user in a personalized way."""

    system_prompt: str
    history: list[ChatMessage]


class MemoryService:
    """Coordinates user identity, conversation history and long-term facts."""

    def __init__(
        self,
        *,
        user_repository: UserRepository,
        message_repository: MessageRepository,
        fact_repository: FactRepository,
        history_limit: int,
    ) -> None:
        """Store repositories and the history window size.

        Args:
            user_repository: Repository for users.
            message_repository: Repository for conversation messages.
            fact_repository: Repository for durable facts.
            history_limit: Maximum number of past turns to include as context.
        """
        self._users = user_repository
        self._messages = message_repository
        self._facts = fact_repository
        self._history_limit = history_limit

    async def register_user(
        self,
        *,
        telegram_id: int,
        username: str | None,
        full_name: str | None,
        language_code: str | None,
    ) -> User:
        """Fetch or create the user and refresh their profile fields."""
        return await self._users.get_or_create(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            language_code=language_code,
        )

    async def build_context(self, user: User) -> ConversationContext:
        """Assemble the personalized system prompt and recent history.

        Args:
            user: The user the context is for.

        Returns:
            A :class:`ConversationContext` ready to pass to the AI provider.
        """
        base_prompt = get_prompt("system")
        facts = await self._facts.list_for_user(user.id)

        memory_lines: list[str] = []
        if user.full_name:
            memory_lines.append(f"- name: {user.full_name}")
        if user.preferences:
            memory_lines.append(f"- preferences: {user.preferences}")
        memory_lines.extend(f"- {fact.key}: {fact.value}" for fact in facts)

        if memory_lines:
            memory_block = "\n".join(memory_lines)
            system_prompt = f"{base_prompt}\n\nKnown facts about the user:\n{memory_block}"
        else:
            system_prompt = base_prompt

        stored = await self._messages.get_recent(user_id=user.id, limit=self._history_limit)
        history = [
            ChatMessage(
                role=ChatRole.USER if m.role is MessageRole.USER else ChatRole.ASSISTANT,
                content=m.content,
            )
            for m in stored
        ]
        return ConversationContext(system_prompt=system_prompt, history=history)

    async def record_exchange(
        self, *, user: User, user_message: str, assistant_message: str
    ) -> None:
        """Persist a completed user/assistant exchange to history."""
        await self._messages.add(user_id=user.id, role=MessageRole.USER, content=user_message)
        await self._messages.add(
            user_id=user.id, role=MessageRole.ASSISTANT, content=assistant_message
        )

    async def remember_fact(self, *, user: User, key: str, value: str) -> None:
        """Store or update a durable fact about the user."""
        await self._facts.upsert(user_id=user.id, key=key, value=value)

    async def set_preferences(self, *, user: User, preferences: str | None) -> None:
        """Update the user's free-form preferences."""
        await self._users.set_preferences(user, preferences)

    async def clear_memory(self, user: User) -> None:
        """Delete all conversation history and facts for the user.

        Profile identity (the user row) is retained so the person can keep
        using the bot; only their memory is wiped.
        """
        await self._messages.delete_for_user(user.id)
        await self._facts.delete_for_user(user.id)
        await self._users.set_preferences(user, None)
