from __future__ import annotations

import subprocess
from pathlib import Path

from seed.library import init_library, slugify


DEFAULT_AUDIO_BITRATE = "64k"
DEFAULT_SAMPLE_RATE = 16000


def audio_output_path(media_path: Path, library_root: Path) -> Path:
    init_library(library_root)
    return library_root / "raw" / f"{slugify(media_path.stem)}.asr.mp3"


def build_extract_audio_command(
    media_path: Path,
    audio_path: Path,
    *,
    bitrate: str = DEFAULT_AUDIO_BITRATE,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(media_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(audio_path),
    ]


def extract_audio(
    media_path: Path,
    library_root: Path,
    *,
    bitrate: str = DEFAULT_AUDIO_BITRATE,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Path:
    audio_path = audio_output_path(media_path, library_root)
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        build_extract_audio_command(
            media_path,
            audio_path,
            bitrate=bitrate,
            sample_rate=sample_rate,
        ),
        check=True,
    )
    return audio_path


def ensure_upload_size(path: Path, *, max_upload_mb: int) -> None:
    max_bytes = max_upload_mb * 1024 * 1024
    size = path.stat().st_size
    if size > max_bytes:
        actual_mb = size / 1024 / 1024
        raise ValueError(
            f"Audio file is {actual_mb:.1f} MB, above the {max_upload_mb} MB upload limit. "
            "Use a lower bitrate or add chunking before transcription."
        )
