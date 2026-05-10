from __future__ import annotations

import re
from pathlib import Path

import yaml

from seed.models import CreatorVideoList, Methodology, SourceRecord


LIBRARY_DIRS = [
    "raw",
    "transcripts",
    "notes",
    "semantics",
    "graphs",
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


def load_source_records(root: Path) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    notes_dir = root / "notes"
    if not notes_dir.exists():
        return records
    for path in sorted(notes_dir.glob("*.source.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        records.append(SourceRecord.model_validate(data))
    return records


def load_creator_video_list(path: Path) -> CreatorVideoList:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return CreatorVideoList.model_validate(data)


def save_creator_video_list(root: Path, video_list: CreatorVideoList) -> Path:
    init_library(root)
    filename = slugify(
        "-".join([video_list.platform.value, video_list.owner, "creator-videos"])
    )
    path = root / "notes" / f"{filename}.creator-videos.yaml"
    path.write_text(
        yaml.safe_dump(video_list.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
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
