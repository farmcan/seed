from __future__ import annotations

import base64
import os
from pathlib import Path

from openai import OpenAI


DEFAULT_DASHSCOPE_MODEL = os.getenv("SEED_DASHSCOPE_ASR_MODEL", "qwen3-asr-flash")
DEFAULT_DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def transcribe_dashscope_audio(
    audio_path: Path,
    *,
    model: str = DEFAULT_DASHSCOPE_MODEL,
    language: str | None = None,
    prompt: str | None = None,
    base_url: str = DEFAULT_DASHSCOPE_BASE_URL,
) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY or QWEN_API_KEY is required for DashScope ASR")

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = build_messages(audio_data=audio_data_url(audio_path), prompt=prompt)
    asr_options: dict[str, object] = {"enable_itn": True}
    if language:
        asr_options["language"] = language

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={"asr_options": asr_options},
    )
    return str(response.choices[0].message.content or "").strip()


def audio_data_url(audio_path: Path) -> str:
    encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    return f"data:{mime_type_for_audio(audio_path)};base64,{encoded}"


def build_messages(*, audio_data: str, prompt: str | None = None) -> list[dict]:
    messages = []
    if prompt:
        messages.append({"role": "system", "content": [{"text": prompt}]})
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {"data": audio_data},
                }
            ],
        }
    )
    return messages


def mime_type_for_audio(audio_path: Path) -> str:
    suffix = audio_path.suffix.lower()
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".webm":
        return "audio/webm"
    if suffix in {".m4a", ".mp4"}:
        return "audio/mp4"
    return "application/octet-stream"
