from pathlib import Path

import pytest

from seed.asr.chunked import transcribe_audio_with_optional_chunks
from seed.media import AudioChunk


def test_transcribe_audio_chunks_when_duration_exceeds_limit(tmp_path, monkeypatch):
    audio = tmp_path / "demo.mp3"
    audio.write_bytes(b"audio")
    chunks = [
        AudioChunk(path=tmp_path / "chunk-000.mp3", index=0, start_seconds=0),
        AudioChunk(path=tmp_path / "chunk-001.mp3", index=1, start_seconds=300),
    ]
    for chunk in chunks:
        chunk.path.write_bytes(b"chunk")

    monkeypatch.setattr("seed.asr.chunked.media_duration_seconds", lambda path: 961.0)
    monkeypatch.setattr("seed.asr.chunked.split_audio", lambda path, *, chunk_seconds: chunks)
    monkeypatch.setattr(
        "seed.asr.chunked.transcribe_audio",
        lambda path, **kwargs: f"text from {Path(path).stem}",
    )

    text, metadata = transcribe_audio_with_optional_chunks(
        audio,
        provider="dashscope",
        model="qwen-audio-asr",
        language="zh",
        prompt=None,
        max_upload_mb=100,
        chunk_seconds=300,
    )

    assert "## Chunk 1 (00:00:00)" in text
    assert "## Chunk 2 (00:05:00)" in text
    assert metadata[1]["start_seconds"] == 300


def test_transcribe_audio_rejects_long_audio_when_chunking_disabled(tmp_path, monkeypatch):
    audio = tmp_path / "demo.mp3"
    audio.write_bytes(b"audio")
    monkeypatch.setattr("seed.asr.chunked.media_duration_seconds", lambda path: 961.0)

    with pytest.raises(ValueError, match="Enable chunking"):
        transcribe_audio_with_optional_chunks(
            audio,
            provider="dashscope",
            model="qwen-audio-asr",
            language="zh",
            prompt=None,
            max_upload_mb=100,
            chunk_audio=False,
            chunk_seconds=300,
        )
