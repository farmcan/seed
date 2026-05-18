from seed.shorts import (
    build_frame_notes,
    build_motion_relations_artifact,
    build_short_video_profile,
    build_shots_artifact,
    frame_notes_output_path,
    motion_relations_output_path,
    normalize_boundaries,
    normalize_frame_motion_provider,
    normalize_ocr_provider,
    parse_frame_rate,
    short_profile_output_path,
    shots_output_path,
)


def test_short_artifact_paths(tmp_path):
    assert short_profile_output_path(library_root=tmp_path, title="Demo 短视频") == (
        tmp_path / "shorts" / "demo-短视频.short-video-profile.json"
    )
    assert shots_output_path(library_root=tmp_path, title="Demo 短视频") == (
        tmp_path / "shots" / "demo-短视频.shots.json"
    )
    assert frame_notes_output_path(library_root=tmp_path, title="Demo 短视频") == (
        tmp_path / "frames" / "demo-短视频.frame-notes.jsonl"
    )
    assert motion_relations_output_path(library_root=tmp_path, title="Demo 短视频") == (
        tmp_path / "shots" / "demo-短视频.motion-relations.json"
    )


def test_parse_frame_rate():
    assert parse_frame_rate("30000/1001") == 29.97
    assert parse_frame_rate("25/1") == 25.0
    assert parse_frame_rate("0/0") is None


def test_normalize_boundaries():
    assert normalize_boundaries([0.02, 1.5, 3.0, 9.99], duration=10.0) == [0.0, 1.5, 3.0, 10.0]
    assert normalize_boundaries([], duration=8.0) == [0.0, 8.0]


def test_build_shots_artifact_uses_representative_frames(tmp_path, monkeypatch):
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")

    def fake_detect_scene_cut_points(media_path, *, threshold):
        return [2.0, 4.0]

    def fake_extract_representative_frame(*, media_path, output_dir, index, timestamp_seconds):
        path = output_dir / f"shot_{index:04d}.jpg"
        path.write_bytes(b"jpg")
        return path

    monkeypatch.setattr("seed.shorts.detect_scene_cut_points", fake_detect_scene_cut_points)
    monkeypatch.setattr("seed.shorts.extract_representative_frame", fake_extract_representative_frame)

    artifact = build_shots_artifact(
        media_path=media,
        title="Demo",
        profile={"duration_seconds": 6.0},
        library_root=tmp_path / "library",
    )

    assert len(artifact["shots"]) == 3
    assert artifact["shots"][0]["start_seconds"] == 0.0
    assert artifact["shots"][0]["end_seconds"] == 2.0
    assert artifact["shots"][1]["representative_seconds"] == 3.0
    assert artifact["shots"][2]["transition_type"] == "cut"


def test_build_short_video_profile_can_be_short(monkeypatch, tmp_path):
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")

    monkeypatch.setattr(
        "seed.shorts.probe_video",
        lambda media_path: {
            "duration_seconds": 30.0,
            "fps": 30.0,
            "width": 1080,
            "height": 1920,
            "has_audio": True,
        },
    )

    profile = build_short_video_profile(media_path=media, title="Demo", platform="bilibili")

    assert profile["is_short_form"] is True
    assert profile["is_vertical"] is True
    assert profile["aspect_ratio"] == 0.5625


def test_build_frame_notes_from_shot_keyframes(tmp_path, monkeypatch):
    frame = tmp_path / "shot.jpg"
    frame.write_bytes(b"jpg")
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")

    monkeypatch.setattr("seed.shorts.probe_image", lambda path: {"width": 100, "height": 200})

    notes = build_frame_notes(
        media_path=media,
        title="Demo",
        profile={"duration_seconds": 5.0},
        shots_artifact={
            "shots": [
                {
                    "id": "shot-001",
                    "index": 1,
                    "representative_seconds": 2.5,
                    "representative_frame_path": str(frame),
                }
            ]
        },
        library_root=tmp_path / "library",
    )

    assert len(notes) == 1
    assert notes[0]["timestamp_seconds"] == 2.5
    assert notes[0]["shot_id"] == "shot-001"
    assert notes[0]["image"] == {"width": 100, "height": 200}
    assert notes[0]["status"] == "pending_vl"
    assert notes[0]["ocr_status"] == "not_configured"


def test_build_frame_notes_enriches_ocr_from_sidecar_json(tmp_path, monkeypatch):
    frame = tmp_path / "shot.jpg"
    frame.write_bytes(b"jpg")
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")
    ocr_path = tmp_path / "ocr.json"
    ocr_path.write_text(
        """
        {
          "segments": [
            {
              "id": "ocr-1",
              "start_seconds": 2.0,
              "end_seconds": 3.0,
              "text": "Hello Seed",
              "bbox": [10, 20, 120, 40],
              "confidence": 0.91
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    monkeypatch.setattr("seed.shorts.probe_image", lambda path: {"width": 100, "height": 200})

    notes = build_frame_notes(
        media_path=media,
        title="Demo",
        profile={"duration_seconds": 5.0},
        shots_artifact={
            "shots": [
                {
                    "id": "shot-001",
                    "index": 1,
                    "representative_seconds": 2.5,
                    "representative_frame_path": str(frame),
                }
            ]
        },
        library_root=tmp_path / "library",
        ocr_provider="sidecar-json",
        ocr_path=ocr_path,
    )

    assert notes[0]["ocr_provider"] == "sidecar-json"
    assert notes[0]["ocr_status"] == "matched"
    assert notes[0]["ocr_text"] == "Hello Seed"
    assert notes[0]["subtitle"]["present"] is True
    assert notes[0]["subtitle"]["position"] == [10, 20, 120, 40]
    assert notes[0]["visual_effects"]["text_overlay"]["segments"] == 1
    assert notes[0]["status"] == "pending_vl_ocr_enriched"


def test_build_frame_notes_enriches_frame_motion(tmp_path, monkeypatch):
    frame_one = tmp_path / "shot1.jpg"
    frame_two = tmp_path / "shot2.jpg"
    frame_one.write_bytes(b"jpg")
    frame_two.write_bytes(b"jpg")
    media = tmp_path / "demo.mp4"
    media.write_bytes(b"video")

    monkeypatch.setattr("seed.shorts.probe_image", lambda path: {"width": 100, "height": 200})
    monkeypatch.setattr("seed.shorts.frame_difference_score", lambda previous, current: 0.42)

    notes = build_frame_notes(
        media_path=media,
        title="Demo",
        profile={"duration_seconds": 5.0},
        shots_artifact={
            "shots": [
                {
                    "id": "shot-001",
                    "index": 1,
                    "representative_seconds": 1.0,
                    "representative_frame_path": str(frame_one),
                },
                {
                    "id": "shot-002",
                    "index": 2,
                    "representative_seconds": 2.0,
                    "representative_frame_path": str(frame_two),
                },
            ]
        },
        library_root=tmp_path / "library",
        frame_motion_provider="ffmpeg-diff",
    )

    assert notes[0]["frame_motion_status"] == "baseline_start"
    assert notes[1]["frame_motion_status"] == "measured"
    assert notes[1]["frame_delta"]["score"] == 0.42
    assert notes[1]["frame_delta"]["intensity"] == "high"
    assert notes[1]["editing"]["camera_motion"]["needs_provider"] == ["optical_flow", "pose", "vl"]


def test_normalize_ocr_provider_rejects_unknown_provider():
    assert normalize_ocr_provider("sidecar-json") == "sidecar-json"
    try:
        normalize_ocr_provider("heavy-default")
    except ValueError as error:
        assert "Unsupported OCR provider" in str(error)
    else:
        raise AssertionError("unknown OCR provider should fail")


def test_normalize_frame_motion_provider_rejects_unknown_provider():
    assert normalize_frame_motion_provider("ffmpeg-diff") == "ffmpeg-diff"
    try:
        normalize_frame_motion_provider("opencv")
    except ValueError as error:
        assert "Unsupported frame motion provider" in str(error)
    else:
        raise AssertionError("unknown frame motion provider should fail")


def test_build_motion_relations_artifact_creates_traceable_candidates():
    artifact = build_motion_relations_artifact(
        title="Demo",
        profile={"media_path": "demo.mp4"},
        shots_artifact={"shots": [{"id": "shot-001"}, {"id": "shot-002"}]},
        frame_notes=[
            {
                "index": 1,
                "timestamp_seconds": 0.5,
                "frame_path": "frame_1.jpg",
                "shot_id": "shot-001",
                "subtitle": {"present": None},
                "visual_effects": {"sticker": None},
                "editing": {"transition": None},
            },
            {
                "index": 2,
                "timestamp_seconds": 1.5,
                "frame_path": "frame_2.jpg",
                "shot_id": "shot-002",
                "subtitle": {"present": None},
                "visual_effects": {"sticker": None},
                "editing": {"transition": None},
            },
        ],
    )

    assert artifact["provider"] == "schema-baseline"
    assert artifact["capabilities"]["pose_keypoints"] is False
    assert artifact["capabilities"]["frame_difference"] is False
    assert artifact["shots_count"] == 2
    assert artifact["frame_notes_count"] == 2
    assert len(artifact["relations"]) == 1
    relation = artifact["relations"][0]
    assert relation["status"] == "needs_pose_or_vl"
    assert relation["source_frame_paths"] == ["frame_1.jpg", "frame_2.jpg"]
    assert "pose" in relation["needs_provider"]


def test_build_motion_relations_reports_frame_difference_capability():
    artifact = build_motion_relations_artifact(
        title="Demo",
        profile={"media_path": "demo.mp4"},
        shots_artifact={"shots": [{"id": "shot-001"}, {"id": "shot-002"}]},
        frame_notes=[
            {
                "index": 1,
                "timestamp_seconds": 0.5,
                "frame_path": "frame_1.jpg",
                "shot_id": "shot-001",
                "subtitle": {"present": None},
                "visual_effects": {"sticker": None},
                "editing": {"camera_motion": {"intensity": "high"}},
                "frame_motion_status": "measured",
                "frame_delta": {"score": 0.42, "intensity": "high"},
            },
            {
                "index": 2,
                "timestamp_seconds": 1.5,
                "frame_path": "frame_2.jpg",
                "shot_id": "shot-002",
                "subtitle": {"present": None},
                "visual_effects": {"sticker": None},
                "editing": {"camera_motion": {"intensity": "medium"}},
                "frame_motion_status": "measured",
                "frame_delta": {"score": 0.22, "intensity": "medium"},
            },
        ],
    )

    assert artifact["capabilities"]["frame_difference"] is True
    assert artifact["relations"][0]["observed"]["frame_delta"][1]["score"] == 0.22
