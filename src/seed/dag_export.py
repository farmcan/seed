from __future__ import annotations

import json
import os
from pathlib import Path

from seed.library import slugify


DEFAULT_CANVAS_TEMPLATE = Path("tools/video-dag-canvas.html")


def video_dag_html_output_path(*, graph_path: Path, output_dir: Path | None = None) -> Path:
    directory = output_dir or graph_path.parent
    stem = graph_path.name.removesuffix(".video-dag.json").removesuffix(".json")
    return directory / f"{slugify(stem)}.video-dag.html"


def relative_asset_base(*, output_path: Path, repo_root: Path) -> str:
    relative = os.path.relpath(repo_root.resolve(), output_path.parent.resolve())
    return Path(relative).as_posix()


def export_video_dag_html(
    *,
    graph_path: Path,
    output_path: Path,
    template_path: Path = DEFAULT_CANVAS_TEMPLATE,
    asset_base: str,
) -> Path:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")
    payload = "\n".join(
        [
            "<script>",
            f"window.SEED_EMBEDDED_GRAPH = {json.dumps(graph, ensure_ascii=False)};",
            f"window.SEED_ASSET_BASE = {json.dumps(asset_base, ensure_ascii=False)};",
            "window.SEED_DEFAULT_COMPACT = false;",
            "</script>",
        ]
    )
    local_elk_src = f"{asset_base.rstrip('/')}/tools/vendor/elk.bundled.js"
    html = template.replace('src="vendor/elk.bundled.js"', f'src="{local_elk_src}"', 1)
    html = html.replace("  <script>\n", f"  {payload}\n  <script>\n", 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
