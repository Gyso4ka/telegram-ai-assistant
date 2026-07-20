"""Tests for the database repository layer using in-memory SQLite."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.message import MessageRole
from database.repositories.fact_repository import FactRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.user_repository import UserRepository

pytestmark = pytest.mark.asyncio


async def test_get_or_create_creates_then_returns_same(session: AsyncSession) -> None:
    repo = UserRepository(session)

    created = await repo.get_or_create(telegram_id=42, username="alice")
    assert created.id is not None

    again = await repo.get_or_create(telegram_id=42, username="alice")
    assert again.id == created.id


async def test_get_or_create_updates_profile_fields(session: AsyncSession) -> None:
    repo = UserRepository(session)

    await repo.get_or_create(telegram_id=7, username="old")
    updated = await repo.get_or_create(telegram_id=7, username="new")

    assert updated.username == "new"


async def test_message_history_is_chronological_and_capped(
    session: AsyncSession,
) -> None:
    users = UserRepository(session)
    messages = MessageRepository(session)
    user = await users.get_or_create(telegram_id=1)

    for i in range(5):
        await messages.add(user_id=user.id, role=MessageRole.USER, content=f"m{i}")

    recent = await messages.get_recent(user_id=user.id, limit=3)
    assert [m.content for m in recent] == ["m2", "m3", "m4"]


async def test_delete_messages_for_user(session: AsyncSession) -> None:
    users = UserRepository(session)
    messages = MessageRepository(session)
    user = await users.get_or_create(telegram_id=2)
    await messages.add(user_id=user.id, role=MessageRole.USER, content="hi")

    deleted = await messages.delete_for_user(user.id)
    assert deleted == 1
    assert await messages.get_recent(user_id=user.id, limit=10) == []


async def test_fact_upsert_inserts_and_updates(session: AsyncSession) -> None:
    users = UserRepository(session)
    facts = FactRepository(session)
    user = await users.get_or_create(telegram_id=3)

    await facts.upsert(user_id=user.id, key="city", value="Paris")
    await facts.upsert(user_id=user.id, key="city", value="Berlin")

    stored = await facts.list_for_user(user.id)
    assert len(stored) == 1
    assert stored[0].value == "Berlin"


async def test_fact_delete_for_user(session: AsyncSession) -> None:
    users = UserRepository(session)
    facts = FactRepository(session)
    user = await users.get_or_create(telegram_id=4)
    await facts.upsert(user_id=user.id, key="k", value="v")

    deleted = await facts.delete_for_user(user.id)
    assert deleted == 1
    assert await facts.list_for_user(user.id) == []
