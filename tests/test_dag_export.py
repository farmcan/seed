import json
from pathlib import Path

from seed.dag_export import (
    export_pipeline_live_dag_html,
    export_video_dag_html,
    pipeline_live_dag_html_output_path,
    relative_asset_base,
    video_dag_html_output_path,
)


def test_video_dag_html_output_path(tmp_path):
    graph = tmp_path / "library" / "graphs" / "法德欧洲大哥之争.video-dag.json"

    assert video_dag_html_output_path(graph_path=graph) == (
        tmp_path / "library" / "graphs" / "法德欧洲大哥之争.video-dag.html"
    )


def test_pipeline_live_dag_html_output_path(tmp_path):
    status = tmp_path / "library" / "runs" / "demo.video-pipeline.status.json"

    assert pipeline_live_dag_html_output_path(status_path=status) == (
        tmp_path / "library" / "runs" / "demo.video-pipeline.live.html"
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
    assert "window.SEED_EMBEDDED_STATUS = null;" in html
    assert "window.SEED_LIVE_STATUS = false;" in html
    assert 'src="../../tools/vendor/elk.bundled.js"' in html


def test_export_pipeline_live_dag_html_embeds_status_graph(tmp_path):
    status_path = tmp_path / "demo.video-pipeline.status.json"
    status_path.write_text(
        json.dumps(
            {
                "kind": "video_pipeline_status",
                "status": "running",
                "title": "Demo",
                "owner": "owner",
                "platform": "manual",
                "steps": [
                    {
                        "step": "source",
                        "status": "completed",
                        "duration_seconds": 0.1,
                        "artifact_paths": ["library/raw/demo.mp4"],
                    },
                    {
                        "step": "transcribe",
                        "status": "running",
                        "duration_seconds": None,
                        "artifact_paths": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    template = tmp_path / "template.html"
    template.write_text(
        '<html><body>\n  <script src="vendor/elk.bundled.js"></script>\n  <script>\nconsole.log("canvas");\n  </script>\n</body></html>',
        encoding="utf-8",
    )

    output = export_pipeline_live_dag_html(
        status_path=status_path,
        output_path=tmp_path / "demo.live.html",
        template_path=template,
        asset_base="..",
        status_url="demo.video-pipeline.status.json",
    )

    html = output.read_text(encoding="utf-8")
    assert '"id": "source"' in html
    assert '"pipeline_step": "transcribe"' in html
    assert '"run_status": "running"' in html
    assert 'window.SEED_STATUS_URL = "demo.video-pipeline.status.json";' in html
    assert "window.SEED_LIVE_STATUS = true;" in html


def test_vendored_elkjs_exists():
    assert Path("tools/vendor/elk.bundled.js").exists()
    assert Path("tools/vendor/elkjs-LICENSE.md").exists()
    assert "elkjs@0.11.0" in Path("tools/vendor/README.md").read_text(encoding="utf-8")
