"""Rate-limiting (throttling) middleware.

Protects the bot and the AI provider from abuse by limiting how frequently a
single user may trigger handlers. Uses Redis when available for a shared,
sliding-window limiter; falls back to an in-memory limiter otherwise.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from redis.asyncio import Redis

from utils.logging import get_logger

logger = get_logger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Limits each user to a maximum number of requests per time window."""

    def __init__(
        self,
        *,
        redis: Redis | None,
        max_requests: int,
        window_seconds: float,
    ) -> None:
        """Configure the limiter.

        Args:
            redis: Optional async Redis client for a shared limiter.
            max_requests: Maximum allowed requests per window per user.
            window_seconds: Length of the sliding window in seconds.
        """
        self._redis = redis
        self._max_requests = max_requests
        self._window = window_seconds
        self._local: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Allow or drop the update based on the user's recent request rate."""
        user_id = self._extract_user_id(event)
        if user_id is None:
            return await handler(event, data)

        allowed = await self._is_allowed(user_id)
        if not allowed:
            if isinstance(event, Message):
                await event.answer(
                    "You are sending messages too quickly. " "Please wait a moment and try again."
                )
            return None

        return await handler(event, data)

    async def _is_allowed(self, user_id: int) -> bool:
        """Return whether the user is under the rate limit."""
        if self._redis is not None:
            return await self._is_allowed_redis(user_id)
        return self._is_allowed_local(user_id)

    async def _is_allowed_redis(self, user_id: int) -> bool:
        """Sliding-window check backed by Redis sorted sets."""
        assert self._redis is not None  # noqa: S101 - guarded by caller
        key = f"throttle:{user_id}"
        now = time.monotonic()
        cutoff = now - self._window
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, int(self._window) + 1)
                _, _, count, _ = await pipe.execute()
            return int(count) <= self._max_requests
        except Exception as exc:  # noqa: BLE001 - never fail open loudly
            logger.warning("throttle_redis_failed", error=type(exc).__name__)
            return self._is_allowed_local(user_id)

    def _is_allowed_local(self, user_id: int) -> bool:
        """Sliding-window check backed by an in-process dict."""
        now = time.monotonic()
        cutoff = now - self._window
        timestamps = [t for t in self._local[user_id] if t > cutoff]
        timestamps.append(now)
        self._local[user_id] = timestamps
        return len(timestamps) <= self._max_requests

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        """Return the Telegram user id for supported event types."""
        from_user = getattr(event, "from_user", None)
        return from_user.id if from_user is not None else None
