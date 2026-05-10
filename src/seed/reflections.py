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


def revision_suggestions_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "reflections" / f"{slugify(owner)}.revision-suggestions.md"


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


def build_revision_suggestions(*, owner: str, records: list[ReflectionRecord]) -> str:
    lines = [
        f"# {owner} Revision Suggestions",
        "",
        f"- Owner: {owner}",
        f"- Reflections analyzed: {len(records)}",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        "- Status: draft, review before applying to creator profile, skills, or checks.",
        "",
        "## Worked",
        "",
    ]
    lines.extend(_checklist_items(_flatten(record.worked for record in records)))
    lines.extend(["", "## Failed", ""])
    lines.extend(_checklist_items(_flatten(record.failed for record in records)))
    lines.extend(["", "## Revise", ""])
    lines.extend(_checklist_items(_flatten(record.revise for record in records)))
    lines.extend(["", "## Source Reflections", ""])
    for record in records:
        lines.extend(
            [
                f"- Task: {record.task}",
                f"  Outcome: {record.outcome}",
                f"  Created at: {record.created_at.isoformat()}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def write_revision_suggestions(*, library_root: Path, owner: str) -> Path:
    log_path = reflection_log_path(library_root=library_root, owner=owner)
    records = load_reflection_records(log_path)
    output_path = revision_suggestions_path(library_root=library_root, owner=owner)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_revision_suggestions(owner=owner, records=records), encoding="utf-8")
    return output_path


def _flatten(groups) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            normalized = item.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            items.append(item)
    return items


def _checklist_items(items: list[str]) -> list[str]:
    if not items:
        return ["- [ ] No observations yet."]
    return [f"- [ ] {item}" for item in items]
