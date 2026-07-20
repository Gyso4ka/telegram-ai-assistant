"""Repository for durable :class:`UserFact` long-term memory."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.fact import UserFact


class FactRepository:
    """Data-access layer for user facts (key/value long-term memory)."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all operations."""
        self._session = session

    async def upsert(self, *, user_id: int, key: str, value: str) -> UserFact:
        """Insert or update a fact for a user.

        The unique ``(user_id, key)`` constraint means repeated facts update
        in place rather than creating duplicates. Implemented in a
        dialect-agnostic way (read-then-write) so the same code works on
        PostgreSQL in production and SQLite in tests.

        Args:
            user_id: Internal user primary key.
            key: Fact identifier (e.g. ``"favourite_language"``).
            value: Fact value.

        Returns:
            The inserted or updated :class:`UserFact`.
        """
        result = await self._session.execute(
            select(UserFact).where(UserFact.user_id == user_id, UserFact.key == key)
        )
        fact = result.scalar_one_or_none()
        if fact is None:
            fact = UserFact(user_id=user_id, key=key, value=value)
            self._session.add(fact)
        else:
            fact.value = value
        await self._session.flush()
        return fact

    async def list_for_user(self, user_id: int) -> list[UserFact]:
        """Return all stored facts for a user, newest first."""
        result = await self._session.execute(
            select(UserFact).where(UserFact.user_id == user_id).order_by(UserFact.id.desc())
        )
        return list(result.scalars().all())

    async def delete_for_user(self, user_id: int) -> int:
        """Delete all facts belonging to a user.

        Returns:
            The number of deleted rows.
        """
        result = await self._session.execute(delete(UserFact).where(UserFact.user_id == user_id))
        await self._session.flush()
        return int(cast("CursorResult[Any]", result).rowcount or 0)
