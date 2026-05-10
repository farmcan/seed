from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml

from seed.library import init_library, slugify
from seed.markdown import read_markdown_body


def book_note_output_path(*, library_root: Path, author: str, title: str) -> Path:
    init_library(library_root)
    return library_root / "notes" / f"{slugify(author)}-{slugify(title)}.book-note.md"


def book_semantics_output_path(*, library_root: Path, author: str, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(author)}-{slugify(title)}.book-semantics.md"


def topic_profile_output_path(*, library_root: Path, topic: str) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(topic)}.topic-profile.md"


def write_book_note(
    output_path: Path,
    *,
    source_path: Path,
    author: str,
    title: str,
    location: str | None = None,
) -> Path:
    text = source_path.read_text(encoding="utf-8")
    metadata = {
        "source_type": "book-note",
        "author": author,
        "title": title,
        "location": location,
        "source_path": str(source_path),
        "created_at": datetime.now(UTC).isoformat(),
    }
    content = [
        "---",
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        text.strip(),
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(content), encoding="utf-8")
    return output_path


def write_book_semantics(
    output_path: Path,
    *,
    note_path: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    body = read_markdown_body(note_path)
    key_points = extract_key_points(body)
    metadata = {
        "source_type": "book-semantics",
        "author": author,
        "title": title,
        "topic": topic,
        "note_path": str(note_path),
        "created_at": datetime.now(UTC).isoformat(),
    }
    content = [
        "---",
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        "# Book Semantics",
        "",
        "## Key Points",
        "",
        *(f"- {point}" for point in key_points),
        "",
        "## Methods And Principles",
        "",
        "- 待从多条笔记或人工 review 中提炼稳定方法论。",
        "",
        "## Agent Checks",
        "",
        "- 这个观点适用的上下文是什么？",
        "- 是否有反例、边界条件或作者没有展开的前提？",
        "- 能否转成可执行步骤或判断规则？",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(content), encoding="utf-8")
    return output_path


def write_topic_profile(
    output_path: Path,
    *,
    topic: str,
    semantics_paths: list[Path],
) -> Path:
    sections = [
        "---",
        yaml.safe_dump(
            {
                "source_type": "topic-profile",
                "topic": topic,
                "semantics_paths": [str(path) for path in semantics_paths],
                "created_at": datetime.now(UTC).isoformat(),
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip(),
        "---",
        "",
        f"# Topic Profile: {topic}",
        "",
    ]
    for path in semantics_paths:
        sections.extend(
            [
                f"## {path.stem}",
                "",
                read_markdown_body(path)[:1200],
                "",
            ]
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")
    return output_path


def extract_key_points(text: str, *, limit: int = 8) -> list[str]:
    points = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            points.append(stripped[2:].strip())
        elif stripped.startswith("#"):
            continue
        else:
            points.append(stripped)
        if len(points) >= limit:
            break
    return points or ["待补充可提炼观点。"]
