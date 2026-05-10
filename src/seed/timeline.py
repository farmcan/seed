from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.markdown import read_markdown_body
from seed.transcripts import read_transcript_text


KIND_PRIORITY = {
    "transcript_chunk": 0,
    "transcript_timestamp": 1,
    "keyframe": 2,
    "hook": 3,
    "promise": 4,
    "setup": 5,
    "proof": 6,
    "payoff": 7,
    "cta": 8,
    "ad_candidate": 9,
    "visual_notes": 10,
}


def timeline_output_path(
    *,
    library_root: Path,
    title: str | None = None,
    transcript_path: Path | None = None,
) -> Path:
    init_library(library_root)
    name = slugify(title or (transcript_path.stem.removesuffix(".transcript") if transcript_path else "timeline"))
    return library_root / "timelines" / f"{name}.timeline.json"


def build_timeline_artifact(
    *,
    title: str,
    transcript_path: Path | None = None,
    frame_dir: Path | None = None,
    visual_notes_path: Path | None = None,
    semantics_path: Path | None = None,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    uncertainties: list[str] = []

    if transcript_path:
        transcript = read_transcript_text(transcript_path)
        events.extend(_transcript_events(transcript, transcript_path))

    if frame_dir:
        events.extend(_frame_events(frame_dir))

    if semantics_path:
        semantics = read_markdown_body(semantics_path)
        events.extend(_structure_events(semantics, semantics_path))
        events.extend(_ad_events(semantics, semantics_path))
        uncertainties.extend(_uncertainties(semantics))

    if visual_notes_path:
        events.append(
            {
                "kind": "visual_notes",
                "label": "Visual notes available",
                "start_seconds": None,
                "order": len(events),
                "evidence_path": str(visual_notes_path),
                "confidence": "high",
            }
        )

    return {
        "title": title,
        "created_at": datetime.now(UTC).isoformat(),
        "inputs": {
            "transcript_path": str(transcript_path) if transcript_path else None,
            "frame_dir": str(frame_dir) if frame_dir else None,
            "visual_notes_path": str(visual_notes_path) if visual_notes_path else None,
            "semantics_path": str(semantics_path) if semantics_path else None,
        },
        "events": _sort_events(events),
        "uncertainties": uncertainties,
    }


def write_timeline_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _transcript_events(transcript: str, transcript_path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, match in enumerate(
        re.finditer(r"^## Chunk (?P<chunk>\d+) \((?P<timestamp>\d{2}:\d{2}:\d{2})\)", transcript, re.M)
    ):
        chunk = int(match.group("chunk"))
        events.append(
            {
                "kind": "transcript_chunk",
                "label": f"Transcript chunk {chunk}",
                "start_seconds": _timestamp_to_seconds(match.group("timestamp")),
                "order": index,
                "evidence_path": str(transcript_path),
                "confidence": "high",
            }
        )

    if events:
        return events

    timestamps = []
    for match in re.finditer(r"\b(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\b", transcript):
        seconds = _timestamp_to_seconds(match.group("timestamp"))
        if seconds not in timestamps:
            timestamps.append(seconds)
    return [
        {
            "kind": "transcript_timestamp",
            "label": f"Transcript timestamp {_format_timestamp(seconds)}",
            "start_seconds": seconds,
            "order": index,
            "evidence_path": str(transcript_path),
            "confidence": "medium",
        }
        for index, seconds in enumerate(timestamps)
    ]


def _frame_events(frame_dir: Path) -> list[dict[str, Any]]:
    manifest_path = frame_dir / "frames.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    every_seconds = int(manifest.get("every_seconds") or 0)
    frame_paths = manifest.get("frame_paths") or []
    return [
        {
            "kind": "keyframe",
            "label": f"Keyframe {index + 1}",
            "start_seconds": index * every_seconds if every_seconds else None,
            "order": index,
            "evidence_path": str(frame_path),
            "confidence": "high" if every_seconds else "medium",
        }
        for index, frame_path in enumerate(frame_paths)
    ]


def _structure_events(semantics: str, semantics_path: Path) -> list[dict[str, Any]]:
    section = _section_text(semantics, "Video Structure")
    events: list[dict[str, Any]] = []
    stage_map = {
        "Hook": "hook",
        "Promise or value": "promise",
        "Setup/context": "setup",
        "Proof/reveal/demo": "proof",
        "Payoff": "payoff",
        "CTA": "cta",
    }
    for label, kind in stage_map.items():
        value = _bullet_value(section, label)
        if not value:
            continue
        events.append(
            {
                "kind": kind,
                "label": label,
                "description": value,
                "start_seconds": None,
                "order": len(events),
                "evidence_path": str(semantics_path),
                "confidence": "medium",
            }
        )
    return events


def _ad_events(semantics: str, semantics_path: Path) -> list[dict[str, Any]]:
    if "广告" not in semantics and "ad" not in semantics.lower():
        return []
    return [
        {
            "kind": "ad_candidate",
            "label": "Ad or sponsor candidate",
            "description": "Semantics mention an ad, sponsor, or product insertion; exact timestamp is not yet known.",
            "start_seconds": None,
            "order": 0,
            "evidence_path": str(semantics_path),
            "confidence": "low",
        }
    ]


def _uncertainties(semantics: str) -> list[str]:
    section = _section_text(semantics, "Open Questions")
    items = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])
    return items


def _section_text(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.M | re.S,
    )
    return match.group("body").strip() if match else ""


def _bullet_value(section: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*(?P<value>.+)$", section, flags=re.M)
    return match.group("value").strip() if match else None


def _sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        events,
        key=lambda event: (
            event["start_seconds"] is None,
            event["start_seconds"] if event["start_seconds"] is not None else event["order"],
            KIND_PRIORITY.get(event["kind"], 99),
            event["order"],
        ),
    )


def _timestamp_to_seconds(value: str) -> int:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def _format_timestamp(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
