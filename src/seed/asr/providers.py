from __future__ import annotations

import os
from pathlib import Path

from seed.asr.dashscope_provider import DEFAULT_DASHSCOPE_MODEL, transcribe_dashscope_audio
from seed.asr.openai_provider import DEFAULT_OPENAI_TRANSCRIBE_MODEL, transcribe_openai_audio


DEFAULT_ASR_PROVIDER = os.getenv("SEED_ASR_PROVIDER", "dashscope")
DEFAULT_MODEL_BY_PROVIDER = {
    "dashscope": DEFAULT_DASHSCOPE_MODEL,
    "qwen": DEFAULT_DASHSCOPE_MODEL,
    "openai": DEFAULT_OPENAI_TRANSCRIBE_MODEL,
}


def default_model_for_provider(provider: str) -> str:
    return DEFAULT_MODEL_BY_PROVIDER.get(provider, DEFAULT_DASHSCOPE_MODEL)


def default_max_upload_mb_for_provider(provider: str) -> int:
    if provider in {"dashscope", "qwen"}:
        return 9
    return 24


def transcribe_audio(
    audio_path: Path,
    *,
    provider: str,
    model: str,
    language: str | None = None,
    prompt: str | None = None,
) -> str:
    if provider in {"dashscope", "qwen"}:
        return transcribe_dashscope_audio(
            audio_path,
            model=model,
            language=language,
            prompt=prompt,
        )
    if provider == "openai":
        return transcribe_openai_audio(
            audio_path,
            model=model,
            language=language,
            prompt=prompt,
        )
    raise ValueError(f"Unsupported ASR provider: {provider}")
