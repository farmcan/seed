from seed.shorts import (
    build_frame_notes,
    build_motion_relations_artifact,
    build_short_video_profile,
    build_shots_artifact,
    frame_notes_output_path,
    motion_relations_output_path,
    normalize_boundaries,
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
    assert artifact["shots_count"] == 2
    assert artifact["frame_notes_count"] == 2
    assert len(artifact["relations"]) == 1
    relation = artifact["relations"][0]
    assert relation["status"] == "needs_pose_or_vl"
    assert relation["source_frame_paths"] == ["frame_1.jpg", "frame_2.jpg"]
    assert "pose" in relation["needs_provider"]
