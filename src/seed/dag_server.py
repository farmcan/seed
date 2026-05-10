from __future__ import annotations

import functools
import http.server
import webbrowser
from pathlib import Path
from urllib.parse import quote


def video_dag_canvas_url(
    *,
    graph_path: Path,
    repo_root: Path,
    host: str,
    port: int,
) -> str:
    relative_graph = graph_path.resolve().relative_to(repo_root.resolve())
    graph_from_tools = Path("..") / relative_graph
    return (
        f"http://{host}:{port}/tools/video-dag-canvas.html"
        f"?graph={quote(graph_from_tools.as_posix())}"
    )


def serve_video_dag(
    *,
    graph_path: Path,
    repo_root: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(repo_root),
    )
    with http.server.ThreadingHTTPServer((host, port), handler) as server:
        actual_port = int(server.server_address[1])
        url = video_dag_canvas_url(
            graph_path=graph_path,
            repo_root=repo_root,
            host=host,
            port=actual_port,
        )
        print(f"Serving Seed video DAG at {url}", flush=True)
        if open_browser:
            webbrowser.open(url)
        server.serve_forever()
