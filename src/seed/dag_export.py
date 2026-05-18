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


def pipeline_live_dag_html_output_path(*, status_path: Path, output_dir: Path | None = None) -> Path:
    directory = output_dir or status_path.parent
    stem = status_path.name.removesuffix(".video-pipeline.status.json").removesuffix(".status.json")
    return directory / f"{slugify(stem)}.video-pipeline.live.html"


def relative_asset_base(*, output_path: Path, repo_root: Path) -> str:
    relative = os.path.relpath(repo_root.resolve(), output_path.parent.resolve())
    return Path(relative).as_posix()


def export_video_dag_html(
    *,
    graph_path: Path,
    output_path: Path,
    template_path: Path = DEFAULT_CANVAS_TEMPLATE,
    asset_base: str,
    default_compact: bool = True,
    status_path: Path | None = None,
    status_url: str | None = None,
    live_status: bool = False,
) -> Path:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    return export_video_dag_html_from_graph(
        graph=graph,
        output_path=output_path,
        template_path=template_path,
        asset_base=asset_base,
        default_compact=default_compact,
        status_path=status_path,
        status_url=status_url,
        live_status=live_status,
    )


def export_pipeline_live_dag_html(
    *,
    status_path: Path,
    output_path: Path,
    template_path: Path = DEFAULT_CANVAS_TEMPLATE,
    asset_base: str,
    status_url: str | None = None,
    live_status: bool = True,
) -> Path:
    status = json.loads(status_path.read_text(encoding="utf-8"))
    graph = build_pipeline_status_graph(status)
    return export_video_dag_html_from_graph(
        graph=graph,
        output_path=output_path,
        template_path=template_path,
        asset_base=asset_base,
        default_compact=False,
        status_path=status_path,
        status_url=status_url,
        live_status=live_status,
    )


def export_video_dag_html_from_graph(
    *,
    graph: dict,
    output_path: Path,
    template_path: Path = DEFAULT_CANVAS_TEMPLATE,
    asset_base: str,
    default_compact: bool = True,
    status_path: Path | None = None,
    status_url: str | None = None,
    live_status: bool = False,
) -> Path:
    embedded_status = (
        json.loads(status_path.read_text(encoding="utf-8"))
        if status_path and status_path.exists()
        else None
    )
    template = template_path.read_text(encoding="utf-8")
    payload = "\n".join(
        [
            "<script>",
            f"window.SEED_EMBEDDED_GRAPH = {json.dumps(graph, ensure_ascii=False)};",
            f"window.SEED_ASSET_BASE = {json.dumps(asset_base, ensure_ascii=False)};",
            f"window.SEED_DEFAULT_COMPACT = {json.dumps(default_compact)};",
            f"window.SEED_EMBEDDED_STATUS = {json.dumps(embedded_status, ensure_ascii=False)};",
            f"window.SEED_STATUS_URL = {json.dumps(status_url, ensure_ascii=False)};",
            f"window.SEED_LIVE_STATUS = {json.dumps(live_status)};",
            "</script>",
        ]
    )
    local_elk_src = f"{asset_base.rstrip('/')}/tools/vendor/elk.bundled.js"
    html = template.replace('src="vendor/elk.bundled.js"', f'src="{local_elk_src}"', 1)
    html = html.replace("  <script>\n", f"  {payload}\n  <script>\n", 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def build_pipeline_status_graph(status: dict) -> dict:
    steps = status.get("steps") or []
    nodes = []
    edges = []
    for index, step in enumerate(steps):
        step_id = str(step.get("step") or f"step-{index + 1}")
        nodes.append(
            {
                "id": step_id,
                "type": "asset",
                "title": step_title(step_id),
                "body": pipeline_step_body(step),
                "x": index * 320,
                "y": 0,
                "metrics": pipeline_step_metrics(step),
                "path": first_artifact_path(step),
                "pipeline_step": step_id,
                "run_status": step.get("status") or "pending",
            }
        )
        if index > 0:
            previous_id = str(steps[index - 1].get("step") or f"step-{index}")
            edges.append([previous_id, step_id])
    return {
        "version": 1,
        "title": status.get("title") or "Pipeline Run",
        "owner": status.get("owner") or "unknown",
        "platform": status.get("platform") or "unknown",
        "nodes": nodes,
        "edges": edges,
    }


def step_title(step_id: str) -> str:
    return step_id.replace("_", " ").title()


def pipeline_step_body(step: dict) -> str:
    status = step.get("status") or "pending"
    duration = step.get("duration_seconds")
    elapsed = step.get("elapsed_seconds")
    estimate = step.get("estimated_duration_seconds")
    remaining = step.get("remaining_estimated_seconds")
    artifacts = step.get("artifact_paths") or []
    message = step.get("message")
    error = step.get("error")
    parts = [f"status={status}"]
    if duration is not None:
        parts.append(f"duration={duration}s")
    elif elapsed is not None:
        parts.append(f"elapsed={elapsed}s")
    if estimate is not None:
        parts.append(f"estimate={estimate}s")
    if remaining is not None and status in {"pending", "running"}:
        parts.append(f"remaining={remaining}s")
    if artifacts:
        parts.append(f"artifacts={len(artifacts)}")
    if message:
        parts.append(f"message={message}")
    if error:
        parts.append(f"error={error}")
    return "；".join(parts) + "。"


def pipeline_step_metrics(step: dict) -> list[str]:
    metrics = [str(step.get("status") or "pending")]
    duration = step.get("duration_seconds")
    if duration is not None:
        metrics.append(f"{duration}s")
    elif step.get("elapsed_seconds") is not None:
        metrics.append(f"{step.get('elapsed_seconds')}s elapsed")
    if step.get("estimated_duration_seconds") is not None:
        metrics.append(f"~{step.get('estimated_duration_seconds')}s")
    provider = step.get("provider")
    if provider:
        metrics.append(str(provider))
    artifacts = step.get("artifact_paths") or []
    if artifacts:
        metrics.append(f"{len(artifacts)} artifacts")
    return metrics


def first_artifact_path(step: dict) -> str | None:
    artifacts = step.get("artifact_paths") or []
    return str(artifacts[0]) if artifacts else None
