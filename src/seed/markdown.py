from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def read_markdown_body(path: Path) -> str:
    return split_frontmatter(path.read_text(encoding="utf-8"))[1].strip()


def read_markdown_metadata(path: Path) -> dict[str, Any]:
    return split_frontmatter(path.read_text(encoding="utf-8"))[0]


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text

    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, parts[2]


def find_markdown_field(text: str, field: str) -> str | None:
    metadata, body = split_frontmatter(text)
    for key, value in metadata.items():
        if str(key).casefold() == field.casefold() and value is not None:
            return str(value).strip()

    prefix = field.casefold()
    for line in body.splitlines():
        normalized = line.strip()
        lowered = normalized.casefold()
        if lowered.startswith(f"- {prefix}:"):
            return normalized.split(":", 1)[1].strip()
        if lowered.startswith(f"{prefix}:"):
            return normalized.split(":", 1)[1].strip()
    return None
