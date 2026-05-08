from pathlib import Path

import pytest

from seed.media import build_extract_audio_command, ensure_upload_size


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
