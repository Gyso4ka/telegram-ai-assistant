"""Handlers package.

Aggregates all feature routers into a single list consumed by the
application entrypoint. Order matters: command and text handlers are
registered before media handlers so command filtering takes precedence.
"""

from aiogram import Router

from bot.handlers.commands import router as commands_router
from bot.handlers.photo import router as photo_router
from bot.handlers.text import router as text_router
from bot.handlers.voice import router as voice_router

routers: tuple[Router, ...] = (
    commands_router,
    photo_router,
    voice_router,
    text_router,
)

__all__ = ["routers"]
