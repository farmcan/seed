import json

from seed.graphs.video_dag import build_video_dag_graph, video_dag_output_path, write_video_dag_graph


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
    video.write_bytes(b"video")
    audio.write_bytes(b"audio")
    transcript.write_text("# Transcript\n\n## Chunk 01\n\nhello\n\n## Chunk 02\n\nworld", encoding="utf-8")
    frames.mkdir(parents=True)
    (frames / "frame_0001.jpg").write_bytes(b"jpg")
    semantics.write_text(
        "## Metadata\n\n- Owner: demo-up\n- Platform: bilibili\n\n## Creator Signals\n\n- Teaching style: explain with jokes",
        encoding="utf-8",
    )

    graph = build_video_dag_graph(
        title="demo",
        source_path=video,
        transcript_path=transcript,
        frame_dir=frames,
        semantics_path=semantics,
    )

    assert graph["owner"] == "demo-up"
    assert graph["platform"] == "bilibili"
    transcript_node = next(node for node in graph["nodes"] if node["id"] == "transcript")
    frame_node = next(node for node in graph["nodes"] if node["id"] == "frames")
    video_node = next(node for node in graph["nodes"] if node["id"] == "video-media")
    audio_node = next(node for node in graph["nodes"] if node["id"] == "audio-media")
    creator_signal_node = next(node for node in graph["nodes"] if node["id"] == "creator-signals")
    assert "2 chunks" in transcript_node["metrics"]
    assert "1 frames" in frame_node["metrics"]
    assert video_node["preview"]["type"] == "video"
    assert audio_node["preview"]["type"] == "audio"
    assert frame_node["preview"]["type"] == "gallery"
    assert "Teaching style" in creator_signal_node["body"]
    assert ["timeline", "semantics"] in graph["edges"]
    assert ["creator-signals", "creator"] in graph["edges"]


def test_write_video_dag_graph(tmp_path):
    path = write_video_dag_graph(tmp_path / "graph.json", {"nodes": [], "edges": []})

    assert json.loads(path.read_text(encoding="utf-8")) == {"nodes": [], "edges": []}
