"""Structured logging configuration.

Uses ``structlog`` to emit JSON-friendly, context-rich logs. Secrets are
never logged: callers must pass only non-sensitive fields.
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure standard logging and structlog processors.

    Args:
        level: Log level name (e.g. ``"INFO"``, ``"DEBUG"``).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger.

    Args:
        name: Optional logger name, typically ``__name__``.

    Returns:
        A configured structlog logger instance.
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
