from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


EVIDENCE_PATTERN = re.compile(
    r"(\[(?:T|V|F)\d+\]|\.video-semantics\.md|timestamp|keyframe|transcript chunk|source video)",
    flags=re.I,
)
PROVISIONAL_PATTERN = re.compile(r"\b(provisional|needs confirmation|insufficient evidence)\b", flags=re.I)
CHECKED_SECTIONS = {
    "Creator Summary",
    "Recurring Methods",
    "Verbal Language Patterns",
    "Visual Language Patterns",
    "Video Structure Patterns",
    "Agent Skills",
}


def creator_profile_validation_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(owner)}.creator-profile.validation.json"


def validate_creator_profile(profile_path: Path, *, owner: str | None = None) -> dict[str, Any]:
    text = profile_path.read_text(encoding="utf-8")
    findings = []
    current_section = ""
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            continue
        if current_section not in CHECKED_SECTIONS or not requires_evidence(line):
            continue
        if has_evidence(line) or is_marked_provisional(line):
            continue
        findings.append(
            {
                "line": line_number,
                "section": current_section,
                "severity": "warning",
                "message": "Strong creator-level statement lacks evidence reference or provisional marker.",
                "text": line,
            }
        )
    return {
        "version": 1,
        "owner": owner or profile_path.stem.removesuffix(".creator-profile"),
        "profile_path": str(profile_path),
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "passed" if not findings else "warnings",
        "checked_sections": sorted(CHECKED_SECTIONS),
        "findings": findings,
    }


def write_creator_profile_validation(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def requires_evidence(line: str) -> bool:
    if not line or line.startswith("|") or line.startswith("```"):
        return False
    if line.startswith("- ") or line[:2].isdigit():
        return True
    if len(line) >= 80 and not line.endswith(":"):
        return True
    return False


def has_evidence(line: str) -> bool:
    return bool(EVIDENCE_PATTERN.search(line))


def is_marked_provisional(line: str) -> bool:
    return bool(PROVISIONAL_PATTERN.search(line))
