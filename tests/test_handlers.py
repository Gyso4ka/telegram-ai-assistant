"""Tests for Telegram handlers.

Handlers are thin: they validate input, call services and send a response.
These tests use lightweight fakes for the aiogram ``Message`` so no network
or real bot is required, verifying the handler wires input to services and
replies correctly.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.text import handle_text
from database.repositories.fact_repository import FactRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.user_repository import UserRepository
from services.chat_service import ChatService
from services.memory.memory_service import MemoryService
from tests.conftest import FakeAIService

pytestmark = pytest.mark.asyncio


class FakeBot:
    """Minimal stand-in for ``message.bot`` recording chat actions."""

    def __init__(self) -> None:
        self.actions: list[tuple[int, str]] = []

    async def send_chat_action(self, chat_id: int, action: str) -> None:
        self.actions.append((chat_id, action))


class FakeChat:
    """Minimal chat with an id."""

    def __init__(self, chat_id: int = 999) -> None:
        self.id = chat_id


class FakeMessage:
    """Minimal stand-in for aiogram ``Message`` used by handlers."""

    def __init__(self, text: str | None) -> None:
        self.text = text
        self.chat = FakeChat()
        self.bot = FakeBot()
        self.answers: list[str] = []

    async def answer(self, text: str, **_: Any) -> None:
        self.answers.append(text)


def _build_memory(session: AsyncSession) -> MemoryService:
    return MemoryService(
        user_repository=UserRepository(session),
        message_repository=MessageRepository(session),
        fact_repository=FactRepository(session),
        history_limit=20,
    )


async def test_handle_text_replies_with_ai_output(
    session: AsyncSession, fake_ai: FakeAIService
) -> None:
    memory = _build_memory(session)
    user = await memory.register_user(
        telegram_id=100, username=None, full_name=None, language_code=None
    )
    chat = ChatService(ai=fake_ai, memory=memory)
    message = FakeMessage("hello there")

    await handle_text(
        message=message,  # type: ignore[arg-type]
        user=user,
        chat_service=chat,
        max_input_chars=4000,
    )

    assert message.answers == ["fake reply"]
    assert message.bot.actions  # typing indicator was sent


async def test_handle_text_rejects_empty_input(
    session: AsyncSession, fake_ai: FakeAIService
) -> None:
    memory = _build_memory(session)
    user = await memory.register_user(
        telegram_id=101, username=None, full_name=None, language_code=None
    )
    chat = ChatService(ai=fake_ai, memory=memory)
    message = FakeMessage("    ")

    await handle_text(
        message=message,  # type: ignore[arg-type]
        user=user,
        chat_service=chat,
        max_input_chars=4000,
    )

    assert len(message.answers) == 1
    assert "couldn't process" in message.answers[0]
    assert fake_ai.text_calls == []
