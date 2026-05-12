from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


DEFAULT_SHORT_MAX_SECONDS = 60.0
DEFAULT_SCENE_THRESHOLD = 0.35


def short_profile_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "shorts" / f"{slugify(title)}.short-video-profile.json"


def shots_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "shots" / f"{slugify(title)}.shots.json"


def shot_frame_output_dir(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "frames" / f"{slugify(title)}.shots"


def build_short_video_profile(
    *,
    media_path: Path,
    title: str,
    platform: str | None = None,
    short_max_seconds: float = DEFAULT_SHORT_MAX_SECONDS,
) -> dict[str, Any]:
    probe = probe_video(media_path)
    duration = probe.get("duration_seconds")
    width = probe.get("width")
    height = probe.get("height")
    fps = probe.get("fps")
    aspect_ratio = round(width / height, 4) if width and height else None
    return {
        "kind": "short_video_profile",
        "version": 1,
        "title": title,
        "platform": platform or "unknown",
        "media_path": str(media_path),
        "generated_at": datetime.now(UTC).isoformat(),
        "short_max_seconds": short_max_seconds,
        "duration_seconds": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "is_vertical": bool(width and height and height > width),
        "has_audio": probe.get("has_audio"),
        "is_short_form": bool(duration is not None and duration <= short_max_seconds),
        "probe": probe,
    }


def write_short_video_profile(path: Path, profile: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_shots_artifact(
    *,
    media_path: Path,
    title: str,
    profile: dict[str, Any],
    library_root: Path,
    threshold: float = DEFAULT_SCENE_THRESHOLD,
    provider: str = "ffmpeg-scene",
) -> dict[str, Any]:
    duration = as_float(profile.get("duration_seconds"))
    cut_points = detect_scene_cut_points(media_path, threshold=threshold)
    boundaries = normalize_boundaries(cut_points, duration=duration)
    frame_dir = shot_frame_output_dir(library_root=library_root, title=title)
    frame_dir.mkdir(parents=True, exist_ok=True)
    shots = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:], strict=False), start=1):
        representative_seconds = representative_time(start, end, duration=duration)
        representative_frame = extract_representative_frame(
            media_path=media_path,
            output_dir=frame_dir,
            index=index,
            timestamp_seconds=representative_seconds,
        )
        shots.append(
            {
                "id": f"shot-{index:03d}",
                "index": index,
                "start_seconds": round(start, 3),
                "end_seconds": round(end, 3) if end is not None else None,
                "duration_seconds": round(end - start, 3) if end is not None else None,
                "representative_seconds": round(representative_seconds, 3),
                "representative_frame_path": str(representative_frame),
                "transition_type": "cut" if index > 1 else "start",
                "confidence": "medium" if len(boundaries) > 2 else "low",
            }
        )
    return {
        "kind": "short_video_shots",
        "version": 1,
        "title": title,
        "media_path": str(media_path),
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": provider,
        "threshold": threshold,
        "duration_seconds": duration,
        "frame_dir": str(frame_dir),
        "shots": shots,
    }


def write_shots_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def probe_video(media_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(media_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip() or "ffprobe failed"}
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams") or []
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = as_float(video_stream.get("duration")) or as_float((data.get("format") or {}).get("duration"))
    return {
        "duration_seconds": duration,
        "fps": parse_frame_rate(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")),
        "width": as_int(video_stream.get("width")),
        "height": as_int(video_stream.get("height")),
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "has_audio": audio_stream is not None,
        "format_name": (data.get("format") or {}).get("format_name"),
        "size_bytes": as_int((data.get("format") or {}).get("size")),
    }


def detect_scene_cut_points(media_path: Path, *, threshold: float) -> list[float]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(media_path),
            "-filter:v",
            f"select='gt(scene,{threshold})',showinfo",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return sorted({round(float(match), 3) for match in re.findall(r"pts_time:([0-9.]+)", result.stderr)})


def normalize_boundaries(cut_points: list[float], *, duration: float | None) -> list[float]:
    boundaries = [0.0]
    for point in cut_points:
        if point > 0.05 and (duration is None or point < duration - 0.05):
            boundaries.append(point)
    if duration and duration > boundaries[-1]:
        boundaries.append(duration)
    elif len(boundaries) == 1:
        boundaries.append(boundaries[0])
    return boundaries


def representative_time(start: float, end: float | None, *, duration: float | None) -> float:
    if end is not None and end > start:
        return start + ((end - start) / 2)
    if duration and duration > start:
        return start + min((duration - start) / 2, 0.5)
    return start


def extract_representative_frame(
    *,
    media_path: Path,
    output_dir: Path,
    index: int,
    timestamp_seconds: float,
) -> Path:
    output_path = output_dir / f"shot_{index:04d}.jpg"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp_seconds:.3f}",
            "-i",
            str(media_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ],
        check=True,
    )
    return output_path


def parse_frame_rate(value: Any) -> float | None:
    if not value:
        return None
    text = str(value)
    if "/" not in text:
        return as_float(text)
    numerator, denominator = text.split("/", 1)
    denominator_value = as_float(denominator)
    if not denominator_value:
        return None
    numerator_value = as_float(numerator)
    return round(numerator_value / denominator_value, 3) if numerator_value is not None else None


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
