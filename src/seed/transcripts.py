from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml

from seed.library import init_library, slugify


def transcript_output_path(
    *,
    library_root: Path,
    media_path: Path,
    title: str | None = None,
) -> Path:
    init_library(library_root)
    name = slugify(title or media_path.stem)
    return library_root / "transcripts" / f"{name}.transcript.md"


def write_transcript_markdown(
    path: Path,
    *,
    text: str,
    media_path: Path,
    audio_path: Path,
    provider: str,
    model: str,
    title: str | None = None,
    language: str | None = None,
) -> Path:
    metadata = {
        "title": title or media_path.stem,
        "source_media": str(media_path),
        "audio_path": str(audio_path),
        "asr_provider": provider,
        "asr_model": model,
        "language": language,
        "created_at": datetime.now(UTC).isoformat(),
    }
    body = [
        "---",
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        "# Transcript",
        "",
        text.strip(),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def read_transcript_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()
