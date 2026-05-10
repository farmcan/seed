from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.markdown import find_markdown_field, read_markdown_body


DEFAULT_CLAIM_STATUS = "unverified"


def claims_output_path(
    *,
    library_root: Path,
    title: str | None = None,
    semantics_path: Path | None = None,
) -> Path:
    init_library(library_root)
    name = slugify(title or (semantics_path.stem.removesuffix(".video-semantics") if semantics_path else "claims"))
    return library_root / "claims" / f"{name}.claims.json"


def build_claims_artifact(
    *,
    semantics_path: Path,
    title: str | None = None,
) -> dict[str, Any]:
    raw_text = semantics_path.read_text(encoding="utf-8")
    body = read_markdown_body(semantics_path)
    resolved_title = title or find_markdown_field(raw_text, "title") or semantics_path.stem
    claims = []
    for text in _main_claims(body):
        claims.append(_claim(text, semantics_path=semantics_path, source_section="Verbal Language"))
    for text in _open_questions(body):
        claims.append(_claim(text, semantics_path=semantics_path, source_section="Open Questions"))

    return {
        "title": resolved_title,
        "created_at": datetime.now(UTC).isoformat(),
        "semantics_path": str(semantics_path),
        "claims": [
            {**claim, "id": f"claim-{index + 1:03d}"}
            for index, claim in enumerate(_dedupe_claims(claims))
        ],
    }


def write_claims_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _claim(text: str, *, semantics_path: Path, source_section: str) -> dict[str, Any]:
    return {
        "text": text,
        "status": DEFAULT_CLAIM_STATUS,
        "source_section": source_section,
        "evidence_path": str(semantics_path),
    }


def _main_claims(text: str) -> list[str]:
    section = _section_text(text, "Verbal Language")
    claims: list[str] = []
    capture = False
    for line in section.splitlines():
        if line.startswith("- Main claims:"):
            capture = True
            continue
        if capture and re.match(r"^- [A-Z]", line):
            break
        if capture:
            stripped = line.strip()
            if stripped.startswith("- "):
                claims.append(stripped[2:])
    return claims


def _open_questions(text: str) -> list[str]:
    section = _section_text(text, "Open Questions")
    questions = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            questions.append(stripped[2:])
    return questions


def _section_text(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.M | re.S,
    )
    return match.group("body").strip() if match else ""


def _dedupe_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped = []
    for claim in claims:
        key = claim["text"].casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped
