"""Common reply keyboards used across handlers."""

from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the persistent main-menu reply keyboard.

    Returns:
        A reply keyboard exposing the most common commands as buttons.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="Помощь")
    builder.button(text="Моя память")
    builder.button(text="Стереть память")
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True, is_persistent=True)
