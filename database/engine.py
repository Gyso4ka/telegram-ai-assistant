"""Async SQLAlchemy engine and session factory.

Provides a single place to construct the async engine and an
``async_sessionmaker`` used by the dependency-injection middleware.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Owns the async engine and session factory.

    A single instance is created at application startup and disposed at
    shutdown. Sessions are short-lived and created per update.
    """

    def __init__(self, url: str, *, echo: bool = False) -> None:
        """Create the engine and session factory.

        Args:
            url: Async SQLAlchemy connection URL.
            echo: Whether to log emitted SQL (development only).
        """
        self._engine: AsyncEngine = create_async_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Return the underlying async engine."""
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Return the session factory."""
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield a transactional session, committing or rolling back.

        Yields:
            An :class:`AsyncSession` that is committed on success and rolled
            back if the enclosed block raises.
        """
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        """Dispose the engine and close all pooled connections."""
        await self._engine.dispose()
