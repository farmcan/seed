from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from seed.library import init_library, slugify


class ReflectionRecord(BaseModel):
    owner: str
    task: str
    asset_path: Path | None = None
    outcome: str
    worked: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    revise: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def reflection_log_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "reflections" / f"{slugify(owner)}.reflection.jsonl"


def append_reflection_record(*, library_root: Path, record: ReflectionRecord) -> Path:
    path = reflection_log_path(library_root=library_root, owner=record.owner)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False))
        output.write("\n")
    return path


def load_reflection_records(path: Path) -> list[ReflectionRecord]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(ReflectionRecord.model_validate_json(line))
    return records
