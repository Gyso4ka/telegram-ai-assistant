# syntax=docker/dockerfile:1

# ---- Base image ----
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy the full project (source is required to build the package, and
# pyproject.toml references README.md and the packages).
COPY . .

# Install the application and its runtime dependencies.
RUN pip install --upgrade pip setuptools wheel \
    && pip install .

# Run as a non-root user for security.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Default command: apply migrations then start the bot.
CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]
