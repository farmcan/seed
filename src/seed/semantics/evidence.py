from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from seed.markdown import read_markdown_metadata
from seed.transcripts import read_transcript_text


DEFAULT_MAX_TRANSCRIPT_ANCHORS = 12
DEFAULT_MAX_FRAME_ANCHORS = 12


def build_video_evidence_anchors(
    *,
    transcript_path: Path,
    visual_notes_path: Path | None = None,
    max_transcript_anchors: int = DEFAULT_MAX_TRANSCRIPT_ANCHORS,
    max_frame_anchors: int = DEFAULT_MAX_FRAME_ANCHORS,
) -> str:
    anchors = ["# Evidence Anchors", ""]
    transcript_anchors = transcript_chunk_anchors(transcript_path, limit=max_transcript_anchors)
    anchors.extend(["## Transcript Anchors", ""])
    anchors.extend(transcript_anchors or [f"- T1: Full transcript at `{transcript_path}`."])
    anchors.extend(["", "## Visual Anchors", ""])
    if visual_notes_path:
        anchors.append(f"- V1: Visual notes at `{visual_notes_path}`.")
        anchors.extend(frame_anchors_from_visual_notes(visual_notes_path, limit=max_frame_anchors))
    else:
        anchors.append("- V1: Visual notes unavailable.")
    anchors.extend(
        [
            "",
            "Use these IDs in the final artifact when making strong claims, for example `[T1]`, `[V1]`, or `[F3]`.",
        ]
    )
    return "\n".join(anchors)


def transcript_chunk_anchors(transcript_path: Path, *, limit: int) -> list[str]:
    text = read_transcript_text(transcript_path)
    matches = list(
        re.finditer(
            r"^## Chunk (?P<chunk>\d+)(?: \((?P<timestamp>\d{2}:\d{2}:\d{2})\))?",
            text,
            flags=re.M,
        )
    )
    if not matches:
        return []
    anchors = []
    for index, match in enumerate(matches[:limit], start=1):
        timestamp = match.group("timestamp") or "time unknown"
        anchors.append(
            f"- T{index}: Transcript chunk {match.group('chunk')} at {timestamp}, path `{transcript_path}`."
        )
    if len(matches) > limit:
        anchors.append(f"- T+: {len(matches) - limit} additional transcript chunks omitted.")
    return anchors


def frame_anchors_from_visual_notes(visual_notes_path: Path, *, limit: int) -> list[str]:
    metadata = read_markdown_metadata(visual_notes_path)
    frames = _metadata_list(metadata.get("frames"))
    anchors = [
        f"- F{index}: Keyframe `{frame_path}`."
        for index, frame_path in enumerate(frames[:limit], start=1)
    ]
    if len(frames) > limit:
        anchors.append(f"- F+: {len(frames) - limit} additional keyframes omitted.")
    return anchors


def _metadata_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]
