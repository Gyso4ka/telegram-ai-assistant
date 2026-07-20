"""Shared pytest fixtures.

Provides an in-memory SQLite database (async), initialized schema, a session
factory, and a fake AI provider so tests run without PostgreSQL, Redis or any
network access.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.models.base import Base
from services.ai.base import AIService, ChatMessage


class FakeAIService(AIService):
    """Deterministic in-memory AI provider for tests.

    Records the arguments it receives and returns canned responses so tests
    can assert on orchestration without hitting a real provider.
    """

    def __init__(self) -> None:
        self.text_calls: list[dict[str, object]] = []
        self.image_calls: list[dict[str, object]] = []
        self.audio_calls: list[dict[str, object]] = []
        self.text_response = "fake reply"
        self.image_response = "a fake image description"
        self.audio_response = "fake transcription"

    async def generate_text(
        self,
        *,
        system_prompt: str,
        history: list[ChatMessage],
        user_message: str,
    ) -> str:
        self.text_calls.append(
            {
                "system_prompt": system_prompt,
                "history": history,
                "user_message": user_message,
            }
        )
        return self.text_response

    async def describe_image(self, *, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        self.image_calls.append(
            {"image_bytes": image_bytes, "mime_type": mime_type, "prompt": prompt}
        )
        return self.image_response

    async def transcribe_audio(self, *, audio_bytes: bytes, mime_type: str) -> str:
        self.audio_calls.append({"audio_bytes": audio_bytes, "mime_type": mime_type})
        return self.audio_response


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Create an isolated in-memory SQLite database with the schema applied."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a single committed session for repository/service tests."""
    async with session_factory() as db_session:
        yield db_session
        await db_session.commit()


@pytest.fixture
def fake_ai() -> FakeAIService:
    """Return a fresh fake AI provider."""
    return FakeAIService()
