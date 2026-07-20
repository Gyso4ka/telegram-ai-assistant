"""Tests for vision/speech services and the AI provider factory."""

from __future__ import annotations

import pytest

from config.settings import Settings
from services.ai.factory import UnknownProviderError, create_ai_service
from services.speech.speech_service import SpeechService
from services.vision.vision_service import VisionService
from tests.conftest import FakeAIService


async def test_vision_service_passes_question_into_prompt(
    fake_ai: FakeAIService,
) -> None:
    service = VisionService(ai=fake_ai)

    result = await service.analyze(
        image_bytes=b"img", mime_type="image/jpeg", question="what colour?"
    )

    prompt = fake_ai.image_calls[0].get("prompt")
    mime_type = fake_ai.image_calls[0].get("mime_type")
    assert result == "a fake image description"
    assert mime_type == "image/jpeg"
    assert isinstance(prompt, str) and "what colour?" in prompt


async def test_speech_service_transcribes(fake_ai: FakeAIService) -> None:
    service = SpeechService(ai=fake_ai)

    result = await service.transcribe(audio_bytes=b"snd", mime_type="audio/ogg")

    assert result == "fake transcription"
    assert fake_ai.audio_calls[0]["mime_type"] == "audio/ogg"


def _settings(provider: str) -> Settings:
    return Settings(
        BOT_TOKEN="x",
        GEMINI_API_KEY="y",
        AI_PROVIDER=provider,
    )  # type: ignore[call-arg]


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(UnknownProviderError):
        create_ai_service(_settings("does-not-exist"))


def test_factory_builds_gemini_service() -> None:
    service = create_ai_service(_settings("gemini"))
    # Imported lazily inside the factory; assert by class name to avoid import.
    assert type(service).__name__ == "GeminiService"
