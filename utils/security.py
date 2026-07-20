"""Security helpers: input validation and prompt-injection mitigation.

Telegram user data is untrusted. These utilities sanitize and constrain
user-provided text before it reaches the AI provider or the database.
"""

from __future__ import annotations

import re

# Patterns commonly used in prompt-injection attempts. Matches are neutralized
# rather than rejected, so legitimate messages that happen to contain these
# words still work while obvious override attempts lose their power.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all\s+previous)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\s+different", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"</?(system|assistant|user)>", re.IGNORECASE),
)

# Control characters except common whitespace (\t, \n, \r).
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class InputValidationError(ValueError):
    """Raised when user input fails validation."""


def sanitize_text(text: str, *, max_chars: int) -> str:
    """Validate and sanitize free-form user text.

    Args:
        text: Raw text received from the user.
        max_chars: Maximum number of characters allowed.

    Returns:
        Cleaned text safe to persist and forward to the AI provider.

    Raises:
        InputValidationError: If the text is empty or exceeds ``max_chars``.
    """
    if text is None:
        raise InputValidationError("Empty message.")

    cleaned = _CONTROL_CHARS.sub("", text).strip()

    if not cleaned:
        raise InputValidationError("Empty message.")

    if len(cleaned) > max_chars:
        raise InputValidationError(f"Message too long ({len(cleaned)} chars, max {max_chars}).")

    return cleaned


def neutralize_injection(text: str) -> str:
    """Defang common prompt-injection phrases in untrusted text.

    The intent is defense-in-depth: the system prompt already isolates user
    content, but neutralizing known override phrases reduces risk further.

    Args:
        text: User-provided text.

    Returns:
        Text with injection phrases wrapped so they read as inert quotes.
    """
    result = text
    for pattern in _INJECTION_PATTERNS:
        result = pattern.sub(lambda m: f"[redacted: {m.group(0)}]", result)
    return result


def sanitize_external_text(text: str, *, max_chars: int = 8000) -> str:
    """Sanitize text returned by an external API before use.

    Args:
        text: Raw text from an external service (e.g. AI provider).
        max_chars: Hard cap to avoid unbounded output.

    Returns:
        Cleaned, length-limited text.
    """
    if not text:
        return ""
    cleaned = _CONTROL_CHARS.sub("", text).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip() + "…"
    return cleaned
