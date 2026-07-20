"""Обработчики команд: /start, /help, /memory, /forget, /preferences.

Обработчики лишь получают обновления, проверяют входные данные, вызывают сервисы и отправляют ответы.
Вся бизнес-логика сосредоточена на уровне сервисов.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.common import main_menu_keyboard
from bot.states.preferences import PreferencesStates
from database.models.user import User
from services.memory.memory_service import MemoryService
from utils.security import InputValidationError, sanitize_text

router = Router(name="commands")


@router.message(CommandStart())
async def handle_start(message: Message, user: User) -> None:
    """Приветствие пользователя и регистрация его в памяти."""
    name = user.full_name or "there"
    await message.answer(
        f"Привет {name}! Я твой ИИ ассистент.\n\n"
        "Отправь мне текст, фото или голосовое сообщение и я помогу тебе!\n"
        "Я запоминаю наши разговоры, чтобы давать вам персонализированные ответы.\n\n"
        "Используйте /help, чтобы узнать, что я умею.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Вывести список доступных команд"""
    await message.answer(
        "Вот что я могу делать:\n\n"
        "- Чат: просто отправьте текстовое сообщение.\n"
        "- Изображения: отправьте фото (можно добавить к нему вопрос или комментарий).\n"
        "- Голос: отправьте голосовое сообщение — я расшифрую его и отвечу.\n\n"
        "Команды:\n"
        "/memory — показать, что я о вас помню\n"
        "/preferences — настроить стиль моих ответов\n"
        "/forget — удалить всё, что я о вас помню\n"
        "/help — показать раздел с помощью",
    )


@router.message(Command("memory"))
async def handle_memory(message: Message, user: User, memory: MemoryService) -> None:
    """Покажите пользователю, что именно ассистент помнит в данный момент."""
    context = await memory.build_context(user)
    facts = context.system_prompt
    if "Known facts about the user:" in facts:
        block = facts.split("Known facts about the user:", 1)[1].strip()
        await message.answer(f"Вот что я помню о тебе:\n\n{block}")
    else:
        await message.answer(
            "У меня пока нет никаких сведений о вас."
            "Продолжайте общаться, и я узнаю о ваших предпочтениях."
        )


@router.message(Command("forget"))
async def handle_forget(message: Message, user: User, memory: MemoryService) -> None:
    """Удалить все данные (историю, факты, предпочтения), связанные с пользователем."""
    await memory.clear_memory(user)
    await message.answer(
        "Готово. Я удалил историю вашего общения, сохраненные факты и настройки."
    )


@router.message(Command("preferences"))
async def handle_preferences_start(message: Message, state: FSMContext) -> None:
    """Процесс настройки предпочтений"""
    await state.set_state(PreferencesStates.waiting_for_preferences)
    await message.answer(
        "Скажите, как бы вы хотели, чтобы я отвечал. Например: "
        '"Ответьте кратко и формальным тоном."\n\n'
        "Отправьте /cancel для отмены."
    )


@router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext) -> None:
    """Отмена настройки предпочтений"""
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer("Отменено.")


@router.message(PreferencesStates.waiting_for_preferences)
async def handle_preferences_set(
    message: Message,
    state: FSMContext,
    user: User,
    memory: MemoryService,
    max_input_chars: int,
) -> None:
    """Сохранить предпочтения, указанные пользователем."""
    try:
        preferences = sanitize_text(message.text or "", max_chars=max_input_chars)
    except InputValidationError as exc:
        await message.answer(f"Я не смог это сохранить: {exc}")
        return

    await memory.set_preferences(user=user, preferences=preferences)
    await state.clear()
    await message.answer("Сохранил. Буду иметь это в виду.")
