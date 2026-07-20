"""Load prompt templates from text files.

Prompts live as ``.txt`` files alongside this module so non-developers can
edit them without touching Python. Loaded prompts are cached in memory.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


class PromptNotFoundError(KeyError):
    """Raised when a requested prompt template does not exist."""


@cache
def get_prompt(name: str) -> str:
    """Return the text of a named prompt template.

    Args:
        name: Prompt file stem, e.g. ``"system"`` for ``system.txt``.

    Returns:
        The prompt contents with surrounding whitespace stripped.

    Raises:
        PromptNotFoundError: If no matching ``.txt`` file exists.
    """
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.is_file():
        raise PromptNotFoundError(name)
    return path.read_text(encoding="utf-8").strip()
