from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seed.dag_export import video_dag_html_output_path
from seed.graphs.video_dag import count_frames, list_frame_paths, resolve_video_dag_artifacts, video_dag_output_path
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
    library_root: Path | None = None,
    creator_profile_path: Path | None = None,
    skill_paths: list[Path] | None = None,
    check_paths: list[Path] | None = None,
    validation_path: Path | None = None,
    cost_ledger_path: Path | None = None,
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
        node(
            "profile-validation",
            "asset",
            "Profile Evidence Validation",
            "检查 creator profile 中的强结论是否带视频、timestamp、keyframe、transcript chunk 或 provisional 标记。",
            720,
            220,
            [path_metric(validation_path)],
            validation_path,
        ),
        node(
            "cost-ledger",
            "asset",
            "Creator Cost Ledger",
            "汇总创作者级 pipeline 的视频分析成本，并为预算门槛提供依据。",
            720,
            420,
            [path_metric(cost_ledger_path)],
            cost_ledger_path,
        ),
    ]
    edges = [
        ["creator", "profile"],
        ["profile", "agent-assets"],
        ["profile", "profile-validation"],
        ["creator", "cost-ledger"],
    ]

    for index, semantics_path in enumerate(semantics_paths, start=1):
        title = video_title_from_semantics(semantics_path) or semantics_path.stem.removesuffix(
            ".video-semantics"
        )
        video_id = f"video-{index:03d}"
        artifacts = resolve_creator_video_artifacts(
            library_root=library_root,
            title=title,
            semantics_path=semantics_path,
        )
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
        media_nodes, media_edges = build_creator_video_media_nodes(
            video_id=video_id,
            title=title,
            artifacts=artifacts,
            index=index,
        )
        nodes.extend(media_nodes)
        edges.extend(media_edges)

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
    validation_candidates = sorted(distilled.glob(f"*{owner_slug}*.creator-profile.validation.json"))
    cost_candidates = sorted((library_root / "costs").glob(f"*{owner_slug}*.ledger.json"))
    skills_dir = library_root / "skills"
    checks_dir = library_root / "checks"
    return {
        "creator_profile_path": profile_candidates[-1] if profile_candidates else None,
        "skill_paths": sorted(skills_dir.glob(f"*{owner_slug}*/SKILL.md")),
        "check_paths": sorted(checks_dir.glob(f"*{owner_slug}*.md")),
        "validation_path": validation_candidates[-1] if validation_candidates else None,
        "cost_ledger_path": cost_candidates[-1] if cost_candidates else None,
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
    preview: dict[str, Any] | None = None,
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
    if preview:
        result["preview"] = preview
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


def resolve_creator_video_artifacts(
    *,
    library_root: Path | None,
    title: str,
    semantics_path: Path,
) -> dict[str, Path | None]:
    if library_root is None:
        return {
            "source_path": None,
            "audio_path": None,
            "frame_dir": None,
            "ai_practice_signals_path": None,
            "finance_signals_path": None,
            "video_dag_path": None,
            "video_dag_html_path": None,
        }
    artifacts = resolve_video_dag_artifacts(
        library_root=library_root,
        title=title,
        semantics_path=semantics_path,
    )
    graph_path = video_dag_output_path(library_root=library_root, title=title)
    html_path = video_dag_html_output_path(graph_path=graph_path)
    artifacts["video_dag_path"] = graph_path if graph_path.exists() else None
    artifacts["video_dag_html_path"] = html_path if html_path.exists() else None
    return artifacts


def build_creator_video_media_nodes(
    *,
    video_id: str,
    title: str,
    artifacts: dict[str, Path | None],
    index: int,
) -> tuple[list[dict[str, Any]], list[list[str]]]:
    y = (index - 1) * 300
    source_path = artifacts.get("source_path")
    audio_path = artifacts.get("audio_path")
    frame_dir = artifacts.get("frame_dir")
    ai_practice_signals_path = artifacts.get("ai_practice_signals_path")
    finance_signals_path = artifacts.get("finance_signals_path")
    video_dag_html_path = artifacts.get("video_dag_html_path")
    frame_paths = list_frame_paths(frame_dir)
    nodes: list[dict[str, Any]] = [
        node(
            f"{video_id}-dag",
            "asset",
            "Video DAG HTML",
            f"单条视频的完整证据 DAG，可展开查看 {title} 的视频、音频、截图、timeline、claims 和 cost ledger。",
            -720,
            y,
            [path_metric(video_dag_html_path), "single video DAG"],
            video_dag_html_path,
        ),
        node(
            f"{video_id}-video",
            "source",
            "Video Preview",
            "本地原始视频。UP 级画布中保留它，方便从创作者画像回到具体视频证据。",
            -1080,
            y,
            [path_metric(source_path), "video"],
            source_path,
            preview={"type": "video", "src": str(source_path)} if source_path else None,
        ),
        node(
            f"{video_id}-audio",
            "transcript",
            "Audio Preview",
            "ASR 使用的本地音频，可回听口播节奏、语气和广告段。",
            -1080,
            y + 190,
            [path_metric(audio_path), "audio"],
            audio_path,
            preview={"type": "audio", "src": str(audio_path)} if audio_path else None,
        ),
        node(
            f"{video_id}-frames",
            "frame",
            "Frame Gallery",
            "抽样关键帧截图，用于从创作者级结论回看视觉证据。",
            -1080,
            y + 380,
            [path_metric(frame_dir), f"{count_frames(frame_dir)} frames" if frame_dir else "no frames"],
            frame_dir,
            preview={"type": "gallery", "items": [str(path) for path in frame_paths[:8]]}
            if frame_paths
            else None,
        ),
    ]
    if finance_signals_path:
        nodes.append(
            node(
                f"{video_id}-finance",
                "asset",
                "Finance Signals",
                "单条财经视频中结构化提取的标的、方向、动作、时间窗口、风险控制和证据引用；这些是创作者观点，不是投资建议。",
                -720,
                y + 190,
                [path_metric(finance_signals_path), "not advice"],
                finance_signals_path,
            )
        )
    if ai_practice_signals_path:
        nodes.append(
            node(
                f"{video_id}-ai-practice",
                "asset",
                "AI Practice Signals",
                "单条 AI 方法论视频中结构化提取的实践事件、时代判断、能力信号、个人实验和 Seed 项目反补候选。",
                -720,
                y + 300,
                [path_metric(ai_practice_signals_path), "practice ledger"],
                ai_practice_signals_path,
            )
        )
    edges = [
        [video_id, f"{video_id}-video"],
        [video_id, f"{video_id}-audio"],
        [video_id, f"{video_id}-frames"],
        [video_id, f"{video_id}-dag"],
    ]
    if finance_signals_path:
        edges.append([video_id, f"{video_id}-finance"])
    if ai_practice_signals_path:
        edges.append([video_id, f"{video_id}-ai-practice"])
    return nodes, edges
