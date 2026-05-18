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
DEFAULT_FRAME_MODE = "shot-keyframes"
DEFAULT_OCR_PROVIDER = "none"
SUPPORTED_OCR_PROVIDERS = {"none", "sidecar-json"}
DEFAULT_FRAME_MOTION_PROVIDER = "none"
SUPPORTED_FRAME_MOTION_PROVIDERS = {"none", "ffmpeg-diff"}


def short_profile_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "shorts" / f"{slugify(title)}.short-video-profile.json"


def shots_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "shots" / f"{slugify(title)}.shots.json"


def shot_frame_output_dir(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "frames" / f"{slugify(title)}.shots"


def dense_frame_output_dir(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "frames" / f"{slugify(title)}.dense"


def frame_notes_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "frames" / f"{slugify(title)}.frame-notes.jsonl"


def motion_relations_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "shots" / f"{slugify(title)}.motion-relations.json"


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


def build_frame_notes(
    *,
    media_path: Path,
    title: str,
    profile: dict[str, Any],
    shots_artifact: dict[str, Any] | None,
    library_root: Path,
    frame_mode: str = DEFAULT_FRAME_MODE,
    fps: float = 1.0,
    ocr_provider: str = DEFAULT_OCR_PROVIDER,
    ocr_path: Path | None = None,
    ocr_match_tolerance_seconds: float = 0.5,
    frame_motion_provider: str = DEFAULT_FRAME_MOTION_PROVIDER,
) -> list[dict[str, Any]]:
    resolved_mode = normalize_frame_mode(frame_mode)
    if resolved_mode == "shot-keyframes":
        frames = frame_records_from_shots(shots_artifact or {})
    else:
        frames = extract_dense_frames(
            media_path=media_path,
            title=title,
            library_root=library_root,
            frame_mode=resolved_mode,
            fps=fps,
            profile=profile,
        )
    notes = [
        {
            "kind": "short_frame_note",
            "version": 1,
            "title": title,
            "frame_mode": resolved_mode,
            "index": index,
            "timestamp_seconds": frame["timestamp_seconds"],
            "frame_path": frame["frame_path"],
            "shot_id": frame.get("shot_id"),
            "shot_index": frame.get("shot_index"),
            "image": probe_image(Path(frame["frame_path"])),
            "visual_provider": "none",
            "vl_caption": None,
            "ocr_provider": DEFAULT_OCR_PROVIDER,
            "ocr_status": "not_configured",
            "ocr_text": None,
            "ocr_segments": [],
            "frame_motion_provider": DEFAULT_FRAME_MOTION_PROVIDER,
            "frame_motion_status": "not_configured",
            "frame_delta": None,
            "subjects": [],
            "objects": [],
            "scene": None,
            "composition": None,
            "motion_or_action": None,
            "human_motion_relation": None,
            "subtitle": {
                "present": None,
                "text": None,
                "style": None,
                "position": None,
            },
            "visual_effects": {
                "mask": None,
                "picture_in_picture": None,
                "sticker": None,
                "filter_or_lut": None,
                "speed_ramp": None,
                "text_overlay": None,
            },
            "editing": {
                "transition": None,
                "cut_type": None,
                "camera_motion": None,
                "pacing": None,
                "sound_sync": None,
            },
            "editing_intent": None,
            "status": "pending_vl",
        }
        for index, frame in enumerate(frames, start=1)
    ]
    return enrich_frame_notes_with_ocr(
        enrich_frame_notes_with_motion(notes, provider=frame_motion_provider),
        provider=ocr_provider,
        ocr_path=ocr_path,
        match_tolerance_seconds=ocr_match_tolerance_seconds,
    )


def write_frame_notes(path: Path, notes: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(note, ensure_ascii=False) for note in notes) + ("\n" if notes else ""),
        encoding="utf-8",
    )
    return path


def load_frame_notes(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def enrich_frame_notes_with_ocr(
    notes: list[dict[str, Any]],
    *,
    provider: str = DEFAULT_OCR_PROVIDER,
    ocr_path: Path | None = None,
    match_tolerance_seconds: float = 0.5,
) -> list[dict[str, Any]]:
    resolved_provider = normalize_ocr_provider(provider)
    if resolved_provider == "none":
        return notes

    if not ocr_path:
        return [mark_ocr_status(note, provider=resolved_provider, status="missing_ocr_path") for note in notes]
    if not ocr_path.exists():
        return [mark_ocr_status(note, provider=resolved_provider, status="missing_ocr_path") for note in notes]

    segments = load_ocr_segments(ocr_path)
    enriched = []
    for note in notes:
        matches = match_ocr_segments(
            timestamp_seconds=as_float(note.get("timestamp_seconds")),
            segments=segments,
            tolerance_seconds=match_tolerance_seconds,
        )
        enriched.append(apply_ocr_matches(note, provider=resolved_provider, matches=matches))
    return enriched


def normalize_ocr_provider(provider: str | None) -> str:
    resolved = (provider or DEFAULT_OCR_PROVIDER).strip().lower()
    if resolved not in SUPPORTED_OCR_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_OCR_PROVIDERS))
        raise ValueError(f"Unsupported OCR provider: {provider}. Allowed: {allowed}")
    return resolved


def mark_ocr_status(note: dict[str, Any], *, provider: str, status: str) -> dict[str, Any]:
    updated = dict(note)
    updated["ocr_provider"] = provider
    updated["ocr_status"] = status
    updated.setdefault("ocr_segments", [])
    return updated


def load_ocr_segments(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        raw_segments = data
    elif isinstance(data, dict):
        raw_segments = data.get("segments") or data.get("items") or data.get("results") or []
    else:
        raw_segments = []
    return [
        segment
        for item in raw_segments
        if isinstance(item, dict)
        if (segment := normalize_ocr_segment(item)) is not None
    ]


def normalize_ocr_segment(item: dict[str, Any]) -> dict[str, Any] | None:
    text = item.get("text") or item.get("ocr_text") or item.get("content")
    if text is None or not str(text).strip():
        return None
    start = first_float(item, "start_seconds", "start", "timestamp_seconds", "timestamp")
    end = first_float(item, "end_seconds", "end")
    if start is None and end is None:
        start = 0.0
    if end is not None and start is not None and end < start:
        end = start
    return {
        "text": str(text).strip(),
        "start_seconds": start,
        "end_seconds": end,
        "bbox": item.get("bbox") or item.get("box") or item.get("bounding_box"),
        "confidence": first_float(item, "confidence", "score"),
        "source_id": item.get("id") or item.get("source_id"),
    }


def first_float(item: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = as_float(item.get(key))
        if value is not None:
            return value
    return None


def match_ocr_segments(
    *,
    timestamp_seconds: float | None,
    segments: list[dict[str, Any]],
    tolerance_seconds: float,
) -> list[dict[str, Any]]:
    if timestamp_seconds is None:
        return []
    matches = []
    for segment in segments:
        start = as_float(segment.get("start_seconds"))
        end = as_float(segment.get("end_seconds"))
        if start is not None and end is not None:
            if start - tolerance_seconds <= timestamp_seconds <= end + tolerance_seconds:
                matches.append(segment)
            continue
        anchor = start if start is not None else end
        if anchor is not None and abs(timestamp_seconds - anchor) <= tolerance_seconds:
            matches.append(segment)
    return matches


def apply_ocr_matches(note: dict[str, Any], *, provider: str, matches: list[dict[str, Any]]) -> dict[str, Any]:
    updated = dict(note)
    updated["ocr_provider"] = provider
    updated["ocr_segments"] = matches
    if not matches:
        updated["ocr_status"] = "no_match"
        return updated

    text = " ".join(segment["text"] for segment in matches if segment.get("text"))
    updated["ocr_status"] = "matched"
    updated["ocr_text"] = text or None
    updated["subtitle"] = {
        **(updated.get("subtitle") or {}),
        "present": bool(text),
        "text": text or None,
        "position": first_non_empty([segment.get("bbox") for segment in matches]),
        "source": provider,
    }
    updated["visual_effects"] = {
        **(updated.get("visual_effects") or {}),
        "text_overlay": {
            "present": bool(text),
            "text": text or None,
            "source": provider,
            "segments": len(matches),
        },
    }
    updated["status"] = "pending_vl_ocr_enriched"
    return updated


def first_non_empty(values: list[Any]) -> Any:
    for value in values:
        if value:
            return value
    return None


def enrich_frame_notes_with_motion(
    notes: list[dict[str, Any]],
    *,
    provider: str = DEFAULT_FRAME_MOTION_PROVIDER,
) -> list[dict[str, Any]]:
    resolved_provider = normalize_frame_motion_provider(provider)
    if resolved_provider == "none":
        return notes
    if len(notes) < 2:
        return [
            mark_frame_motion_status(note, provider=resolved_provider, status="needs_multiple_frames")
            for note in notes
        ]

    enriched = [mark_frame_motion_status(notes[0], provider=resolved_provider, status="baseline_start")]
    for previous, current in zip(notes, notes[1:], strict=False):
        enriched.append(
            apply_frame_delta(
                current,
                previous=previous,
                provider=resolved_provider,
                delta=frame_difference_score(
                    Path(str(previous.get("frame_path"))),
                    Path(str(current.get("frame_path"))),
                ),
            )
        )
    return enriched


def normalize_frame_motion_provider(provider: str | None) -> str:
    resolved = (provider or DEFAULT_FRAME_MOTION_PROVIDER).strip().lower()
    if resolved not in SUPPORTED_FRAME_MOTION_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_FRAME_MOTION_PROVIDERS))
        raise ValueError(f"Unsupported frame motion provider: {provider}. Allowed: {allowed}")
    return resolved


def mark_frame_motion_status(note: dict[str, Any], *, provider: str, status: str) -> dict[str, Any]:
    updated = dict(note)
    updated["frame_motion_provider"] = provider
    updated["frame_motion_status"] = status
    return updated


def apply_frame_delta(
    note: dict[str, Any],
    *,
    previous: dict[str, Any],
    provider: str,
    delta: float | None,
) -> dict[str, Any]:
    updated = dict(note)
    updated["frame_motion_provider"] = provider
    if delta is None:
        updated["frame_motion_status"] = "unavailable"
        return updated

    intensity = classify_frame_delta(delta)
    previous_timestamp = as_float(previous.get("timestamp_seconds"))
    current_timestamp = as_float(note.get("timestamp_seconds"))
    updated["frame_motion_status"] = "measured"
    updated["frame_delta"] = {
        "provider": provider,
        "previous_frame_index": previous.get("index"),
        "previous_frame_path": previous.get("frame_path"),
        "previous_timestamp_seconds": previous_timestamp,
        "current_timestamp_seconds": current_timestamp,
        "score": delta,
        "intensity": intensity,
        "summary": (
            "Frame-difference baseline measures visual change between sampled frames; "
            "it does not identify people, objects, pose, or true optical flow."
        ),
    }
    updated["editing"] = {
        **(updated.get("editing") or {}),
        "camera_motion": {
            "provider": provider,
            "status": "candidate",
            "intensity": intensity,
            "score": delta,
            "needs_provider": ["optical_flow", "pose", "vl"],
        },
    }
    return updated


def classify_frame_delta(delta: float) -> str:
    if delta >= 0.35:
        return "high"
    if delta >= 0.12:
        return "medium"
    return "low"


def frame_difference_score(previous_path: Path, current_path: Path) -> float | None:
    if not previous_path.exists() or not current_path.exists():
        return None
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(previous_path),
            "-i",
            str(current_path),
            "-filter_complex",
            "[0:v][1:v]blend=all_mode=difference,signalstats,metadata=print:file=-",
            "-frames:v",
            "1",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"lavfi\.signalstats\.YAVG=([0-9.]+)", output)
    if not match:
        return None
    return round(min(max(float(match.group(1)) / 255.0, 0.0), 1.0), 4)


def build_motion_relations_artifact(
    *,
    title: str,
    profile: dict[str, Any],
    shots_artifact: dict[str, Any] | None,
    frame_notes: list[dict[str, Any]],
    provider: str = "schema-baseline",
) -> dict[str, Any]:
    relations = []
    sorted_notes = sorted(
        frame_notes,
        key=lambda note: as_float(note.get("timestamp_seconds")) or 0,
    )
    for previous, current in zip(sorted_notes, sorted_notes[1:], strict=False):
        relations.append(build_temporal_relation(previous=previous, current=current))
    if not relations and sorted_notes:
        relations.append(build_single_frame_relation(sorted_notes[0]))
    return {
        "kind": "short_motion_relations",
        "version": 1,
        "title": title,
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": provider,
        "profile_path": profile.get("media_path"),
        "shots_count": len((shots_artifact or {}).get("shots") or []),
        "frame_notes_count": len(frame_notes),
        "capabilities": {
            "person_bbox": False,
            "pose_keypoints": False,
            "object_tracking": False,
            "ocr": False,
            "frame_difference": any(note.get("frame_motion_status") == "measured" for note in frame_notes),
            "optical_flow": False,
        },
        "provider_notes": [
            "Baseline only creates traceable relation candidates from frame timing and schema fields.",
            "Install optional pose/OCR/motion providers to fill person-object and person-person relations.",
        ],
        "relations": relations,
    }


def write_motion_relations_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_temporal_relation(*, previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    previous_time = as_float(previous.get("timestamp_seconds"))
    current_time = as_float(current.get("timestamp_seconds"))
    return {
        "id": f"relation-{previous.get('index', 0)}-{current.get('index', 0)}",
        "kind": "temporal_frame_relation",
        "status": "needs_pose_or_vl",
        "label": "frame-to-frame motion candidate",
        "start_seconds": previous_time,
        "end_seconds": current_time,
        "source_frame_indices": [previous.get("index"), current.get("index")],
        "source_frame_paths": [previous.get("frame_path"), current.get("frame_path")],
        "shot_ids": [previous.get("shot_id"), current.get("shot_id")],
        "observed": {
            "subtitle": [previous.get("subtitle"), current.get("subtitle")],
            "visual_effects": [previous.get("visual_effects"), current.get("visual_effects")],
            "editing": [previous.get("editing"), current.get("editing")],
            "frame_delta": [previous.get("frame_delta"), current.get("frame_delta")],
        },
        "needs_provider": ["pose", "object_tracking", "optical_flow", "vl"],
        "summary": (
            "Frame sequence is available, but person/object motion cannot be asserted until a "
            "pose, tracking, optical-flow, or VL provider enriches the frame notes."
        ),
    }


def build_single_frame_relation(note: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"relation-{note.get('index', 1)}",
        "kind": "single_frame_relation_candidate",
        "status": "needs_pose_or_vl",
        "label": "single-frame motion candidate",
        "start_seconds": as_float(note.get("timestamp_seconds")),
        "source_frame_indices": [note.get("index")],
        "source_frame_paths": [note.get("frame_path")],
        "shot_ids": [note.get("shot_id")],
        "observed": {
            "subtitle": note.get("subtitle"),
            "visual_effects": note.get("visual_effects"),
            "editing": note.get("editing"),
            "frame_delta": note.get("frame_delta"),
        },
        "needs_provider": ["pose", "object_tracking", "vl"],
        "summary": "Only one frame is available, so motion relation requires pose/tracking/VL enrichment.",
    }


def normalize_frame_mode(frame_mode: str) -> str:
    allowed = {"shot-keyframes", "fps", "every-frame"}
    if frame_mode not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported frame mode: {frame_mode}. Allowed: {allowed_text}")
    return frame_mode


def frame_records_from_shots(shots_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for shot in shots_artifact.get("shots") or []:
        frame_path = shot.get("representative_frame_path")
        if not frame_path:
            continue
        records.append(
            {
                "timestamp_seconds": shot.get("representative_seconds"),
                "frame_path": frame_path,
                "shot_id": shot.get("id"),
                "shot_index": shot.get("index"),
            }
        )
    return records


def extract_dense_frames(
    *,
    media_path: Path,
    title: str,
    library_root: Path,
    frame_mode: str,
    fps: float,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    output_dir = dense_frame_output_dir(library_root=library_root, title=title)
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in output_dir.glob("dense_*.jpg"):
        existing.unlink()
    resolved_fps = profile.get("fps") if frame_mode == "every-frame" else fps
    if not resolved_fps or float(resolved_fps) <= 0:
        resolved_fps = fps
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(media_path),
            "-vf",
            f"fps={float(resolved_fps):.6f}",
            "-q:v",
            "2",
            str(output_dir / "dense_%05d.jpg"),
        ],
        check=True,
    )
    return [
        {
            "timestamp_seconds": round((index - 1) / float(resolved_fps), 3),
            "frame_path": str(path),
        }
        for index, path in enumerate(sorted(output_dir.glob("dense_*.jpg")), start=1)
    ]


def probe_image(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    data = json.loads(result.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    return {
        "width": as_int(stream.get("width")),
        "height": as_int(stream.get("height")),
    }


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
