from seed.dag_server import video_dag_canvas_url


def test_video_dag_canvas_url(tmp_path):
    graph_path = tmp_path / "library" / "graphs" / "demo graph.video-dag.json"
    graph_path.parent.mkdir(parents=True)
    graph_path.write_text("{}", encoding="utf-8")

    url = video_dag_canvas_url(
        graph_path=graph_path,
        repo_root=tmp_path,
        host="127.0.0.1",
        port=8765,
    )

    assert url == (
        "http://127.0.0.1:8765/tools/video-dag-canvas.html"
        "?graph=../library/graphs/demo%20graph.video-dag.json"
    )
