"""Repository for :class:`User` persistence and retrieval."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User


class UserRepository:
    """Data-access layer for users.

    Repositories encapsulate all query logic so services never build SQL
    directly. A repository operates on a single :class:`AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all operations."""
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Return the user with the given Telegram id, if any."""
        result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
        language_code: str | None = None,
    ) -> User:
        """Return an existing user or create one, keeping profile fields fresh.

        Args:
            telegram_id: Stable Telegram user identifier.
            username: Optional Telegram @username.
            full_name: Optional display name.
            language_code: Optional Telegram language code.

        Returns:
            The persisted :class:`User` instance.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                language_code=language_code,
            )
            self._session.add(user)
            await self._session.flush()
            return user

        # Keep denormalized profile fields up to date.
        changed = False
        if username is not None and user.username != username:
            user.username = username
            changed = True
        if full_name is not None and user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if language_code is not None and user.language_code != language_code:
            user.language_code = language_code
            changed = True
        if changed:
            await self._session.flush()
        return user

    async def set_preferences(self, user: User, preferences: str | None) -> None:
        """Update a user's free-form preferences string."""
        user.preferences = preferences
        await self._session.flush()

    async def set_blocked(self, user: User, blocked: bool) -> None:
        """Mark a user as blocked or unblocked."""
        user.is_blocked = blocked
        await self._session.flush()
