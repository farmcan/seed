import json

from seed.graphs.video_dag import build_video_dag_graph, video_dag_output_path, write_video_dag_graph


def test_video_dag_output_path(tmp_path):
    assert video_dag_output_path(library_root=tmp_path, title="法德 欧洲") == (
        tmp_path / "graphs" / "法德-欧洲.video-dag.json"
    )


def test_build_video_dag_graph_uses_artifact_paths_and_metadata(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    frames = tmp_path / "frames" / "demo"
    semantics = tmp_path / "demo.video-semantics.md"
    transcript.write_text("# Transcript\n\n## Chunk 01\n\nhello\n\n## Chunk 02\n\nworld", encoding="utf-8")
    frames.mkdir(parents=True)
    (frames / "frame_0001.jpg").write_bytes(b"jpg")
    semantics.write_text("## Metadata\n\n- Owner: demo-up\n- Platform: bilibili\n", encoding="utf-8")

    graph = build_video_dag_graph(
        title="demo",
        transcript_path=transcript,
        frame_dir=frames,
        semantics_path=semantics,
    )

    assert graph["owner"] == "demo-up"
    assert graph["platform"] == "bilibili"
    transcript_node = next(node for node in graph["nodes"] if node["id"] == "transcript")
    frame_node = next(node for node in graph["nodes"] if node["id"] == "frames")
    assert "2 chunks" in transcript_node["metrics"]
    assert "1 frames" in frame_node["metrics"]
    assert ["timeline", "semantics"] in graph["edges"]


def test_write_video_dag_graph(tmp_path):
    path = write_video_dag_graph(tmp_path / "graph.json", {"nodes": [], "edges": []})

    assert json.loads(path.read_text(encoding="utf-8")) == {"nodes": [], "edges": []}
