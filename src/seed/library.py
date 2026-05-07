from __future__ import annotations

import re
from pathlib import Path

import yaml

from seed.models import Methodology, SourceRecord


LIBRARY_DIRS = [
    "raw",
    "transcripts",
    "notes",
    "distilled",
    "skills",
    "checks",
]


def init_library(root: Path) -> list[Path]:
    created: list[Path] = []
    for name in LIBRARY_DIRS:
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        keep = directory / ".gitkeep"
        keep.touch(exist_ok=True)
        created.append(directory)
    return created


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip()).strip("-")
    return slug.lower() or "untitled"


def save_source_record(root: Path, record: SourceRecord) -> Path:
    init_library(root)
    filename = slugify("-".join([record.platform.value, record.owner, record.title or "source"]))
    path = root / "notes" / f"{filename}.source.yaml"
    path.write_text(
        yaml.safe_dump(record.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def save_methodology(root: Path, methodology: Methodology) -> Path:
    init_library(root)
    path = root / "distilled" / f"{slugify(methodology.id)}.yaml"
    path.write_text(
        yaml.safe_dump(methodology.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path
