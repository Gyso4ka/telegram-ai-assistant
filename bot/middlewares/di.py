"""Dependency-injection middleware.

Creates a fresh database session per update and constructs the
per-request services (repositories, memory, chat, vision, speech), injecting
them into handler keyword arguments. This keeps handlers free of wiring and
ensures each update runs in its own transaction.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser

from database.engine import Database
from database.repositories.fact_repository import FactRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.user_repository import UserRepository
from services.ai.base import AIService
from services.chat_service import ChatService
from services.memory.memory_service import MemoryService
from services.speech.speech_service import SpeechService
from services.vision.vision_service import VisionService


class ServicesMiddleware(BaseMiddleware):
    """Injects a DB session and constructed services into each handler.

    The AI provider is created once at startup and shared (it is stateless
    and safe for concurrent use); repositories and services that depend on a
    session are created per update.
    """

    def __init__(
        self,
        *,
        database: Database,
        ai: AIService,
        history_limit: int,
        max_input_chars: int,
    ) -> None:
        """Store shared, long-lived dependencies.

        Args:
            database: The application database (engine + session factory).
            ai: The shared AI provider instance.
            history_limit: Conversation history window size for memory.
            max_input_chars: Maximum accepted input length, forwarded to handlers.
        """
        self._database = database
        self._ai = ai
        self._history_limit = history_limit
        self._max_input_chars = max_input_chars

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Open a session, register the user, build services, run the handler.

        Updates without an associated Telegram user (e.g. some service
        messages) are passed through without a session or services, since
        every feature is user-scoped.
        """
        tg_user: TelegramUser | None = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        async with self._database.session() as session:
            user_repo = UserRepository(session)
            message_repo = MessageRepository(session)
            fact_repo = FactRepository(session)

            memory = MemoryService(
                user_repository=user_repo,
                message_repository=message_repo,
                fact_repository=fact_repo,
                history_limit=self._history_limit,
            )

            user = await memory.register_user(
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
                language_code=tg_user.language_code,
            )

            data["user"] = user
            data["ai"] = self._ai
            data["memory"] = memory
            data["chat_service"] = ChatService(ai=self._ai, memory=memory)
            data["vision_service"] = VisionService(ai=self._ai)
            data["speech_service"] = SpeechService(ai=self._ai)
            data["max_input_chars"] = self._max_input_chars

            return await handler(event, data)
