"""Prompt templates package.

Prompts are kept out of business logic so they can be reviewed, versioned
and iterated on independently of code.
"""

from services.ai.prompts.loader import get_prompt

__all__ = ["get_prompt"]
