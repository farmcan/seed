import json
from pathlib import Path

import yaml

from seed.pipeline import VideoPipelineOptions, run_manifest_output_path, run_status_output_path, run_video_pipeline


def test_run_manifest_output_path(tmp_path):
    assert run_manifest_output_path(library_root=tmp_path, title="Demo 视频") == (
        tmp_path / "runs" / "demo-视频.video-pipeline.yaml"
    )
    assert run_status_output_path(library_root=tmp_path, title="Demo 视频") == (
        tmp_path / "runs" / "demo-视频.video-pipeline.status.json"
    )


def test_run_video_pipeline_for_local_media(tmp_path, monkeypatch):
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")
    library_root = tmp_path / "library"
    history_path = library_root / "runs" / "history.video-pipeline.yaml"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        yaml.safe_dump(
            {
                "steps": [
                    {"step": "source", "status": "completed", "duration_seconds": 2.0},
                    {"step": "transcribe", "status": "completed", "duration_seconds": 8.0},
                    {"step": "extract_frames", "status": "completed", "duration_seconds": 4.0},
                ]
            }
        ),
        encoding="utf-8",
    )

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
    progress_events = []

    context, manifest_path = run_video_pipeline(
        VideoPipelineOptions(
            source=str(media),
            library_root=library_root,
            title="Demo",
            owner="demo-owner",
            vision=False,
            progress_callback=progress_events.append,
        )
    )

    assert context.transcript_path.exists()
    assert context.semantics_path.exists()
    assert context.cost_ledger_path.exists()
    assert context.timeline_path.exists()
    assert context.claims_path.exists()
    assert context.graph_path.exists()
    assert context.html_path.exists()
    assert context.live_html_path.exists()
    status_path = manifest_path.with_suffix(".status.json")
    assert status_path.exists()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert data["title"] == "Demo"
    assert data["run_started_at"]
    assert data["run_finished_at"]
    assert data["duration_seconds"] is not None
    assert data["step_counts"]["completed"] >= 1
    assert [step["step"] for step in data["steps"]] == [
        "source",
        "short_profile",
        "transcribe",
        "extract_frames",
        "detect_shots",
        "build_frame_notes",
        "build_motion_relations",
        "analyze_video_semantics",
        "build_cost_ledger",
        "build_timeline",
        "extract_claims",
        "build_video_dag",
        "export_video_dag_html",
    ]
    assert all(step["status"] in {"completed", "skipped"} for step in data["steps"])
    assert all(step["duration_seconds"] is not None for step in data["steps"])
    assert any(str(context.transcript_path) in step["artifact_paths"] for step in data["steps"])
    assert status["kind"] == "video_pipeline_status"
    assert status["status"] == "completed"
    assert status["summary"].startswith("status=completed")
    assert status["estimated_total_seconds"] == 14.0
    assert status["step_counts"]["pending"] == 0
    assert status["current_step"] is None
    assert [step["step"] for step in status["steps"]] == [step["step"] for step in data["steps"]]
    assert status["steps"][0]["estimated_duration_seconds"] == 2.0
    assert status["steps"][0]["historical_sample_count"] == 1
    assert status["steps"][0]["message"]
    assert any(event["event"] == "run_started" for event in progress_events)
    run_started_event = next(event for event in progress_events if event["event"] == "run_started")
    assert run_started_event["estimated_total_seconds"] == 14.0
    assert run_started_event["step_estimates"]["transcribe"]["estimated_duration_seconds"] == 8.0
    assert any(event["event"] == "step_started" for event in progress_events)
    assert any(event["event"] == "run_finished" for event in progress_events)
    assert "window.SEED_EMBEDDED_STATUS" in context.live_html_path.read_text(encoding="utf-8")
