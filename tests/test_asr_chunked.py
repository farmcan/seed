from pathlib import Path

from seed.asr.chunked import transcribe_audio_with_optional_chunks
from seed.media import AudioChunk


def test_transcribe_audio_with_optional_chunks_uses_single_call_for_small_audio(
    tmp_path,
    monkeypatch,
):
    audio = tmp_path / "small.mp3"
    audio.write_bytes(b"small")
    calls: list[Path] = []

    def fake_transcribe_audio(audio_path, **kwargs):
        calls.append(audio_path)
        return "single transcript"

    monkeypatch.setattr("seed.asr.chunked.transcribe_audio", fake_transcribe_audio)

    text, chunks = transcribe_audio_with_optional_chunks(
        audio,
        provider="dashscope",
        model="qwen3-asr-flash",
        language="zh",
        prompt=None,
        max_upload_mb=1,
    )

    assert text == "single transcript"
    assert chunks == []
    assert calls == [audio]


def test_transcribe_audio_with_optional_chunks_splits_large_audio(tmp_path, monkeypatch):
    audio = tmp_path / "large.mp3"
    audio.write_bytes(b"0" * 11)
    chunk_paths = [tmp_path / "chunk-000.mp3", tmp_path / "chunk-001.mp3"]
    for path in chunk_paths:
        path.write_bytes(b"1")

    monkeypatch.setattr(
        "seed.asr.chunked.audio_exceeds_upload_size",
        lambda audio_path, max_upload_mb: True,
    )
    monkeypatch.setattr(
        "seed.asr.chunked.split_audio",
        lambda audio_path, chunk_seconds: [
            AudioChunk(path=chunk_paths[0], index=0, start_seconds=0),
            AudioChunk(path=chunk_paths[1], index=1, start_seconds=600),
        ],
    )
    monkeypatch.setattr(
        "seed.asr.chunked.estimate_chunk_seconds",
        lambda max_upload_mb: 600,
    )

    def fake_transcribe_audio(audio_path, **kwargs):
        return f"text for {audio_path.name}"

    monkeypatch.setattr("seed.asr.chunked.transcribe_audio", fake_transcribe_audio)

    text, chunks = transcribe_audio_with_optional_chunks(
        audio,
        provider="dashscope",
        model="qwen3-asr-flash",
        language="zh",
        prompt="terms",
        max_upload_mb=1,
    )

    assert "## Chunk 1 (00:00:00)" in text
    assert "text for chunk-000.mp3" in text
    assert "## Chunk 2 (00:10:00)" in text
    assert chunks == [
        {
            "index": 0,
            "start_seconds": 0,
            "audio_path": str(chunk_paths[0]),
            "text_length": len("text for chunk-000.mp3"),
        },
        {
            "index": 1,
            "start_seconds": 600,
            "audio_path": str(chunk_paths[1]),
            "text_length": len("text for chunk-001.mp3"),
        },
    ]
