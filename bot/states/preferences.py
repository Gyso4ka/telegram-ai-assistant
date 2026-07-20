"""FSM states for the preferences-setting conversation flow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PreferencesStates(StatesGroup):
    """States for capturing a user's free-form preferences."""

    waiting_for_preferences = State()
