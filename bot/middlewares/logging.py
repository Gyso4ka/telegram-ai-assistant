"""Logging context middleware.

Binds per-update context (user id, chat id, update type) to structlog's
context vars so all logs emitted while handling an update carry that context.
No message content or secrets are logged.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class LoggingMiddleware(BaseMiddleware):
    """Binds contextual fields to structlog for the duration of an update."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Bind context vars, run the handler, then clear them."""
        from_user = getattr(event, "from_user", None)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            event_type=type(event).__name__,
            user_id=from_user.id if from_user is not None else None,
        )
        try:
            return await handler(event, data)
        finally:
            structlog.contextvars.clear_contextvars()
