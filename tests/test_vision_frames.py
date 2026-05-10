import json
from pathlib import Path

from seed.vision.frames import (
    build_extract_frames_command,
    frame_output_dir,
    write_frame_manifest,
)


def test_frame_output_dir_uses_slug(tmp_path):
    assert frame_output_dir(Path("raw/视频 Demo.mp4"), tmp_path) == tmp_path / "frames" / "视频-demo"


def test_build_extract_frames_command():
    command = build_extract_frames_command(
        Path("input.mp4"),
        Path("frames"),
        every_seconds=5,
        max_frames=12,
    )

    assert command[:5] == ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    assert "fps=1/5" in command
    assert "12" in command
    assert command[-1] == "frames/frame_%04d.jpg"


def test_write_frame_manifest(tmp_path):
    manifest = write_frame_manifest(
        tmp_path / "frames.json",
        media_path=Path("input.mp4"),
        every_seconds=3,
        max_frames=2,
        frame_paths=[Path("frame_0001.jpg"), Path("frame_0002.jpg")],
    )

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["media_path"] == "input.mp4"
    assert data["every_seconds"] == 3
    assert data["frame_paths"] == ["frame_0001.jpg", "frame_0002.jpg"]
