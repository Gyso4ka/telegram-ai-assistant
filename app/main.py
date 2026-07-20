"""Application entrypoint (composition root).

Wires configuration, logging, the database, the AI provider, Redis-backed
FSM storage and all bot routers/middlewares, then starts long-polling.
Everything is constructed here so the rest of the codebase stays decoupled.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.handlers import routers
from bot.middlewares.di import ServicesMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from config.settings import Settings, get_settings
from database.engine import Database
from services.ai.base import AIService
from services.ai.factory import create_ai_service
from utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def _build_redis(settings: Settings) -> Redis | None:
    """Create and probe a Redis client, returning ``None`` if unavailable.

    Redis is optional: if it cannot be reached the bot degrades gracefully to
    in-memory FSM storage and an in-process rate limiter.

    Args:
        settings: Application settings holding the Redis URL.

    Returns:
        A connected :class:`Redis` client, or ``None`` on failure.
    """
    try:
        redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        return redis
    except Exception as exc:  # noqa: BLE001 - optional dependency
        logger.warning("redis_unavailable", error=type(exc).__name__)
        return None


def _register_middlewares(
    dispatcher: Dispatcher,
    *,
    database: Database,
    ai: AIService,
    redis: Redis | None,
    settings: Settings,
) -> None:
    """Attach all middlewares to the dispatcher's message/callback pipelines."""
    logging_mw = LoggingMiddleware()
    throttling_mw = ThrottlingMiddleware(
        redis=redis,
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_seconds,
    )
    services_mw = ServicesMiddleware(
        database=database,
        ai=ai,
        history_limit=settings.history_limit,
        max_input_chars=settings.max_input_chars,
    )

    for observer in (dispatcher.message, dispatcher.callback_query):
        observer.middleware(logging_mw)
        observer.middleware(throttling_mw)
        observer.middleware(services_mw)


async def _run() -> None:
    """Construct dependencies and run the bot until cancelled."""
    settings = get_settings()
    configure_logging(settings.log_level)

    database = Database(settings.database_url)
    ai = create_ai_service(settings)
    redis = await _build_redis(settings)

    storage = RedisStorage(redis) if redis is not None else MemoryStorage()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=storage)

    _register_middlewares(
        dispatcher,
        database=database,
        ai=ai,
        redis=redis,
        settings=settings,
    )
    dispatcher.include_routers(*routers)

    logger.info("bot_starting", provider=settings.ai_provider)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        logger.info("bot_shutting_down")
        await bot.session.close()
        await ai.aclose()
        await database.dispose()
        if redis is not None:
            await redis.aclose()


def main() -> None:
    """Synchronous entrypoint used by the console script and Docker."""
    try:
        asyncio.run(_run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("bot_stopped")


if __name__ == "__main__":
    main()
