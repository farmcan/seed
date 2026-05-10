from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

from seed.library import init_library, slugify


DEFAULT_AUDIO_BITRATE = "64k"
DEFAULT_SAMPLE_RATE = 16000
MIN_CHUNK_SECONDS = 60


@dataclass(frozen=True)
class AudioChunk:
    path: Path
    index: int
    start_seconds: int
    duration_seconds: int | None = None


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


def audio_exceeds_upload_size(path: Path, *, max_upload_mb: int) -> bool:
    max_bytes = max_upload_mb * 1024 * 1024
    return path.stat().st_size > max_bytes


def ensure_upload_size(path: Path, *, max_upload_mb: int) -> None:
    max_bytes = max_upload_mb * 1024 * 1024
    size = path.stat().st_size
    if size > max_bytes:
        actual_mb = size / 1024 / 1024
        raise ValueError(
            f"Audio file is {actual_mb:.1f} MB, above the {max_upload_mb} MB upload limit. "
            "Use a lower bitrate or add chunking before transcription."
        )


def estimate_chunk_seconds(
    *,
    max_upload_mb: int,
    bitrate: str = DEFAULT_AUDIO_BITRATE,
    safety_ratio: float = 0.75,
) -> int:
    bits_per_second = _parse_bitrate_bits_per_second(bitrate)
    max_bits = max_upload_mb * 1024 * 1024 * 8
    seconds = math.floor((max_bits / bits_per_second) * safety_ratio)
    return max(seconds, MIN_CHUNK_SECONDS)


def audio_chunk_dir(audio_path: Path) -> Path:
    return audio_path.parent / f"{audio_path.stem}.chunks"


def build_split_audio_command(
    audio_path: Path,
    chunk_dir: Path,
    *,
    chunk_seconds: int,
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
        str(audio_path),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(chunk_dir / "chunk-%03d.mp3"),
    ]


def split_audio(
    audio_path: Path,
    *,
    chunk_seconds: int,
    bitrate: str = DEFAULT_AUDIO_BITRATE,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> list[AudioChunk]:
    chunk_dir = audio_chunk_dir(audio_path)
    chunk_dir.mkdir(parents=True, exist_ok=True)
    for existing_chunk in chunk_dir.glob("chunk-*.mp3"):
        existing_chunk.unlink()
    subprocess.run(
        build_split_audio_command(
            audio_path,
            chunk_dir,
            chunk_seconds=chunk_seconds,
            bitrate=bitrate,
            sample_rate=sample_rate,
        ),
        check=True,
    )
    return [
        AudioChunk(path=path, index=index, start_seconds=index * chunk_seconds)
        for index, path in enumerate(sorted(chunk_dir.glob("chunk-*.mp3")))
    ]


def _parse_bitrate_bits_per_second(bitrate: str) -> int:
    value = bitrate.strip().lower()
    if value.endswith("k"):
        return int(value[:-1]) * 1000
    if value.endswith("m"):
        return int(value[:-1]) * 1000 * 1000
    return int(value)
