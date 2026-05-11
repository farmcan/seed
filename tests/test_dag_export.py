import json
from pathlib import Path

from seed.dag_export import (
    export_video_dag_html,
    relative_asset_base,
    video_dag_html_output_path,
)


def test_video_dag_html_output_path(tmp_path):
    graph = tmp_path / "library" / "graphs" / "法德欧洲大哥之争.video-dag.json"

    assert video_dag_html_output_path(graph_path=graph) == (
        tmp_path / "library" / "graphs" / "法德欧洲大哥之争.video-dag.html"
    )


def test_relative_asset_base_from_library_graphs(tmp_path):
    output = tmp_path / "library" / "graphs" / "demo.video-dag.html"
    output.parent.mkdir(parents=True)

    assert relative_asset_base(output_path=output, repo_root=tmp_path) == "../.."


def test_export_video_dag_html_embeds_graph_and_asset_base(tmp_path):
    graph_path = tmp_path / "demo.video-dag.json"
    graph_path.write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")
    template = tmp_path / "template.html"
    template.write_text(
        '<html><body>\n  <script src="vendor/elk.bundled.js"></script>\n  <script>\nconsole.log("canvas");\n  </script>\n</body></html>',
        encoding="utf-8",
    )

    output = export_video_dag_html(
        graph_path=graph_path,
        output_path=tmp_path / "demo.html",
        template_path=template,
        asset_base="../..",
    )

    html = output.read_text(encoding="utf-8")
    assert "window.SEED_EMBEDDED_GRAPH" in html
    assert '"nodes": []' in html
    assert 'window.SEED_ASSET_BASE = "../..";' in html
    assert "window.SEED_DEFAULT_COMPACT = true;" in html
    assert 'src="../../tools/vendor/elk.bundled.js"' in html


def test_vendored_elkjs_exists():
    assert Path("tools/vendor/elk.bundled.js").exists()
    assert Path("tools/vendor/elkjs-LICENSE.md").exists()
    assert "elkjs@0.11.0" in Path("tools/vendor/README.md").read_text(encoding="utf-8")
