from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml

from seed.library import init_library, slugify
from seed.markdown import read_markdown_body


def visual_notes_output_path(
    *,
    library_root: Path,
    source_path: Path,
    title: str | None = None,
) -> Path:
    init_library(library_root)
    return library_root / "notes" / f"{slugify(title or source_path.stem)}.visual.md"


def write_visual_notes_markdown(
    path: Path,
    *,
    analysis: str,
    frame_dir: Path,
    frame_paths: list[Path],
    provider: str,
    model: str,
    title: str | None = None,
) -> Path:
    metadata = {
        "title": title or frame_dir.name,
        "frame_dir": str(frame_dir),
        "frames": [str(path) for path in frame_paths],
        "vision_provider": provider,
        "vision_model": model,
        "created_at": datetime.now(UTC).isoformat(),
    }
    body = [
        "---",
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        "# Visual Notes",
        "",
        analysis.strip(),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def read_visual_notes_text(path: Path) -> str:
    return read_markdown_body(path)
