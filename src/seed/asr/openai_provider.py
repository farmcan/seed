from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openai import OpenAI


DEFAULT_OPENAI_TRANSCRIBE_MODEL = os.getenv("SEED_OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe")


def transcribe_openai_audio(
    audio_path: Path,
    *,
    model: str = DEFAULT_OPENAI_TRANSCRIBE_MODEL,
    language: str | None = None,
    prompt: str | None = None,
) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI ASR")

    client = OpenAI()
    request: dict[str, Any] = {
        "model": model,
        "response_format": "json",
    }
    if language:
        request["language"] = language
    if prompt:
        request["prompt"] = prompt

    with audio_path.open("rb") as audio_file:
        response = client.audio.transcriptions.create(file=audio_file, **request)

    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return str(response.get("text", "")).strip()
    return str(getattr(response, "text", "")).strip()
