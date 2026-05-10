from __future__ import annotations

from pathlib import Path

from seed.asr.providers import transcribe_audio
from seed.media import (
    audio_exceeds_upload_size,
    estimate_chunk_seconds,
    ensure_upload_size,
    split_audio,
)


def transcribe_audio_with_optional_chunks(
    audio_path: Path,
    *,
    provider: str,
    model: str,
    language: str | None,
    prompt: str | None,
    max_upload_mb: int,
    chunk_audio: bool = True,
    chunk_seconds: int | None = None,
) -> tuple[str, list[dict[str, object]]]:
    if not audio_exceeds_upload_size(audio_path, max_upload_mb=max_upload_mb):
        ensure_upload_size(audio_path, max_upload_mb=max_upload_mb)
        text = transcribe_audio(
            audio_path,
            provider=provider,
            model=model,
            language=language,
            prompt=prompt,
        )
        return text, []

    if not chunk_audio:
        ensure_upload_size(audio_path, max_upload_mb=max_upload_mb)

    resolved_chunk_seconds = chunk_seconds or estimate_chunk_seconds(max_upload_mb=max_upload_mb)
    chunks = split_audio(audio_path, chunk_seconds=resolved_chunk_seconds)
    chunk_texts: list[str] = []
    chunk_metadata: list[dict[str, object]] = []
    for chunk in chunks:
        ensure_upload_size(chunk.path, max_upload_mb=max_upload_mb)
        text = transcribe_audio(
            chunk.path,
            provider=provider,
            model=model,
            language=language,
            prompt=prompt,
        ).strip()
        chunk_texts.append(_format_chunk_text(chunk.index, chunk.start_seconds, text))
        chunk_metadata.append(
            {
                "index": chunk.index,
                "start_seconds": chunk.start_seconds,
                "audio_path": str(chunk.path),
                "text_length": len(text),
            }
        )
    return "\n\n".join(chunk_texts), chunk_metadata


def _format_chunk_text(index: int, start_seconds: int, text: str) -> str:
    return f"## Chunk {index + 1} ({_format_timestamp(start_seconds)})\n\n{text}"


def _format_timestamp(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
