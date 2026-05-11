from __future__ import annotations

from pathlib import Path


DEFAULT_VIDEO_ANALYSIS_LENSES_PATH = Path(
    "skills/video-semantics-analyzer/references/video-analysis-lenses.md"
)


def read_video_analysis_lenses(path: Path = DEFAULT_VIDEO_ANALYSIS_LENSES_PATH) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
