from pathlib import Path

import yaml

from seed.pipeline import VideoPipelineOptions, run_manifest_output_path, run_video_pipeline


def test_run_manifest_output_path(tmp_path):
    assert run_manifest_output_path(library_root=tmp_path, title="Demo 视频") == (
        tmp_path / "runs" / "demo-视频.video-pipeline.yaml"
    )


def test_run_video_pipeline_for_local_media(tmp_path, monkeypatch):
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")

    def fake_extract_audio(media_path, library_root):
        path = library_root / "raw" / "demo.asr.mp3"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"audio")
        return path

    def fake_transcribe_audio_with_optional_chunks(audio_path, **kwargs):
        return "# Transcript\n\nhello", []

    def fake_extract_frames(media_path, library_root, *, every_seconds, max_frames):
        frame_dir = library_root / "frames" / "demo"
        frame_dir.mkdir(parents=True, exist_ok=True)
        (frame_dir / "frame_0001.jpg").write_bytes(b"jpg")
        (frame_dir / "frames.json").write_text(
            '{"every_seconds": 5, "frame_paths": ["library/frames/demo/frame_0001.jpg"]}',
            encoding="utf-8",
        )
        return frame_dir

    def fake_run_video_semantics_analysis(**kwargs):
        Path(kwargs["output_path"]).write_text(
            "\n".join(
                [
                    "---",
                    "title: Demo",
                    "owner: demo-owner",
                    "platform: manual",
                    "---",
                    "",
                    "## Verbal Language",
                    "",
                    "- Main claims:",
                    "  - Claim A.",
                    "",
                    "## Video Structure",
                    "",
                    "- Hook: Start.",
                    "",
                    "## Open Questions",
                    "",
                    "- Question A?",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr("seed.pipeline.extract_audio", fake_extract_audio)
    monkeypatch.setattr(
        "seed.pipeline.transcribe_audio_with_optional_chunks",
        fake_transcribe_audio_with_optional_chunks,
    )
    monkeypatch.setattr("seed.pipeline.extract_frames", fake_extract_frames)
    monkeypatch.setattr(
        "seed.pipeline.run_video_semantics_analysis",
        fake_run_video_semantics_analysis,
    )

    context, manifest_path = run_video_pipeline(
        VideoPipelineOptions(
            source=str(media),
            library_root=tmp_path / "library",
            title="Demo",
            owner="demo-owner",
            vision=False,
        )
    )

    assert context.transcript_path.exists()
    assert context.semantics_path.exists()
    assert context.timeline_path.exists()
    assert context.claims_path.exists()
    assert context.graph_path.exists()
    assert context.html_path.exists()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["title"] == "Demo"
    assert [step["step"] for step in data["steps"]] == [
        "source",
        "transcribe",
        "extract_frames",
        "analyze_video_semantics",
        "build_timeline",
        "extract_claims",
        "build_video_dag",
        "export_video_dag_html",
    ]
    assert all(step["status"] in {"completed", "skipped"} for step in data["steps"])
