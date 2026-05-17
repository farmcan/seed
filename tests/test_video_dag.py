import json

from seed.graphs.video_dag import (
    build_video_dag_graph,
    resolve_video_dag_artifacts,
    video_dag_output_path,
    write_video_dag_graph,
)


def test_video_dag_output_path(tmp_path):
    assert video_dag_output_path(library_root=tmp_path, title="法德 欧洲") == (
        tmp_path / "graphs" / "法德-欧洲.video-dag.json"
    )


def test_build_video_dag_graph_uses_artifact_paths_and_metadata(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    video = tmp_path / "demo.mp4"
    audio = tmp_path / "demo.asr.mp3"
    frames = tmp_path / "frames" / "demo"
    semantics = tmp_path / "demo.video-semantics.md"
    finance = tmp_path / "demo.finance-signals.json"
    timeline = tmp_path / "demo.timeline.json"
    claims = tmp_path / "demo.claims.json"
    cost = tmp_path / "demo.cost.json"
    short_profile = tmp_path / "demo.short-video-profile.json"
    shots = tmp_path / "demo.shots.json"
    frame_notes = tmp_path / "demo.frame-notes.jsonl"
    motion_relations = tmp_path / "demo.motion-relations.json"
    video.write_bytes(b"video")
    audio.write_bytes(b"audio")
    transcript.write_text("# Transcript\n\n## Chunk 01\n\nhello\n\n## Chunk 02\n\nworld", encoding="utf-8")
    frames.mkdir(parents=True)
    (frames / "frame_0001.jpg").write_bytes(b"jpg")
    semantics.write_text(
        "## Metadata\n\n- Owner: demo-up\n- Platform: bilibili\n\n## Creator Signals\n\n- Teaching style: explain with jokes",
        encoding="utf-8",
    )
    finance.write_text(
        json.dumps(
            {
                "domain": "finance",
                "stance_summary": "Creator is watching semiconductors.",
                "instruments": [{"name": "Semiconductors"}],
                "recommendations": [{"instrument": "Semiconductors", "action": "watch"}],
                "methodology_signals": [{"method": "event catalyst"}],
            }
        ),
        encoding="utf-8",
    )
    timeline.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "kind": "keyframe",
                        "label": "Keyframe 1",
                        "start_seconds": 0,
                        "evidence_path": str(frames / "frame_0001.jpg"),
                        "confidence": "high",
                    },
                    {
                        "kind": "cta",
                        "label": "CTA",
                        "start_seconds": None,
                        "description": "Ask for follow.",
                        "confidence": "medium",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    claims.write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "id": "claim-001",
                        "text": "Claim A.",
                        "status": "unverified",
                        "source_section": "Verbal Language",
                        "evidence_path": str(semantics),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    cost.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "kind": "qwen_vl",
                        "usage": {
                            "input_tokens": 1000,
                            "output_tokens": 200,
                            "total_tokens": 1200,
                        },
                        "estimated_cost": {"amount": 0.001, "currency": "USD"},
                    }
                ],
                "totals": {"USD": 0.001},
            }
        ),
        encoding="utf-8",
    )
    short_profile.write_text(
        json.dumps(
            {
                "is_short_form": True,
                "duration_seconds": 12,
                "fps": 30,
                "width": 1080,
                "height": 1920,
                "is_vertical": True,
            }
        ),
        encoding="utf-8",
    )
    shots.write_text(
        json.dumps(
            {
                "provider": "ffmpeg-scene",
                "threshold": 0.35,
                "shots": [
                    {
                        "start_seconds": 0,
                        "end_seconds": 3,
                        "duration_seconds": 3,
                        "transition_type": "start",
                        "representative_frame_path": str(frames / "frame_0001.jpg"),
                        "confidence": "medium",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    frame_notes.write_text(
        json.dumps(
            {
                "frame_mode": "shot-keyframes",
                "index": 1,
                "timestamp_seconds": 1.5,
                "frame_path": str(frames / "frame_0001.jpg"),
                "shot_id": "shot-001",
                "image": {"width": 1080, "height": 1920},
                "status": "pending_vl",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    motion_relations.write_text(
        json.dumps(
            {
                "provider": "schema-baseline",
                "capabilities": {
                    "person_bbox": False,
                    "pose_keypoints": False,
                    "object_tracking": False,
                    "ocr": False,
                    "optical_flow": False,
                },
                "relations": [
                    {
                        "id": "relation-1",
                        "kind": "temporal_frame_relation",
                        "status": "needs_pose_or_vl",
                        "label": "frame-to-frame motion candidate",
                        "start_seconds": 1.5,
                        "end_seconds": 2.5,
                        "source_frame_indices": [1, 2],
                        "source_frame_paths": [str(frames / "frame_0001.jpg")],
                        "shot_ids": ["shot-001"],
                        "needs_provider": ["pose", "object_tracking", "vl"],
                        "summary": "Need pose or tracking enrichment.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    graph = build_video_dag_graph(
        title="demo",
        source_path=video,
        transcript_path=transcript,
        frame_dir=frames,
        semantics_path=semantics,
        finance_signals_path=finance,
        timeline_path=timeline,
        claims_path=claims,
        cost_path=cost,
        short_profile_path=short_profile,
        shots_path=shots,
        frame_notes_path=frame_notes,
        motion_relations_path=motion_relations,
    )

    assert graph["owner"] == "demo-up"
    assert graph["platform"] == "bilibili"
    transcript_node = next(node for node in graph["nodes"] if node["id"] == "transcript")
    frame_node = next(node for node in graph["nodes"] if node["id"] == "frames")
    video_node = next(node for node in graph["nodes"] if node["id"] == "video-media")
    audio_node = next(node for node in graph["nodes"] if node["id"] == "audio-media")
    creator_signal_node = next(node for node in graph["nodes"] if node["id"] == "creator-signals")
    finance_node = next(node for node in graph["nodes"] if node["id"] == "finance-signals")
    timeline_node = next(node for node in graph["nodes"] if node["id"] == "timeline")
    timeline_event_node = next(node for node in graph["nodes"] if node["id"] == "timeline-event-1")
    cta_event_node = next(node for node in graph["nodes"] if node["id"] == "timeline-event-2")
    factcheck_node = next(node for node in graph["nodes"] if node["id"] == "factcheck")
    cost_node = next(node for node in graph["nodes"] if node["id"] == "costs")
    short_profile_node = next(node for node in graph["nodes"] if node["id"] == "short-profile")
    shots_node = next(node for node in graph["nodes"] if node["id"] == "shots")
    shot_node = next(node for node in graph["nodes"] if node["id"] == "shot-1")
    frame_notes_node = next(node for node in graph["nodes"] if node["id"] == "frame-notes")
    frame_note_node = next(node for node in graph["nodes"] if node["id"] == "frame-note-1")
    motion_relations_node = next(node for node in graph["nodes"] if node["id"] == "motion-relations")
    motion_relation_node = next(node for node in graph["nodes"] if node["id"] == "motion-relation-1")
    assert "2 chunks" in transcript_node["metrics"]
    assert "1 frames" in frame_node["metrics"]
    assert "2 events" in timeline_node["metrics"]
    assert "真实 timeline artifact" in timeline_node["body"]
    assert any(node["id"] == "timeline-event-1" for node in graph["nodes"])
    assert timeline_event_node["media_anchor"]["start_seconds"] == 0
    assert timeline_event_node["media_anchor"]["label"] == "00:00:00"
    assert timeline_event_node["media_anchor"]["video_src"] == str(video)
    assert timeline_event_node["media_anchor"]["audio_src"] == str(audio)
    assert "media_anchor" not in cta_event_node
    assert ["timeline", "timeline-event-1"] in graph["edges"]
    assert "1 claims" in factcheck_node["metrics"]
    assert any(node["id"] == "claim-1" for node in graph["nodes"])
    assert ["factcheck", "claim-1"] in graph["edges"]
    assert "input 1000 tokens" in cost_node["body"]
    assert "短视频" in short_profile_node["body"]
    assert "1 shots" in shots_node["metrics"]
    assert shots_node["preview"]["type"] == "gallery"
    assert shot_node["media_anchor"]["start_seconds"] == 0
    assert "1 frames" in frame_notes_node["metrics"]
    assert frame_notes_node["preview"]["type"] == "gallery"
    assert frame_note_node["media_anchor"]["start_seconds"] == 1
    assert "1 relations" in motion_relations_node["metrics"]
    assert "schema-baseline" in motion_relations_node["metrics"]
    assert motion_relation_node["media_anchor"]["start_seconds"] == 1
    assert ["visual", "costs"] in graph["edges"]
    assert ["short-profile", "shots"] in graph["edges"]
    assert ["shots", "frame-notes"] in graph["edges"]
    assert ["frame-notes", "motion-relations"] in graph["edges"]
    assert ["motion-relations", "semantics"] in graph["edges"]
    assert ["shots", "shot-1"] in graph["edges"]
    assert ["frame-notes", "frame-note-1"] in graph["edges"]
    assert ["motion-relations", "motion-relation-1"] in graph["edges"]
    assert ["costs", "skills"] in graph["edges"]
    assert video_node["preview"]["type"] == "video"
    assert audio_node["preview"]["type"] == "audio"
    assert frame_node["preview"]["type"] == "gallery"
    assert "Teaching style" in creator_signal_node["body"]
    assert "1 recs" in finance_node["metrics"]
    assert "Creator is watching semiconductors" in finance_node["body"]
    assert ["semantics", "finance-signals"] in graph["edges"]
    assert ["finance-signals", "creator-signals"] in graph["edges"]
    assert ["timeline", "semantics"] in graph["edges"]
    assert ["creator-signals", "creator"] in graph["edges"]


def test_write_video_dag_graph(tmp_path):
    path = write_video_dag_graph(tmp_path / "graph.json", {"nodes": [], "edges": []})

    assert json.loads(path.read_text(encoding="utf-8")) == {"nodes": [], "edges": []}


def test_resolve_video_dag_artifacts_by_title(tmp_path):
    raw = tmp_path / "raw"
    transcripts = tmp_path / "transcripts"
    frames = tmp_path / "frames"
    notes = tmp_path / "notes"
    semantics = tmp_path / "semantics"
    timelines = tmp_path / "timelines"
    claims = tmp_path / "claims"
    costs = tmp_path / "costs"
    shots = tmp_path / "shots"
    for directory in [raw, transcripts, frames, notes, semantics, timelines, claims, costs, shots]:
        directory.mkdir()
    video = raw / "bilibili-bv-demo-法德欧洲大哥之争.mp4"
    audio = raw / "bilibili-bv-demo-法德欧洲大哥之争.asr.mp3"
    transcript = transcripts / "法德欧洲大哥之争.transcript.md"
    frame_dir = frames / "bilibili-bv-demo-法德欧洲大哥之争"
    visual = notes / "法德欧洲大哥之争.visual.md"
    semantic = semantics / "法德欧洲大哥之争.video-semantics.md"
    finance = semantics / "法德欧洲大哥之争.finance-signals.json"
    timeline = timelines / "法德欧洲大哥之争.timeline.json"
    claim = claims / "法德欧洲大哥之争.claims.json"
    verified_claim = claims / "法德欧洲大哥之争.verified.json"
    cost = costs / "法德欧洲大哥之争.cost.json"
    motion_relations = shots / "法德欧洲大哥之争.motion-relations.json"
    for path in [
        video,
        audio,
        transcript,
        visual,
        semantic,
        finance,
        timeline,
        claim,
        verified_claim,
        cost,
        motion_relations,
    ]:
        path.write_text("x", encoding="utf-8")
    frame_dir.mkdir()

    artifacts = resolve_video_dag_artifacts(
        library_root=tmp_path,
        title="法德欧洲大哥之争",
    )

    assert artifacts == {
        "source_path": video,
        "audio_path": audio,
        "transcript_path": transcript,
        "frame_dir": frame_dir,
        "visual_notes_path": visual,
        "semantics_path": semantic,
        "finance_signals_path": finance,
        "news_facts_path": None,
        "earnings_analysis_path": None,
        "timeline_path": timeline,
        "claims_path": verified_claim,
        "cost_path": cost,
        "creator_profile_path": None,
        "short_profile_path": None,
        "shots_path": None,
        "frame_notes_path": None,
        "motion_relations_path": motion_relations,
    }
