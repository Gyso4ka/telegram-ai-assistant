"""Repository for conversation :class:`Message` history."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.message import Message, MessageRole


class MessageRepository:
    """Data-access layer for conversation messages."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all operations."""
        self._session = session

    async def add(self, *, user_id: int, role: MessageRole, content: str) -> Message:
        """Persist a single conversation message.

        Args:
            user_id: Internal user primary key.
            role: Whether the message is from the user or the assistant.
            content: The textual content of the message.

        Returns:
            The persisted :class:`Message`.
        """
        message = Message(user_id=user_id, role=role, content=content)
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_recent(self, *, user_id: int, limit: int) -> list[Message]:
        """Return the most recent messages for a user in chronological order.

        Args:
            user_id: Internal user primary key.
            limit: Maximum number of messages to return.

        Returns:
            Messages ordered oldest-to-newest, capped at ``limit`` items.
        """
        result = await self._session.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def delete_for_user(self, user_id: int) -> int:
        """Delete all messages belonging to a user.

        Args:
            user_id: Internal user primary key.

        Returns:
            The number of deleted rows.
        """
        result = await self._session.execute(delete(Message).where(Message.user_id == user_id))
        await self._session.flush()
        return int(cast("CursorResult[Any]", result).rowcount or 0)
