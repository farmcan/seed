from __future__ import annotations

import json
import subprocess
from pathlib import Path

from seed.library import init_library, slugify


def frame_output_dir(media_path: Path, library_root: Path) -> Path:
    init_library(library_root)
    return library_root / "frames" / slugify(media_path.stem)


def build_extract_frames_command(
    media_path: Path,
    output_dir: Path,
    *,
    every_seconds: int,
    max_frames: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(media_path),
        "-vf",
        f"fps=1/{every_seconds}",
        "-frames:v",
        str(max_frames),
        "-q:v",
        "2",
        str(output_dir / "frame_%04d.jpg"),
    ]


def extract_frames(
    media_path: Path,
    library_root: Path,
    *,
    every_seconds: int = 5,
    max_frames: int = 12,
) -> Path:
    output_dir = frame_output_dir(media_path, library_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        build_extract_frames_command(
            media_path,
            output_dir,
            every_seconds=every_seconds,
            max_frames=max_frames,
        ),
        check=True,
    )
    frame_paths = sorted(output_dir.glob("frame_*.jpg"))
    write_frame_manifest(
        output_dir / "frames.json",
        media_path=media_path,
        every_seconds=every_seconds,
        max_frames=max_frames,
        frame_paths=frame_paths,
    )
    return output_dir


def write_frame_manifest(
    manifest_path: Path,
    *,
    media_path: Path,
    every_seconds: int,
    max_frames: int,
    frame_paths: list[Path],
) -> Path:
    manifest = {
        "media_path": str(media_path),
        "every_seconds": every_seconds,
        "max_frames": max_frames,
        "frame_paths": [str(path) for path in frame_paths],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def load_frame_paths(frame_dir: Path) -> list[Path]:
    return sorted(frame_dir.glob("frame_*.jpg"))
