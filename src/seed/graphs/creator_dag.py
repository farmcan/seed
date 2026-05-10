from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.markdown import find_markdown_field


def creator_dag_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "graphs" / f"{slugify(owner)}.creator-dag.json"


def creator_dag_html_output_path(*, graph_path: Path) -> Path:
    return graph_path.with_suffix(".html")


def build_creator_dag_graph(
    *,
    owner: str,
    semantics_paths: list[Path],
    creator_profile_path: Path | None = None,
    skill_paths: list[Path] | None = None,
    check_paths: list[Path] | None = None,
) -> dict[str, Any]:
    nodes = [
        node(
            "creator",
            "creator",
            f"Creator: {owner}",
            "UP/作者级聚合入口，用来查看多条视频的共性方法论、表达结构、证据和 Agent 资产。",
            0,
            0,
            [f"{len(semantics_paths)} videos"],
            creator_profile_path,
        ),
        node(
            "profile",
            "semantics",
            "Creator Profile",
            "跨视频聚合画像。每个稳定结论都应能回溯到具体视频语义、timeline、关键帧或 transcript chunk。",
            360,
            0,
            [path_metric(creator_profile_path)],
            creator_profile_path,
        ),
        node(
            "agent-assets",
            "asset",
            "Agent Assets",
            "从 creator profile 生成的 draft skills、pre-check 和 reflection 资产；人工 review 后才应安装使用。",
            720,
            0,
            [
                f"{len(skill_paths or [])} skills",
                f"{len(check_paths or [])} checks",
            ],
            None,
        ),
    ]
    edges = [["creator", "profile"], ["profile", "agent-assets"]]

    for index, semantics_path in enumerate(semantics_paths, start=1):
        title = video_title_from_semantics(semantics_path) or semantics_path.stem.removesuffix(
            ".video-semantics"
        )
        video_id = f"video-{index:03d}"
        nodes.append(
            node(
                video_id,
                "semantics",
                title,
                video_summary_from_semantics(semantics_path),
                -360,
                (index - 1) * 180,
                [path_metric(semantics_path), "video semantics"],
                semantics_path,
            )
        )
        edges.append([video_id, "creator"])

    for index, skill_path in enumerate(skill_paths or [], start=1):
        skill_id = f"skill-{index:03d}"
        nodes.append(
            node(
                skill_id,
                "asset",
                skill_path.name,
                "候选 skill。默认是 draft，必须人工 review 后再安装。",
                1080,
                (index - 1) * 160,
                [path_metric(skill_path)],
                skill_path,
            )
        )
        edges.append(["agent-assets", skill_id])

    for index, check_path in enumerate(check_paths or [], start=1):
        check_id = f"check-{index:03d}"
        nodes.append(
            node(
                check_id,
                "asset",
                check_path.name,
                "候选 check/reflection 资产。默认是 draft。",
                1080,
                360 + (index - 1) * 160,
                [path_metric(check_path)],
                check_path,
            )
        )
        edges.append(["agent-assets", check_id])

    return {
        "version": 1,
        "kind": "creator-dag",
        "owner": owner,
        "nodes": nodes,
        "edges": edges,
    }


def write_creator_dag_graph(path: Path, graph: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def find_creator_asset_paths(*, library_root: Path, owner: str) -> dict[str, list[Path] | Path | None]:
    owner_slug = slugify(owner)
    distilled = library_root / "distilled"
    profile_candidates = sorted(distilled.glob(f"*{owner_slug}*.creator-profile.md"))
    skills_dir = library_root / "skills"
    checks_dir = library_root / "checks"
    return {
        "creator_profile_path": profile_candidates[-1] if profile_candidates else None,
        "skill_paths": sorted(skills_dir.glob(f"*{owner_slug}*/SKILL.md")),
        "check_paths": sorted(checks_dir.glob(f"*{owner_slug}*.md")),
    }


def node(
    node_id: str,
    node_type: str,
    title: str,
    body: str,
    x: int,
    y: int,
    metrics: list[str],
    path: Path | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": node_id,
        "type": node_type,
        "title": title,
        "body": body,
        "x": x,
        "y": y,
        "metrics": [metric for metric in metrics if metric and metric != "missing"],
    }
    if path:
        result["path"] = str(path)
    return result


def video_title_from_semantics(path: Path) -> str | None:
    return find_markdown_field(path.read_text(encoding="utf-8"), "title")


def video_summary_from_semantics(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = [
        line.strip(" -")
        for line in text.splitlines()
        if line.strip() and not line.startswith("---") and not line.startswith("## ")
    ]
    summary = " ".join(lines[:8])
    return summary[:520] + ("..." if len(summary) > 520 else "")


def path_metric(path: Path | None) -> str:
    if not path:
        return "missing"
    return path.name if path.exists() else f"missing: {path.name}"
