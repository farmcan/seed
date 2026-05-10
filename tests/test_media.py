from pathlib import Path

import pytest

from seed.media import (
    audio_exceeds_upload_size,
    build_extract_audio_command,
    build_split_audio_command,
    ensure_upload_size,
    estimate_chunk_seconds,
)


def test_build_extract_audio_command():
    command = build_extract_audio_command(
        Path("input.mp4"),
        Path("output.mp3"),
        bitrate="48k",
        sample_rate=16000,
    )

    assert command[:5] == ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    assert "-vn" in command
    assert "libmp3lame" in command
    assert command[-1] == "output.mp3"


def test_ensure_upload_size_raises_when_too_large(tmp_path):
    path = tmp_path / "audio.m4a"
    path.write_bytes(b"0" * 11)

    with pytest.raises(ValueError, match="above the 0 MB upload limit"):
        ensure_upload_size(path, max_upload_mb=0)


def test_audio_exceeds_upload_size(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"0" * 11)

    assert audio_exceeds_upload_size(path, max_upload_mb=0)


def test_estimate_chunk_seconds_uses_upload_limit_and_bitrate():
    assert estimate_chunk_seconds(max_upload_mb=9, bitrate="64k") == 884


def test_build_split_audio_command(tmp_path):
    command = build_split_audio_command(
        Path("audio.mp3"),
        tmp_path / "chunks",
        chunk_seconds=600,
        bitrate="48k",
    )

    assert command[:5] == ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    assert "-f" in command
    assert "segment" in command
    assert "-segment_time" in command
    assert command[-1] == str(tmp_path / "chunks" / "chunk-%03d.mp3")
