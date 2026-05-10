import json
from pathlib import Path

from seed.timeline import build_timeline_artifact, timeline_output_path, write_timeline_artifact


def test_timeline_output_path_uses_title(tmp_path):
    path = timeline_output_path(
        library_root=tmp_path,
        title="增长 方法论",
        transcript_path=Path("demo.transcript.md"),
    )

    assert path == tmp_path / "timelines" / "增长-方法论.timeline.json"


def test_build_timeline_artifact_from_transcript_frames_and_semantics(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    transcript.write_text(
        """---
title: Demo
---

# Transcript

## Chunk 1 (00:00:00)

hook text

## Chunk 2 (00:10:00)

body text
""",
        encoding="utf-8",
    )
    frame_dir = tmp_path / "frames"
    frame_dir.mkdir()
    (frame_dir / "frames.json").write_text(
        json.dumps(
            {
                "every_seconds": 5,
                "frame_paths": [
                    str(frame_dir / "frame_0001.jpg"),
                    str(frame_dir / "frame_0002.jpg"),
                ],
            }
        ),
        encoding="utf-8",
    )
    semantics = tmp_path / "demo.video-semantics.md"
    semantics.write_text(
        """## Video Structure

- Hook: Start with a conflict.
- Proof/reveal/demo: Show the evidence.
- CTA: Ask for follow.

## Open Questions

- Missing source A.
- Missing source B.
""",
        encoding="utf-8",
    )

    artifact = build_timeline_artifact(
        title="Demo",
        transcript_path=transcript,
        frame_dir=frame_dir,
        semantics_path=semantics,
    )

    assert artifact["title"] == "Demo"
    assert artifact["events"][0]["kind"] == "transcript_chunk"
    assert artifact["events"][0]["start_seconds"] == 0
    assert any(event["kind"] == "keyframe" for event in artifact["events"])
    assert any(event["kind"] == "hook" for event in artifact["events"])
    assert any(event["kind"] == "cta" for event in artifact["events"])
    assert artifact["uncertainties"] == ["Missing source A.", "Missing source B."]


def test_write_timeline_artifact(tmp_path):
    path = tmp_path / "demo.timeline.json"

    write_timeline_artifact(path, {"title": "Demo", "events": [], "uncertainties": []})

    assert json.loads(path.read_text(encoding="utf-8"))["title"] == "Demo"
